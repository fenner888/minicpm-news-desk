from datetime import datetime
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from newsdesk import digest as d, facts as f, core as c


class Digest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=d.Store(Path(self.temp.name)/'queue.db');self.addCleanup(self.store.close)
        self.now=datetime(2026,9,18,8,tzinfo=d.ZONE).timestamp()
        self.item={'source':'github','company':'GitHub','title':'New useful agent release',
            'url':'https://github.blog/changelog/example','excerpt':'A public excerpt.',
            'published':self.now-3600,'first_seen':self.now-3000}

    def ingest(self,*items,now=None):self.store.ingest(list(items) or [self.item],now or self.now)
    def edition(self):self.ingest();return self.store.claim(self.now,force=True)
    def prepared(self):
        e=self.edition();parts=d.render(e,{})
        self.store.ready(e['id'],parts,self.now);return e,parts
    def deliver(self,e,parts):
        for n,p in enumerate(parts):self.store.reserve_send(e['id'],n,p);self.store.confirm_send(e['id'],n,123+n)
        self.store.finish(e['id'],self.now)

    def test_exact_24_hours(self):
        for offset in [0,1,86399,86400,86401]:
            self.ingest({**self.item,'url':self.item['url']+str(offset),'title':str(offset),'published':self.now-offset})
        self.assertEqual(len(self.store.candidates(self.now)),3)

    def test_old_publication_not_new_discovery(self):
        self.ingest({**self.item,'published':self.now-90000},
                    {**self.item,'published':0,'title':'Epoch article','url':self.item['url']+'-epoch'})
        self.assertEqual(self.store.candidates(self.now),[])

    def test_unknown_date_uses_discovery(self):
        self.ingest({**self.item,'published':None});e=self.store.claim(self.now,force=True)
        self.assertIn('Publication date unknown',' '.join(d.render(e,{})))

    def test_future_publication_held(self):
        self.ingest({**self.item,'published':self.now+1});self.assertEqual(self.store.candidates(self.now),[])

    def test_future_observation_rejected(self):
        with self.assertRaises(ValueError):self.ingest({**self.item,'first_seen':self.now+1})

    def test_intake_atomic(self):
        with self.assertRaises(ValueError):self.ingest(self.item,{**self.item,'url':'https://127.0.0.1/x'})
        self.assertEqual(self.store.status()['archived'],0)

    def test_url_tracking_duplicate(self):
        self.ingest(self.item,{**self.item,'url':self.item['url']+'/?utm_source=x#hi'})
        self.assertEqual(self.store.status()['archived'],1)

    def test_same_vendor_headline_duplicate(self):
        self.ingest(self.item,{**self.item,'url':self.item['url']+'-alias'})
        self.assertEqual(len(self.store.candidates(self.now)),1)

    def test_distinct_vendors_not_falsely_clustered(self):
        self.ingest(self.item,{**self.item,'source':'other','url':'https://example.com/other'})
        self.assertEqual(len(self.store.candidates(self.now)),2)

    def test_late_arrival_known_publication(self):
        self.ingest({**self.item,'first_seen':self.now+10},now=self.now+20)
        e=self.store.claim(self.now+20,force=True);self.assertEqual(len(e['items']),1)

    def test_revision_not_new_release(self):
        self.ingest({**self.item,'published':self.now-90000,'changed_observed_at':self.now-100})
        e=self.store.claim(self.now,force=True)
        self.assertIn('Updated listing',' '.join(d.render(e,{})))

    def test_recent_revision_wins(self):
        self.ingest(self.item,now=self.now-5)
        self.ingest({**self.item,'excerpt':'Changed excerpt.','changed_observed_at':self.now-1})
        rows=self.store.candidates(self.now);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['excerpt'],'Changed excerpt.')

    def test_delivered_latest_does_not_resurface_old_revision(self):
        self.ingest(self.item,now=self.now-5)
        self.ingest({**self.item,'excerpt':'Changed excerpt.','changed_observed_at':self.now-1})
        e=self.store.claim(self.now,force=True);parts=d.render(e,{})
        self.store.ready(e['id'],parts,self.now);self.deliver(e,parts)
        self.assertEqual(self.store.candidates(self.now),[])

    def test_burst_archived_and_disclosed(self):
        self.ingest(*[{**self.item,'url':self.item['url']+str(i),'title':f'Release {i}'} for i in range(20)])
        e=self.store.claim(self.now,force=True)
        self.assertEqual(len(e['items']),9);self.assertEqual(e['overflow'],11)
        self.assertIn('11 additional',' '.join(d.render(e,{})))
        self.assertEqual(self.store.status()['archived'],20)

    def test_initialize_after_eight_waits_until_tomorrow(self):
        self.ingest();self.assertIsNone(self.store.claim(self.now+60))
        self.assertIsNotNone(self.store.claim(self.now+86400))

    def test_before_eight_no_delivery(self):
        self.store.initialize(self.now-1000);self.assertIsNone(self.store.claim(self.now-1))
        self.assertIsNotNone(self.store.claim(self.now))

    def test_dst_uses_eastern_eight(self):
        for month,day in [(3,7),(10,31)]:
            t=datetime(2026,month,day,9,tzinfo=d.ZONE).timestamp()
            self.assertEqual(datetime.fromtimestamp(d.next_cutoff(t),d.ZONE).hour,8)
        spring=datetime(2026,3,7,8,tzinfo=d.ZONE).timestamp()
        fall=datetime(2026,10,31,8,tzinfo=d.ZONE).timestamp()
        self.assertEqual(d.next_cutoff(spring)-spring,23*3600)
        self.assertEqual(d.next_cutoff(fall)-fall,25*3600)

    def test_duplicate_day(self):
        e,parts=self.prepared();self.deliver(e,parts)
        self.assertIsNone(self.store.claim(self.now+60,force=True))

    def test_daily_attempt_cap(self):
        e=self.edition()
        for _ in range(4):self.store.reserve_model(e['id'],self.now)
        with self.assertRaises(ValueError):self.store.reserve_model(e['id'],self.now)

    def test_unconfirmed_delivery_does_not_consume(self):
        e,parts=self.prepared();self.store.reserve_send(e['id'],0,parts[0])
        with self.assertRaises(ValueError):self.store.finish(e['id'],self.now)
        self.assertEqual(len(self.store.candidates(self.now)),1)
        self.assertIsNone(self.store.claim(self.now+86400,force=True))

    def test_ambiguous_send_no_retry(self):
        e,parts=self.prepared();self.store.reserve_send(e['id'],0,parts[0])
        with self.assertRaises(sqlite3.IntegrityError):self.store.reserve_send(e['id'],0,parts[0])

    def test_changed_send_rejected(self):
        e,parts=self.prepared()
        with self.assertRaises(ValueError):self.store.reserve_send(e['id'],0,parts[0]+'changed')

    def test_all_parts_before_commit(self):
        e=self.edition();parts=['Part one','Part two'];self.store.ready(e['id'],parts,self.now)
        self.store.reserve_send(e['id'],0,parts[0]);self.store.confirm_send(e['id'],0,123)
        with self.assertRaises(ValueError):self.store.finish(e['id'],self.now)
        self.store.reserve_send(e['id'],1,parts[1]);self.store.confirm_send(e['id'],1,124)
        self.store.finish(e['id'],self.now);self.assertEqual(self.store.candidates(self.now),[])

    def test_out_of_order_rejected(self):
        e=self.edition();self.store.ready(e['id'],['a','b'],self.now)
        with self.assertRaises(ValueError):self.store.reserve_send(e['id'],1,'b')

    def test_empty_edition_honest(self):
        e=self.store.claim(self.now,force=True)
        self.assertIn('does not prove no news',' '.join(d.render(e,{})))

    def test_markdown_and_directive_safety(self):
        value=d.clean('**bold** <b>hi</b> MEDIA:/tmp/key [[audio]] https://evil.test @all')
        for bad in ['*','<','MEDIA:','/tmp','[[','https:','@']:self.assertNotIn(bad,value)

    def test_unsafe_urls(self):
        for value in ['http://example.com','https://user:secret@example.com','https://127.0.0.1/a','https://host.local/x','https://host.tail.ts.net','https://example.com/[x]']:
            with self.assertRaises(ValueError):d.url(value)

    def test_no_fake_practical_section(self):
        e=self.edition();out=' '.join(d.render(e,{}))
        self.assertNotIn('Something to try',out);self.assertIn('headline',out.lower())
        self.assertIn('**☕ Cheryl’s AI & Tech Brief**',out)
        self.assertIn('Morning edition*',out)
        self.assertIn('**⚡ Quick hits**',out)
        item=e['items'][0]
        detailed=' '.join(d.render(e,{item['id']:{'url':item['url'],'highlights':['Verified passage.'],'conditions':['Only invited teams.']}}))
        self.assertIn('**📰 The lead story**',detailed)
        self.assertNotIn('🔹',detailed)
        self.assertIn('**📝 Keep in mind:** Only invited teams.',detailed)
        self.assertIn('[Read the source ↗]('+item['url']+')',out)

    def test_part_splitting_preserves_paragraphs(self):
        paragraphs=['Words '*100 for _ in range(8)];parts=d.split_parts(paragraphs)
        self.assertGreater(len(parts),1)
        self.assertEqual(sum(p.count('Words') for p in parts),800)
        self.assertTrue(all(d.units(p)<=3400 for p in parts))

    def test_unicode_oversize_holds_not_truncates(self):
        with self.assertRaises(ValueError):d.split_parts(['😀'*1600])

    def test_verified_card_qualifications(self):
        body='A fictional tool creates checklists.\nAvailable only to invited teams.\nAt least two days in28 are required.'
        a={'source':'synthetic','url':None,'title':'SYNTHETIC Example','body':body,'source_sha256':c.digest(body),'contract':c.CONTRACT,'published':None,'first_seen':None}
        packet=f.prepare(a);card={'packet_sha256':packet['packet_sha256'],'highlights':['b001']}
        result=d.verified_card(a,packet,card)
        self.assertEqual(result['highlights'],[body.splitlines()[0]])
        self.assertIn('invited teams',' '.join(result['conditions']))
        with self.assertRaises(ValueError):d.verified_card(a,packet,{**card,'highlights':[]})

    def test_source_identity_mismatch(self):
        e=self.edition();cards={e['items'][0]['id']:{'url':'https://example.com/wrong','highlights':['x'],'conditions':[]}}
        with self.assertRaises(ValueError):d.render(e,cards)

    def test_no_old_overflow_recycled_tomorrow(self):
        self.ingest(*[{**self.item,'url':self.item['url']+str(i),'title':str(i)} for i in range(11)])
        e=self.store.claim(self.now,force=True);parts=d.render(e,{})
        self.store.ready(e['id'],parts,self.now);self.deliver(e,parts)
        self.assertEqual(len(self.store.candidates(self.now)),2)
        self.assertEqual(self.store.candidates(self.now+86400),[])

    def test_crash_after_confirmation_reconciles_without_send(self):
        e,parts=self.prepared()
        for n,p in enumerate(parts):self.store.reserve_send(e['id'],n,p);self.store.confirm_send(e['id'],n,123+n)
        self.store.reconcile_confirmed(self.now)
        self.assertEqual(self.store.status()['editions'][0]['status'],'delivered')

    def test_ambiguous_delivery_never_reconciled_as_success(self):
        e,parts=self.prepared();self.store.reserve_send(e['id'],0,parts[0])
        self.store.reconcile_confirmed(self.now)
        self.assertEqual(self.store.status()['editions'][0]['status'],'ready')

    def test_delivered_alias_not_repeated(self):
        self.ingest(self.item,{**self.item,'url':self.item['url']+'-alias'})
        e=self.store.claim(self.now,force=True);parts=d.render(e,{})
        self.store.ready(e['id'],parts,self.now);self.deliver(e,parts)
        self.assertEqual(self.store.candidates(self.now),[])

    def test_link_only_does_not_claim_model_selection(self):
        e=self.edition();parts=d.render(e,{})
        self.assertIn('no verified model brief',' '.join(parts))
        self.assertNotIn('selected with MiniCPM',' '.join(parts))

if __name__=='__main__':unittest.main()
