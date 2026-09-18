"""Bounded public retrieval and explicitly opted-in numeric-loopback inference."""
import base64
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlsplit
from .core import SOURCES, article_url, retrieval_url, loads, text

MAX_HTML = 2_000_000


def public_addresses(host, resolver=socket.getaddrinfo):
    values = sorted({r[4][0] for r in resolver(host,443,type=socket.SOCK_STREAM)})
    if not values or any(not ipaddress.ip_address(v).is_global for v in values):
        raise ValueError('nonpublic_dns')
    return values


def fetch_direct(sid, url):
    sid = article_url(sid, url)
    url = retrieval_url(sid, url)
    host = SOURCES[sid][1]; address = public_addresses(host)[0]
    start = time.monotonic()
    context = ssl.create_default_context()
    connection = http.client.HTTPSConnection(host, timeout=15, context=context)
    raw_socket = socket.create_connection((address,443),timeout=15)
    try:
        connection.sock = context.wrap_socket(raw_socket,server_hostname=host)
        connection.request('GET', urlsplit(url).path, headers={
            'User-Agent':'MiniCPM-News-Desk/0.6.2 source review',
            'Accept':'text/html', 'Accept-Encoding':'identity'})
        response = connection.getresponse()
        if response.status == 403 and response.getheader('cf-mitigated') == 'challenge':
            raise ValueError('http_status_403_challenge')
        if response.status != 200:
            raise ValueError('http_status_' + str(response.status))
        if response.getheader('Content-Encoding','identity') not in ('identity',''):
            raise ValueError('compressed_response_rejected')
        if response.getheader('Content-Type','').split(';')[0].strip().lower() != 'text/html':
            raise ValueError('not_html')
        size = response.getheader('Content-Length')
        if size and (not size.isdecimal() or int(size)>MAX_HTML):
            raise ValueError('html_size_limit')
        parts = []; total = 0
        while True:
            remaining = 30-(time.monotonic()-start)
            if remaining <= 0: raise TimeoutError('fetch_deadline')
            if connection.sock: connection.sock.settimeout(min(10,remaining))
            chunk = response.read1(min(65536,MAX_HTML+1-total))
            if not chunk: break
            total += len(chunk)
            if total > MAX_HTML: raise ValueError('html_size_limit')
            parts.append(chunk)
        return b''.join(parts)
    finally:
        connection.close(); raw_socket.close()


def config_checked(config):
    expected = {'endpoint','model','api_key_env','context_tokens','max_tokens'}
    if not isinstance(config,dict) or set(config)!=expected:
        raise ValueError('invalid_model_config')
    u = urlsplit(text(config['endpoint'],150))
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','::1') or u.username or u.password or u.path not in ('','/') or u.query or u.fragment or u.port is None or not 1024 <= u.port <= 65535:
        raise ValueError('model_requires_explicit_loopback_port')
    if config['model'] != 'MiniCPM5-2B-Q4_K_M':
        raise ValueError('unqualified_model_identity')
    if not isinstance(config['api_key_env'],str) or not re.fullmatch(r'MINICPM_[A-Z0-9_]+',config['api_key_env']):
        raise ValueError('invalid_key_environment_name')
    if type(config['context_tokens']) is not int or config['context_tokens']!=8192 or type(config['max_tokens']) is not int or config['max_tokens']!=4096:
        raise ValueError('unqualified_budget')
    return config


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def model_direct(config, body, opener=None):
    config_checked(config)
    if body.get('response_format',{}).get('json_schema',{}).get('name')=='source_highlights':
        if type(body.get('reasoning_budget_tokens')) is not int or body['reasoning_budget_tokens']!=512:
            raise ValueError('highlight_reasoning_budget_required')
    key = os.environ.get(config['api_key_env'],'')
    if not 16 <= len(key) <= 4096 or any(ord(c)<33 or ord(c)>126 for c in key):
        raise ValueError('missing_or_invalid_model_key')
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    endpoint = config['endpoint'].rstrip('/')
    def call(path, payload=None, timeout=10):
        req=urllib.request.Request(endpoint+path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
        with opener.open(req,timeout=timeout) as r:
            if r.status != 200: raise ValueError('model_http_error')
            raw=r.read(1_000_001)
        if len(raw)>1_000_000: raise ValueError('model_response_size')
        parsed=loads(raw)
        if key in json.dumps(parsed,ensure_ascii=False): raise ValueError('credential_echo')
        return parsed
    if body.get('model')!=config['model'] or body.get('max_tokens')!=4096:
        raise ValueError('request_config_mismatch')
    models=call('/v1/models')
    if config['model'] not in [m['id'] for m in models['data']]:
        raise ValueError('wrong_model_server')
    props=call('/props')
    if props.get('default_generation_settings',{}).get('n_ctx')!=8192:
        raise ValueError('server_context_mismatch')
    prompt=call('/apply-template',{'messages':body['messages'],'add_generation_prompt':True})['prompt']
    text(prompt,50000)
    tokens=call('/tokenize',{'content':prompt,'add_special':True})['tokens']
    if not isinstance(tokens,list) or len(tokens)+4096+64>8192:
        raise ValueError('context_budget_exceeded')
    if prompt.endswith('<think>\n\n</think>\n\n'):
        raise ValueError('thinking_disabled')
    return call('/v1/chat/completions',body,timeout=420)


def worker(mode, payload):
    """Hard process deadline also covers DNS and slow-drip responses."""
    raw=json.dumps(payload).encode()
    if len(raw)>100000: raise ValueError('worker_input_size')
    result=subprocess.run([sys.executable,'-m','newsdesk.network',mode],
        input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        timeout=45 if mode=='fetch' else 480)
    if result.returncode or len(result.stdout)>3_000_000:
        raise ValueError('worker_failed')
    envelope=loads(result.stdout)
    if 'error' in envelope:
        code=envelope['error']
        if not isinstance(code,str) or not re.fullmatch(r'[A-Za-z0-9_]{1,80}',code): code='worker_error'
        raise ValueError(code)
    return envelope


def fetch(sid,url):
    article_url(sid,url)  # validate before any child or network operation
    result=worker('fetch',{'source':sid,'url':url})
    raw=base64.b64decode(result['body'],validate=True)
    if len(raw)>MAX_HTML: raise ValueError('html_size_limit')
    return raw


def infer(config,body):
    config_checked(config)
    return worker('model',{'config':config,'body':body})['response']


if __name__=='__main__':
    try:
        request=loads(sys.stdin.buffer.read(100001))
        if sys.argv[1:] == ['fetch']:
            body=fetch_direct(request['source'],request['url'])
            print(json.dumps({'body':base64.b64encode(body).decode()}))
        elif sys.argv[1:] == ['model']:
            print(json.dumps({'response':model_direct(request['config'],request['body'])}))
        else: raise ValueError('invalid_worker_mode')
    except Exception as exc:
        # Do not serialize URL/auth response text or exception details.
        code=str(exc) if type(exc) is ValueError and re.fullmatch(r'[a-z0-9_]{1,80}',str(exc)) else type(exc).__name__
        print(json.dumps({'error':code}))
