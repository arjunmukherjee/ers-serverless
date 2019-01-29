import requests
import logging
import json
import re
import time

from src.helpers.environment_helper import get_tr_api_key
from src.helpers.environment_helper import get_tr_url
from src.tr.entity import Entity
from src.tr.entity import default_not_found_result
from src.tr.entity import ResolutionAlgo
from src.helpers.keyword_helper import get_correct_keyword

log = logging.getLogger()
log.setLevel(logging.INFO)
NOT_FOUND_MATCH_LEVEL = 'No Match'


def issue_entity_match_request(keyword_arg, max_retry=5):
    keyword = get_correct_keyword(keyword=keyword_arg)
    log.info(f'Issuing request to TR for {keyword}')

    url = f'{get_tr_url()}/match'
    data = f"LocalID,Name\n1,{keyword}"

    retry_count = 0
    result = requests.post(url=url, headers=__get_headers(), data=data.encode('utf-8'))
    while result.status_code == requests.codes.too_many_requests:
        log.error(f'{result.status_code}, {result.text}')

        retry_count += 1
        if retry_count > max_retry:
            log.error(f'Max Retry(s) reached for {keyword}, unable to resolve via Entity Match- EM issue!')
            return None
        else:
            log.info(f'Retry {retry_count}/{max_retry}...')
            time.sleep(1)
            result = requests.post(url=url, headers=__get_headers(), data=data)

    log.info(f'Got a result for {data} from Entity Match Code : {result.status_code}, Result : {result.text}')
    if result.status_code != requests.codes.ok:
        log.error(f'{result.status_code}, {result.text}')
        return None

    json_result = json.loads(result.text)
    relevant_result = get_val(keyword, json_result['outputContentResponse'][0])

    return relevant_result


def __get_headers():
    return {
        'Content-type': 'text/plain',
        'Accept': 'application/json',
        'x-ag-access-token': f'{get_tr_api_key()}',
        'x-openmatch-numberOfMatchesPerRecord': '1',
        'x-openmatch-dataType': 'Organization'
    }


def get_val(keyword, relevant_operator):
    if relevant_operator['Match Level'] == NOT_FOUND_MATCH_LEVEL:
        return default_not_found_result(resolution_algorithm=ResolutionAlgo.ENTITY_MATCH, keyword=keyword)
    else:
        perm_id_url = relevant_operator['Match OpenPermID']

        if perm_id_url is not None:
            pattern = 'https://permid\\.org/1\\-([0-9]+)'
            match = re.match(pattern=pattern, string=perm_id_url)
            if match:
                perm_id = int(match.group(1))
                confidence = str(float(int(relevant_operator['Match Score'].replace('%', '')) / 100))
                entity = Entity(keyword=keyword,
                                org_name=_get_org_name(relevant_operator),
                                confidence=confidence,
                                perm_id=perm_id)
                return entity.__dict__
            else:
                log.error('Unable to find a correct PermId from Entity Match')
    return None


def _get_org_name(relevant_operator):
    try:
        return relevant_operator['Match OrgName']
    except KeyError:
        return 'Unknown'
