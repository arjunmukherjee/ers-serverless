import os


def get_sns_arn():
    return os.environ['AWS_SNS_ARN']


def get_environment():
    return os.environ['ERS_ENVIRONMENT_NAME']


def get_aws_region():
    return os.environ['ERS_AWS_REGION']


def get_tr_api_key():
    import random
    tr_api_str = os.environ['TR_API_KEY']
    tr_api = eval(tr_api_str)
    index = random.randint(0, len(tr_api) - 1)
    return tr_api[index]


def get_tr_url():
    return os.environ['TR_URL']

