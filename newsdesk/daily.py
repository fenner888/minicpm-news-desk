"""Public reference workflow. Every network, inference and send is explicit."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import time
from zoneinfo import ZoneInfo
from . import core, digest as d, feeds, facts, network, presentation, quickhits, selector, telegram, workflow as w


def checked_file(path):
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:
        raise ValueError('private_regular_file_required')


@contextmanager
def locked(root):
    if os.name!='posix':raise ValueError('reference_workflow_requires_posix')
    import fcntl
    root=Path(root).absolute()
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    info=root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:
        raise ValueError('private_state_directory_required')
    fd=os.open(root/'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    store=None
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for path in root.iterdir():
            if path.is_symlink():raise ValueError('state_symlink_forbidden')
        settings_path=root/'settings.json'
        if not settings_path.exists():raise ValueError('initialize_state_first')
        checked_file(settings_path);settings=w.read_json(settings_path,4000)
        if set(settings)!={'title','timezone'}:raise ValueError('invalid_settings')
        d.split_parts(['Settings check'],settings['title'])
        zone=ZoneInfo(settings['timezone'])
        db=root/'archive.sqlite3'
        if db.exists():checked_file(db)
        store=d.Store(db,zone=zone)
        yield root,store,settings
    finally:
        if store is not None:store.close()
        os.close(fd)


def initialize(root,title,timezone):
    ZoneInfo(timezone);d.split_parts(['Settings check'],title)
    root=Path(root).absolute()
    # Refuse existing directories: init must never overwrite another deployment.
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    w.save(root/'settings.json',{'title':title,'timezone':timezone})
    with locked(root) as (_,store,_):store.initialize(time.time())
    return {'status':'initialized','state':str(root),'network_calls':0}


def set_meta(store,key,value):
    with store.db:store.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',(key,json.dumps(value)))


def get_meta(store,key):
    row=store.db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
    return json.loads(row[0]) if row else None


def collect(root,store,sources,now,get=feeds.fetch):
    if not sources or len(sources)!=len(set(sources)) or any(s not in feeds.FEEDS for s in sources):
        raise ValueError('invalid_feed_selection')
    receipt={'observed_at':now,'sources':{}}
    for source in sources:
        receipt['sources'][source]={'status':'reserved'}
        set_meta(store,'collection',receipt)
        try:
            result=feeds.parse(source,get(source),now)
            count=store.ingest(result['items'],now)
            receipt['sources'][source]={'status':'ok','items':count,'rejected_items':result['rejected_items']}
        except Exception:
            receipt['sources'][source]={'status':'failed','detail':'No retry; inspect source availability.'}
        set_meta(store,'collection',receipt)
    return receipt


def build(root,store,settings,now,*,allow_network=False,model_config=None,current_window=False):
    if model_config is not None:
        if not allow_network:raise ValueError('article_network_required_for_inference')
        network.config_checked(model_config)
    edition=store.claim(now,current_window=current_window,force=current_window)
    if edition is None:return {'status':'not_due_or_blocked','state':store.status()}
    eid=edition['id'];out=root/'editions'/eid
    out.mkdir(parents=True,mode=0o700)
    w.save(out/'edition.json',edition)
    cards={};failures={};fetches=0
    for index,item in enumerate(edition['items']):
        if model_config is None or len(cards)>=4:break
        attempts=store.db.execute('SELECT attempts FROM editions WHERE id=?',(eid,)).fetchone()[0]
        if fetches>=6 or attempts>=4:break
        try:
            core.article_url(item['source'],item['url'])
            fetches+=1;set_meta(store,'fetches:'+eid,fetches)
            article_out=out/f'article-{index}'
            w.article_report(item['source'],item['url'],article_out,
                             metadata={k:item[k] for k in ('source','title','url','published','first_seen')})
            article=w.read_json(article_out/'article.json',500000)
            packet=facts.prepare(article)
            if packet['hold_reasons']:raise ValueError('source_held')
            store.reserve_model(eid,time.time())
            selected_out=out/f'selection-{index}'
            selector.selection_report(article,model_config,selected_out)
            selection=w.read_json(selected_out/'selection.json',10000)
            cards[item['id']]=d.verified_card(article,packet,selection)
        except Exception:
            failures[item['id']]='Source/model unavailable or held; no verified brief. Read the original source.'
    # Feed excerpts only here: do not add unreserved metadata fetches.
    descriptions,_=quickhits.collect(edition['items'],cards,failures,0)
    collection=get_meta(store,'collection')
    coverage=None
    if collection:
        coverage={'ok':sum(v['status']=='ok' for v in collection['sources'].values()),
                  'total':len(collection['sources']),
                  'stale':collection['observed_at']<edition['cutoff']-3600}
    parts=d.render(edition,cards,failures=failures,descriptions=descriptions,
                   coverage=coverage,live_test=current_window,title=settings['title'],zone=store.zone)
    w.save(out/'cards.json',cards);w.save(out/'failures.json',failures)
    w.atomic(out/'supporting-report.html',d.supporting_report(edition,cards,settings['title']))
    w.atomic(out/'preview.html',presentation.preview(parts,settings['title']))
    for i,part in enumerate(parts,1):w.atomic(out/f'part-{i}.md',part)
    w.save(out/'manifest.json',{'version':d.VERSION,'edition':eid,'fetch_attempts':fetches,
        'model_attempts':store.db.execute('SELECT attempts FROM editions WHERE id=?',(eid,)).fetchone()[0],
        'model_cards':len(cards),'source_only_items':len(edition['items'])-len(cards),
        'delivery':'not_sent','parts':len(parts),'policy_sha256':facts.POLICY_HASH})
    store.ready(eid,parts,time.time())
    return {'status':'ready_review_required','edition':eid,'preview':str(out/'preview.html'),
            'model_cards':len(cards),'parts':len(parts),'delivery':'not_sent'}


def ready_parts(root,store,eid):
    if not re.fullmatch(r'[0-9a-f-]{36}',eid):raise ValueError('invalid_edition_id')
    row=store.db.execute('SELECT status,parts FROM editions WHERE id=?',(eid,)).fetchone()
    if not row or row['status']!='ready':raise ValueError('edition_not_ready')
    out=root/'editions'/eid
    for name in ('supporting-report.html','preview.html','manifest.json'):checked_file(out/name)
    parts=json.loads(row['parts'])
    if not parts or len(parts)>d.MAX_PARTS:raise ValueError('part_budget')
    for part in parts:presentation.telegram_html(part)
    return parts


def intent(root,store,eid,token,chat):
    parts=ready_parts(root,store,eid)
    # Include full supporting report in the intent so a changed source review
    # invalidates approval. Never save the bot token or chat ID in artifacts.
    report=(root/'editions'/eid/'supporting-report.html').read_bytes()
    return core.digest(json.dumps({'edition':eid,'parts':parts,'chat':chat,
        'bot':token.split(':')[0],'report_sha256':hashlib.sha256(report).hexdigest()},sort_keys=True))


def approve(root,store,eid,now,token,chat):
    if store.db.execute("SELECT 1 FROM deliveries WHERE edition=? AND status='reserved'",(eid,)).fetchone():
        raise ValueError('uncertain_delivery_reconcile_first')
    binding=intent(root,store,eid,token,chat)
    approval={'intent':binding,'expires':now+900,'nonce':secrets.token_hex(16),'used':False}
    approval['id']=core.digest(json.dumps(approval,sort_keys=True))
    set_meta(store,'approval:'+eid,approval)
    return {'approval':approval['id'],'expires_at':approval['expires'],'edition':eid,'delivery':'not_sent'}


def send(root,store,eid,approval_id,now,token,chat,transport=telegram.send):
    approval=get_meta(store,'approval:'+eid)
    if not approval or approval['used'] or now>=approval['expires'] or not secrets.compare_digest(approval['id'],approval_id):
        raise ValueError('valid_unconsumed_approval_required')
    if approval['intent']!=intent(root,store,eid,token,chat):raise ValueError('approval_target_or_content_changed')
    if store.db.execute("SELECT 1 FROM deliveries WHERE edition=? AND status='reserved'",(eid,)).fetchone():
        raise ValueError('uncertain_delivery_reconcile_first')
    parts=ready_parts(root,store,eid)
    approval['used']=True;set_meta(store,'approval:'+eid,approval)
    for index,part in enumerate(parts):
        done=store.db.execute('SELECT status FROM deliveries WHERE edition=? AND part=?',(eid,index)).fetchone()
        if done:
            if done[0]!='confirmed':raise ValueError('uncertain_delivery_reconcile_first')
            continue
        store.reserve_send(eid,index,part)
        mid=transport(part,token,chat)
        store.confirm_send(eid,index,mid)
    store.finish(eid,time.time())
    return {'status':'delivered','edition':eid,'confirmed_parts':len(parts)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True,help='Dedicated private state directory')
    sub=parser.add_subparsers(dest='action',required=True)
    init=sub.add_parser('init');init.add_argument('--title',default='MiniCPM News Desk');init.add_argument('--timezone',default='America/New_York')
    col=sub.add_parser('collect');col.add_argument('--sources',nargs='+',choices=sorted(feeds.FEEDS),default=['github'])
    col.add_argument('--allow-network',action='store_true',required=True)
    b=sub.add_parser('build');b.add_argument('--allow-network',action='store_true')
    b.add_argument('--allow-local-inference',action='store_true');b.add_argument('--config',type=Path)
    b.add_argument('--current-window',action='store_true',help='One test edition ending now; use isolated test state')
    sub.add_parser('status')
    a=sub.add_parser('approve');a.add_argument('--edition',required=True)
    s=sub.add_parser('send');s.add_argument('--edition',required=True);s.add_argument('--approval',required=True)
    s.add_argument('--allow-send',action='store_true',required=True)
    cancel=sub.add_parser('cancel-unsent');cancel.add_argument('--edition',required=True)
    confirm=sub.add_parser('confirm-observed');confirm.add_argument('--edition',required=True)
    confirm.add_argument('--part',type=int,required=True,help='Zero-based part index')
    confirm.add_argument('--message-id',type=int,required=True,help='Actual ID verified in the configured chat; never guess')
    sub.add_parser('reconcile')
    args=parser.parse_args(argv);os.umask(0o077);now=time.time()
    try:
        if args.action=='init':result=initialize(args.state,args.title,args.timezone)
        else:
            with locked(args.state) as (root,store,settings):
                if args.action=='collect':result=collect(root,store,args.sources,now)
                elif args.action=='build':
                    if bool(args.config)!=args.allow_local_inference:raise ValueError('config_and_explicit_inference_required_together')
                    config=w.read_json(args.config,4000) if args.config else None
                    result=build(root,store,settings,now,allow_network=args.allow_network,model_config=config,current_window=args.current_window)
                elif args.action=='status':result={'state':store.status(),'collection':get_meta(store,'collection')}
                elif args.action=='approve':result=approve(root,store,args.edition,now,*telegram.credentials())
                elif args.action=='send':result=send(root,store,args.edition,args.approval,now,*telegram.credentials())
                elif args.action=='cancel-unsent':
                    store.cancel_unsent(args.edition,now);result={'status':'cancelled','same_day_rebuild':False}
                elif args.action=='confirm-observed':
                    if args.part<0 or args.message_id<=0:raise ValueError('invalid_observed_receipt')
                    # This records an operator-verified receipt; it does not claim
                    # independent verification by Telegram and makes no API call.
                    store.confirm_send(args.edition,args.part,args.message_id)
                    set_meta(store,f'manual_receipt:{args.edition}:{args.part}',{'observed_at':now,'provenance':'operator_verified'})
                    store.reconcile_confirmed(now);result={'status':'operator_receipt_recorded','network_calls':0}
                else:store.reconcile_confirmed(now);result={'status':'reconciled','network_calls':0}
        print(json.dumps(result))
        if args.action=='collect' and any(v['status']!='ok' for v in result['sources'].values()):return 1
        return 0
    except Exception as exc:
        # Do not expose untrusted feed text, HTTP URLs, tokens or raw exceptions.
        detail=str(exc) if type(exc) is ValueError and re.fullmatch(r'[a-z_]{1,90}',str(exc)) else 'operation_failed_inspect_private_state'
        print(json.dumps({'status':'failed','detail':detail,'retry':'none'}))
        return 1


if __name__=='__main__':raise SystemExit(main())
