"""Render only application-owned Markdown tokens; source entities stay inert."""
import html
from html.parser import HTMLParser
import re
from . import digest as d

TOKENS=re.compile(r'\[Read the source ↗\]\((https://[^\s)]+)\)|\*\*(.+?)\*\*|\*([^*]+)\*',re.S)


def escaped(value):
    # Decode entities only after identifying app-owned formatting, then escape
    # for HTML. Source '**', '<script>' and entity-like literals stay plain text.
    return html.escape(html.unescape(value),quote=False)


def telegram_html(markdown):
    if not isinstance(markdown,str) or d.units(markdown)>3400:
        raise ValueError('message_budget')
    chunks=[];offset=0
    for match in TOKENS.finditer(markdown):
        chunks.append(escaped(markdown[offset:match.start()]))
        link,bold,italic=match.groups()
        if link:
            target=d.url(link)
            chunks.append('<a href="'+html.escape(target,quote=True)+'">Read the source ↗</a>')
        elif bold is not None:chunks.append('<b>'+escaped(bold)+'</b>')
        else:chunks.append('<i>'+escaped(italic)+'</i>')
        offset=match.end()
    chunks.append(escaped(markdown[offset:]))
    rendered=''.join(chunks)
    if d.units(visible_text(rendered))>4096:raise ValueError('telegram_text_budget')
    return rendered


def visible_text(markup):
    class Text(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
        def handle_data(self,data):self.parts.append(data)
    parser=Text();parser.feed(markup)
    return ''.join(parser.parts)


def preview(parts,title='MiniCPM News Desk'):
    blocks=''.join('<section>'+telegram_html(p)+'</section>' for p in parts)
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            '<title>'+html.escape(title)+' — preview</title><style>'
            'body{max-width:760px;margin:32px auto;padding:0 20px;background:#f5f3e9;color:#203b30;font:16px/1.65 system-ui}'
            'section{white-space:pre-wrap;overflow-wrap:anywhere;background:white;border:1px solid #d9dfd6;border-radius:12px;padding:24px;margin:20px 0}'
            'a{color:#276049}h1{font-size:26px}</style><h1>'+html.escape(title)+'</h1>'
            '<p>Private preview · review sources before sending. This page does not send messages.</p>'+blocks+'</html>')
