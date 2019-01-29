import logging
import requests
import json

from src.helpers.event_response import construct_response
from src.helpers.event_response import error_response
from src.dynamo.dynamo_handler import dynamo_save_override_entity
from src.helpers.date_helper import get_timestamp
from src.dynamo.dynamo_handler import dynamo_lookup_entity
from src.tr.entity import ResolutionAlgo

log = logging.getLogger()
log.setLevel(logging.INFO)


def add_override(event, context):
    try:
        override_request = json.loads(event['body'])
        keyword = override_request['keyword']
        override_request['keyword'] = keyword

        manual_override = override_request[ResolutionAlgo.MANUAL_OVERRIDE.value]
        manual_override['update_timestamp'] = get_timestamp()
        manual_override['keyword'] = keyword

        log.info(f'Received manual override request for keyword {keyword}, and payload {override_request}')

        if override_request is not None:
            dynamo_result = dynamo_lookup_entity(keyword)
            if not dynamo_result:
                dynamo_save_override_entity(override_request)
            else:
                dynamo_result[ResolutionAlgo.MANUAL_OVERRIDE.value] = manual_override
                dynamo_save_override_entity(dynamo_result)

        return construct_response(requests.codes.ok, f'Successfully added manual override for {keyword}')
    except:
        message = 'MANUAL-OVERRIDE: Error while processing a manual override request, ' \
                  'dropping into SNS for some hand holding'
        return error_response(event, message, log)
