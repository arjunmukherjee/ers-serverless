import fuzzy

#######################################################################
# Tread carefully, depending on the allowed edit distance,
# you could be drastically changing the entity name
# The phonetic similarity check can prevent some of these,
# but (as it is currently implemented) it really does more harm than good
#
# https://www.python-course.eu/levenshtein_distance.php
# http://www.informit.com/articles/article.aspx?p=1848528
#######################################################################

COMMON_WORDS = frozenset(
    ['Company', 'Technology', 'Electric', 'Electronic', 'Electronics', 'Corporation', 'Cooperation',
     'Incorporated', 'System', 'Systems', 'Limited', 'Research', 'Products', 'Product',
     'Group', 'Groups', 'International', 'Solution', 'Solutions', 'Enterprise', 'Enterprises',
     'Development', 'Industries', 'Industry', 'Industrial', 'Holding', 'Holdings',
     'National', 'Technologies', 'Consultant', 'Consultants', 'Consulting', 'Science', 'Sciences',
     'Organization', 'Organization', 'Rational'])
MAX_ALLOWED_DISTANCE = 2
memo = {}


def __levenshtein(s, t):
    if s == "":
        return len(t)
    if t == "":
        return len(s)
    cost = 0 if s[-1].lower() == t[-1].lower() else 1

    i1 = (s[:-1], t)
    if i1 not in memo:
        memo[i1] = __levenshtein(*i1)
    i2 = (s, t[:-1])
    if i2 not in memo:
        memo[i2] = __levenshtein(*i2)
    i3 = (s[:-1], t[:-1])
    if i3 not in memo:
        memo[i3] = __levenshtein(*i3)
    res = min([memo[i1] + 1, memo[i2] + 1, memo[i3] + cost])

    return res


def __has_comma_end(word):
    if ',' == word[-1]:
        return True
    return False


def __is_phonetically_similar(keyword, suggestion):
    return fuzzy.nysiis(keyword) == fuzzy.nysiis(suggestion)


def word_suggestion(keyword, max_distance=MAX_ALLOWED_DISTANCE, apply_phonetic_check=False):
    has_comma = __has_comma_end(keyword)
    keyword_no_comma = keyword
    if has_comma:
        keyword_no_comma = keyword.strip(',')

    min_distance = max_distance + 1
    suggestion = keyword_no_comma
    for known_word in COMMON_WORDS:
        distance = __levenshtein(keyword_no_comma, known_word)
        if distance < min_distance:
            min_distance = distance
            suggestion = known_word

    if has_comma:
        suggestion = suggestion + ','

    phonetically_similar = __is_phonetically_similar(keyword, suggestion) if apply_phonetic_check else True

    if (min_distance <= max_distance) and phonetically_similar:
        return suggestion, min_distance
    else:
        return keyword, min_distance


def spell_check_entity_name(name, max_distance=MAX_ALLOWED_DISTANCE, apply_phonetic_check=False):
    entity_parts = name.split()
    final_list = []
    for entity_part in entity_parts:
        (suggestion, distance) = word_suggestion(entity_part, max_distance, apply_phonetic_check)
        final_list.append(suggestion)

    return ' '.join(final_list)
