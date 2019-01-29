import os

from unittest import TestCase
from src.mds.mds_helper import get_mds_org
from unittest.mock import patch

mds_url = 'https://marketdata-dummy.com'
mds_env = {'MARKET_DATA_SERVICE_URL': mds_url}

# Found case
found_perm_id = 4296977663
found_org_id = 1335346
found_org_name = 'Found Org Corp'
found_organization_response = '{"id": ' + str(found_org_id) + \
                              ', "permId": ' + str(found_perm_id) + \
                              ',"name": "' + found_org_name + '"}'

# Not found org case
not_found_perm_id = 9999


def mocked_requests_get(**kwargs):
    class MockResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    url = kwargs['url']
    if url == f'{mds_url}/organization?querytype=permid&permid={found_perm_id}':
        return MockResponse(200, found_organization_response)
    elif url == f'{mds_url}/organization?querytype=permid&permid={not_found_perm_id}':
        return MockResponse(404, None)

    return MockResponse(None, 404)


class TestGet_ultimate_parent(TestCase):

    @patch.dict(os.environ, mds_env)
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_organization_found(self, mock_get):
        result = get_mds_org(perm_id=found_perm_id)

        self.assertEqual(result['id'], found_org_id)
        self.assertEqual(result['name'], found_org_name)
        self.assertEqual(result['perm_id'], found_perm_id)
        pass

    @patch.dict(os.environ, mds_env)
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_organization_not_found(self, mock_get):
        result = get_mds_org(perm_id=not_found_perm_id)

        self.assertEqual(result, None)
        pass
