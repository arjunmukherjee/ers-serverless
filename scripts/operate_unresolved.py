import boto3
import urllib
import requests

from src.tr.entity import UnresolvedEntityState
from src.helpers.date_helper import get_timestamp


CORRECTED_COUNT = 0
inspected_count = 0

ers_url = 'https://entityresolution-prod.defaulttest.com/api/v1/resolve/force/keyword'


def resolve_from_file(filename):
    global CORRECTED_COUNT
    try:
        file = open(filename, 'r')
        keywords = file.readlines()
        for keyword_arg in keywords:
            CORRECTED_COUNT = CORRECTED_COUNT + 1

            keyword = urllib.parse.quote(keyword_arg, safe='')
            print(f'{CORRECTED_COUNT}: Fetching entity for [{keyword_arg}]')
            result = requests.post(url=f'{ers_url}/{keyword}')
            print(f'FORCE-RESOLVE: {result.status_code}, {result.text}\n')
    except Exception as e:
        print(f'Corrected {CORRECTED_COUNT} entries')
        print(e)


def resolve_from_table():
    try:
        global CORRECTED_COUNT, inspected_count
        dynamo_client = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamo_client.Table('research-unresolved-entities-prod')

        response = table.scan()
        __force_resolve_entity(response, table)
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            __force_resolve_entity(response, table)

    except Exception as e:
        print(f'Corrected {CORRECTED_COUNT}/{inspected_count} entries')
        print(e)


def __force_resolve_entity(response, table):
    global inspected_count, CORRECTED_COUNT
    for item in response['Items']:
        inspected_count = inspected_count + 1
        keyword_arg = item['keyword']

        # Force Resolve
        keyword = urllib.parse.quote(keyword_arg, safe='')
        result = requests.post(url=f'{ers_url}/{keyword}')

        if result.status_code is requests.codes.ok:
            CORRECTED_COUNT = CORRECTED_COUNT + 1
            __delete_item(keyword_arg, table)
            print(f'{CORRECTED_COUNT}/{inspected_count}: Fetched entity for [{keyword_arg}]')
            print(f'FORCE-RESOLVE: {result.status_code}\n')
        else:
            if (result.status_code - requests.codes.internal_server_error) >= 0:
                state = str(UnresolvedEntityState.FAILED.value)
            else:
                state = str(UnresolvedEntityState.RESOLUTION_FAILED.value)

            item = {
                'keyword': keyword_arg,
                'state': state,
                'timestamp': get_timestamp()
            }
            table.put_item(Item=item)


def __delete_item(keyword, table):
    table.delete_item(
        Key={
            'keyword': keyword
        }
    )


resolve_from_table()
print(f'Corrected {CORRECTED_COUNT}/{inspected_count} entries')