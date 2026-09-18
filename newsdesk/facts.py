"""Exact-source block preservation; heuristic recall is explicitly not certainty."""
from datetime import datetime, timezone
import html
import json
import re
import time
from . import core as c

CONTRACT = 'newsdesk-highlights-v2'
POLICY = {
    'version': 'protected-blocks-v3-definitions',
    'rules': {
        'price': r'[$€£]\s*\d|\b(?:prices?|pricing|costs?|credits?|billing|subscriptions?|free)\b',
        'access_limits': r'\b(?:available|availability|only|invited?|preview|approval|eligible|rollout|rolling out|markets?|US-based|international|opt[ -]?in(?:to)?|if enabled|limited|limits?|requires?|cannot|must|not yet|not supported|select advertisers|being tested)\b',
        'setup_scope': r'/(?:new|memory|dream)\b|\b(?:first completed turn|after (?:a|the) turn|new sessions|current conversation|per project|global set)\b',
        'separation': r'\b(?:clearly labeled|independent answers|separate from|distinct from)\b',
        'exclusions': r'\b(?:excluded?|left out|does not|do not|will not)\b',
        'definitions': r'\b(?:at least|at most|up to|means|defined as|counts?|counted|denominator|numerator|omitted|absent|null|not measured|rolling \d+[ -]day)\b',
        'effective_dates': r'\b(?:on|from|by|starting|beginning|until|after|before)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',
    },
    'sections': ['availability','pricing','limitations','restrictions','new commands','getting started','access','requirements','important notes','new secure defaults'],
    'pool': 'lead4_plus_first3_practical_use_blocks',
    'context': r'^(?:It\b|This\b|That\b|They\b|These\b|The app\b)',
    'injection': r'ignore (?:all |previous |the )?(?:instructions|task)|reveal (?:the |your )?(?:credentials|secrets)|<\|(?:system|im_start)\|>|\[INST\]',
    'demo_start': r'^~/|^[❯◆]|^Enter:|^Thought for|^Edit(?:src|tests|/)',
    'budgets': {'source':7000,'blocks':120,'block':2000,'protected_chars':5500,'protected_blocks':30,'pool_chars':4000,'pool_blocks':25,'selected_chars':1800},
}
POLICY_HASH = c.digest(json.dumps(POLICY,sort_keys=True))
ROLES = {'highlights':2}


def canonical(value):
    return c.digest(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')))


def checked_article(article):
    if not isinstance(article,dict) or article.get('contract')!=c.CONTRACT:
        raise ValueError('invalid_article_contract')
    body=c.text(article.get('body'),100000)
    if not body.strip() or c.digest(body)!=article.get('source_sha256'):
        raise ValueError('source_hash_mismatch')
    title=c.text(article.get('title'),2000)
    sid=c.source_id(article.get('source'))
    url=article.get('url')
    if sid=='synthetic':
        if url is not None: raise ValueError('synthetic_source_must_have_no_url')
        if not title.startswith('SYNTHETIC'): title='SYNTHETIC — '+title
    else:sid=c.article_url(sid,url)
    return {'source':sid,'url':url,'title':title,'body':body,'source_sha256':c.digest(body),
            'published':c.timestamp(article.get('published')),'first_seen':c.timestamp(article.get('first_seen'))}


def blocks(body):
    result=[]
    for match in re.finditer(r'[^\n]+',body):
        raw=match.group();value=raw.strip()
        if not value:continue
        start=match.start()+len(raw)-len(raw.lstrip());end=start+len(value)
        result.append({'id':f'b{len(result)+1:03d}','start':start,'end':end,'text':body[start:end]})
    return result


def is_heading(value):
    # Narrow English heading shape; do not treat short terminal output as headings.
    return bool(re.fullmatch(r'[A-Z][A-Za-z /-]{2,70}',value))


def prepare(article):
    a=checked_article(article);body=a['body'];all_blocks=blocks(body);held=[];warnings=[]
    limits=POLICY['budgets']
    if len(body)>limits['source']:held.append('source_exceeds_selector_budget')
    if len(all_blocks)>limits['blocks'] or any(len(b['text'])>limits['block'] for b in all_blocks):held.append('block_budget_exceeded')
    if re.search(POLICY['injection'],body,re.I):held.append('untrusted_instruction_pattern_requires_review')
    if any(a[k] is not None and a[k]>time.time() for k in ('published','first_seen')):held.append('future_date_requires_review')
    if re.search(r'\b(?:today|now|tomorrow|yesterday|next week)\b',body,re.I):warnings.append('Relative dates are source quotations, not the report date. Publication date may be unknown.')
    candidates=[];reasons={};demo=False;section=None;ignored=[];previous=None
    for block in all_blocks:
        value=block['text'];heading=is_heading(value)
        if heading and value.lower() in POLICY['sections']:
            demo=False;section=value.lower();previous=None;continue
        if re.search(POLICY['demo_start'],value):demo=True
        if heading and not re.search(POLICY['demo_start'],value) and not re.match(r'^[|\d.%]+$',value):
            # Short non-terminal headings end a recognized section/demo.
            if value not in ('Try Free',) and not re.match(r'^Grok \d',value):demo=False
            section=None
            previous=None
        if demo or heading:
            ignored.append(block['id']);continue
        candidates.append(block)
        matched=[key for key,pattern in POLICY['rules'].items() if re.search(pattern,value,re.I)]
        if section:matched.append('section:'+section)
        if matched:
            reasons.setdefault(block['id'],[]).extend(matched)
            if previous is not None and re.search(POLICY['context'],value,re.I):
                reasons.setdefault(previous['id'],[]).append('context_for:'+block['id'])
        previous=block
    protected=[dict(b,rules=sorted(set(reasons[b['id']]))) for b in all_blocks if b['id'] in reasons]
    pool=candidates[:4]
    extra=[b for b in candidates[4:] if re.search(r'\b(?:can|helps?|enables?|lets?|useful|able to)\b',b['text'],re.I)][:3]
    pool+=extra
    if len(protected)>limits['protected_blocks'] or sum(len(b['text']) for b in protected)>limits['protected_chars']:held.append('protected_detail_budget_exceeded')
    if len(pool)>limits['pool_blocks'] or sum(len(b['text']) for b in pool)>limits['pool_chars']:held.append('selector_pool_budget_exceeded')
    if not pool:held.append('no_eligible_overview_blocks')
    price_found=any('price' in b['rules'] or 'section:pricing' in b['rules'] for b in protected)
    if not price_found:warnings.append('No pricing passage identified by these rules. This does not mean free or that pricing is unannounced; inspect the source.')
    if ignored:warnings.append('Some headings or recognizable demo lines are excluded from selection. The full source remains available.')
    warnings.append('Rules can miss conditions and context. Source quotations are not independently verified facts; meaning review is required.')
    packet={'contract':CONTRACT,'policy_sha256':POLICY_HASH,'article_identity_sha256':canonical(a),'source_sha256':a['source_sha256'],
        'title':a['title'],'protected':protected,'pool':pool,'warnings':warnings,'hold_reasons':held,
        'status':'held_for_review' if held else 'ready_for_selection_review_required',
        'counts':{'source_chars':len(body),'blocks':len(all_blocks),'protected_chars':sum(len(b['text']) for b in protected),
                  'pool_chars':sum(len(b['text']) for b in pool),'eligible_blocks_not_in_pool':len(candidates)-len(pool),'ignored_block_ids':ignored}}
    packet['packet_sha256']=canonical(packet)
    return packet


def verify(article,packet):
    if packet!=prepare(article):raise ValueError('packet_source_policy_or_metadata_mismatch')


def validate_card(article,packet,card):
    verify(article,packet)
    if packet['hold_reasons']:raise ValueError('source_held_for_review')
    if not isinstance(card,dict) or set(card)!=set(ROLES)|{'packet_sha256'} or card['packet_sha256']!=packet['packet_sha256']:
        raise ValueError('selection_contract_or_packet_mismatch')
    allowed={b['id']:b for b in packet['pool']};used=[]
    for role,maximum in ROLES.items():
        ids=card[role]
        if not isinstance(ids,list) or len(ids)>maximum or any(type(i) is not str or i not in allowed for i in ids):raise ValueError('invalid_selected_ids')
        used.extend(ids)
    if len(set(used))!=len(used):raise ValueError('duplicate_selected_ids')
    if sum(len(allowed[i]['text']) for i in used)>POLICY['budgets']['selected_chars']:raise ValueError('selection_length_requires_review')
    return {role:[allowed[i] for i in card[role]] for role in ROLES}


def render(article,packet,card=None,origin='source_only_no_model'):
    verify(article,packet);a=checked_article(article)
    if origin not in ('source_only_no_model','synthetic_selector_demo','saved_response_unverified_origin','local_model_unreviewed'):raise ValueError('invalid_origin')
    selected=validate_card(article,packet,card) if card is not None else {}
    source_fallback=card is not None and not any(selected.values())
    esc=html.escape
    pieces=[];plain=['MINICPM NEWS DESK — SOURCE QUOTES / REVIEW REQUIRED',a['title'],origin,packet['status']]
    for key in ('published','first_seen'):
        value=a[key];plain.append(key+': '+(datetime.fromtimestamp(value,timezone.utc).isoformat() if value is not None else 'Unknown'))
    def quote(block):
        return '<blockquote><p>'+esc(block['text'])+'</p><small>'+esc(block['id'])+' · exact source quotation</small></blockquote>'
    for role,label in [('highlights','Highlights — what changed and how it is used')]:
        rows=selected.get(role,[])
        if rows:
            pieces.append('<section><h2>'+label+'</h2>'+''.join(quote(b) for b in rows)+'</section>')
            plain+=[label]+[b['text'] for b in rows]
    if card is None:pieces.append('<p>No model overview generated. The source details below were retained by rules.</p>')
    if source_fallback:
        notice='SOURCE-ONLY FALLBACK — the model selected no highlights. The complete original text follows without model ranking or summarization. Review required.'
        pieces.append('<section class="warning"><h2>Source-only fallback</h2><p>'+esc(notice)+'</p><pre>'+esc(a['body'])+'</pre></section>')
        plain+=[notice,a['body']]
    if packet['hold_reasons']:
        pieces.append('<h2>Held for source review</h2><p>'+esc(', '.join(packet['hold_reasons']))+'</p>')
        plain+=packet['hold_reasons']
    else:
        pieces.append('<section><h2>Details retained independently of the model</h2>')
        already_visible={b['id'] for rows in selected.values() for b in rows}
        if source_fallback:already_visible={b['id'] for b in blocks(a['body'])}
        overlap=sum(b['id'] in already_visible for b in packet['protected'])
        if overlap:
            note=f'{overlap} protected source block(s) are already quoted in full above; they are not repeated here.'
            pieces.append('<p>'+note+'</p>');plain.append(note)
        for b in packet['protected']:
            if b['id'] not in already_visible:
                pieces.append(quote(b));plain.append(b['text'])
        if not packet['protected']:
            pieces.append('<p>No protected detail was identified; this is not proof that none exists.</p>')
        pieces.append('</section>')
    warnings=''.join('<li>'+esc(s)+'</li>' for s in packet['warnings']);plain+=packet['warnings']
    link='<p>No original source link: synthetic evaluation example.</p>' if a['source']=='synthetic' else '<p><a rel="noreferrer" href="'+esc(a['url'],quote=True)+'">Read original source ↗</a></p>'
    styles='body{margin:0;background:#f4f2e9;color:#193d31;font:16px/1.6 system-ui}main{max-width:840px;margin:auto;padding:28px}h1{line-height:1.2}h2{font-size:21px}section{margin:28px 0}blockquote{margin:14px 0;padding:14px 18px;background:white;border-left:3px solid #789985}blockquote p{margin:0 0 8px}small{color:#53665c}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}.warning{background:#fff0d2;padding:16px}a{color:#17664b}'
    archive='' if source_fallback else '<details><summary>Full source text — inspect context</summary><pre>'+esc(a['body'])+'</pre></details>'
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>MiniCPM News Desk — review</title><style>'+styles+'</style><main><p>LOCAL · EXTRACTIVE · REVIEW REQUIRED</p><h1>'+esc(a['title'])+'</h1><p>'+esc(origin)+' · '+esc(packet['status'])+'</p><p>'+esc(' | '.join(plain[4:6]))+'</p>'+link+'<aside class="warning"><ul>'+warnings+'</ul></aside>'+''.join(pieces)+archive+'<p>Overview candidates: '+str(len(packet['pool']))+' blocks. Other eligible blocks outside the overview pool: '+str(packet['counts']['eligible_blocks_not_in_pool'])+'. Nothing is automatically approved or sent.</p></main></html>'
    return '\n\n'.join(plain),page
