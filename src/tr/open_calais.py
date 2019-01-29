import time
import requests
import logging
import json
import traceback

from src.helpers.environment_helper import get_tr_api_key
from src.helpers.environment_helper import get_tr_url
from src.tr.entity import Entity
from src.tr.entity import default_not_found_result
from src.tr.entity import ResolutionAlgo
from src.helpers.keyword_helper import get_correct_keyword

log = logging.getLogger()
log.setLevel(logging.INFO)


def issue_open_calais_request(keyword_arg, max_retry=3, do_smart_phrasing=True):
    keyword = get_correct_keyword(keyword=keyword_arg)
    log.info(f'Issuing request to TR (Open Calais) for {keyword}')
    smart_keyword = smart_phrasing(keyword=keyword, do_smart_phrasing=do_smart_phrasing)

    try:
        url = f'{get_tr_url()}/calais'

        retry_count = 0
        result = requests.post(url=url, headers=__get_headers(), data=smart_keyword.encode('utf-8'))
        while result.status_code != requests.codes.ok:
            log.error(f'{result.status_code}, {result.text}')
            retry_count += 1
            if retry_count > max_retry:
                log.error(f'Max Retry(s) reached for {smart_keyword}, unable to resolve via Open Calais- OC issue!')
                return None
            elif 'which is not currently supported' in result.text or 'Unrecognized-Language' in result.text:
                log.error(f'Unsupported language for {keyword}, unable to resolve via Open Calais- OC Language !')
                return default_not_found_result(resolution_algorithm=ResolutionAlgo.OPEN_CALAIS, keyword=keyword)
            else:
                log.info(f'Retry {retry_count}/{max_retry}...')
                time.sleep(1)
                result = requests.post(url, headers=__get_headers(), data=smart_keyword.encode('utf-8'))

        result = json.loads(result.text)
        companies = [v for v in result.values() if v.get('_type') == 'Company' and v.get('resolutions') is not None]
        vals = [_get_val(keyword, r) for r in companies for i in r['instances']]

        log.info(f'Got a result from Open Calais {vals}')
        if vals is None or len(vals) <= 0:
            log.error(f'No result in Open Calais for {smart_keyword}- No confident match')
            return default_not_found_result(resolution_algorithm=ResolutionAlgo.OPEN_CALAIS, keyword=keyword)

        return vals
    except:
        log.error(traceback.format_exc())
        log.error(f'OPEN-CALAIS: Unable to successfully issue request to OC for entity resolution for {smart_keyword}')
        return None


def smart_phrasing(keyword, do_smart_phrasing):
    if do_smart_phrasing:
        return f'{keyword} is a company'
    else:
        return keyword


def __get_headers():
    return {
        'Content-Type': 'text/raw',
        'Accept': 'application/json',
        'outputFormat': 'application/json',
        'x-ag-access-token': f'{get_tr_api_key()}'
    }


def _get_val(keyword, result):
    perm_id = int(result['resolutions'][0]['permid'])
    entity = Entity(keyword=keyword,
                    org_name=str(result['resolutions'][0]['name']),
                    confidence=str(result.get('confidence').get('resolution')),
                    perm_id=perm_id,
                    is_company_score=str(result.get('confidence').get('aggregate')))

    return entity.__dict__
