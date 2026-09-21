"""Reference workflow v1: isolated state and synthetic/mock transports only."""
from contextlib import redirect_stdout
from datetime import datetime
import html
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch, Mock
from zoneinfo import ZoneInfo
from newsdesk import daily, digest as d, feeds, presentation, telegram, core, facts

TOKEN='123456:'+('x'*30)  # deliberately synthetic; never sent
CHAT='123456789'


def rss(url='https://github.blog/changelog/test-release/',description='A useful tool can export local project data.'):
    return ('<?xml version="1.0" encoding="UTF-8"?><rss><channel><item>'
            '<title>New local export tool</title><link>'+url+'</link>'
            '<description>'+description+'</description>'
            '<pubDate>Mon, 21 Sep 2026 08:00:00 +0000</pubDate>'
            '</item></channel></rss>').encode()


class Feeds(unittest.TestCase):
    def test_rss_dates_and_identity(self):
        result=feeds.parse('github',rss(),time.time())
        self.assertEqual(len(result['items']),1)
        self.assertEqual(result['items'][0]['published'],datetime(2026,9,21,8,tzinfo=ZoneInfo('UTC')).timestamp())

    def test_host_mismatch_not_ingested(self):
        r=feeds.parse('github',rss(url='https://attacker.example/changelog/story'),time.time())
        self.assertEqual(r['items'],[]);self.assertEqual(r['rejected_items'],1)

    def test_dtd_and_unsupported_formats_fail_closed(self):
        for raw in [b'<!DOCTYPE rss [<!ENTITY x "abc">]><rss/>',b'<feed/>',b'<html/>',b'\x00<rss/>']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):feeds.parse('github',raw,time.time())

    def test_unknown_feed_no_transport(self):
        with patch('newsdesk.network.worker') as worker:
            with self.assertRaises(ValueError):feeds.fetch('attacker')
            worker.assert_not_called()

    def test_feed_item_limit(self):
        raw=b'<rss><channel>'+b'<item/>'*(feeds.MAX_ITEMS+1)+b'</channel></rss>'
        with self.assertRaises(ValueError):feeds.parse('github',raw,time.time())

    def test_unknown_date_not_invented(self):
        raw=rss().replace(b'Mon, 21 Sep 2026 08:00:00 +0000',b'unknown')
        self.assertIsNone(feeds.parse('github',raw,time.time())['items'][0]['published'])

    def test_unsafe_description_markup_removed(self):
        self.assertEqual(feeds.plain('<p>A tool.</p><script>steal()</script><p>Details.</p>'),'A tool. Details.')

    def test_xml_entities_and_encodings(self):
        for raw in [rss().replace(b'UTF-8',b'UTF-16'),rss().replace(b'<rss>',b'<!ENTITY x "y"><rss>')]:
            with self.assertRaises(ValueError):feeds.parse('github',raw,time.time())

    def test_inert_html_doctype_inside_cdata_is_not_xml_dtd(self):
        raw=rss(description='<![CDATA[<!DOCTYPE html><p>A useful tool can export project data.</p>]]>')
        result=feeds.parse('github',raw,time.time())
        self.assertEqual(len(result['items']),1)
        self.assertEqual(result['items'][0]['excerpt'],'A useful tool can export project data.')

    def test_xml_dtd_after_comment_still_rejected(self):
        raw=b'<!-- harmless --><!DOCTYPE rss [<!ENTITY x "abc">]><rss/>'
        with self.assertRaises(ValueError):feeds.parse('github',raw,time.time())

    def test_historical_feed_larger_than_200_supported(self):
        raw=b'<rss><channel>'+b'<item/>'*300+b'</channel></rss>'
        self.assertEqual(feeds.parse('github',raw,time.time())['listed_items'],300)


class Display(unittest.TestCase):
    def test_markup_inert_and_technical_text_exact_after_render(self):
        text='Set retries=0; /memory; x < 100/day; **bold**; a_b; &lt;literal&gt;; <script>x()</script>.'
        value=presentation.telegram_html('**App heading**\n'+d.clean(text))
        self.assertIn('<b>App heading</b>',value)
        self.assertNotIn('<script>',value);self.assertNotIn('<b>bold</b>',value)
        self.assertEqual(presentation.visible_text(value),'App heading\n'+text)

    def test_link_is_application_owned(self):
        text=d.clean('[click](https://attacker.example)')+'\n'+d.source_link('https://github.blog/changelog/news')
        value=presentation.telegram_html(text)
        self.assertEqual(value.count('<a '),1)
        self.assertNotIn('attacker.example',value)

    def test_oversize_is_held(self):
        with self.assertRaises(ValueError):presentation.telegram_html('a'*3401)

    def test_mobile_report_stacks_and_full_source_present(self):
        page=d.supporting_report({'items':[{'id':'x','title':'Test','url':'https://example.com/x'}]},
            {'x':{'url':'https://example.com/x','highlights':['A tool.'],'conditions':[], 'source_body':'Full source text.'}})
        self.assertIn('@media(max-width:600px)',page);self.assertIn('data-label="Passage"',page)
        self.assertIn('Full source text.',page)


class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'state'
        self.old_umask=os.umask(0o077);self.addCleanup(os.umask,self.old_umask)
        daily.initialize(self.root,'My News Desk','UTC')
        self.now=time.time()

    def item(self,n=0):
        return {'source':'github','title':f'New local tool {n}',
                'url':f'https://github.blog/changelog/test-{n}',
                'excerpt':'The tool can export useful local project data.',
                'published':self.now-60-n,'first_seen':self.now-1}

    def prepared(self,store):
        store.ingest([self.item()],self.now)
        return daily.build(self.root,store,{'title':'My News Desk'},self.now,current_window=True)

    def test_init_private_and_nonoverwriting(self):
        self.assertEqual(self.root.stat().st_mode&0o777,0o700)
        self.assertEqual((self.root/'settings.json').stat().st_mode&0o777,0o600)
        with self.assertRaises(FileExistsError):daily.initialize(self.root,'Other','UTC')

    def test_lock_prevents_second_writer(self):
        with daily.locked(self.root):
            with self.assertRaises(BlockingIOError):
                with daily.locked(self.root):pass

    def test_symlink_state_rejected(self):
        link=Path(self.temp.name)/'link';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):
            with daily.locked(link):pass

    def test_world_readable_settings_rejected(self):
        (self.root/'settings.json').chmod(0o644)
        with self.assertRaises(ValueError):
            with daily.locked(self.root):pass

    def test_collect_mixed_coverage_no_retries(self):
        get=Mock(side_effect=[rss(),ValueError('blocked')])
        with daily.locked(self.root) as (_,store,_):
            result=daily.collect(self.root,store,['github','openai'],self.now,get=get)
            self.assertEqual(get.call_count,2)
            self.assertEqual(result['sources']['github']['status'],'ok')
            self.assertEqual(result['sources']['openai']['status'],'failed')

    def test_collect_repeated_source_rejected(self):
        get=Mock()
        with daily.locked(self.root) as (_,store,_):
            with self.assertRaises(ValueError):daily.collect(self.root,store,['github','github'],self.now,get=get)
            get.assert_not_called()

    def test_build_offline_saves_review_before_ready(self):
        with daily.locked(self.root) as (_,store,_),patch('newsdesk.network.worker') as worker:
            result=self.prepared(store);eid=result['edition']
            self.assertEqual(result['model_cards'],0);worker.assert_not_called()
            parts=daily.ready_parts(self.root,store,eid)
            self.assertIn('Source links only',''.join(parts))
            self.assertIn('My News Desk',''.join(parts))
            self.assertIn('UTC',''.join(parts))

    def test_model_requires_network_permission_before_claim(self):
        with daily.locked(self.root) as (_,store,_):
            with self.assertRaises(ValueError):daily.build(self.root,store,{'title':'Test'},self.now,model_config={})
            self.assertEqual(store.status()['editions'],[])

    def test_cancel_preparation_retains_day_and_allows_next_day(self):
        with daily.locked(self.root) as (_,store,_):
            e=store.claim(self.now,force=True,current_window=True)
            store.reserve_model(e['id'],self.now)
            store.cancel_unsent(e['id'],self.now)
            self.assertIsNone(store.claim(self.now,force=True,current_window=True))
            self.assertEqual(store.status()['editions'][0]['attempts'],1)
            self.assertIsNotNone(store.claim(self.now+86400,force=True,current_window=True))

    def test_reserved_send_cannot_be_cancelled_or_reapproved(self):
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition'];part=daily.ready_parts(self.root,store,eid)[0]
            store.reserve_send(eid,0,part)
            with self.assertRaises(ValueError):store.cancel_unsent(eid,self.now)
            with self.assertRaises(ValueError):daily.approve(self.root,store,eid,self.now,TOKEN,CHAT)

    def test_send_confirmed_once_and_no_repeat(self):
        transport=Mock(return_value=456)
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition']
            approval=daily.approve(self.root,store,eid,self.now,TOKEN,CHAT)['approval']
            result=daily.send(self.root,store,eid,approval,self.now,TOKEN,CHAT,transport=transport)
            self.assertEqual(result['status'],'delivered');self.assertEqual(transport.call_count,1)
            with self.assertRaises(ValueError):daily.send(self.root,store,eid,approval,self.now,TOKEN,CHAT,transport=transport)
            self.assertEqual(transport.call_count,1)

    def test_changed_destination_and_expired_approval_block_transport(self):
        transport=Mock()
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition'];a=daily.approve(self.root,store,eid,self.now,TOKEN,CHAT)['approval']
            for now,chat in [(self.now,CHAT+'1'),(self.now+901,CHAT)]:
                with self.assertRaises(ValueError):daily.send(self.root,store,eid,a,now,TOKEN,chat,transport=transport)
            transport.assert_not_called()

    def test_report_change_invalidates_approval(self):
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition'];a=daily.approve(self.root,store,eid,self.now,TOKEN,CHAT)['approval']
            from newsdesk.workflow import atomic
            atomic(self.root/'editions'/eid/'supporting-report.html','Changed report')
            with self.assertRaises(ValueError):daily.send(self.root,store,eid,a,self.now,TOKEN,CHAT,transport=Mock())

    def test_ambiguous_send_stays_reserved_and_not_retried(self):
        transport=Mock(side_effect=TimeoutError())
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition'];a=daily.approve(self.root,store,eid,self.now,TOKEN,CHAT)['approval']
            with self.assertRaises(TimeoutError):daily.send(self.root,store,eid,a,self.now,TOKEN,CHAT,transport=transport)
            self.assertEqual(store.status()['pending_delivery_parts'],1)
            with self.assertRaises(ValueError):daily.send(self.root,store,eid,a,self.now,TOKEN,CHAT,transport=transport)
            self.assertEqual(transport.call_count,1)

    def test_confirmed_crash_reconciles_without_send(self):
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition'];parts=daily.ready_parts(self.root,store,eid)
            for i,p in enumerate(parts):store.reserve_send(eid,i,p);store.confirm_send(eid,i,123+i)
            store.reconcile_confirmed(self.now)
            self.assertEqual(store.status()['editions'][0]['status'],'delivered')

    def test_missing_send_flag_rejected_by_cli(self):
        with redirect_stdout(io.StringIO()),patch('sys.stderr',new=io.StringIO()),self.assertRaises(SystemExit):
            daily.main(['--state',str(self.root),'send','--edition','x','--approval','x'])

    def test_model_fetch_budget_and_failure_labels(self):
        cfg={'endpoint':'http://127.0.0.1:8093','model':'MiniCPM5-2B-Q4_K_M',
             'api_key_env':'MINICPM_API_KEY','context_tokens':8192,'max_tokens':4096}
        with daily.locked(self.root) as (_,store,_),patch('newsdesk.workflow.article_report',side_effect=ValueError('blocked')) as fetch:
            store.ingest([self.item(i) for i in range(9)],self.now)
            result=daily.build(self.root,store,{'title':'Test'},self.now,allow_network=True,model_config=cfg,current_window=True)
            self.assertEqual(fetch.call_count,6)
            self.assertEqual(daily.get_meta(store,'fetches:'+result['edition']),6)
            self.assertEqual(store.status()['editions'][0]['attempts'],0)
            self.assertIn('no verified brief',''.join(daily.ready_parts(self.root,store,result['edition'])))

    def test_full_mock_model_path_preserves_restriction_and_four_call_budget(self):
        from newsdesk import workflow, selector
        cfg={'endpoint':'http://127.0.0.1:8093','model':'MiniCPM5-2B-Q4_K_M',
             'api_key_env':'MINICPM_API_KEY','context_tokens':8192,'max_tokens':4096}
        original_article=workflow.article_report;original_selection=selector.selection_report
        body='<h1>Synthetic tool</h1><div class="PostContent-main"><p>The tool can export files for local teams.</p><p>It costs $5/month.</p><p>Commercial use is prohibited.</p><p>Users must set retries=0.</p></div>'
        response={'choices':[{'finish_reason':'stop','message':{'reasoning_content':'Synthetic fixture.',
            'content':json.dumps({'highlights':['b001']})}}]}
        def article(source,url,out,metadata):
            return original_article(source,url,out,raw=body.encode(),metadata=metadata)
        def selection(a,c,out):return original_selection(a,c,out,call=lambda *_:response)
        with daily.locked(self.root) as (_,store,_),patch('newsdesk.workflow.article_report',side_effect=article) as fetch,patch('newsdesk.selector.selection_report',side_effect=selection) as model:
            store.ingest([self.item(i) for i in range(9)],self.now)
            result=daily.build(self.root,store,{'title':'Test'},self.now,allow_network=True,model_config=cfg,current_window=True)
            self.assertEqual(result['model_cards'],4)
            self.assertEqual((fetch.call_count,model.call_count),(4,4))
            self.assertEqual(store.status()['editions'][0]['attempts'],4)
            visible=presentation.visible_text('\n'.join(presentation.telegram_html(p) for p in daily.ready_parts(self.root,store,result['edition'])))
            self.assertIn('Commercial use is prohibited.',visible)
            self.assertIn('$5/month',visible);self.assertIn('retries=0',visible)

    def test_partial_confirmed_delivery_sends_only_remaining_parts(self):
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition']
            with store.db:store.db.execute('UPDATE editions SET parts=? WHERE id=?',(json.dumps(['First','Second']),eid))
            store.reserve_send(eid,0,'First');store.confirm_send(eid,0,321)
            a=daily.approve(self.root,store,eid,self.now,TOKEN,CHAT)['approval']
            transport=Mock(return_value=322)
            daily.send(self.root,store,eid,a,self.now,TOKEN,CHAT,transport=transport)
            transport.assert_called_once_with('Second',TOKEN,CHAT)

    def test_changed_message_and_bot_invalidates_approval(self):
        with daily.locked(self.root) as (_,store,_):
            eid=self.prepared(store)['edition'];a=daily.approve(self.root,store,eid,self.now,TOKEN,CHAT)['approval']
            transport=Mock()
            with self.assertRaises(ValueError):daily.send(self.root,store,eid,a,self.now,'987654:'+('x'*30),CHAT,transport=transport)
            with store.db:store.db.execute('UPDATE editions SET parts=? WHERE id=?',(json.dumps(['Changed']),eid))
            with self.assertRaises(ValueError):daily.send(self.root,store,eid,a,self.now,TOKEN,CHAT,transport=transport)
            transport.assert_not_called()

    def test_report_write_failure_leaves_preparing_not_sendable(self):
        with daily.locked(self.root) as (_,store,_),patch('newsdesk.digest.supporting_report',side_effect=OSError('disk')):
            with self.assertRaises(OSError):self.prepared(store)
            row=store.status()['editions'][0]
            self.assertEqual(row['status'],'preparing')
            with self.assertRaises(ValueError):daily.approve(self.root,store,row['id'],self.now,TOKEN,CHAT)

    def test_no_config_implies_no_model_or_article_fetch(self):
        with daily.locked(self.root) as (_,store,_),patch('newsdesk.workflow.article_report') as fetch,patch('newsdesk.selector.selection_report') as model:
            self.prepared(store);fetch.assert_not_called();model.assert_not_called()

    def test_unsafe_database_symlink_rejected(self):
        target=Path(self.temp.name)/'other.sqlite3';target.touch()
        (self.root/'archive.sqlite3').rename(self.root/'archive.original.sqlite3')
        (self.root/'archive.sqlite3').symlink_to(target)
        with self.assertRaises(ValueError):
            with daily.locked(self.root):pass


class Telegram(unittest.TestCase):
    def response(self,chat=CHAT,mid=123):
        response=Mock();response.status=200
        response.read.return_value=json.dumps({'ok':True,'result':{'message_id':mid,'chat':{'id':int(chat)}}}).encode()
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        opener=Mock();opener.open.return_value=response
        return opener

    def test_success_checked_chat_and_html(self):
        opener=self.response()
        self.assertEqual(telegram.send(d.clean('x < 10/day'),TOKEN,CHAT,opener),123)
        req=opener.open.call_args.args[0];payload=json.loads(req.data)
        self.assertEqual(payload['parse_mode'],'HTML');self.assertEqual(payload['text'],'x &lt; 10/day')
        self.assertTrue(payload['link_preview_options']['is_disabled'])

    def test_wrong_chat_never_confirmed(self):
        with self.assertRaises(ValueError):telegram.send('Test',TOKEN,CHAT,self.response(chat=CHAT+'1'))

    def test_exception_never_leaks_url_token(self):
        opener=Mock();opener.open.side_effect=RuntimeError('URL /bot'+TOKEN)
        with self.assertRaises(ValueError) as caught:telegram.send('Test',TOKEN,CHAT,opener)
        self.assertNotIn(TOKEN,str(caught.exception));self.assertEqual(opener.open.call_count,1)

    def test_invalid_credentials_rejected_before_network(self):
        for token,chat in [('bad',CHAT),(TOKEN,'@public')]:
            opener=Mock()
            with self.assertRaises(ValueError):telegram.send('Test',token,chat,opener)
            opener.open.assert_not_called()
