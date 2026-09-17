import copy
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from newsdesk import core as c, network as n, workflow as w

BODY='Dr. Doe describes U.S. workshops for U.K. teams. The tool costs $1.25 per request. Access requires approval. Pricing for larger teams has not been announced.'
URL='https://x.ai/news/example'
CONFIG={'endpoint':'http://127.0.0.1:8093','model':'MiniCPM5-2B-Q4_K_M','api_key_env':'MINICPM_API_KEY','context_tokens':8192,'max_tokens':4096}


def markup(sid,body=BODY):
    if sid=='xai': return ('<h1>Example</h1><div class="prose">'+body+'</div>').encode()
    if sid=='openai': return ('<article><h1>Example</h1><div data-toc-content>'+body+'</div><section id="citations">Excluded</section><div>Keep reading</div></article>').encode()
    return ('<h1>Example</h1><div class="PostContent-main">'+body+'</div>').encode()


def article(): return c.extract('xai',URL,markup('xai'))


def response(claim='The tool has a per-request price.'):
    card={k:None for k in c.FIELDS}
    card['what_changed']={'text':claim,'evidence_ids':['p002']}
    return {'choices':[{'finish_reason':'stop','message':{'reasoning_content':'Synthetic test reasoning.','content':json.dumps(card)}}]}


class CoreTests(unittest.TestCase):
    def test_all_three_containers(self):
        for sid,(_,host,path) in c.SOURCES.items():
            with self.subTest(source=sid):
                a=c.extract(sid,'https://'+host+path+'test',markup(sid))
                self.assertEqual(a['body'],BODY)
                self.assertEqual(a['title'],'Example')
                self.assertNotIn('Keep reading',a['body'])

    def test_no_generic_fallback(self):
        for raw in (b'<main>'+BODY.encode()+b'</main>',b'<article>'+BODY.encode()+b'</article>'):
            with self.assertRaises(ValueError):c.extract('openai','https://openai.com/index/test',raw)

    def test_openai_marker_must_be_in_article(self):
        with self.assertRaises(ValueError):c.extract('openai','https://openai.com/index/test',b'<div data-toc-content>'+BODY.encode()+b'</div>')

    def test_duplicate_container(self):
        with self.assertRaises(ValueError):c.extract('xai',URL,markup('xai')*2)

    def test_nested_container(self):
        with self.assertRaises(ValueError):c.extract('xai',URL,b'<div class="prose"><div class="prose">'+BODY.encode()+b'</div></div>')

    def test_truncated_container(self):
        with self.assertRaises(ValueError):c.extract('xai',URL,markup('xai')[:-6])

    def test_bad_nesting(self):
        with self.assertRaises(ValueError):c.extract('xai',URL,b'<div class="prose"><p>'+BODY.encode()+b'</div>')

    def test_excludes_unsafe_or_hidden_content(self):
        raw=b'<div class="prose"><p>'+BODY.encode()+b'</p><script>BAD</script><nav>BAD</nav><div hidden>BAD</div><span aria-hidden="true">BAD</span><i style="display:none">BAD</i><iframe>BAD</iframe></div>'
        self.assertNotIn('BAD',c.extract('xai',URL,raw)['body'])

    def test_hidden_body_rejected(self):
        with self.assertRaises(ValueError):c.extract('xai',URL,b'<div hidden class="prose">'+BODY.encode()+b'</div>')

    def test_multiblock_and_inline_spacing(self):
        raw=markup('xai','<p>Pay <b>only</b> when approved.</p><p>'+BODY+'</p>')
        self.assertIn('Pay only when approved.\n',c.extract('xai',URL,raw)['body'])

    def test_archive_large_body_but_model_rejects(self):
        a=c.extract('xai',URL,markup('xai','a'*8000))
        self.assertEqual(len(a['body']),8000)
        with self.assertRaises(ValueError):w.request_for(a,CONFIG)

    def test_too_short(self):
        with self.assertRaises(ValueError):c.extract('xai',URL,markup('xai','tiny'))

    def test_size_and_encoding(self):
        for raw in (b'x'*2000001,b'\xff'):
            with self.assertRaises((ValueError,UnicodeError)):c.extract('xai',URL,raw)

    def test_url_boundaries(self):
        for url in ('http://x.ai/news/a','https://x.ai.evil.test/news/a','https://x.ai@evil.test/news/a','https://127.0.0.1/news/a','https://x.ai/news/a?secret=x','https://x.ai/news/a#x','https://x.ai/news/../a','https://x.ai/news/%2e%2e','https://x.ai/news/','https://x.ai:8080/news/a','https://x.ai\\evil.test/news/a'):
            with self.subTest(url=url),self.assertRaises(ValueError):c.article_url('xai',url)

    def test_source_mismatch(self):
        with self.assertRaises(ValueError):c.article_url('openai',URL)

    def test_alias_deduplication(self):
        data={'version':1,'items':[{'source':s,'title':'Example','url':URL,'excerpt':''} for s in ('xai','SpaceXAI','grok')]}
        self.assertEqual(len(c.normalize_snapshot(data)),1)

    def test_unsupported_retained(self):
        rows=c.normalize_snapshot({'version':1,'items':[{'source':'other','title':'Untested','url':'http://127.0.0.1/private'}]})
        self.assertEqual(rows[0]['status'],'unsupported_source')
        self.assertFalse(rows[0]['eligible_for_fetch'])
        self.assertNotIn('href=',c.render(rows,'test')[1])

    def test_timestamp_validation(self):
        for value in (True,'yesterday',float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError):c.timestamp(value)
        self.assertIsNone(c.timestamp(None))

    def test_duplicate_json_and_nan(self):
        for raw in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):c.loads(raw)

    def test_offsets_abbreviations(self):
        ps=c.passages(BODY)
        self.assertEqual(len(ps),4)
        self.assertIn('U.S.',ps[0]['text'])
        for p in ps:self.assertEqual(BODY[p['start']:p['end']],p['text'])

    def test_passage_limit(self):
        with self.assertRaises(ValueError):c.passages('Sentence. '*81)

    def test_resolve_review_required(self):
        draft=c.resolve_response(response(),article())
        self.assertEqual(draft['status'],'unreviewed_model_draft')
        self.assertEqual(draft['fields']['what_changed']['evidence'][0]['text'],'The tool costs $1.25 per request.')

    def test_real_citation_never_certifies_false_claim(self):
        draft=c.resolve_response(response('Everything is free.'),article())
        self.assertEqual(draft['status'],'unreviewed_model_draft')
        self.assertIn('do not prove',draft['warning'])

    def test_source_hash_and_contract(self):
        for field,value in [('body','tampered'),('contract','old')]:
            a=article();a[field]=value
            with self.assertRaises(ValueError):c.resolve_response(response(),a)

    def test_invalid_ids(self):
        for ids in (['p999'],['p001','p001'],[{}],[]):
            r=response(); card=json.loads(r['choices'][0]['message']['content']);card['what_changed']['evidence_ids']=ids
            r['choices'][0]['message']['content']=json.dumps(card)
            with self.assertRaises(ValueError):c.resolve_response(r,article())

    def test_reject_incomplete_tool_and_no_reasoning(self):
        for change in ('finish','tool','reason'):
            r=response()
            if change=='finish':r['choices'][0]['finish_reason']='length'
            if change=='tool':r['choices'][0]['message']['tool_calls']=[{'name':'shell'}]
            if change=='reason':r['choices'][0]['message']['reasoning_content']=''
            with self.assertRaises(ValueError):c.resolve_response(r,article())

    def test_escape_report(self):
        a=article();a.update(title='<img src=x onerror=alert(1)>',body='<script>BAD</script>')
        page=c.render([a],'<iframe>')[1]
        self.assertNotIn('<script>',page);self.assertNotIn('<img',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertIn("default-src 'none'",page)


class NetworkTests(unittest.TestCase):
    def test_private_dns(self):
        for ip in ('127.0.0.1','10.0.0.1','169.254.169.254','::1','fd00::1'):
            with self.assertRaises(ValueError):n.public_addresses('x.ai',lambda *a,**k:[(0,0,0,'',(ip,443))])

    def test_mixed_dns(self):
        with self.assertRaises(ValueError):n.public_addresses('x.ai',lambda *a,**k:[(0,0,0,'',(i,443)) for i in ('1.1.1.1','127.0.0.1')])

    def test_empty_dns(self):
        with self.assertRaises(ValueError):n.public_addresses('x.ai',lambda *a,**k:[])

    def test_valid_public_dns(self):
        self.assertEqual(n.public_addresses('x.ai',lambda *a,**k:[(0,0,0,'',('1.1.1.1',443))]),['1.1.1.1'])

    def test_redirect_disabled(self):
        self.assertIsNone(n.NoRedirect().redirect_request(None,None,None,None,None,None))

    def test_loopback_only(self):
        for endpoint in ('https://api.example.com','http://localhost:8093','http://127.0.0.1','http://127.0.0.1:8093/foo','http://127.0.0.1:22','http://user:key@127.0.0.1:8093'):
            cfg=dict(CONFIG,endpoint=endpoint)
            with self.subTest(endpoint=endpoint),self.assertRaises(ValueError):n.config_checked(cfg)

    def test_config_identity_budget_key(self):
        for key,value in [('max_tokens',True),('max_tokens',5000),('context_tokens',4096),('api_key_env','HOME'),('model','different-model')]:
            with self.assertRaises(ValueError):n.config_checked(dict(CONFIG,**{key:value}))

    def test_worker_timeout(self):
        with patch.object(n.subprocess,'run',side_effect=subprocess.TimeoutExpired('test',45)):
            with self.assertRaises(subprocess.TimeoutExpired):n.fetch('xai',URL)

    def test_bad_url_before_worker(self):
        with patch.object(n,'worker',side_effect=AssertionError('must not call')):
            with self.assertRaises(ValueError):n.fetch('xai','https://127.0.0.1/a')

    def test_worker_safe_error(self):
        fake=type('R',(),{'returncode':0,'stdout':b'{"error":"http_status_403"}'})()
        with patch.object(n.subprocess,'run',return_value=fake):
            with self.assertRaisesRegex(ValueError,'http_status_403'):n.fetch('openai','https://openai.com/index/test')

    def test_missing_model_key_no_network(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'missing_or_invalid_model_key'):n.model_direct(CONFIG,{},opener=object())

    def fake_opener(self, mutate=None):
        calls=[]
        class Result(io.BytesIO):
            status=200
        class Opener:
            def open(self,req,timeout):
                calls.append(req.full_url)
                path=req.full_url.split(':8093')[-1]
                payload={'/v1/models':{'data':[{'id':CONFIG['model']}]},
                    '/props':{'default_generation_settings':{'n_ctx':8192}},
                    '/apply-template':{'prompt':'<think>\n'},'/tokenize':{'tokens':[1,2]},
                    '/v1/chat/completions':response()}[path]
                if mutate:payload=mutate(path,payload)
                return Result(json.dumps(payload).encode())
        return Opener(),calls

    def test_model_preflight_and_single_inference(self):
        opener,calls=self.fake_opener()
        with patch.dict(os.environ,{'MINICPM_API_KEY':'synthetic-unit-test-key'}):
            result=n.model_direct(CONFIG,w.request_for(article(),CONFIG),opener)
        self.assertIn('choices',result)
        self.assertEqual(len(calls),5)
        self.assertEqual(sum('/chat/completions' in u for u in calls),1)

    def test_model_wrong_context_no_generation(self):
        opener,calls=self.fake_opener(lambda path,p:{'default_generation_settings':{'n_ctx':4096}} if path=='/props' else p)
        with patch.dict(os.environ,{'MINICPM_API_KEY':'synthetic-unit-test-key'}):
            with self.assertRaises(ValueError):n.model_direct(CONFIG,w.request_for(article(),CONFIG),opener)
        self.assertFalse(any('/chat/completions' in u for u in calls))

    def test_model_context_overflow_no_generation(self):
        opener,calls=self.fake_opener(lambda path,p:{'tokens':[1]*5000} if path=='/tokenize' else p)
        with patch.dict(os.environ,{'MINICPM_API_KEY':'synthetic-unit-test-key'}):
            with self.assertRaises(ValueError):n.model_direct(CONFIG,w.request_for(article(),CONFIG),opener)
        self.assertFalse(any('/chat/completions' in u for u in calls))

    def test_secret_echo_withheld(self):
        opener,_=self.fake_opener(lambda path,p:{'echo':'synthetic-unit-test-key'} if path=='/v1/chat/completions' else p)
        with patch.dict(os.environ,{'MINICPM_API_KEY':'synthetic-unit-test-key'}):
            with self.assertRaisesRegex(ValueError,'credential_echo'):n.model_direct(CONFIG,w.request_for(article(),CONFIG),opener)


class WorkflowTests(unittest.TestCase):
    def test_snapshot_offline(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report'
            w.snapshot_report({'version':1,'items':[{'source':'xai','title':'Example','url':URL}]},out)
            self.assertEqual(w.read_json(out/'manifest.json')['model_attempts'],0)
            self.assertTrue((out/'index.html').exists())

    def test_fetch_failure_receipt_no_retry(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report';calls=[]
            def fail(*args):calls.append(args);raise ValueError('http_status_403')
            with self.assertRaises(ValueError):w.article_report('openai','https://openai.com/index/test',out,get=fail)
            self.assertEqual(len(calls),1)
            self.assertEqual(w.read_json(out/'manifest.json')['error_code'],'http_status_403')
            self.assertFalse((out/'article.json').exists())

    def test_saved_html_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report'
            w.article_report('xai',URL,out,raw=markup('xai'))
            self.assertIn('origin not authenticated',w.read_json(out/'article.json')['provenance'])
            self.assertEqual(w.read_json(out/'manifest.json')['fetch_attempts'],0)

    def test_no_overwrite_or_duplicate_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report'
            w.article_report('xai',URL,out,raw=markup('xai'))
            with self.assertRaises(FileExistsError):w.article_report('xai',URL,out,get=lambda *a:self.fail('network'))

    def test_model_reserved_before_call(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report';calls=[]
            def fake(cfg,body):
                calls.append(1)
                self.assertEqual(w.read_json(out/'manifest.json')['model_attempts'],1)
                return response()
            w.model_report(article(),CONFIG,out,call=fake)
            self.assertEqual(len(calls),1)
            self.assertEqual(w.read_json(out/'draft.json')['status'],'unreviewed_model_draft')
            self.assertTrue((out/'response.json').exists())

    def test_model_failure_no_retry_or_secret_error(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report';calls=[]
            def fail(*args):calls.append(1);raise RuntimeError('credential detail MUST NOT LOG')
            with self.assertRaises(RuntimeError):w.model_report(article(),CONFIG,out,call=fail)
            self.assertEqual(len(calls),1)
            self.assertNotIn('MUST NOT LOG',(out/'manifest.json').read_text())
            self.assertFalse((out/'index.html').exists())

    def test_validation_precedes_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report';a=article();a['body']='changed'
            with self.assertRaises(ValueError):w.model_report(a,CONFIG,out,call=lambda *a:self.fail('inference'))
            self.assertFalse(out.exists())

    def test_snapshot_dates_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report'
            meta={'source':'SpaceXAI','title':'Example','url':URL,'published':1000,'first_seen':2000}
            w.article_report('xai',URL,out,raw=markup('xai'),metadata=meta)
            a=w.read_json(out/'article.json')
            self.assertEqual((a['published'],a['first_seen']),(1000,2000))

    def test_wrong_metadata_rejected_before_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            meta={'source':'xai','title':'Example','url':'https://x.ai/news/other'}
            with self.assertRaises(ValueError):w.article_report('xai',URL,Path(d)/'r',metadata=meta,get=lambda *a:self.fail('network'))

    def test_future_model_input_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            a=article();a['published']=4000000000
            with self.assertRaises(ValueError):w.model_report(a,CONFIG,Path(d)/'r',call=lambda *a:self.fail('inference'))

    def test_oversize_file(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'large.json';f.write_text('x'*30)
            with self.assertRaises(ValueError):w.read_json(f,20)


class FetchBoundaryTests(unittest.TestCase):
    def run_fetch(self,status=200,content_type='text/html',encoding='identity',length=None,payload=b'ok'):
        from unittest.mock import MagicMock
        response=MagicMock();response.status=status
        headers={'Content-Type':content_type,'Content-Encoding':encoding,'Content-Length':length}
        response.getheader.side_effect=lambda k,default=None:headers.get(k,default)
        response.read1.side_effect=[payload,b'']
        connection=MagicMock();connection.getresponse.return_value=response
        raw=MagicMock();tls=MagicMock();ctx=MagicMock();ctx.wrap_socket.return_value=tls
        with patch.object(n,'public_addresses',return_value=['1.1.1.1']),patch.object(n.socket,'create_connection',return_value=raw) as connect,patch.object(n.ssl,'create_default_context',return_value=ctx),patch.object(n.http.client,'HTTPSConnection',return_value=connection):
            result=n.fetch_direct('xai',URL)
            connect.assert_called_once_with(('1.1.1.1',443),timeout=15)
            ctx.wrap_socket.assert_called_once_with(raw,server_hostname='x.ai')
        self.assertTrue(connection.close.called);self.assertTrue(raw.close.called)
        return result

    def test_ip_pinned_and_tls_hostname(self):self.assertEqual(self.run_fetch(),b'ok')
    def test_redirect_response_rejected(self):
        with self.assertRaisesRegex(ValueError,'http_status_301'):self.run_fetch(status=301)
    def test_access_block_rejected(self):
        with self.assertRaisesRegex(ValueError,'http_status_403'):self.run_fetch(status=403)
    def test_non_html_rejected(self):
        with self.assertRaisesRegex(ValueError,'not_html'):self.run_fetch(content_type='application/json')
    def test_compression_rejected(self):
        with self.assertRaisesRegex(ValueError,'compressed_response_rejected'):self.run_fetch(encoding='gzip')
    def test_declared_size_rejected(self):
        with self.assertRaisesRegex(ValueError,'html_size_limit'):self.run_fetch(length='3000000')
    def test_actual_size_rejected(self):
        with self.assertRaisesRegex(ValueError,'html_size_limit'):self.run_fetch(payload=b'x'*2000001)


if __name__=='__main__':unittest.main()
