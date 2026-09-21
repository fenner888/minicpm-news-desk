"""Audit regressions v1, synthetic source text; no model or network."""
import html
import time
import unittest
from newsdesk import core, facts, digest


class Preservation(unittest.TestCase):
    def render_source(self, lines):
        now=time.time();body='\n'.join(lines)
        article={'source':'github','url':'https://github.blog/changelog/synthetic-audit',
                 'title':'Synthetic update','body':body,'source_sha256':core.digest(body),
                 'contract':core.CONTRACT,'published':now-60,'first_seen':now-60}
        packet=facts.prepare(article)
        card=digest.verified_card(article,packet,{'packet_sha256':packet['packet_sha256'],'highlights':['b001']})
        edition={'cutoff':now,'items':[{'id':'one','title':article['title'],'url':article['url'],'published':now-60}]}
        return html.unescape('\n'.join(digest.render(edition,{'one':card})))

    def test_technical_syntax_survives_daily_output(self):
        lines=['The API costs $5/month and supports input/output streaming.',
               'This preview is available only when usage < 100 requests/day.',
               'Users must set retries=0 and use /memory before restarting.']
        result=self.render_source(lines)
        for line in lines:self.assertIn(line,result)

    def test_licensing_and_prohibition_outside_model_pool(self):
        for condition in ['Commercial use is prohibited.', 'Redistribution is forbidden.',
                          'A commercial license is required.', 'Research use only.',
                          'You may not redistribute the weights.', 'Production usage is disallowed.']:
            with self.subTest(condition=condition):
                result=self.render_source(['Cedar can export files for teams.',
                    'It helps teams process their archives.','Teams can search local documents.',
                    'Developers can review their own files.',condition])
                self.assertIn(condition,result)

    def test_escaped_source_roundtrips_without_active_markup(self):
        source='Use a_b, retries=0, /memory, x <= 10, **literal**, [text], and `code`.'
        escaped=digest.clean(source)
        self.assertEqual(html.unescape(escaped),source)
        self.assertNotIn('<',escaped)
        self.assertNotIn('**literal**',escaped)

    def test_selected_navigation_with_prohibition_stays_visible(self):
        line='To learn more, commercial use is prohibited under this license.'
        self.assertIn(line,self.render_source([line,'The API can export files.']))

    def test_prohibited_list_intro_holds_incomplete_card(self):
        card={'highlights':['A new API exports files.'],'conditions':['Commercial use is prohibited for:']}
        self.assertTrue(digest.reading_card(card)['held'])

    def preparation_card(self,following=None):
        intro='The migration may break builds. To prepare:'
        following=following if following is not None else [
            'Test your workflows against cedar-26 before October 19.',
            'If you are not ready, pin workflows to cedar-24 to stay on the current image.']
        body='\n'.join(['Cedar 26 adds a new runner.',intro]+following)
        return {'highlights':['Cedar 26 adds a new runner.'],
                'conditions':[intro]+following,'source_body':body,
                'source_sha256':core.digest(body)}

    def test_complete_preparation_context_retained(self):
        card=self.preparation_card();view=digest.reading_card(card)
        self.assertFalse(view['held'])
        combined=' '.join(card['conditions'])
        self.assertEqual(view['conditions'],[combined])
        self.assertIn('complete_preparation_context',[a['reason'] for a in view['audit']])

    def test_preparation_stops_at_heading_without_losing_steps(self):
        card=self.preparation_card()
        card['source_body']+='\nLearn more\nVisit the docs.'
        card['source_sha256']=core.digest(card['source_body'])
        view=digest.reading_card(card)
        self.assertFalse(view['held'])
        self.assertNotIn('Visit the docs.',' '.join(view['conditions']))

    def test_preparation_recovers_unselected_source_steps(self):
        card=self.preparation_card();card['conditions']=card['conditions'][:1]
        view=digest.reading_card(card)
        self.assertFalse(view['held'])
        self.assertIn('Test your workflows',view['conditions'][0])
        self.assertIn('pin workflows',view['conditions'][0])

    def test_incomplete_preparation_still_held(self):
        for following in [[],['Learn more','Visit the docs.'],['Test these:'],
                          ['Test your workflows...'],['Test your workflows…'],['Test your workflows']]:
            with self.subTest(following=following):
                self.assertTrue(digest.reading_card(self.preparation_card(following))['held'])

    def test_preparation_requires_verified_unique_source(self):
        for kind in ['absent','hash','duplicate']:
            card=self.preparation_card()
            if kind=='absent':card.pop('source_body')
            elif kind=='hash':card['source_sha256']='wrong'
            else:
                card['source_body']+='\n'+card['conditions'][0]+'\nTest again.'
                card['source_sha256']=core.digest(card['source_body'])
            with self.subTest(kind=kind):self.assertTrue(digest.reading_card(card)['held'])

    def test_oversized_preparation_not_truncated(self):
        card=self.preparation_card(['Test '+('a '*1500)+'before migrating.'])
        self.assertTrue(digest.reading_card(card)['held'])

    def test_general_restriction_list_not_auto_completed(self):
        card=self.preparation_card(['Commercial customers.'])
        old=card['conditions'][0];new='Commercial use is prohibited for:'
        card['conditions'][0]=new;card['source_body']=card['source_body'].replace(old,new)
        card['source_sha256']=core.digest(card['source_body'])
        self.assertTrue(digest.reading_card(card)['held'])
