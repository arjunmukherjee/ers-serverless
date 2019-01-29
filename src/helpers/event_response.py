import json
import traceback
import requests

from src.helpers.serializers import DecimalEncoder
from src.sns.sns_handler import drop_into_sns


def construct_response(status_code, body):
    response = {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder)
    }

    return response


def error_response(event, message, log):
    log.error(traceback.format_exc())
    log.error(message)
    drop_into_sns(json.dumps(event))
    return construct_response(requests.codes.internal_server_error, message)


def failure_response(api_type, keyword):
    return {"status": "failed",
            "message": "Could not successfully " + api_type + " entity for keyword [" + keyword + "]"}
