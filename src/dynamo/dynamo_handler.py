import boto3
import logging

from src.dynamo.dynamo_helper import get_entity_resolution_table_name
from src.dynamo.dynamo_helper import get_unresolved_entities_table_name
from src.helpers.environment_helper import get_aws_region
from boto3.dynamodb.conditions import Key
from src.tr.entity import UnresolvedEntityState
from src.helpers.date_helper import get_timestamp

log = logging.getLogger()
log.setLevel(logging.INFO)
dynamo_client = None


def dynamo_lookup_entity(keyword):
    log.info(f'Looking up {keyword}, in {get_entity_resolution_table_name()}')
    global dynamo_client
    if not dynamo_client:
        dynamo_client = boto3.resource('dynamodb', region_name=get_aws_region())

    result = ""
    entity_resolution_table = dynamo_client.Table(get_entity_resolution_table_name())
    resolved_entities = entity_resolution_table.query(
        KeyConditionExpression=Key('keyword').eq(keyword)
    )

    items = resolved_entities['Items']
    if len(items) is not 0:
        result = items[0]
        log.info(f'Found entity in dynamo: {result}')

    return result


def persist_unresolved_entity(keyword, state=UnresolvedEntityState.NEW.value):
    item = {
        'keyword': keyword,
        'state': str(state),
        'timestamp': get_timestamp()
    }
    __dynamo_save_item(item, get_unresolved_entities_table_name())


def dynamo_save_entity(resolved_entity):
    entity_to_persist = resolved_entity.__dict__
    __dynamo_save_item(entity_to_persist, get_entity_resolution_table_name())


def dynamo_save_override_entity(resolved_entity):
    __dynamo_save_item(resolved_entity, get_entity_resolution_table_name())


def __dynamo_save_item(item_to_save, table_name):
    log.info(f'Persisting {item_to_save} into Dynamo {table_name}')
    global dynamo_client
    if not dynamo_client:
        dynamo_client = boto3.resource('dynamodb', region_name=get_aws_region())
    table = dynamo_client.Table(table_name)

    table.put_item(Item=item_to_save)

