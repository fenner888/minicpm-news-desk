"""Small fixed-source RSS collector; no arbitrary feed URLs or XML entities."""
import base64
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import re
from xml.etree import ElementTree as ET
from . import core, digest, network

FEEDS={'github':'https://github.blog/changelog/feed/',
       'openai':'https://openai.com/news/rss.xml'}
MAX_ITEMS=2000  # OpenAI publishes a historical RSS archive, not just recent items.


def fetch(source):
    if source not in FEEDS:raise ValueError('unsupported_feed')
    result=network.worker('feed',{'source':source})
    raw=base64.b64decode(result['body'],validate=True)
    if len(raw)>network.MAX_HTML:raise ValueError('feed_size')
    return raw


def plain(value):
    class Text(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.skip=0
        def handle_starttag(self,tag,attrs):
            if tag in ('script','style'):self.skip+=1
        def handle_endtag(self,tag):
            if tag in ('script','style'):self.skip=max(0,self.skip-1)
            if tag in ('p','div','br','li'):self.parts.append(' ')
        def handle_data(self,data):
            if not self.skip:self.parts.append(data)
    parser=Text();parser.feed(value)
    return ' '.join(''.join(parser.parts).split())


def parse(source,raw,now):
    if source not in FEEDS:raise ValueError('unsupported_feed')
    digest.stamp(now)
    if not isinstance(raw,bytes) or len(raw)>network.MAX_HTML:raise ValueError('feed_size')
    # XML is required to be UTF-8; rejecting other encodings closes declaration
    # obfuscation and lets this check precede all parsing/entity expansion.
    value=raw.decode('utf-8-sig')
    declarations=re.sub(r'<!\[CDATA\[.*?\]\]>|<!--.*?-->',' ',value,flags=re.S)
    if '\x00' in value or re.search(r'<!\s*(?:DOCTYPE|ENTITY)',declarations,re.I):raise ValueError('unsafe_feed_xml')
    encoding=re.search(r'<\?xml[^>]*encoding=[\"\x27]([^\"\x27]+)',value,re.I)
    if encoding and encoding[1].lower() not in ('utf-8','utf8'):raise ValueError('feed_encoding')
    root=ET.fromstring(value)
    if root.tag!='rss' or root.find('channel') is None:raise ValueError('unsupported_feed_format')
    nodes=root.findall('./channel/item')
    if len(nodes)>MAX_ITEMS:raise ValueError('feed_item_budget')
    rows=[];rejected=0
    for node in nodes:
        try:
            target=(node.findtext('link') or '').strip()
            core.article_url(source,target)
            title=plain(node.findtext('title') or '')
            excerpt=plain(node.findtext('description') or '')
            published=None;date=node.findtext('pubDate')
            if date:
                try:
                    parsed=parsedate_to_datetime(date)
                    if parsed.tzinfo is not None:published=core.timestamp(parsed.timestamp())
                except (ValueError,TypeError,OverflowError):pass
            row={'source':source,'title':title,'url':target,'excerpt':excerpt,
                 'published':published,'first_seen':now}
            digest.normalized(row,now)
            rows.append(row)
        except (ValueError,TypeError):rejected+=1
    return {'items':rows,'rejected_items':rejected,'listed_items':len(nodes)}
