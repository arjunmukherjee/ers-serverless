import os

from unittest import TestCase
from unittest.mock import patch
from src.tr.open_calais import issue_open_calais_request
from src.tr.open_calais import default_not_found_result
from src.tr.open_calais import ResolutionAlgo
from src.helpers.keyword_helper import get_correct_keyword

found_keyword = 'Microsoft'
not_found_keyword = 'RandomCompany'
unsupported_language_keyword = 'UnsupportedLanguage'
api_error_keyword = 'ApiError'


tr_url = 'https://tr-dummy.com'
tr_env = {'TR_URL': tr_url}

tr_api_key = "'some-key'"
tr_api_key_env = {'TR_API_KEY': tr_api_key}


def mocked_requests(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    url = kwargs['url']
    data = str(kwargs['data'])
    if url == f'{tr_url}/calais':
        print(data)
        if get_correct_keyword(found_keyword) in data:
            return MockResponse(200,
                                '{"http://d.opencalais.com/comphash-1/520f1c53": {"_type": "Company",'
                                '"confidence": {"aggregate": "1.0", "resolution": "1.0"},'
                                '"resolutions": [{"name": "MICROSOFT CORPORATION",'
                                '"permid": "4295907168", "score": 0.9946112}],'
                                '"instances": [{"exact": "Microsoft"}]}}')
        elif get_correct_keyword(not_found_keyword) in data:
            return MockResponse(200, '{}')
        elif get_correct_keyword(unsupported_language_keyword) in data:
            return MockResponse(400, '{which is not currently supported}')
        elif get_correct_keyword(api_error_keyword) in data:
            return MockResponse(429, '{}')

    return MockResponse(None, 404)


class TestIssue_open_calais_request(TestCase):

    @patch.dict(os.environ, tr_env)
    @patch.dict(os.environ, tr_api_key_env)
    @patch('requests.post', side_effect=mocked_requests)
    def test_open_calais_when_found(self, mock_post):
        response = issue_open_calais_request(keyword_arg=found_keyword)

        self.assertEqual(len(response), 1)

        result = response[0]
        self.assertEqual(result['perm_id'], 4295907168)
        self.assertEqual(result['confidence'], '1.0')
        self.assertEqual(result['org_name'], 'MICROSOFT CORPORATION')
        pass


    @patch.dict(os.environ, tr_env)
    @patch.dict(os.environ, tr_api_key_env)
    @patch('requests.post', side_effect=mocked_requests)
    def test_open_calais_when_not_found(self, mock_post):
        response = issue_open_calais_request(keyword_arg=not_found_keyword)
        expected_result = default_not_found_result(resolution_algorithm=ResolutionAlgo.OPEN_CALAIS,
                                                   keyword=get_correct_keyword(not_found_keyword))

        self.assertEqual(response, expected_result)
        pass

    @patch.dict(os.environ, tr_env)
    @patch.dict(os.environ, tr_api_key_env)
    @patch('requests.post', side_effect=mocked_requests)
    def test_open_calais_when_unsupported_language(self, mock_post):
        response = issue_open_calais_request(keyword_arg=unsupported_language_keyword)
        expected_result = default_not_found_result(resolution_algorithm=ResolutionAlgo.OPEN_CALAIS,
                                                   keyword=get_correct_keyword(unsupported_language_keyword))

        self.assertEqual(response, expected_result)
        pass

    @patch.dict(os.environ, tr_env)
    @patch.dict(os.environ, tr_api_key_env)
    @patch('requests.post', side_effect=mocked_requests)
    def test_open_calais_when_api_error(self, mock_post):
        response = issue_open_calais_request(keyword_arg=api_error_keyword)

        self.assertEqual(response, None)
        pass

