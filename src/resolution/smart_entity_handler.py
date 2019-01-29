import logging
import copy
import requests

from src.tr.entity import ResolutionAlgo
from src.helpers.keyword_helper import extract_keyword
from src.dynamo.dynamo_handler import dynamo_lookup_entity
from src.tr.thompson_reuters_helper import search_tr
from src.dynamo.dynamo_handler import persist_unresolved_entity
from src.helpers.event_response import construct_response
from src.helpers.event_response import failure_response
from src.helpers.event_response import error_response

log = logging.getLogger()
log.setLevel(logging.INFO)


MIN_CONFIDENCE = 0.7
MIN_IS_COMPANY_SCORE = 0.3
RESOLUTION_ALGO_BY_PRECEDENCE = [ResolutionAlgo.MANUAL_OVERRIDE,
                                 ResolutionAlgo.ENTITY_MATCH,
                                 ResolutionAlgo.OPEN_CALAIS]


def entity_resolution_smart(event, context):
    try:
        keyword = extract_keyword(event)
        min_confidence = __min_confidence(event)
        log.info(f'Received resolution query for {keyword}')

        result = dynamo_lookup_entity(keyword)
        if not result:
            result = search_tr(keyword=keyword)
            if not result:
                persist_unresolved_entity(keyword=keyword)
                return construct_response(requests.codes.not_found, failure_response('smart-resolve', keyword))
            else:
                result = __get_result_by_algo_precedence(result, min_confidence)
                if not result:
                    return construct_response(requests.codes.not_found, failure_response('smart-resolve', keyword))
        else:
            result = __get_result_by_algo_precedence(result, min_confidence)
            if not result:
                return construct_response(requests.codes.not_found, failure_response('smart-resolution', keyword))

        return construct_response(requests.codes.ok, result)
    except:
        message = 'ENTITY-RESOLUTION-SMART: Error while processing request, dropping into SNS for some hand holding'
        return error_response(event, message, log)


def entity_lookup_smart(event, context):
    try:
        keyword = extract_keyword(event)
        min_confidence = __min_confidence(event)
        log.info(f'Received smart lookup query for {keyword}')

        result = dynamo_lookup_entity(keyword)
        if not result:
            return construct_response(requests.codes.not_found, failure_response('smart-lookup', keyword))
        else:
            result = __get_result_by_algo_precedence(result, min_confidence=min_confidence)
            if not result:
                return construct_response(requests.codes.not_found, failure_response('smart-lookup', keyword))

        return construct_response(requests.codes.ok, result)
    except:
        message = 'ENTITY-LOOKUP-SMART: Error while processing request, dropping into SNS for some hand holding'
        return error_response(event, message, log)


def __get_result_by_algo_precedence(result, min_confidence=MIN_CONFIDENCE):
    for algo in RESOLUTION_ALGO_BY_PRECEDENCE:
        try:
            result_by_algo = result[algo.value]
            results_list = []
            if result_by_algo is not None:
                if algo is ResolutionAlgo.OPEN_CALAIS:
                    results_list = result_by_algo
                else:
                    if algo is ResolutionAlgo.MANUAL_OVERRIDE:
                        try:
                            prevent_resolution = result_by_algo['prevent_resolution']
                            if prevent_resolution:
                                log.info(f'Forcing a resolution prevention')
                                return None
                        except KeyError:
                            pass
                    results_list.append(result_by_algo)

                extraction_result = __apply_filters_and_extract_result(results_list, algo, min_confidence)
                if extraction_result is not None:
                    return extraction_result
        except KeyError:
            pass


def __apply_filters_and_extract_result(results_list, algo, min_confidence):
    max_confidence = 0.0
    result_to_return = None

    for result_by_algo in results_list:
        try:
            confidence = result_by_algo['confidence']
            perm_id = int(result_by_algo['perm_id'])
            if confidence is not None:
                confidence = float(confidence) if __is_number(confidence) else 0
                log.info(f'Confidence for {algo.value} is {confidence}')

                if algo is not ResolutionAlgo.OPEN_CALAIS:
                    if confidence >= min_confidence and perm_id != 0:
                        result_by_algo['resolution_algorithm'] = algo.value
                        return result_by_algo
                else:
                    try:
                        is_company_score = result_by_algo['is_company_score']
                    except KeyError:
                        is_company_score = 1

                    is_company_score = float(is_company_score) if __is_number(is_company_score) else 1
                    if (is_company_score > MIN_IS_COMPANY_SCORE) and (
                            confidence >= min_confidence and confidence >= max_confidence):
                        max_confidence = confidence
                        result_by_algo['resolution_algorithm'] = algo.value
                        result_to_return = copy.deepcopy(result_by_algo)

        except KeyError:
            pass
        except TypeError:
            pass

    return result_to_return


def __min_confidence(event):
    min_confidence = event['pathParameters'].get('minconfidence')
    if min_confidence is None:
        min_confidence = MIN_CONFIDENCE

    log.info(f'Using a Min confidence level of {min_confidence}')

    return float(min_confidence)


def __is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        pass

    return False
