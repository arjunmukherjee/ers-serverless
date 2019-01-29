import boto3
import requests
import json

from src.helpers.keyword_helper import chomp
from src.helpers.keyword_helper import get_correct_keyword
from src.tr.entity_match import get_val
from src.tr.entity import ResolutionAlgo
from src.helpers.date_helper import get_timestamp
from boto3.dynamodb.conditions import Key

"""
Script to pick up all keywords from entityresolution/cached (RDS)
and add them to the ERS's DynamoDB cache with a resolved Entity (via Record matching)
"""

FILE_NAME = '/tmp/unresolved_keywords.txt'
ERROR_FILE_NAME = '/tmp/em_errors.txt'
AWS_REGION = 'us-west-2'
RESOLVED_ENTITY_TABLE_NAME = 'resolved-entities-prod'
ORIG_KEYWORD_DICT = {}
EM_KEYWORD_DICT = {}
BATCH_SIZE = 900
SKIP_BATCHES_UNTIL = 79
CORRECTED_COUNT = 0
TR_EM_URL = 'https://api.thomsonreuters.com/permid/match'
tr_api_key = "'<1>', '<2>'"

#################
TEST_MODE = True
#################

error_fp = open(ERROR_FILE_NAME, "w")


def process_redo_data():
    global CORRECTED_COUNT
    dynamo_client = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamo_client.Table(RESOLVED_ENTITY_TABLE_NAME)

    local_list = []
    with open(FILE_NAME) as fp:
        keyword_orig = fp.readline()
        batch_count = 0
        local_count = 0
        while keyword_orig:
            keyword_orig = chomp(keyword_orig)
            local_count = local_count + 1

            if keyword_orig is not None and keyword_orig is not '':
                keyword = get_correct_keyword(keyword_orig)
                local_list.append(f'{local_count},{keyword}')

                ORIG_KEYWORD_DICT[f'{local_count}'] = chomp(keyword_orig)
                EM_KEYWORD_DICT[f'{local_count}'] = keyword

            if local_count % BATCH_SIZE is 0:
                batch_count = batch_count + 1

                if batch_count >= SKIP_BATCHES_UNTIL:
                    __issue_em_request(local_list, table)
                    print(f'Finished processing {batch_count} batches of {BATCH_SIZE} entities each')

                local_list.clear()

            keyword_orig = fp.readline()

        __issue_em_request(local_list, table)

    print(f'Corrected {CORRECTED_COUNT} entries')


def __issue_em_request(batched_list, table):
    global ef
    data = f'LocalID,Name\n'
    for entity in batched_list:
        data = f'{data}{entity}\n'

    result = requests.post(url=TR_EM_URL, headers=__get_headers(), data=data.encode('utf-8'))
    if result.status_code is requests.codes.ok:
        result_json = json.loads(result.text)
        try:
            result_content = result_json['outputContentResponse']
            for entity in result_content:
                keyword_id = entity['Input_LocalID']
                original_keyword = ORIG_KEYWORD_DICT[keyword_id]
                keyword_for_em = EM_KEYWORD_DICT[keyword_id]
                resolved_result = get_val(keyword=keyword_for_em, relevant_operator=entity)
                __re_resolve(orig_keyword=original_keyword, result=resolved_result, table=table)
        except KeyError:
            for entity in batched_list:
                error_fp.write(f'{entity}\n')
    else:
        print(f'ERROR: {result.status_code} {result.text}')
        for entity in batched_list:
            error_fp.write(f'{entity}\n')


def __re_resolve(orig_keyword, result, table):
    global CORRECTED_COUNT, NEW_COUNT

    if result is not None and result is not '':
        response = table.query(
            KeyConditionExpression=Key('keyword').eq(orig_keyword)
        )

        if len(response['Items']) > 0:
            for item in response['Items']:
                item[ResolutionAlgo.ENTITY_MATCH.value] = result
                item['update_timestamp'] = get_timestamp()
                __put_item(item, table)
        else:
            item = {
                'keyword': orig_keyword,
                ResolutionAlgo.ENTITY_MATCH.value: result,
                'update_timestamp': get_timestamp()
            }
            print(f'Item {orig_keyword} not found, should add new entry')
            NEW_COUNT = NEW_COUNT + 1
            __put_item(item, table)

        CORRECTED_COUNT = CORRECTED_COUNT + 1
        print(f'{CORRECTED_COUNT}/{NEW_COUNT}:- {result} \n')


def __put_item(item, table):
    if not TEST_MODE:
        table.put_item(Item=item)


def __get_headers():
    return {
        'Content-type': 'text/plain',
        'Accept': 'application/json',
        'x-ag-access-token': f'{__get_tr_api_key()}',
        'x-openmatch-numberOfMatchesPerRecord': '1',
        'x-openmatch-dataType': 'Organization'
    }


def __get_tr_api_key():
    import random
    tr_api = eval(tr_api_key)
    index = random.randint(0, len(tr_api) - 1)
    return tr_api[index]


# MAIN
process_redo_data()