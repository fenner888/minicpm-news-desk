"""Pure validation, source boundaries, evidence contract and escaped reporting."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import html
import json
import math
import re
from urllib.parse import urlsplit

SOURCES = {
    'openai': ('OpenAI', 'openai.com', '/index/'),
    'xai': ('SpaceXAI / Grok (xAI)', 'x.ai', '/news/'),
    'github': ('GitHub / Copilot', 'github.blog', '/changelog/'),
}
ALIASES = {'spacexai': 'xai', 'grok': 'xai'}
FIELDS = ('what_changed', 'why_it_matters', 'who_its_for', 'availability', 'pricing', 'limitations')
CONTRACT = 'newsdesk-passages-v1'


def text(value, maximum):
    if not isinstance(value, str) or len(value) > maximum or any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise ValueError('invalid_text')
    return value


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def loads(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    def bad_constant(_):
        raise ValueError('nonfinite_json_number')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)


def source_id(value):
    text(value, 60)
    return ALIASES.get(value.lower(), value.lower())


def public_url(value):
    text(value, 2048)
    if re.search(r'[\s\\<>\[\]{}\x7f]', value):
        raise ValueError('invalid_url')
    u = urlsplit(value)
    if u.scheme != 'https' or u.username or u.password or u.port not in (None, 443) or u.fragment or u.query:
        raise ValueError('invalid_url')
    if u.hostname not in {v[1] for v in SOURCES.values()}:
        raise ValueError('unsupported_host')
    if '%' in u.path or '..' in u.path or '//' in u.path:
        raise ValueError('noncanonical_path')
    return u


def article_url(sid, url):
    sid = source_id(sid)
    if sid not in SOURCES:
        raise ValueError('unsupported_source')
    u = public_url(url)
    if u.hostname != SOURCES[sid][1] or not u.path.startswith(SOURCES[sid][2]) or not u.path[len(SOURCES[sid][2]):].strip('/'):
        raise ValueError('source_url_mismatch')
    return sid


def retrieval_url(sid, url):
    """GitHub's observed canonical slash, never a server-chosen redirect."""
    sid = article_url(sid, url)
    target = url + '/' if sid == 'github' and not url.endswith('/') else url
    article_url(sid, target)
    return target


def timestamp(value):
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 4102444800):
        raise ValueError('invalid_timestamp')
    return value


def normalize_snapshot(data):
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1 or not isinstance(data.get('items'), list) or len(data['items']) > 30000:
        raise ValueError('invalid_snapshot')
    result = []; seen = set()
    for item in data['items']:
        sid = source_id(item['source'])
        title = text(item['title'], 2000)
        url = text(item['url'], 2048)
        # Unsupported discovery records are retained as inert text, never fetched.
        try:
            article_url(sid, url)
            supported = True
        except ValueError:
            supported = False
        identity = (sid, url.rstrip('/'))
        if identity in seen:
            continue
        seen.add(identity)
        result.append({'source': sid, 'title': title, 'url': url,
                       'published': timestamp(item.get('published')),
                       'first_seen': timestamp(item.get('first_seen')),
                       'excerpt': text(item.get('excerpt', ''), 20000),
                       'status': 'discovered_only' if supported else 'unsupported_source',
                       'eligible_for_fetch': supported})
    return result


class ArticleParser(HTMLParser):
    """One known body container, strict nesting, no generic main/body fallback."""
    VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
    EXCLUDE = set('script style nav footer header aside noscript svg button iframe template'.split())
    BLOCK = set('p li h1 h2 h3 h4 h5 h6 div section br pre tr blockquote'.split())

    def __init__(self, sid):
        super().__init__(convert_charrefs=True)
        self.sid = sid; self.stack = []; self.parts = []
        self.target_depth = None; self.count = 0; self.closed = False
        self.title_depth = None; self.titles = []; self.title_count = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs); classes = d.get('class', '').split()
        parent_tags = [s[0] for s in self.stack]
        blocked = (any(s[1] for s in self.stack) or tag in self.EXCLUDE or
                   'hidden' in d or 'sr-only' in classes or d.get('aria-hidden') == 'true' or
                   bool(re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', d.get('style',''), re.I)))
        if tag not in self.VOID:
            self.stack.append((tag, blocked))
        match = ((self.sid == 'xai' and 'prose' in classes) or
                 (self.sid == 'openai' and 'data-toc-content' in d and 'article' in parent_tags) or
                 (self.sid == 'github' and 'PostContent-main' in classes))
        if match:
            self.count += 1
            if blocked or tag in self.VOID or self.target_depth is not None:
                raise ValueError('ambiguous_article_container')
            self.target_depth = len(self.stack)
        if tag == 'h1' and not blocked:
            self.title_count += 1; self.title_depth = len(self.stack)
        if tag in self.BLOCK:
            self.handle_data('\n')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            if self.target_depth is not None:
                raise ValueError('malformed_article_nesting')
            # Browser HTML can omit end tags outside the protected body.
            positions = [i for i, s in enumerate(self.stack) if s[0] == tag]
            if positions:
                del self.stack[positions[-1]:]
            return
        if tag in self.BLOCK:
            self.handle_data('\n')
        if self.title_depth == len(self.stack):
            self.title_depth = None
        if self.target_depth == len(self.stack):
            self.closed = True; self.target_depth = None
        self.stack.pop()

    def handle_data(self, value):
        if any(s[1] for s in self.stack):
            return
        if self.title_depth is not None:
            self.titles.append(value)
        if self.target_depth is not None:
            self.parts.append(value)

    def result(self):
        if self.count != 1 or not self.closed or self.target_depth is not None:
            raise ValueError('missing_ambiguous_or_unclosed_body')
        body = '\n'.join(' '.join(line.split()) for line in ''.join(self.parts).splitlines() if line.strip())
        if not 80 <= len(body) <= 100000:
            raise ValueError('article_size_outside_archive_budget')
        text(body, 100000)
        return body, ' '.join(''.join(self.titles).split()) if self.title_count == 1 else ''


def extract(sid, url, raw):
    sid = article_url(sid, url)
    if not isinstance(raw, bytes) or len(raw) > 2_000_000:
        raise ValueError('html_size_limit')
    parser = ArticleParser(sid)
    parser.feed(raw.decode('utf-8', errors='strict')); parser.close()
    body, title = parser.result()
    return {'source': sid, 'url': url, 'title': title or SOURCES[sid][0] + ' article',
            'body': body, 'source_sha256': digest(body), 'html_sha256': hashlib.sha256(raw).hexdigest(),
            'contract': CONTRACT, 'adapter': sid + '-body-v1',
            'coverage': 'known HTML body; embedded media and linked documents not transcribed',
            'published': None, 'first_seen': None, 'review_status': 'needs_review'}


def passages(body):
    text(body, 7000)
    if not body.strip():
        raise ValueError('empty_body')
    result = []; start = 0
    for match in list(re.finditer(r'(?<=[.!?])\s+|\n+', body)) + [None]:
        if match and '\n' not in match.group() and re.search(r'(?:\b(?:[A-Za-z]\.){2,}|\b(?:Dr|Mr|Mrs|Ms|Prof|St|vs|etc)\.)$', body[:match.start()], re.I):
            continue
        end = match.start() if match else len(body)
        left = start
        while left < end and body[left].isspace(): left += 1
        while end > left and body[end-1].isspace(): end -= 1
        if left < end:
            result.append({'id': f'p{len(result)+1:03d}', 'start': left, 'end': end, 'text': body[left:end]})
        start = match.end() if match else len(body)
    if len(result) > 80:
        raise ValueError('too_many_passages')
    return result


def resolve_response(response, article):
    if article.get('contract') != CONTRACT or digest(article['body']) != article['source_sha256']:
        raise ValueError('source_contract_or_hash_mismatch')
    choices = response['choices']
    if len(choices) != 1 or choices[0].get('finish_reason') != 'stop':
        raise ValueError('incomplete_response')
    message = choices[0]['message']
    if message.get('tool_calls') or message.get('function_call'):
        raise ValueError('tool_output_forbidden')
    if not isinstance(message.get('reasoning_content'), str) or not message['reasoning_content'].strip():
        raise ValueError('reasoning_not_verified')
    card = loads(text(message['content'], 18000))
    if not isinstance(card, dict) or set(card) != set(FIELDS):
        raise ValueError('invalid_card_schema')
    lookup = {p['id']: p for p in passages(article['body'])}
    resolved = {}
    for field, value in card.items():
        if value is None:
            resolved[field] = None; continue
        if not isinstance(value, dict) or set(value) != {'text','evidence_ids'}:
            raise ValueError('invalid_field')
        claim = text(value['text'], 600)
        ids = value['evidence_ids']
        if not claim.strip() or not isinstance(ids, list) or not 1 <= len(ids) <= 8 or any(type(i) is not str for i in ids) or len(set(ids)) != len(ids) or any(i not in lookup for i in ids):
            raise ValueError('invalid_evidence_ids')
        resolved[field] = {'text': claim, 'evidence': [lookup[i] for i in ids]}
    return {'contract': CONTRACT, 'source_sha256': article['source_sha256'],
            'status': 'unreviewed_model_draft', 'fields': resolved,
            'warning': 'Passage IDs do not prove meaning or completeness. Review price, access and restrictions against the full source.'}


def render(rows, label):
    pieces = []; lines = ['MINICPM NEWS DESK', label, 'Review required. Discovery time is not release time.', '']
    for row in rows:
        title = text(row['title'], 2000)
        status = row.get('status', row.get('review_status', 'needs_review'))
        body = row.get('body', row.get('excerpt', 'No article body available.'))
        bits = [title, 'Status: ' + status]
        for key in ('published', 'first_seen'):
            stamp = timestamp(row.get(key))
            bits.append(key.replace('_',' ').capitalize() + ': ' + (datetime.fromtimestamp(stamp,timezone.utc).isoformat() if stamp is not None else 'Unknown'))
        bits += [row.get('coverage', 'Discovery excerpt only; not a full article.'), body]
        for field, value in row.get('draft', {}).get('fields', {}).items():
            bits.append(field.replace('_',' ').capitalize() + ': ' + (value['text'] if value else 'Not extracted; check source.'))
        link = ''
        try:
            article_url(row['source'], row['url'])
            link = '<a href="' + html.escape(row['url'], quote=True) + '" rel="noreferrer">Read original source ↗</a>'
            bits.append('Source: ' + row['url'])
        except (KeyError, ValueError):
            bits.append('No qualified source link; discovery retained in local JSON.')
        lines.extend(bits + [''])
        pieces.append('<article><h2>' + html.escape(title) + '</h2><p class="badge">' + html.escape(status) + '</p><pre>' + html.escape('\n'.join(bits[2:])) + '</pre>' + link + '</article>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>MiniCPM News Desk</title><style>body{margin:0;background:#f4f2e9;color:#193d31;font:16px/1.6 system-ui}main{max-width:820px;margin:auto;padding:28px}h1{font-size:clamp(30px,6vw,44px);line-height:1.15}h2{font-size:23px;line-height:1.3}article{padding:24px;background:white;border:1px solid #d8dfd8;border-radius:12px;margin:24px 0}pre{font:inherit;white-space:pre-wrap;overflow-wrap:anywhere}a{color:#17664b}.badge{font-size:13px;color:#684922}footer{font-size:13px}</style><main><p>LOCAL · SOURCE-LINKED · REVIEW REQUIRED</p><h1>MiniCPM News Desk</h1><p>''' + html.escape(label) + '</p>' + ''.join(pieces) + '<footer>Read the original for depth. Exact source text and model prose are separate; cited passages still require meaning review.</footer></main></html>'
    return '\n'.join(lines), page
