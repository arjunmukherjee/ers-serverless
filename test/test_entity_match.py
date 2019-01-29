import os

from unittest import TestCase
from unittest.mock import patch
from src.tr.entity_match import issue_entity_match_request
from src.tr.open_calais import default_not_found_result
from src.tr.open_calais import ResolutionAlgo
from src.helpers.keyword_helper import get_correct_keyword

found_keyword = 'Apple'
found_perm_id = 4295905573
found_perm_id_url = f'https://permid.org/1-{found_perm_id}'
found_org_name = 'Apple Inc'
found_match_level = 'Excellent'
found_match_score = '100%'
found_match_confidence = '1.0'

not_found_keyword = 'RandomCompany'
not_found_match_level = 'No Match'

api_error_keyword = 'ApiErrorCompany'

tr_url = 'https://tr-dummy.com'
tr_env = {'TR_URL': tr_url}

tr_api_key = "'some-key'"
tr_api_key_env = {'TR_API_KEY': tr_api_key}


def mocked_requests(**kwargs):
    class MockResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    url = kwargs['url']
    data = str(kwargs['data'])
    if url == f'{tr_url}/match':
        if get_correct_keyword(found_keyword) in data:
            return MockResponse(200,
                                '{"outputContentResponse": [{"Match OpenPermID":"' + found_perm_id_url + '", '
                                '"Match OrgName": "' + found_org_name + '","Match Score": "' + found_match_score + '",'
                                '"Match Level": "' + found_match_level + '", "Input_Name": "' + get_correct_keyword(found_keyword) + '"}]}')
        elif get_correct_keyword(not_found_keyword) in data:
            return MockResponse(200,
                                '{"outputContentResponse": [{"Match Level": "' + not_found_match_level +
                                '", "Input_Name": "' + get_correct_keyword(not_found_keyword) + '"}]}')
        elif get_correct_keyword(api_error_keyword) in data:
            return MockResponse(429, '{}')

    return MockResponse(None, 404)


class TestIssue_entity_match_request(TestCase):

    @patch.dict(os.environ, tr_env)
    @patch.dict(os.environ, tr_api_key_env)
    @patch('requests.post', side_effect=mocked_requests)
    def test_entity_match_when_found(self, mock_post):
        result = issue_entity_match_request(found_keyword)

        self.assertEqual(result['confidence'], found_match_confidence)
        self.assertEqual(result['perm_id'], found_perm_id)
        self.assertEqual(result['org_name'], found_org_name)
        self.assertEqual(result['keyword'], found_keyword)
        pass

    @patch.dict(os.environ, tr_env)
    @patch.dict(os.environ, tr_api_key_env)
    @patch('requests.post', side_effect=mocked_requests)
    def test_entity_match_when_not_found(self, mock_post):
        result = issue_entity_match_request(not_found_keyword)

        expected_result = default_not_found_result(resolution_algorithm=ResolutionAlgo.ENTITY_MATCH.value,
                                                   keyword=get_correct_keyword(not_found_keyword))
        self.assertEqual(result, expected_result)
        pass

    @patch.dict(os.environ, tr_env)
    @patch.dict(os.environ, tr_api_key_env)
    @patch('requests.post', side_effect=mocked_requests)
    def test_entity_match_when_api_error(self, mock_post):
        result = issue_entity_match_request(api_error_keyword)

        self.assertEqual(result, None)
        pass

