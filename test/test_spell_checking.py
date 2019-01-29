from unittest import TestCase

from src.helpers.spell_check_helper import spell_check_entity_name
from src.helpers.spell_check_helper import word_suggestion


class TestSpellCheck(TestCase):
    def test_entity_name_correction(self):
        input_entities = {'Hewlett Packarrd Develoment': 'Hewlett Packarrd Development',
                          'Pioneer Hi-Bred Internationak, Inc.': 'Pioneer Hi-Bred International, Inc.',
                          'Technologias Avanzadas Inspiralia S.L.': 'Technologies Avanzadas Inspiralia S.L.',
                          'Microsoft Technology': 'Microsoft Technology',
                          'Rockwell Automation Technolgies, Inc.': 'Rockwell Automation Technologies, Inc.',
                          'Honeywell Internations, Inc.': 'Honeywell International, Inc.'}

        for (entity_name, expected_word) in input_entities.items():
            corrected_word = spell_check_entity_name(entity_name, apply_phonetic_check=False)
            self.assertEqual(expected_word, corrected_word)

    def test_individual_word_correction(self):
        input_words = {'TECHNOLOGU': 'Technology', 'copmany': 'Company', 'INCORPORRATED': 'Incorporated',
                       'systemmss': 'Systems', 'orporration': 'Corporation', 'llimite': 'Limited',
                       'rresarch': 'Research',
                       'Groups': 'Groups', 'Products': 'Products', 'Internationak': 'International',
                       'Limiteds': 'Limited',
                       'SOLUTIONS': 'Solutions', 'Enterprises': 'Enterprises', 'Developmentt': 'Development',
                       'Industriess': 'Industries', 'Nationals': 'National', 'Technologie': 'Technologies',
                       'Holdngss': 'Holdings', 'konsultan': 'Consultant', 'United': 'United', 'Group,': 'Group,',
                       'RATIONAL': 'Rational'}
        for (keyword, expected_word) in input_words.items():
            (suggestion, distance) = word_suggestion(keyword, apply_phonetic_check=False)
            self.assertEqual(expected_word, suggestion)

    def test_individual_word_correction_failures_without_phonetic_check(self):
        input_words = {'Compact': 'Company'}
        for (keyword, expected_word) in input_words.items():
            (suggestion, distance) = word_suggestion(keyword, apply_phonetic_check=False)
            self.assertEqual(expected_word, suggestion, )

    def test_individual_word_correction_failures_with_phonetic_check(self):
        input_words = {'Compact': 'Compact'}
        for (keyword, expected_word) in input_words.items():
            (suggestion, distance) = word_suggestion(keyword, apply_phonetic_check=True)
            self.assertEqual(expected_word, suggestion, )
