import unittest
import os
import boto3
import json

from unittest.mock import patch
from src.dynamo.dynamo_handler import dynamo_lookup_entity
from src.dynamo.dynamo_handler import dynamo_save_entity
from src.dynamo.dynamo_helper import get_entity_resolution_table_name
from src.tr.thompson_reuters_helper import ResolvedItem
from src.helpers.serializers import DecimalEncoder
from moto import mock_dynamodb2

aws_region = 'us-west-2'
env_name = 'test'
resolved_table_name = 'test'
region_env_var = {'ERS_AWS_REGION': aws_region}
env_name_var = {'ERS_ENVIRONMENT_NAME': env_name}
resolved_table_env_var = {'RESOLVED_TABLE_NAME': resolved_table_name}


class DynamoTest(unittest.TestCase):

    @patch.dict(os.environ, region_env_var)
    @patch.dict(os.environ, env_name_var)
    @patch.dict(os.environ, resolved_table_env_var)
    def test_dynamo_lookup_entity_when_no_result(self):
        with mock_dynamodb2():
            DynamoTest.setup_dynamo()
            dynamo_result = dynamo_lookup_entity('keyword_not_found')
            self.assertEqual(dynamo_result, '')

    @patch.dict(os.environ, region_env_var)
    @patch.dict(os.environ, env_name_var)
    @patch.dict(os.environ, resolved_table_env_var)
    def test_dynamo_lookup_entity_when_result_found(self):
        with mock_dynamodb2():
            dynamo_table = DynamoTest.setup_dynamo()
            item = {"entity_match": {"mds_organization": {"name": "LinkedIn Corp", "permId": 4296977663,
                                                          "id": 1335346}, "score": "37%", "ticker": "--",
                                     "level": "Possible", "confidence": "NA", "is_public": "NA",
                                     "keyword": "Linkedin", "org_name": "LinkedIn Corp"},
                    "keyword": "Linkedin",
                    "open_calais": [{"mds_organization": {"name": "LinkedIn Corp", "permId": 4296977663,
                                                          "id": 1335346}, "score": "0.67992806",
                                     "ticker": "LNKD", "level": "NA", "confidence": "1.0", "is_public": "false",
                                     "keyword": "Linkedin", "org_name": "LINKEDIN CORPORATION"}]}
            dynamo_table.put_item(Item=item)

            dynamo_result = json.dumps(dynamo_lookup_entity('Linkedin'), cls=DecimalEncoder)
            expected_result = f'{json.dumps(item)}'

            self.assertEqual(dynamo_result, expected_result)

    @patch.dict(os.environ, region_env_var)
    @patch.dict(os.environ, env_name_var)
    @patch.dict(os.environ, resolved_table_env_var)
    def test_dynamo_save_entity(self):
        with mock_dynamodb2():
            DynamoTest.setup_dynamo()
            entity_match = {"entity_match": {"mds_organization": {"name": "LinkedIn Corp", "permId": 4296977663,
                                                                  "id": 1335346}, "score": "37%", "ticker": "--",
                                             "level": "Possible", "confidence": "NA", "is_public": "NA",
                                             "keyword": "Linkedin", "org_name": "LinkedIn Corp"}}
            open_calais = {"open_calais": [{"mds_organization": {"name": "LinkedIn Corp", "permId": 4296977663,
                                                                 "id": 1335346}, "score": "0.67992806",
                                            "ticker": "LNKD", "level": "NA", "confidence": "1.0", "is_public": "false",
                                            "keyword": "Linkedin", "org_name": "LINKEDIN CORPORATION"}]}

            keyword = 'Linkedin'

            entity = ResolvedItem(keyword=keyword,
                                  entity_match=entity_match,
                                  open_calais=open_calais)

            dynamo_save_entity(entity)
            dynamo_result = json.dumps(dynamo_lookup_entity(keyword=keyword), cls=DecimalEncoder)
            expected_result = f'{json.dumps(entity.__dict__)}'

            self.assertEqual(dynamo_result, expected_result)

    @staticmethod
    def setup_dynamo():
        with mock_dynamodb2():
            mock_dynamo_client = boto3.resource('dynamodb', region_name=aws_region)
            mock_dynamo_table = mock_dynamo_client.create_table(
                TableName=get_entity_resolution_table_name(),
                KeySchema=[
                    {
                        'AttributeName': 'keyword',
                        'KeyType': 'HASH'
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'keyword',
                        'AttributeType': 'S'
                    },

                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )

            return mock_dynamo_table


if __name__ == '__main__':
    unittest.main()
