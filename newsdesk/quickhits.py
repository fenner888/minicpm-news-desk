"""Publisher descriptions for quick hits; never full-article/model summaries."""
import hashlib
from html.parser import HTMLParser
import json
import re
import subprocess
import sys
from urllib.parse import urlsplit
from . import digest as d
from .network import _public_html, MAX_HTML

SOURCES = {
    'aws': ('aws.amazon.com', '/blogs/machine-learning/'),
    'google': ('blog.google', '/'),
    'vercel': ('vercel.com', '/changelog/'),
    'langchain': ('www.langchain.com', '/blog/'),
    'lmstudio': ('lmstudio.ai', '/blog/'),
}


def checked(item):
    d.text(item['title'],2000)
    target=d.url(item['url']); parsed=urlsplit(target)
    host,prefix=SOURCES[item['source']]
    if parsed.hostname!=host or not parsed.path.startswith(prefix) or parsed.path==prefix or parsed.query:
        raise ValueError('description_source_mismatch')
    return target,host


def excerpt(value,title):
    """Keep the whole usable description, or complete feed sentences only.

    The trailing fragment is never completed. All complete sentences within the
    accepted excerpt are retained, including qualifications; no word-count trim.
    """
    if not isinstance(value,str) or len(value)>2000:return ''
    value=' '.join(value.split())
    if not value or re.search(r'<|>|\bMEDIA\s*:|https?://|www\.|\[|\]|\*|`|[\u202a-\u202e\u2066-\u2069]',value,re.I):return ''
    # Sentence boundaries require whitespace/end, avoiding decimal/version dots.
    ends=list(re.finditer(r'(?<!\.)[.!?](?!\.)(?:[”\"])?(?=\s|$)',value))
    if not ends:return ''
    result=value[:ends[-1].end()].strip()
    if '…' in result or '...' in result or len(result.split())>100:return ''
    if len(result.split())<6 or result.casefold().rstrip('.')==title.casefold().rstrip('.'):return ''
    return result


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.values=[];self.in_head=False;self.done=False

    def handle_starttag(self,tag,attrs):
        if tag=='head' and not self.done:self.in_head=True
        if tag!='meta' or not self.in_head:return
        a=dict(attrs)
        if a.get('name','').lower()=='description' or a.get('property','').lower()=='og:description':
            self.values.append(a.get('content',''))

    def handle_endtag(self,tag):
        if tag=='head':self.in_head=False;self.done=True


def extract(raw,title):
    if not isinstance(raw,bytes) or len(raw)>MAX_HTML:raise ValueError('html_size_limit')
    parser=Metadata();parser.feed(raw.decode('utf-8',errors='replace'))
    if not parser.done:return ''
    # Conflicting metadata is held rather than choosing the more flattering text.
    values={' '.join(v.split()) for v in parser.values if v.strip()}
    if len(values)!=1:return ''
    value=values.pop()
    result=excerpt(value,title)
    words=lambda s:set(re.findall(r'[a-z]{3,}',s.lower()))-{'the','and','with','for','now','new','available','introducing'}
    if not words(title).intersection(words(result)):return ''
    # Metadata must be complete; only collector excerpts may be known truncations.
    return result if result==value else ''


def fetch(item):
    checked(item)
    payload={k:item[k] for k in ('source','url','title')}
    if len(json.dumps(payload))>6000:raise ValueError('description_request_size')
    result=subprocess.run([sys.executable,'-m','newsdesk.quickhits'],input=json.dumps(payload).encode(),
                          capture_output=True,timeout=45)
    if result.returncode or len(result.stdout)>10000:raise ValueError('description_worker_failed')
    row=json.loads(result.stdout)
    if row.get('error'):raise ValueError('description_unavailable')
    if row.get('url')!=d.url(item['url']) or row.get('source')!=item['source']:raise ValueError('description_identity')
    if row.get('text')!=excerpt(row.get('text'),item['title']):raise ValueError('description_invalid')
    return row


def collect(items,cards,failures,fetch_budget,get=fetch):
    if type(fetch_budget) is not int or not 0<=fetch_budget<=6:raise ValueError('description_budget')
    rows={};attempts=0
    for item in items:
        if item['id'] in cards or item['id'] in failures:continue
        value=excerpt(item.get('excerpt',''),item['title'])
        row={'url':d.url(item['url']),'source':item['source'],'text':value,
             'provenance':'feed excerpt','excerpt_sha256':hashlib.sha256(item.get('excerpt','').encode()).hexdigest()}
        if not value and attempts<fetch_budget:
            try:checked(item)
            except (ValueError,KeyError):continue
            attempts+=1
            try:row=get(item)
            except Exception:continue
            if row.get('url')!=d.url(item['url']) or row.get('source')!=item['source']:continue
            value=excerpt(row.get('text'),item['title'])
            if value!=row.get('text'):continue
        if value:rows[item['id']]=row
    return rows,attempts


if __name__=='__main__':
    try:
        raw=sys.stdin.buffer.read(6001)
        if len(raw)>6000:raise ValueError('description_request_size')
        item=json.loads(raw);target,host=checked(item)
        body=_public_html(target,host)
        print(json.dumps({'source':item['source'],'url':target,'text':extract(body,item['title']),
                          'provenance':'page description','html_sha256':hashlib.sha256(body).hexdigest()}))
    except Exception:
        print(json.dumps({'error':'description_unavailable'}))
