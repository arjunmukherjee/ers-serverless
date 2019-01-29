import logging
import requests

from src.dynamo.dynamo_handler import dynamo_lookup_entity
from src.tr.thompson_reuters_helper import search_tr
from src.helpers.event_response import construct_response
from src.helpers.event_response import failure_response
from src.helpers.event_response import error_response
from src.helpers.keyword_helper import extract_keyword

log = logging.getLogger()
log.setLevel(logging.INFO)


def entity_resolution(event, context):
    try:
        keyword = extract_keyword(event)
        log.info(f'Received resolution query for {keyword}')

        result = dynamo_lookup_entity(keyword)
        if not result:
            result = search_tr(keyword=keyword)
            if not result:
                return construct_response(requests.codes.not_found, failure_response('resolve', keyword))

        return construct_response(requests.codes.ok, result)
    except:
        message = 'ENTITY-RESOLUTION: Error while processing request, dropping into SNS for some hand holding'
        return error_response(event, message, log)


def entity_resolution_force(event, context):
    try:
        keyword = extract_keyword(event)
        result = search_tr(keyword=keyword)
        if not result:
            return construct_response(requests.codes.not_found, failure_response('resolve', keyword))

        return construct_response(requests.codes.ok, result)
    except:
        message = 'ENTITY-RESOLUTION-FORCE: Error while processing request, dropping into SNS for some hand holding'
        return error_response(event, message, log)


def entity_lookup(event, context):
    try:
        keyword = extract_keyword(event)
        log.info(f'Received lookup query for {keyword}')

        result = dynamo_lookup_entity(keyword)
        if not result:
            return construct_response(requests.codes.not_found, failure_response('lookup', keyword))

        return construct_response(requests.codes.ok, result)
    except:
        message = 'ENTITY-LOOKUP: Error while processing request, dropping into SNS for some hand holding'
        return error_response(event, message, log)
