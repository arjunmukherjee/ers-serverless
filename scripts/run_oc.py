import boto3
import requests
import html
import time

from src.helpers.keyword_helper import chomp
from src.tr.entity import ResolutionAlgo
from src.helpers.date_helper import get_timestamp
from src.tr.entity import default_not_found_result
from src.tr.entity import Entity
from boto3.dynamodb.conditions import Key

"""
Script to pick up all keywords from entityresolution/cached (RDS)
and add them to the ERS's DynamoDB cache
"""

FILE_NAME = '/tmp/unresolved_keywords.txt'
ERROR_FILE_NAME = '/tmp/oc_errors.txt'
AWS_REGION = 'us-west-2'
RESOLVED_ENTITY_TABLE_NAME = 'resolved-entities-prod'
BATCH_SIZE = 200
SKIP_BATCHES_UNTIL = 0
CORRECTED_COUNT = 0
RESOLVED_COUNT = 0
DEFAULTED_COUNT = 0
BATCH_COUNT = 0
NEW_COUNT = 0
TR_EM_URL = 'https://api.thomsonreuters.com/permid/match'
tr_api_key = "'<1>', '<2>'"

#################
TEST_MODE = True
#################

error_fp = open(ERROR_FILE_NAME, "w")


def process_redo_data():
    global CORRECTED_COUNT, BATCH_COUNT
    dynamo_client = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamo_client.Table(RESOLVED_ENTITY_TABLE_NAME)

    local_list = []
    with open(FILE_NAME) as fp:
        keyword_orig = fp.readline()
        while keyword_orig:
            keyword_orig = chomp(keyword_orig)

            if keyword_orig is not None and keyword_orig is not '':
                local_list.append(keyword_orig)

            keyword_orig = fp.readline()

        tr_calais_match(entities=local_list, table=table)

    print(f'Corrected {CORRECTED_COUNT} entries')


def _divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def _indexed_join(strings, joiner):
    result = joiner.join(strings)
    ixs = [{'string': strings[0], 'start': 0, 'end': len(strings[0])}]
    for i in range(1, len(strings)):
        i1 = ixs[i - 1]['end'] + len(joiner)
        i2 = i1 + len(strings[i])
        ixs.append({'string': strings[i], 'start': i1, 'end': i2})
    return result, ixs


def tr_calais_match(entities, table, max_trys=5):
    [_tr_calais_match_subset(s, table, max_trys) for s in _divide_chunks(entities, BATCH_SIZE)]


def _tr_calais_match_subset(entities, table, max_trys=5):
    global BATCH_COUNT, error_fp
    BATCH_COUNT = BATCH_COUNT + 1

    if BATCH_COUNT >= SKIP_BATCHES_UNTIL:
        joiner = ' is a company\n'
        _strings = [html.unescape(s) for s in entities]
        data, ixs = _indexed_join(_strings, joiner)
        uri = 'https://api.thomsonreuters.com/permid/calais'
        headers = __get_headers()
        trys = 0

        res = requests.post(uri, headers=headers, data=data.encode('utf-8'))
        while res.status_code != requests.codes.ok:
            print(f'Status {res.status_code} returned from {uri}')
            trys += 1
            if trys > max_trys:
                print('Max Retry(s) reached!')
                for entity in entities:
                    error_fp.write(f'{entity}\n')
                return
            else:
                print('Sleeping for {0} seconds..'.format(1 * 2 ** trys))
                time.sleep(1 * 2 ** trys)
                print('Retry {0}/{1}...'.format(trys, max_trys))
                res = requests.post(uri, headers=headers, data=data.encode('utf-8'))

        result = res.json()
        companies = [v for v in result.values() if v.get('_type') == 'Company'
                     and v.get('resolutions') is not None]
        vals = [_get_val(i, r) for r in companies for i in r['instances']]
        _check_results(vals, data)
        matches = _match_results(vals, ixs)

        [__re_resolve(match, table) for match in matches]
        print(f'Finished processing {BATCH_COUNT} batches of {BATCH_SIZE} entities each')
    else:
        print(f'Skipping batch {BATCH_COUNT}')


def _match_results(vals, ixs):
    matches = [{'input': ixs[i]['string'], 'child': None} for i in range(len(ixs))]
    for val in vals:
        for i in range(len(ixs)):
            ix = ixs[i]
            if val['start'] >= ix['start'] and val['end'] <= ix['end']:
                if matches[i]['child'] is None or \
                        (matches[i]['matching']['confidence'] < val['confidence']):
                    matches[i] = {
                        'input': ix['string'],
                        'matching': {
                            'resolver': 'calais',
                            'match': val['match'],
                            'confidence': val['confidence'],
                            'score': val['score']
                        },
                        'child': {
                            'name': val['name'],
                            'permId': val['permId'],
                        }
                    }
                continue

    return matches


def _check_results(vals, data):
    # The TR API unescapes the supplied string. This checks that
    # the matches match the exact position in the string as expected,
    # ie checking that we're escaping in the same way as the API.
    minmatch = len(data)
    valmatch = None

    for v in vals:
        expected = v['match']
        actual = data[v['start']:v['end']]
        if expected != actual and v['start'] < minmatch:
            valmatch = v
            minmatch = v['start']

    if valmatch is not None:
        print('Error in matching string lengths starting at {0}'
              .format(minmatch))


def _get_val(instance, result):
    return {
        'start': int(instance['offset']),
        'end': int(instance['offset'] + instance['length']),
        'length': int(instance['length']),
        'match': instance['exact'],
        'confidence': float(result.get('confidence').get('aggregate')),
        'name': result['resolutions'][0]['name'],
        'permId': int(result['resolutions'][0]['permid']),
        'ispublic': result['resolutions'][0]['ispublic'],
        'ticker': result['resolutions'][0].get('ticker'),
        'score': float(result['resolutions'][0]['score'])
    }


def __re_resolve(result, table):
    global CORRECTED_COUNT, RESOLVED_COUNT, DEFAULTED_COUNT, NEW_COUNT

    orig_keyword = result['input']
    entity = default_not_found_result(resolution_algorithm=ResolutionAlgo.OPEN_CALAIS, keyword=orig_keyword)

    try:
        if result['matching'] is not None and result['matching'] is not '':
            entity = _get_entity(orig_keyword, result)
            RESOLVED_COUNT = RESOLVED_COUNT + 1
    except KeyError:
        DEFAULTED_COUNT = DEFAULTED_COUNT + 1

    if entity is not None:
        response = table.query(
            KeyConditionExpression=Key('keyword').eq(orig_keyword)
        )

        if len(response['Items']) > 0:
            for item in response['Items']:
                item[ResolutionAlgo.OPEN_CALAIS.value] = entity
                item['update_timestamp'] = get_timestamp()
                __put_item(item, table)
        else:
            item = {
                'keyword': orig_keyword,
                ResolutionAlgo.OPEN_CALAIS.value: entity,
                'update_timestamp': get_timestamp()
            }
            print(f'Item {orig_keyword} not found, should add new entry')
            NEW_COUNT = NEW_COUNT + 1
            __put_item(item, table)

        CORRECTED_COUNT = CORRECTED_COUNT + 1
        print(f'{CORRECTED_COUNT}/{RESOLVED_COUNT}/{DEFAULTED_COUNT}/{NEW_COUNT}:- {entity} \n')


def __put_item(item, table):
    if not TEST_MODE:
        table.put_item(Item=item)


def __get_headers():
    return {
        'Content-Type': 'text/raw',
        'Accept': 'application/json',
        'outputFormat': 'application/json',
        'x-ag-access-token': f'{__get_tr_api_key()}'
    }


def _get_entity(keyword, result):
    perm_id = int(result['child']['permId'])
    entity = Entity(keyword=keyword,
                    org_name=str(result['child']['name']),
                    confidence=str(result['matching']['score']),
                    perm_id=perm_id,
                    is_company_score=str(result['matching']['confidence']))

    return [entity.__dict__]


def __get_tr_api_key():
    import random
    tr_api = eval(tr_api_key)
    index = random.randint(0, len(tr_api) - 1)
    return tr_api[index]


# MAIN
process_redo_data()
