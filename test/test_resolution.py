import requests
import json

from unittest import TestCase
from src.resolution.entity_handler import entity_resolution
from src.resolution.smart_entity_handler import entity_resolution_smart
from src.resolution.entity_handler import entity_resolution_force
from src.resolution.entity_handler import entity_lookup
from src.resolution.smart_entity_handler import entity_lookup_smart
from src.resolution.smart_entity_handler import MIN_CONFIDENCE
from unittest.mock import patch


class ResolutionTest(TestCase):
    keyword = 'test'
    good_event = {'pathParameters': {'keyword': keyword}}
    bad_event = {'pathParameters': {'keywordzz': keyword}}
    encoded_event = {'pathParameters': {'keyword': 'some%20keyword'}}

    @patch('src.resolution.entity_handler.error_response')
    def test_unsuccessful_entity_resolution_incorrect_request(self, mock_error_response):
        mock_error_response.return_value = {"statusCode": requests.codes.ok, "body": "Invalid body"}
        expected_result = {'statusCode': requests.codes.ok, 'body': 'Invalid body'}

        result = entity_resolution(self.bad_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.search_tr')
    @patch('src.resolution.entity_handler.dynamo_lookup_entity')
    def test_successful_entity_resolution_caching_miss(self, mock_dynamo, mock_tr):
        mock_dynamo.return_value = ''
        mock_tr.return_value = 'mock result from TR'
        expected_result = {'statusCode': 200, 'body': f'"{mock_tr.return_value}"'}

        result = entity_resolution(self.good_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.search_tr')
    @patch('src.resolution.entity_handler.dynamo_lookup_entity')
    def test_successful_entity_resolution_url_encoded(self, mock_dynamo, mock_tr):
        mock_dynamo.return_value = ''
        mock_tr.return_value = 'mock result from TR'
        expected_result = {'statusCode': 200, 'body': f'"{mock_tr.return_value}"'}

        result = entity_resolution(self.encoded_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.search_tr')
    @patch('src.resolution.entity_handler.dynamo_lookup_entity')
    def test_failed_entity_resolution_cache_miss(self, mock_dynamo, mock_tr):
        mock_dynamo.return_value = ''
        mock_tr.return_value = ''
        expected_result = {'statusCode': 404, 'body': '{"status": "failed", "message": "Could not successfully '
                                                      'resolve entity for keyword [test]"}'}

        result = entity_resolution(self.good_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.search_tr')
    @patch('src.resolution.entity_handler.dynamo_lookup_entity')
    def test_entity_resolution_keyword_is_title(self, mock_dynamo, mock_tr):
        expected_keyword = self.keyword
        mock_dynamo.return_value = ''
        mock_tr.return_value = ''
        expected_result = {'statusCode': 404,
                           'body': '{"status": "failed", "message": "Could not successfully resolve entity for '
                                   'keyword [' + expected_keyword + ']"}'}

        result = entity_resolution(self.good_event, None)
        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.dynamo_lookup_entity')
    def test_entity_resolution_cache_hit(self, mock_dynamo):
        mock_dynamo.return_value = 'mock result from Cache'

        result = entity_resolution(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': f'"{mock_dynamo.return_value}"'}
        self.assertEqual(expected_result, result)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_manual_override(self, mock_dynamo):
        manual_override = {"confidence": "1.0", "perm_id": 1234}
        mock_dynamo.return_value = {"manual_override": manual_override}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': manual_override}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'manual_override')
        self.assertEqual(expected_result['body']['resolution_algorithm'], result_json['resolution_algorithm'])

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_manual_override_low_confidence(self, mock_dynamo):
        manual_override = {"confidence": "0.6"}
        mock_dynamo.return_value = {"manual_override": manual_override}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 404, 'body':
            {'status': 'failed', 'message': 'Could not successfully smart-resolution entity for keyword [test]'}}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_entity_match(self, mock_dynamo):
        entity_match = {"confidence": "0.9", "perm_id": 1234}
        mock_dynamo.return_value = {"entity_match": entity_match}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': entity_match}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'entity_match')
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_entity_match_low_confidence(self, mock_dynamo):
        entity_match = {"confidence": "0.6"}
        mock_dynamo.return_value = {"entity_match": entity_match}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 404, 'body':
            {'status': 'failed', 'message': 'Could not successfully smart-resolution entity for keyword [test]'}}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_open_calais(self, mock_dynamo):
        open_calais = [{"confidence": "0.9", "is_company_score": "0.9", "perm_id": 1234}]
        mock_dynamo.return_value = {"open_calais": open_calais}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': open_calais[0]}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'open_calais')
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_open_calais_low_confidence(self, mock_dynamo):
        open_calais = [{"confidence": "0.6", "is_company_score": "0.9"}]
        mock_dynamo.return_value = {"open_calais": open_calais}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 404, 'body':
            {'status': 'failed', 'message': 'Could not successfully smart-resolution entity for keyword [test]'}}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_open_calais_low_is_company_score(self, mock_dynamo):
        open_calais = [{"confidence": "0.9", "is_company_score": "0.2"}]
        mock_dynamo.return_value = {"open_calais": open_calais}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 404, 'body':
            {'status': 'failed', 'message': 'Could not successfully smart-resolution entity for keyword [test]'}}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_resolution_cache_hit_open_calais_rank_by_confidence(self, mock_dynamo):
        open_calais = [{"confidence": "0.9", "is_company_score": "0.9", "perm_id": 1234},
                       {"confidence": "0.8", "is_company_score": "0.9", "perm_id": 1234}]
        mock_dynamo.return_value = {"open_calais": open_calais}

        result = entity_resolution_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': open_calais[0]}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'open_calais')
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.entity_handler.search_tr')
    def test_successful_entity_resolution_force(self, mock_tr):
        mock_tr.return_value = 'mock result from TR'
        expected_result = {'statusCode': 200, 'body': f'"{mock_tr.return_value}"'}

        result = entity_resolution_force(self.good_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.search_tr')
    def test_failed_entity_resolution_force(self, mock_tr):
        mock_tr.return_value = ''
        expected_result = {'statusCode': 404,
                           'body': '{"status": "failed", '
                                   '"message": "Could not successfully resolve entity for keyword [test]"}'}

        result = entity_resolution_force(self.good_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.dynamo_lookup_entity')
    def test_entity_lookup_cache_hit(self, mock_dynamo):
        mock_dynamo.return_value = 'mock result from Cache'

        result = entity_lookup(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': f'"{mock_dynamo.return_value}"'}
        self.assertEqual(expected_result, result)

    @patch('src.resolution.entity_handler.dynamo_lookup_entity')
    def test_entity_lookup_cache_miss(self, mock_dynamo):
        mock_dynamo.return_value = ''

        result = entity_lookup(self.good_event, None)

        expected_result = {'statusCode': 404,
                           'body': '{"status": "failed", '
                                   '"message": "Could not successfully lookup entity for keyword [test]"}'}
        self.assertEqual(expected_result, result)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_manual_override(self, mock_dynamo):
        manual_override = {"confidence": "1.0", "perm_id": 1234}
        mock_dynamo.return_value = {"manual_override": manual_override}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': manual_override}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'manual_override')
        self.assertEqual(expected_result['body']['resolution_algorithm'], result_json['resolution_algorithm'])

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_manual_override_null_permid(self, mock_dynamo):
        manual_override = {"confidence": "1.0", "perm_id": None}
        mock_dynamo.return_value = {"manual_override": manual_override}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 404}

        self.assertEqual(expected_result['statusCode'], result['statusCode'])

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_manual_override_prevent_resolution(self, mock_dynamo):
        confidence = str(MIN_CONFIDENCE + 0.1)
        manual_override = {"prevent_resolution": True}
        entity_match = {"confidence": confidence, "perm_id": 1234}
        mock_dynamo.return_value = {"manual_override": manual_override, "entity_match": entity_match}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 404}

        self.assertEqual(expected_result['statusCode'], result['statusCode'])

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_manual_override_low_confidence(self, mock_dynamo):
        confidence = str(MIN_CONFIDENCE - 0.1)
        manual_override = {"confidence": confidence}
        mock_dynamo.return_value = {"manual_override": manual_override}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 404, 'body':
            {'status': 'failed', 'message': 'Could not successfully smart-lookup entity for keyword [test]'}}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_entity_match(self, mock_dynamo):
        entity_match = {"confidence": "0.9", "perm_id": 1234}
        mock_dynamo.return_value = {"entity_match": entity_match}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': entity_match}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'entity_match')
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_entity_match_low_confidence(self, mock_dynamo):
        entity_match = {"confidence": "0.6"}
        mock_dynamo.return_value = {"entity_match": entity_match}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 404, 'body':
                {'status': 'failed', 'message': 'Could not successfully smart-lookup entity for keyword [test]'}}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_open_calais(self, mock_dynamo):
        open_calais = [{"confidence": "0.9", "is_company_score": "0.6", "perm_id": 1234}]
        mock_dynamo.return_value = {"open_calais": open_calais}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': open_calais[0]}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'open_calais')
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_open_calais_low_confidence(self, mock_dynamo):
        open_calais = [{"confidence": "0.6", "is_company_score": "0.6"}]
        mock_dynamo.return_value = {"open_calais": open_calais}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 404, 'body':
                {'status': 'failed', 'message': 'Could not successfully smart-lookup entity for keyword [test]'}}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_hit_precedence_check(self, mock_dynamo):
        open_calais = [{"confidence": "0.9", "is_company_score": "0.9", "perm_id": 1234}]
        manual_override = {"confidence": "0.9", "perm_id": 1234}
        entity_match = {"confidence": "0.9", "perm_id": 1234}
        mock_dynamo.return_value = {"open_calais": open_calais,
                                    "manual_override": manual_override,
                                    "entity_match": entity_match}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': manual_override}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'manual_override')
        self.assertEqual(expected_result['body'], result_json)

        mock_dynamo.return_value = {"open_calais": open_calais,
                                    "entity_match": entity_match}

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 200, 'body': entity_match}
        result_json = json.loads(result['body'])

        self.assertEqual(expected_result['statusCode'], result['statusCode'])
        self.assertEqual(result_json['resolution_algorithm'], 'entity_match')
        self.assertEqual(expected_result['body'], result_json)

    @patch('src.resolution.smart_entity_handler.dynamo_lookup_entity')
    def test_smart_entity_lookup_cache_miss(self, mock_dynamo):
        mock_dynamo.return_value = ''

        result = entity_lookup_smart(self.good_event, None)

        expected_result = {'statusCode': 404,
                           'body': '{"status": "failed", '
                                   '"message": "Could not successfully smart-lookup entity for keyword [test]"}'}
        self.assertEqual(expected_result, result)