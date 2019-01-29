import logging
import boto3
import json

from src.helpers.environment_helper import get_sns_arn
log = logging.getLogger()
log.setLevel(logging.DEBUG)

sns_client = None


# TODO : Setup a dead letter queue
def error_handler(event, context):
    try:
        message = event['Records'][0]['Sns']['Message']
        log.error("Message: " + str(message))
        # TODO: DO SOMETHING : ALERT SOMEONE
    except:
        log.error("Problem processing error message from kinesis")

    return "Processed the poison pill"


def drop_into_sns(message):
    global sns_client
    if not sns_client:
        sns_client = boto3.client('sns')

    response = sns_client.publish(
        TargetArn=get_sns_arn(),
        Message=json.dumps({'default': json.dumps(message)}),
        MessageStructure='json'
    )

    return response

