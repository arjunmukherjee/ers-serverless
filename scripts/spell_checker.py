import fuzzy

from src.helpers.spell_check_helper import spell_check_entity_name
from src.helpers.spell_check_helper import word_suggestion

#################
## POC POC POC ##
#################

"""
Rockwell Automation Technolgies, Inc. - does not resolve
Rockwell Automation Technologies Inc. - resolved via em and oc,
    ENTITY-MATCH: {'keyword': 'Rockwell Automation Technologies Inc.',
    'org_name': 'Rockwell Automation Technologies Inc', 'confidence': '0.92', 'perm_id': 5000187552,
    'is_company_score': '1.0'}

Pioneer Hi-Bred Internationak, Inc. - does not resolve
Pioneer Hi-Bred International Inc. - resolved via em and oc,
    ENTITY-MATCH: {'keyword': 'Pioneer Hi-Bred International Inc.',
    'org_name': 'Pioneer Hi-Bred International Inc', 'confidence': '0.92', 'perm_id': 4295911139,
    'is_company_score': '1.0'}

Honeywell Internations, Inc. - does not resolve
Honeywell International Inc. - resolved via em and oc,
    ENTITY-MATCH: {'keyword': 'Honeywell International Inc.',
    'org_name': 'Honeywell International Inc', 'confidence': '0.92', 'perm_id': 4295912155,
    'is_company_score': '1.0'}

"""


def __internal_assert(value, expected_value):
    try:
        assert value == expected_value
    except AssertionError:
        print(f'\nASSERTION FAILED: [{value}] != [{expected_value}]\n')


def __test_words(print_output=False):
    input_words = {'TECHNOLOGU': 'Technology', 'copmany': 'Company', 'INCORPORRATED': 'Incorporated',
                   'systemmss': 'Systems', 'orporration': 'Corporation', 'llimite': 'Limited', 'rresarch': 'Research',
                   'Groups': 'Groups', 'Products': 'Products', 'Internationak': 'International', 'Limiteds': 'Limited',
                   'SOLUTIONS': 'Solutions', 'Enterprises': 'Enterprises', 'Developmentt': 'Development',
                   'Industriess': 'Industries', 'Nationals': 'National', 'Technologie': 'Technologies',
                   'Holdngss': 'Holdings', 'konsultan': 'Consultant'}
    for (keyword, expected_word) in input_words.items():
        (suggestion, distance) = word_suggestion(keyword)
        if print_output:
            print(f'Input:[{keyword}]\t\t\t\tSuggestion:[{suggestion}]\t\t\t\tDistance:[{distance}]')
        __internal_assert(suggestion, expected_word)


def __test_entities(print_output=False):
    input_entities = {'Hewlett Packarrd Develoment': 'Hewlett Packarrd Development',
                      'Pioneer Hi-Bred Internationak, Inc.': 'Pioneer Hi-Bred International, Inc.',
                      'Technologias Avanzadas Inspiralia S.L.': 'Technologies Avanzadas Inspiralia S.L.',
                      'Microsoft Technology': 'Microsoft Technology',
                      'Rockwell Automation Technolgies, Inc.': 'Rockwell Automation Technologies, Inc.',
                      'Honeywell Internations, Inc.': 'Honeywell International, Inc.'}
    for (entity_name, expected_word) in input_entities.items():
        corrected_word = spell_check_entity_name(entity_name)
        __internal_assert(corrected_word, expected_word)
        if print_output:
            print(f'Input:[{entity_name}], Corrected:[{corrected_word}]')


def __test_false_positives(print_output=False, apply_phonetic_check=False):
    input_words = {'United': 'Limited'}
    for (keyword, expected_word) in input_words.items():
        (suggestion, distance) = word_suggestion(keyword, max_distance=3, apply_phonetic_check=apply_phonetic_check)
        sug_score = fuzzy.nysiis(suggestion)
        orig_score = fuzzy.nysiis(keyword)
        if print_output:
            print(f'Input:[{keyword}] [{orig_score}]\t\t\t\t'
                  f'Suggestion:[{suggestion}][{sug_score}]\t\t\t\tDistance:[{distance}]')
        __internal_assert(suggestion, expected_word)


def main():
    __test_entities(print_output=True)
    __test_words(print_output=True)
    __test_false_positives(print_output=True)
    __test_false_positives(print_output=True, apply_phonetic_check=True)


main()
