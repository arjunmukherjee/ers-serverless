import os
import boto3

from src.helpers.spell_check_helper import spell_check_entity_name
from src.tr.entity import ResolutionAlgo
from src.tr.open_calais import issue_open_calais_request
from src.tr.entity_match import issue_entity_match_request
from src.helpers.keyword_helper import chomp
from boto3.dynamodb.conditions import Key
from src.helpers.date_helper import get_timestamp

tr_url = 'https://api.thomsonreuters.com/permid'
tr_api_key = "'T8O05jZLRmRSwoAO4s7aqQ0pLEdUDc1q', 'n8Lsq8i4Avmtuhb2hIPPahm8IEEeG0UD', 'lYCw3UTd1nEG358m7QzGqtMwuvVSqkZy', 'MK9qN3LOrq08J0yeU4xzrgVXDQpNF6Tc', 'PVAq1PQ4EKuf7trZhR9VHbzNCYATFbjA', 'Hhkg9velWq5J3f9ja59Ine5M2ZP4Hnnu', 'l1gq7Ax5iya3Ihp2Z9GdUF9YJz9BEXF2', '8WrHdINHPy3Z2Njj20rP9fdtDHlGFnLC', 'yYxdhkRrVcok8RRBL01E9KLlyL8iRfI6', 'E3P5ASwAzIzpBsO6jwNvGEn41RO5ZN9n', 'hAZyfD0QSs4YJkCYPfFRNmOoSN5iCtQP', 'bnafQDMOHpDELo9mCD8Tb2DSAdM2wmdh', 'eeevlJlEWFJyPGlbgcb4ujXc3zT5OwYo', 'HJITWshnoVXHzmy5N28dKwGJYuTgf4xb', 'hxYsqdwQxrOzRMpR5Di5R6w1PD6vhTc2', 'Ie7GoXoZwDjzWvISjGR3G88KGEZKhKL2', 'EjWxaMHZXT3BoCJXhmXzSv3ka0b1ZF6Q', 'KAkuqsbTHjAIC4OUEYrW8w5J3nKcGv1l', 'HKQ02EEiOGxXoNxkyTcn97t277J2flZK', '3WvYQqPbecOAodx4aegGhTx7lD7TCGjt', 'YQ5LHGNNzyxaAJvTJJI5F7AtDOyoBTAI', '5a5HZoae9aDQwtdyoDdKq8kU9G7ye9cG'"

FILE_NAME = '/tmp/unresolved_keywords.txt'
RESOLVED_FILE_NAME = '/tmp/spell_resolved.txt'
os.environ['TR_URL'] = tr_url
os.environ['TR_API_KEY'] = tr_api_key
CORRECTED_COUNT = 0
NEW_COUNT = 0
INSPECTED_COUNT = 0
ATTEMPTED_COUNT = 0
AWS_REGION = 'us-west-2'
RESOLVED_ENTITY_TABLE_NAME = 'resolved-entities-prod'

#################
TEST_MODE = True
#################


resolved_fp = open(RESOLVED_FILE_NAME, "w")


def process_redo_data():
    global INSPECTED_COUNT, ATTEMPTED_COUNT
    dynamo_client = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamo_client.Table(RESOLVED_ENTITY_TABLE_NAME)

    with open(FILE_NAME) as fp:
        keyword_orig = fp.readline()
        while keyword_orig:
            keyword_orig = chomp(keyword_orig)
            INSPECTED_COUNT = INSPECTED_COUNT + 1

            if keyword_orig is not None and keyword_orig is not '':
                keyword_spell_checked = spell_check_entity_name(keyword_orig)

                if not keyword_spell_checked.lower() == keyword_orig.lower():
                    (em_result, oc_result) = __issue_em_oc_request(keyword_orig=keyword_orig)

                    if em_result['perm_id'] == 0 and oc_result[0]['perm_id'] == 0:
                        ATTEMPTED_COUNT = ATTEMPTED_COUNT + 1
                        print('----------------------------------------------------------------------------------------'
                              '---------------------------------------------------------------')
                        print(f'{INSPECTED_COUNT}/{ATTEMPTED_COUNT}/{CORRECTED_COUNT}: No em & oc match found '
                              f'with [{keyword_orig}],trying with spell check [{keyword_spell_checked}]')
                        (em_result, oc_result) = __issue_em_oc_request(keyword_orig=keyword_spell_checked)
                        if not (em_result['perm_id'] == 0 and oc_result[0]['perm_id'] == 0):
                            __re_resolve(keyword_orig, table, em_result=em_result, oc_result=oc_result)
                            print(f'{INSPECTED_COUNT}/{ATTEMPTED_COUNT}/{CORRECTED_COUNT}: Orig [{keyword_orig}], '
                                  f'Checked [{keyword_spell_checked}], EM: [{em_result}] OC: [{oc_result}]')
                            resolved_fp.write(f'{INSPECTED_COUNT}/{ATTEMPTED_COUNT}/{CORRECTED_COUNT}: '
                                              f'Orig [{keyword_orig}],Checked [{keyword_spell_checked}], '
                                              f'[{em_result}] [{oc_result}]\n')
                            resolved_fp.flush()
            keyword_orig = fp.readline()


def __issue_em_oc_request(keyword_orig):
    em_result = issue_entity_match_request(keyword_arg=keyword_orig)
    oc_result = issue_open_calais_request(keyword_arg=keyword_orig, max_retry=10)

    return em_result, oc_result


def __re_resolve(orig_keyword, table, em_result = None, oc_result = None):
    global CORRECTED_COUNT

    if em_result is not None or oc_result is not None:
        CORRECTED_COUNT = CORRECTED_COUNT + 1

    if em_result is not None:
        __add_resolution(table, orig_keyword, em_result, ResolutionAlgo.ENTITY_MATCH.value)
    if oc_result is not None:
        __add_resolution(table, orig_keyword, oc_result, ResolutionAlgo.OPEN_CALAIS.value)


def __add_resolution(table, orig_keyword, entity, algo):
    response = table.query(
        KeyConditionExpression=Key('keyword').eq(orig_keyword)
    )

    global NEW_COUNT
    if len(response['Items']) > 0:
        for item in response['Items']:
            item[algo] = entity
            item['update_timestamp'] = get_timestamp()
            __put_item(item, table)
    else:
        item = {
            'keyword': orig_keyword,
            algo: entity,
            'update_timestamp': get_timestamp()
        }
        print(f'Item {orig_keyword} not found, should add new entry')
        NEW_COUNT = NEW_COUNT + 1
        __put_item(item, table)


def __put_item(item, table):
    if not TEST_MODE:
        table.put_item(Item=item)


process_redo_data()