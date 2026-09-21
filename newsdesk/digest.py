"""Local daily-24h recap: durable intake, explicit curation and delivery receipts.

No model, network, scheduler or messaging calls occur in this module. Integrators
provide verified source cards and confirm delivery separately.
"""
import argparse
from datetime import datetime, timedelta
import hashlib
import html
import ipaddress
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
import uuid
from zoneinfo import ZoneInfo
from . import facts as f, workflow as w

VERSION='0.8.1'
ZONE=ZoneInfo('America/New_York')
MAX_STORIES=9
MAX_DETAILED=4
MAX_PARTS=16
PART_UNITS=3000


def stamp(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=4102444800:
        raise ValueError('invalid_timestamp')
    return float(value)


def text(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(c)<32 for c in value):
        raise ValueError('invalid_text')
    return value


def url(value):
    text(value,2000)
    u=urlsplit(value)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.port not in (None,443):raise ValueError('invalid_url')
    host=u.hostname.lower()
    if '.' not in host or host.endswith(('.local','.internal','.localhost','.ts.net')):raise ValueError('private_url')
    try:ipaddress.ip_address(host)
    except ValueError:pass
    else:raise ValueError('ip_url')
    if re.search(r'[\s<>\[\]{}\\"`]',value):raise ValueError('unsafe_url')
    query=urlencode([(k,v) for k,v in parse_qsl(u.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')])
    return urlunsplit(('https',host,u.path.rstrip('/') or '/',query,''))


def clean(value):
    """Inert Markdown text: preserve visible syntax instead of deleting it.

    Numeric entities keep source Markdown from becoming formatting. Consumers
    must render this once, not decode and re-parse it as trusted Markdown.
    Source URLs/directives are deliberately neutralized; links are app-owned.
    """
    value=re.sub(r'\b(?:https?://|www\.)\S+','(link omitted)',str(value))
    value=re.sub(r'\bMEDIA\s*:', 'MEDIA ',value,flags=re.I)
    value=''.join(c if ord(c)>=32 and c not in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\x7f' else ' ' for c in value)
    value=' '.join(value.split())
    value=html.escape(value,quote=False)
    return ''.join('&#'+str(ord(c))+';' if c in '*_`[]\\@#!' else c for c in value)


def source_link(value):
    # Model/source text never supplies a Markdown label. Encode delimiters before
    # inserting the validated HTTPS URL into a renderer-owned link.
    target=quote(url(value),safe=':/?=&%+-._~')
    return '[Read the source ↗]('+target+')'


def reading_paragraphs(passages):
    """Join short related highlights without creating an oversized paragraph."""
    paragraphs=[]
    for raw in passages:
        p=clean(raw)
        if paragraphs and units(paragraphs[-1]+' '+p)<=1400:
            paragraphs[-1]+=' '+p
        else:paragraphs.append(p)
    return paragraphs


def cutoff(now,zone=ZONE):
    local=datetime.fromtimestamp(stamp(now),zone)
    return local.replace(hour=8,minute=0,second=0,microsecond=0).timestamp()


def next_cutoff(now,zone=ZONE):
    due=cutoff(now,zone)
    if due<=now:
        due=(datetime.fromtimestamp(due,zone)+timedelta(days=1)).timestamp()
    return due


def normalized(item,now):
    out={k:text(item.get(k),n) for k,n in [('source',100),('title',2000)]}
    out['url']=url(item.get('url'))
    out['company']=text(item.get('company') or out['source'],200)
    # Excerpts remain archived, but are never treated as full-source summaries.
    excerpt=item.get('excerpt') or ''
    if not isinstance(excerpt,str) or len(excerpt)>20000:raise ValueError('invalid_excerpt')
    out['excerpt']=excerpt
    out['first_seen']=stamp(item['first_seen'])
    if out['first_seen']>now:raise ValueError('future_observation')
    out['published']=None if item.get('published') is None else stamp(item['published'])
    out['changed_observed_at']=None if item.get('changed_observed_at') is None else stamp(item['changed_observed_at'])
    if out['changed_observed_at'] is not None and out['changed_observed_at']>now:raise ValueError('future_revision')
    identity={k:out[k] for k in ('source','title','url','excerpt','published','changed_observed_at')}
    out['revision']=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    out['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,out['url']+'#'+out['revision']))
    return out


def event_time(item):
    for key in ('changed_observed_at','published','first_seen'):
        if item.get(key) is not None:return item[key]
    raise ValueError('missing_event_time')


def rank(item):
    """Transparent editorial heuristic, not a model importance judgment."""
    title=item['title'].lower()
    score=0
    for pattern,weight in [(r'security|vulnerab|credential|privacy',6),
                           (r'launch|introduc|release|available|open.weight|model',4),
                           (r'agent|api|coding|workflow|tool|inference',3),
                           (r'preview|beta|rc\d|spacing|typo',-2)]:
        if re.search(pattern,title):score+=weight
    return (-score,-event_time(item),item['url'])


class Store:
    def __init__(self,path,zone=ZONE):
        self.zone=zone
        self.db=sqlite3.connect(path,timeout=10)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('''
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS stories(id TEXT PRIMARY KEY,url TEXT NOT NULL,revision TEXT NOT NULL,
          payload TEXT NOT NULL,created_at REAL NOT NULL,updated_at REAL NOT NULL,delivered_edition TEXT,
          UNIQUE(url,revision));
        CREATE TABLE IF NOT EXISTS editions(id TEXT PRIMARY KEY,day TEXT UNIQUE NOT NULL,cutoff REAL NOT NULL,
          status TEXT NOT NULL,ids TEXT NOT NULL,parts TEXT,attempts INTEGER NOT NULL DEFAULT 0,
          created_at REAL NOT NULL,updated_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS deliveries(edition TEXT NOT NULL REFERENCES editions(id),
          part INTEGER NOT NULL,sha TEXT NOT NULL,status TEXT NOT NULL,message_id TEXT,
          PRIMARY KEY(edition,part));
        ''')

    def close(self):self.db.close()

    def initialize(self,now):
        with self.db:self.db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',('first_due',str(next_cutoff(now,self.zone))))

    def ingest(self,items,now):
        if not isinstance(items,list) or len(items)>30000:raise ValueError('intake_limit')
        # Validate the whole batch first: a rejected snapshot cannot partially ingest.
        rows=[normalized(i,now) for i in items]
        with self.db:
            for i in rows:
                self.db.execute('INSERT OR IGNORE INTO stories VALUES (?,?,?,?,?,?,NULL)',
                    (i['id'],i['url'],i['revision'],json.dumps(i),now,now))
        return len(rows)

    def candidates(self,until,observed_until=None):
        observed_until=until if observed_until is None else observed_until
        start=until-86400;rows=[];duplicates=set();latest={};delivered_keys=set()
        def event_key(i):
            return (i['source'],re.sub(r'\W+',' ',i['title']).lower().strip(),
                    datetime.fromtimestamp(event_time(i),self.zone).date().isoformat(),i.get('changed_observed_at'))
        for r in self.db.execute('SELECT payload,delivered_edition,created_at FROM stories ORDER BY created_at,id'):
            i=json.loads(r['payload']);t=event_time(i)
            if i['first_seen']>observed_until:continue
            if r['delivered_edition']:delivered_keys.add(event_key(i))
            latest[i['url']]=(i,r['delivered_edition'])
        for i,delivered in latest.values():
            t=event_time(i)
            if not start<t<=until or delivered:continue
            if i['published'] is not None and i['published']>until:continue
            rows.append(i)
        result=[]
        for i in sorted(rows,key=rank):
            key=event_key(i)
            if key not in duplicates and key not in delivered_keys:result.append(i);duplicates.add(key)
        return result

    def claim(self,now,force=False,current_window=False):
        self.initialize(now)
        due=stamp(now) if current_window else cutoff(now,self.zone)
        first=float(self.db.execute("SELECT value FROM meta WHERE key='first_due'").fetchone()[0])
        if not force and (now<due or due<first):return None
        day=datetime.fromtimestamp(due,self.zone).date().isoformat()
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            # Never create a new edition while a previous send needs reconciliation.
            if self.db.execute("SELECT 1 FROM editions WHERE status NOT IN ('delivered','cancelled')").fetchone():return None
            if self.db.execute('SELECT 1 FROM editions WHERE day=?',(day,)).fetchone():return None
            items=self.candidates(due,now);eid=str(uuid.uuid4())
            self.db.execute('INSERT INTO editions VALUES (?,?,?,?,?,?,0,?,?)',
                (eid,day,due,'preparing',json.dumps([i['id'] for i in items[:MAX_STORIES]]),None,now,now))
        return {'id':eid,'day':day,'cutoff':due,'items':items[:MAX_STORIES],'eligible':len(items),'overflow':max(0,len(items)-MAX_STORIES)}

    def cancel_unsent(self,eid,now):
        """Abandon known-unsent work; retain history and the day's budget lock."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute('SELECT 1 FROM deliveries WHERE edition=?',(eid,)).fetchone():
                raise ValueError('delivery_exists_reconcile_required')
            result=self.db.execute("UPDATE editions SET status='cancelled',updated_at=? WHERE id=? AND status IN ('preparing','ready')",(stamp(now),eid))
            if result.rowcount!=1:raise ValueError('edition_not_cancellable')

    def reserve_model(self,eid,now):
        with self.db:
            cur=self.db.execute("UPDATE editions SET attempts=attempts+1,updated_at=? WHERE id=? AND status='preparing' AND attempts<4",(now,eid))
            if cur.rowcount!=1:raise ValueError('model_budget_or_status')

    def ready(self,eid,parts,now):
        if not parts or len(parts)>MAX_PARTS or any(units(p)>3400 for p in parts):raise ValueError('part_budget')
        with self.db:
            cur=self.db.execute("UPDATE editions SET status='ready',parts=?,updated_at=? WHERE id=? AND status='preparing'",(json.dumps(parts),now,eid))
            if cur.rowcount!=1:raise ValueError('edition_not_preparing')

    def reserve_send(self,eid,index,part):
        with self.db:
            row=self.db.execute('SELECT status,parts FROM editions WHERE id=?',(eid,)).fetchone()
            if not row or row['status']!='ready':raise ValueError('edition_not_ready')
            parts=json.loads(row['parts'])
            if type(index) is not int or not 0<=index<len(parts) or part!=parts[index]:raise ValueError('changed_delivery')
            if index and self.db.execute("SELECT count(*) FROM deliveries WHERE edition=? AND status='confirmed'",(eid,)).fetchone()[0]!=index:raise ValueError('previous_part_unconfirmed')
            self.db.execute('INSERT INTO deliveries VALUES (?,?,?,?,NULL)',(eid,index,hashlib.sha256(part.encode()).hexdigest(),'reserved'))

    def confirm_send(self,eid,index,message_id):
        if not str(message_id).isdigit():raise ValueError('missing_delivery_id')
        with self.db:
            cur=self.db.execute("UPDATE deliveries SET status='confirmed',message_id=? WHERE edition=? AND part=? AND status='reserved'",(str(message_id),eid,index))
            if cur.rowcount!=1:raise ValueError('send_not_reserved')

    def finish(self,eid,now):
        with self.db:
            row=self.db.execute('SELECT * FROM editions WHERE id=?',(eid,)).fetchone()
            if not row or row['status']!='ready':raise ValueError('not_ready')
            count=self.db.execute("SELECT count(*) FROM deliveries WHERE edition=? AND status='confirmed'",(eid,)).fetchone()[0]
            if count!=len(json.loads(row['parts'])):raise ValueError('unconfirmed_delivery')
            for sid in json.loads(row['ids']):self.db.execute('UPDATE stories SET delivered_edition=?,updated_at=? WHERE id=?',(eid,now,sid))
            self.db.execute("UPDATE editions SET status='delivered',updated_at=? WHERE id=?",(now,eid))

    def reconcile_confirmed(self,now):
        for row in self.db.execute("SELECT id,parts FROM editions WHERE status='ready'").fetchall():
            count=self.db.execute("SELECT count(*) FROM deliveries WHERE edition=? AND status='confirmed'",(row['id'],)).fetchone()[0]
            if count==len(json.loads(row['parts'])):self.finish(row['id'],now)

    def status(self):
        return {'archived':self.db.execute('SELECT count(*) FROM stories').fetchone()[0],
                'editions':[dict(r) for r in self.db.execute('SELECT id,day,status,attempts FROM editions ORDER BY cutoff')],
                'pending_delivery_parts':self.db.execute("SELECT count(*) FROM deliveries WHERE status='reserved'").fetchone()[0]}


def verified_card(article,packet,card):
    selected=f.validate_card(article,packet,card)['highlights']
    if not selected:raise ValueError('no_model_highlights')
    visible={b['id'] for b in selected}
    conditions=[b for b in packet['protected'] if b['id'] not in visible]
    return {'title':article['title'],'url':article['url'],'source_sha256':article['source_sha256'],
            'highlights':[b['text'] for b in selected],
            'conditions':[b['text'] for b in conditions],
            'condition_rules':[list(b.get('rules',[])) for b in conditions],
            'source_body':article['body'],'selected_ids':[b['id'] for b in selected]}


def preparation_context(card,paragraph):
    """Recover only a complete, bounded preparation passage from verified source."""
    if not re.search(r'\bTo prepare:\s*$',paragraph):return None
    body=card.get('source_body')
    if not isinstance(body,str) or len(body)>f.POLICY['budgets']['source']:return None
    if hashlib.sha256(body.encode()).hexdigest()!=card.get('source_sha256'):return None
    rows=[b['text'] for b in f.blocks(body)]
    if rows.count(paragraph)!=1:return None
    following=[]
    for value in rows[rows.index(paragraph)+1:]:
        if f.is_heading(value):break
        # Do not guess the end of a truncated sentence or nested list.
        if not value.endswith(('.', '!', '?')) or value.endswith(('...', '…')):return None
        following.append(value)
    if not following:return None
    combined=' '.join([paragraph]+following)
    if units(clean(combined))>1400:return None
    return combined,following


def reading_card(card):
    """Conservative extractive reading layer; never a semantic guarantee.

    Model output is unchanged. Every moved passage remains in the report with
    its reason. Unknown conditions stay visible; no arbitrary word-count cutoff.
    """
    highlights=[];conditions=[];audit=[];held=False
    identifiers=lambda s:set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*_[a-zA-Z0-9_]+\b',s))
    material=re.compile(r'[$€£]\s*\d|\b(?:pricing|costs?|billed|billing|subscription|available (?:only |to |in )|invited|eligible|requires?|must|permission|does not apply|not added to|private or internal|enforc\w*|deadline|until|starting|beginning|November|December|January|February|March|April|May|June|July|August|September|October)\b',re.I)
    navigation=re.compile(r'^(?:To get started|To learn more|Visit |For (?:more|further) (?:details|information)|Learn more|Read (?:the|our) (?:docs|documentation))',re.I)
    safety=re.compile(r'\b(?:leaks?|credentials?|exfiltrat\w*|unsafe|cannot|unless|consent|retention|not (?:available|supported)|limited to|only works|supports? only)\b',re.I)
    dates_or_migration=re.compile('|'.join(f.POLICY['rules'][k] for k in ('effective_dates','migration_guidance','licensing_restrictions')),re.I)
    def qualified(p):
        return bool(material.search(p) or safety.search(p) or dates_or_migration.search(p))
    for position,p in enumerate(card['highlights']):
        reason=None
        if p.rstrip().endswith(':'):
            reason='incomplete_highlight';held=True
        elif navigation.search(p) and not qualified(p):reason='navigation_not_news'
        elif position and re.match(r'^`?[A-Za-z]\w*_\w+`?\s*:',p) and not qualified(p):reason='field_reference_not_overview'
        if reason:audit.append({'text':p,'placement':'report','reason':reason})
        else:highlights.append(p);audit.append({'text':p,'placement':'brief','reason':'model_selected_overview'})
    mentioned=identifiers(' '.join(highlights));covered=set()
    # Protection reasons recorded by facts.prepare; older cards carry none.
    rules=card.get('condition_rules') or [[] for _ in card['conditions']]
    if len(rules)!=len(card['conditions']):raise ValueError('condition_rules_mismatch')
    tagged=lambda index:any(r=='exclusions' or r.startswith('section:') for r in rules[index])
    for index,p in enumerate(card['conditions']):
        reason=None;fields=identifiers(p);retained='qualification_retained'
        if p in highlights or p in conditions or p in covered:reason='already_shown'
        elif p.rstrip().endswith(':'):
            expanded=preparation_context(card,p)
            if expanded:
                combined,following=expanded
                conditions.append(combined);covered.update(following)
                audit.append({'text':combined,'placement':'brief','reason':'complete_preparation_context'})
                continue
            reason='list_introduction_requires_context'
            # A restrictive introduction cannot safely be detached from its list.
            if qualified(p) or re.search(r'\b(?:only|must|require\w*|except|unless|limited|cost\w*)\b',p,re.I):held=True
        elif navigation.search(p) and not qualified(p):reason='navigation_not_news'
        elif re.match(r'^To prepare for ',p,re.I) and not re.search(r'\d|\b(?:must|only|unless|cost|price)\b',p,re.I):reason='procedural_reference'
        # An important-notes section or exclusion clause outranks the
        # unmentioned-definition heuristics below; navigation/holds are unchanged.
        elif tagged(index):retained='protected_section_or_exclusion_retained'
        elif re.match(r'^Empty (?:arrays|fields)\b',p,re.I) and not re.search(r'\b(?:null|zero|empty|absent)\b',' '.join(highlights),re.I):reason='unmentioned_missing_value_semantics'
        elif re.match(r'^Plugin metrics count\b',p,re.I) and not re.search(r'\b(?:counts?|totals?|invocations?|interactions?)\b',' '.join(highlights),re.I):reason='unmentioned_count_relationship'
        elif re.match(r'^Active .+ code review means\b',p,re.I) and 'code review' not in ' '.join(highlights).lower():reason='unmentioned_feature_definition'
        elif fields and not fields.intersection(mentioned) and not qualified(p):reason='unmentioned_api_field_detail'
        elif re.search(r'\b(?:previously|commonly exploited)\b',p,re.I) and not qualified(p):reason='background_context'
        if reason:audit.append({'text':p,'placement':'report','reason':reason})
        else:conditions.append(p);audit.append({'text':p,'placement':'brief','reason':retained})
    return {'highlights':highlights,'conditions':conditions,'audit':audit,'held':held or not highlights}


def supporting_report(edition,cards,title='Cheryl’s AI & Tech Brief'):
    """Private full-detail artifact; escape all source content; no scripts/assets."""
    esc=html.escape;sections=[]
    for item in edition['items']:
        card=cards.get(item['id'])
        if card is None:continue
        if url(card['url'])!=item['url']:raise ValueError('card_identity_mismatch')
        view=reading_card(card)
        rows=''.join('<tr><td data-label="Placement">'+esc(r['placement'])+'</td><td data-label="Reason">'+esc(r['reason'])+'</td><td data-label="Passage">'+esc(r['text'])+'</td></tr>' for r in view['audit'])
        sections.append('<section><h2>'+esc(item['title'])+'</h2><p><a rel="noreferrer" href="'+esc(item['url'],quote=True)+'">Original source</a></p><h3>Editorial decisions</h3><table>'+rows+'</table><h3>Complete extracted source</h3><pre>'+esc(card.get('source_body','Full source unavailable in this fixture.'))+'</pre></section>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>'+esc(title)+' — supporting report</title><style>body{max-width:960px;margin:32px auto;padding:0 20px;font:16px/1.6 system-ui;background:#faf8f1;color:#24372e}section{border-top:1px solid #ccc;margin-top:32px}pre,td{white-space:pre-wrap;overflow-wrap:anywhere}td{padding:10px;vertical-align:top;border-bottom:1px solid #ddd}table{width:100%;border-collapse:collapse}@media(max-width:600px){table,tbody,tr,td{display:block}tr{padding:12px 0;border-bottom:1px solid #ccc}td{border:0;padding:4px 0}td:before{content:attr(data-label) ": ";font-weight:600}}</style><h1>'+esc(title)+' — supporting report</h1><p>Exact extracted source and editorial placement decisions. Source claims require review; no independent fact-check is implied.</p>'+''.join(sections)+'</html>'


def units(s):return len(s.encode('utf-16-le'))//2


def split_parts(paragraphs,title='Cheryl’s AI & Tech Brief'):
    text(title,120)
    if units(clean(title))>250:raise ValueError('title_requires_review')
    bodies=[];current=[]
    for p in paragraphs:
        if units(p)>PART_UNITS:raise ValueError('paragraph_requires_review')
        if current and units('\n\n'.join(current+[p]))>PART_UNITS:
            bodies.append('\n\n'.join(current));current=[]
        current.append(p)
    if current:bodies.append('\n\n'.join(current))
    if len(bodies)>MAX_PARTS:raise ValueError('edition_requires_review')
    return [f'**☕ {clean(title)}** · {i}/{len(bodies)}\n\n'+body for i,body in enumerate(bodies,1)]


def story_blocks(paragraphs,title):
    """Keep a whole story together where possible; explicitly label overflow."""
    story='\n\n'.join(paragraphs)
    if units(story)<=PART_UNITS:return [story]
    continuation='**↪ '+clean(title)+' — continued**'
    result=[];current=[]
    for p in paragraphs:
        if units(p)+units(continuation)+4>PART_UNITS:raise ValueError('paragraph_requires_review')
        if current and units('\n\n'.join(current+[p]))>PART_UNITS:
            # Do not strand a section heading/title at the end of a part.
            tail=[]
            while current and current[-1].startswith('**') and current[-1].endswith('**'):
                tail.insert(0,current.pop())
            if not current:raise ValueError('heading_requires_review')
            result.append('\n\n'.join(current));current=[continuation]+tail
        current.append(p)
        if units('\n\n'.join(current))>PART_UNITS:raise ValueError('paragraph_requires_review')
    if current:result.append('\n\n'.join(current))
    return result


def render(edition,cards,failures=None,coverage=None,preview=False,generated_at=None,live_test=False,descriptions=None,title='Cheryl’s AI & Tech Brief',zone=ZONE):
    if preview and live_test:raise ValueError('ambiguous_preview_origin')
    items=edition['items'];failures=failures or {};descriptions=descriptions or {};start=edition['cutoff']-86400
    def date(t):return datetime.fromtimestamp(t,zone).strftime('%b %d, %I:%M %p %Z')
    views={key:reading_card(card) for key,card in cards.items()}
    detailed=[i for i in items if i['id'] in views and not views[i['id']]['held']][:MAX_DETAILED]
    heading=datetime.fromtimestamp(edition['cutoff'],zone).strftime('%A, %B %d')
    if preview:
        generated=time.time() if generated_at is None else stamp(generated_at)
        introduction=['**PREVIEW — saved results; not a new model run**',
                      'Prepared '+date(generated),
                      'Historical source window: '+date(start)+' → '+date(edition['cutoff'])]
    else:introduction=[f'*{heading} · '+('Live test edition*' if live_test else 'Morning edition*'),
                       'Your last 24 hours in AI & tech.']
    if not detailed:introduction.append('Source links only; no verified model brief in this edition.')
    blocks=['\n\n'.join(introduction)]
    quick=[i for i in items if i not in detailed]
    for index,item in enumerate(detailed):
        card=cards[item['id']]
        view=views[item['id']];story=[]
        if url(card['url'])!=item['url']:raise ValueError('card_identity_mismatch')
        if index==0:story.append('**📰 The lead story**')
        elif index==1:story.append('**🗞 Worth knowing**')
        story.append('**'+clean(item['title'])+'**')
        if item.get('changed_observed_at'):story.append('Updated listing — not necessarily a new release.')
        if item['published'] is None:story.append('Publication date unavailable; included by discovery time.')
        story += reading_paragraphs(view['highlights'])
        if len(view['conditions'])==1:
            story.append('**📝 Keep in mind:** '+clean(view['conditions'][0]))
        elif view['conditions']:
            story.append('**📝 Keep in mind**')
            story += ['• '+clean(p) for p in view['conditions']]
        story.append(source_link(item['url']))
        blocks.extend(story_blocks(story,item['title']))
    if quick:
        notice='*Publisher excerpts where available; full-article briefs are not included in this section.*'
        for index,item in enumerate(quick):
            reason=failures.get(item['id'],'')
            if item['id'] in views and views[item['id']]['held']:reason='Brief held: selected text needs more context. Read the original source.'
            description=descriptions.get(item['id'])
            detail=''
            if description and not reason and item['id'] not in views:
                from .quickhits import excerpt
                if url(description['url'])!=item['url'] or description['source']!=item['source']:raise ValueError('description_identity')
                raw=description.get('text','')
                if raw!=excerpt(raw,item['title']):raise ValueError('description_invalid')
                detail=clean(raw)
            if not detail and not reason:reason='Headline only; source detail unavailable.'
            if item.get('changed_observed_at'):reason='Updated listing. '+reason
            if item['published'] is None:reason+=' Publication date unknown; discovered in this window.'
            hit='**'+clean(item['title'])+'**\n'+(detail+'\n' if detail else '')+(clean(reason)+'\n' if reason.strip() else '')+source_link(item['url'])
            # Pack individual intact hits instead of moving the whole section to
            # a new part. A section heading is never detached from its first hit.
            if index==0:hit='**⚡ Quick hits**\n\n'+notice+'\n\n'+hit
            blocks.extend(story_blocks([hit],'Quick hits'))
    if not items:blocks.append('No eligible new items were found in the preceding 24 hours. This does not prove no news occurred.')
    if edition.get('overflow'):blocks.append(f"{edition['overflow']} additional eligible items are retained in the archive. They were not included in this recap; older items will not be recycled as new news.")
    if coverage:
        blocks.append(f"Coverage: {coverage['ok']}/{coverage['total']} registered sources reported successful; not every company channel.")
        if coverage.get('stale'):blocks.append('Collection has not refreshed through the cutoff. Coverage may be incomplete.')
    if not preview:
        blocks.append('*'+('Live test · daily recap schedule unchanged.\n' if live_test else '')+
                      'Window: '+date(start)+' → '+date(edition['cutoff'])+'*')
    return split_parts(blocks,title)


def demo(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    until=datetime(2026,9,18,8,tzinfo=ZONE).timestamp()
    store=Store(out/'demo.sqlite3')
    items=[{'source':f'fictional-{i}','company':title.split()[1]+' (fictional)','title':title,
            'url':f'https://example.com/fictional/{i}','excerpt':'This fictional update adds an export button for saved project notes.',
            'published':until-3600-i,'first_seen':until-3600-i} for i,title in enumerate([
                'Fictional Cedar launches a review checklist tool','Fictional Birch API adds local exports',
                'Fictional Pine fixes a configuration error','Fictional Maple publishes documentation',
                'Fictional Elm updates its editor','Fictional Ash publishes a tutorial'])]
    store.ingest(items,until);edition=store.claim(until,force=True)
    cards={}
    for item in edition['items'][:4]:
        cards[item['id']]={'url':item['url'],'highlights':['This is fictional demonstration text, not a real announcement or model result.','Teams can turn a change list into a checklist for human review.'],
            'conditions':['Available only to invited teams. A person must approve the result.']}
        cards[item['id']]['source_body']='\n'.join(cards[item['id']]['highlights']+cards[item['id']]['conditions'])
    from .quickhits import collect
    descriptions,_=collect(edition['items'],cards,{},0)
    title='MiniCPM News Desk'
    parts=render(edition,cards,preview=True,descriptions=descriptions,title=title)
    parts=[p.replace('**PREVIEW — saved results; not a new model run**','**SYNTHETIC DEMO — fictional, hand-authored; zero model calls**') for p in parts]
    for i,part in enumerate(parts,1):w.atomic(out/f'part-{i}.md',part)
    w.atomic(out/'supporting-report.html',supporting_report(edition,cards,title))
    from .presentation import preview as preview_page
    w.atomic(out/'preview.html',preview_page(parts,title))
    w.save(out/'manifest.json',{'version':VERSION,'synthetic':True,'model_calls':0,'delivery':'not_sent','parts':len(parts)})
    store.close()
    return len(parts)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['demo']);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();print(json.dumps({'parts':demo(args.out),'model_calls':0,'delivery':'not_sent'}))
