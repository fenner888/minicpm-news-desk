"""Editorial regression cases v1: source clauses, layout and private report."""
from datetime import datetime
import unittest
from newsdesk import digest as d


class Editorial(unittest.TestCase):
    def card(self,highlights=None,conditions=None):
        return {'url':'https://example.com/news','highlights':highlights or ['A tool helps teams review changes.'],
                'conditions':conditions or [],'source_body':'Complete original source <script>unsafe()</script>'}

    def edition(self):
        until=datetime(2026,9,18,8,tzinfo=d.ZONE).timestamp()
        return {'items':[{'id':'one','title':'Tool update','url':'https://example.com/news','published':until-60}],
                'cutoff':until,'overflow':0}

    def test_price_access_deadline_retained(self):
        c=self.card(conditions=['It costs $2 per use.','Available only to invited teams.',
                                'Starting October 2, 2026, users must enable it.'])
        self.assertEqual(d.reading_card(c)['conditions'],c['conditions'])

    def test_unknown_conditions_retained(self):
        c=self.card(conditions=['The result is an estimate and can be wrong.'])
        self.assertEqual(d.reading_card(c)['conditions'],c['conditions'])

    def test_list_intro_archived_not_dangling(self):
        c=self.card(conditions=['General availability adds:'])
        view=d.reading_card(c)
        self.assertFalse(view['held']);self.assertFalse(view['conditions'])
        self.assertIn('General availability adds:',d.supporting_report(self.edition(),{'one':c}))

    def test_restrictive_intro_holds_card(self):
        c=self.card(conditions=['Available only to:'])
        self.assertTrue(d.reading_card(c)['held'])
        self.assertIn('Brief held:', ' '.join(d.render(self.edition(),{'one':c})))

    def test_incomplete_highlight_holds_card(self):
        self.assertTrue(d.reading_card(self.card(highlights=['The new features include:']))['held'])

    def test_field_details_only_if_discussed(self):
        condition='request_count counts attempts, including failures.'
        c=self.card(conditions=[condition]);self.assertFalse(d.reading_card(c)['conditions'])
        c['highlights']=['The request_count field measures attempts.']
        self.assertEqual(d.reading_card(c)['conditions'],[condition])

    def test_field_access_not_removed(self):
        c=self.card(conditions=['request_count is available only to administrators.'])
        self.assertEqual(d.reading_card(c)['conditions'],c['conditions'])

    def test_unmentioned_field_safety_not_removed(self):
        c=self.card(conditions=['memory_export can leak credentials.',
                                'image_api is not supported on this hardware.',
                                'request_count cannot measure success.'])
        self.assertEqual(d.reading_card(c)['conditions'],c['conditions'])

    def test_definition_threshold_preserved(self):
        c=self.card(highlights=['A dashboard shows active users.'],
                    conditions=['Active users engaged on at least two days during the 28-day period.'])
        self.assertEqual(d.reading_card(c)['conditions'],c['conditions'])

    def test_field_highlight_moves_to_report(self):
        c=self.card(highlights=['A tool helps teams review changes.','raw_count: Includes every attempt.'])
        view=d.reading_card(c);self.assertEqual(len(view['highlights']),1)
        self.assertIn('raw_count: Includes every attempt.',d.supporting_report(self.edition(),{'one':c}))

    def test_zero_semantics_when_claimed_retained(self):
        p='Empty arrays mean zero matching activity; null means unavailable.'
        c=self.card(highlights=['The dashboard distinguishes zero from unavailable.'],conditions=[p])
        self.assertEqual(d.reading_card(c)['conditions'],[p])

    def test_source_report_escapes_script(self):
        page=d.supporting_report(self.edition(),{'one':self.card()})
        self.assertNotIn('<script>',page);self.assertIn('&lt;script&gt;',page)
        self.assertIn('default-src',page);self.assertIn('Complete original source',page)

    def test_report_identity_bound(self):
        c=self.card();c['url']='https://evil.example/news'
        with self.assertRaises(ValueError):d.supporting_report(self.edition(),{'one':c})

    def test_preview_does_not_claim_morning_or_fresh(self):
        e=self.edition();s=' '.join(d.render(e,{'one':self.card()},preview=True,generated_at=e['cutoff']+7200))
        self.assertNotIn('Morning edition',s);self.assertIn('Historical source window:',s)
        self.assertIn('10:00 AM EDT',s);self.assertIn('not a new model run',s)

    def test_live_morning_label_unchanged(self):
        s=' '.join(d.render(self.edition(),{'one':self.card()}))
        self.assertIn('Friday, September 18 · Morning edition',s)

    def test_whole_story_kept_together(self):
        story=d.story_blocks(['**Headline**','A useful paragraph.','Source link'],'Headline')
        parts=d.split_parts(['x'*2990]+story)
        self.assertEqual(len(parts),2);self.assertNotIn('Headline',parts[0])
        self.assertIn('A useful paragraph.',parts[1]);self.assertIn('Source link',parts[1])

    def test_long_story_has_named_continuation_no_orphan(self):
        paragraphs=['**Headline**','A '*1000,'**Details**','B '*700,'Source link']
        chunks=d.story_blocks(paragraphs,'Headline')
        self.assertEqual(len(chunks),2);self.assertNotIn('**Details**',chunks[0])
        self.assertTrue(chunks[1].startswith('**↪ Headline — continued**'))
        self.assertIn('**Details**\n\nB ',chunks[1]);self.assertIn('Source link',chunks[1])

    def test_oversize_never_truncates(self):
        with self.assertRaises(ValueError):d.story_blocks(['x'*4000],'Headline')

    def test_duplicate_qualification_not_repeated(self):
        c=self.card(conditions=['Only invited teams.','Only invited teams.'])
        self.assertEqual(d.reading_card(c)['conditions'],['Only invited teams.'])

    def test_reading_paragraphs_join_without_loss(self):
        self.assertEqual(d.reading_paragraphs(['One sentence.','Related sentence.']),['One sentence. Related sentence.'])
        self.assertEqual(len(d.reading_paragraphs(['a'*1000,'b'*1000])),2)

    def test_inline_one_condition_bullets_for_multiple(self):
        e=self.edition()
        s=' '.join(d.render(e,{'one':self.card(conditions=['Only invited teams.'])}))
        self.assertIn('**📝 Keep in mind:** Only invited teams.',s)
        self.assertNotIn('• Only',s)
        s=' '.join(d.render(e,{'one':self.card(conditions=['Only invited teams.','It costs $2.'])}))
        self.assertIn('**📝 Keep in mind**\n\n• Only invited teams.\n\n• It costs $2.',s)

    def test_source_link_delimiters_encoded(self):
        self.assertEqual(d.source_link('https://example.com/a(b)'),
                         '[Read the source ↗](https://example.com/a%28b%29)')
        with self.assertRaises(ValueError):d.source_link('https://example.com/[injected]')
        with self.assertRaises(ValueError):d.source_link('https://user:token@example.com/a')

    def test_live_test_labels_not_saved_or_scheduled(self):
        s=' '.join(d.render(self.edition(),{'one':self.card()},live_test=True))
        self.assertIn('Live test edition',s);self.assertIn('schedule unchanged',s)
        self.assertNotIn('saved results',s);self.assertNotIn('Morning edition',s)
        self.assertIn('Your last 24 hours in AI & tech.',s)
        with self.assertRaises(ValueError):d.render(self.edition(),{},preview=True,live_test=True)

    def test_quick_hits_share_one_notice_keep_uncertainty(self):
        e=self.edition();e['items'] += [{**e['items'][0],'id':'two','title':'Another story','published':None}]
        s=' '.join(d.render(e,{}))
        self.assertEqual(s.count('full-article briefs are not included'),1)
        self.assertIn('Publication date unknown',s)
        self.assertEqual(s.count('[Read the source ↗]'),2)


if __name__=='__main__':unittest.main()
