from unittest.mock import patch
from unittest import TestCase
from src.tr.thompson_reuters_helper import search_tr


class TestSearch_tr(TestCase):

    @patch('src.tr.thompson_reuters_helper.dynamo_save_entity')
    @patch('src.tr.thompson_reuters_helper.issue_open_calais_request')
    @patch('src.tr.thompson_reuters_helper.issue_entity_match_request')
    def test_search_tr_no_results_from_services(self, mock_entity_search, mock_open_calais, mock_save_dynamo):
        mock_entity_search.return_value = ''
        mock_open_calais.return_value = ''
        result = search_tr('good_keyword')
        self.assertEqual(result, None)
        pass

    @patch('src.tr.thompson_reuters_helper.dynamo_lookup_entity')
    @patch('src.tr.thompson_reuters_helper.dynamo_save_entity')
    @patch('src.tr.thompson_reuters_helper.get_timestamp')
    @patch('src.tr.thompson_reuters_helper.issue_open_calais_request')
    @patch('src.tr.thompson_reuters_helper.issue_entity_match_request')
    def test_search_tr_all_pass(self, mock_entity_search, mock_open_calais, mock_clock, mock_save_dynamo,
                                mock_lookup_dynamo):
        mock_lookup_dynamo.return_value = ''
        mock_entity_search.return_value = 'some em result'
        mock_open_calais.return_value = 'some oc result'
        mock_clock.return_value = '2018-09-25 12:37:03.883790'

        result = search_tr('good_keyword')

        expected_result = {'keyword': 'good_keyword',
                           'entity_match': 'some em result',
                           'open_calais': 'some oc result',
                           'manual_override': None,
                           'update_timestamp': '2018-09-25 12:37:03.883790'
                           }

        self.assertEqual(result, expected_result)
        pass

    @patch('src.tr.thompson_reuters_helper.dynamo_lookup_entity')
    @patch('src.tr.thompson_reuters_helper.dynamo_save_entity')
    @patch('src.tr.thompson_reuters_helper.get_timestamp')
    @patch('src.tr.thompson_reuters_helper.issue_open_calais_request')
    @patch('src.tr.thompson_reuters_helper.issue_entity_match_request')
    def test_search_tr_all_pass_found_previous_manual_override(self, mock_entity_search, mock_open_calais, mock_clock,
                                                               mock_save_dynamo,
                                                               mock_lookup_dynamo):
        mock_lookup_dynamo.return_value = {"manual_override": "some previous override"}
        mock_entity_search.return_value = 'some em result'
        mock_open_calais.return_value = 'some oc result'
        mock_clock.return_value = '2018-09-25 12:37:03.883790'

        result = search_tr('good_keyword')

        expected_result = {'keyword': 'good_keyword',
                           'entity_match': 'some em result',
                           'open_calais': 'some oc result',
                           'manual_override': 'some previous override',
                           'update_timestamp': '2018-09-25 12:37:03.883790'
                           }

        self.assertEqual(result, expected_result)
        pass

    @patch('src.tr.thompson_reuters_helper.dynamo_lookup_entity')
    @patch('src.tr.thompson_reuters_helper.dynamo_save_entity')
    @patch('src.tr.thompson_reuters_helper.get_timestamp')
    @patch('src.tr.thompson_reuters_helper.issue_open_calais_request')
    @patch('src.tr.thompson_reuters_helper.issue_entity_match_request')
    def test_search_tr_no_result_from_entity_match(self, mock_entity_search, mock_open_calais, mock_clock,
                                                   mock_save_dynamo, mock_lookup_dynamo):
        mock_entity_search.return_value = ''
        mock_open_calais.return_value = 'some oc result'
        mock_clock.return_value = '2018-09-25 12:37:03.883790'
        mock_lookup_dynamo.return_value = ''

        result = search_tr('good_keyword')

        expected_result = {'keyword': 'good_keyword',
                           'entity_match': '',
                           'open_calais': 'some oc result',
                           'manual_override': None,
                           'update_timestamp': '2018-09-25 12:37:03.883790'
                           }

        self.assertEqual(result, expected_result)
        pass

    @patch('src.tr.thompson_reuters_helper.dynamo_lookup_entity')
    @patch('src.tr.thompson_reuters_helper.dynamo_save_entity')
    @patch('src.tr.thompson_reuters_helper.get_timestamp')
    @patch('src.tr.thompson_reuters_helper.issue_open_calais_request')
    @patch('src.tr.thompson_reuters_helper.issue_entity_match_request')
    def test_search_tr_no_result_from_open_calais(self, mock_entity_search, mock_open_calais,
                                                  mock_clock, mock_save_dynamo, mock_lookup_dynamo):
        mock_entity_search.return_value = 'some em result'
        mock_open_calais.return_value = ''
        mock_clock.return_value = '2018-09-25 12:37:03.883790'
        mock_lookup_dynamo.return_value = ''

        result = search_tr('good_keyword')

        expected_result = {'keyword': 'good_keyword',
                           'entity_match': 'some em result',
                           'open_calais': '',
                           'manual_override': None,
                           'update_timestamp': '2018-09-25 12:37:03.883790'}

        self.assertEqual(result, expected_result)
        pass
