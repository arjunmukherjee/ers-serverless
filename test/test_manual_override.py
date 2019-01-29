import requests

from unittest import TestCase
from unittest.mock import patch
from src.resolution.manual_override import add_override


class TestAdd_override(TestCase):
    keyword = 'test'
    keyword_titled = 'Test'

    @patch('src.resolution.manual_override.dynamo_lookup_entity')
    @patch('src.resolution.manual_override.dynamo_save_override_entity')
    def test_successful_manual_override_previously_not_present(self, mock_dynamo_save, mock_dynamo_lookup):
        good_override_event = {"body": '{"keyword": "test", "manual_override": {"key": "value"}}'}
        mock_dynamo_save.return_value = ''
        mock_dynamo_lookup.return_value = ''

        expected_result = {'statusCode': 200, 'body': f'"Successfully added manual override for {self.keyword}"'}

        result = add_override(good_override_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.manual_override.dynamo_lookup_entity')
    @patch('src.resolution.manual_override.dynamo_save_override_entity')
    def test_successful_manual_override_previously_present(self, mock_dynamo_save, mock_dynamo_lookup):
        good_override_event = {"body": '{"keyword": "test", "manual_override": {"key": "value"}}'}
        mock_dynamo_save.return_value = ''
        mock_dynamo_lookup.return_value = {"keyword": "test"}

        expected_result = {'statusCode': 200, 'body': f'"Successfully added manual override for {self.keyword}"'}

        result = add_override(good_override_event, None)

        self.assertEqual(expected_result, result)

    @patch('src.resolution.manual_override.error_response')
    def test_unsuccessful_manual_override_incorrect_body(self, mock_error_response):
        bad_event_without_body = {"bodyzz": '{"keyword": "test"}'}
        mock_error_response.return_value = {"statusCode": requests.codes.internal_server_error}
        result = add_override(bad_event_without_body, None)

        self.assertEqual(result['statusCode'], requests.codes.internal_server_error)

    @patch('src.resolution.manual_override.error_response')
    def test_unsuccessful_manual_override_incorrect_keyword(self, mock_error_response):
        bad_event_without_keyword = {"body": '{"keywordzz": "test"}'}
        mock_error_response.return_value = {"statusCode": requests.codes.internal_server_error}
        result = add_override(bad_event_without_keyword, None)

        self.assertEqual(result['statusCode'], requests.codes.internal_server_error)

    @patch('src.resolution.manual_override.error_response')
    def test_unsuccessful_manual_override_incorrect_literal_for_override(self, mock_error_response):
        bad_event_incorrect_literal = {"body": '{"keyword": "test", "manual_overridezz": "some override"}'}
        mock_error_response.return_value = {"statusCode": requests.codes.internal_server_error}
        result = add_override(bad_event_incorrect_literal, None)

        self.assertEqual(result['statusCode'], requests.codes.internal_server_error)
