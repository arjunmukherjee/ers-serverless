import requests
import logging
import json

from src.helpers.environment_helper import get_mds_url

log = logging.getLogger()
log.setLevel(logging.INFO)


def get_mds_org(perm_id, mds_base_url=None):
    organization = None

    if mds_base_url is None:
        mds_base_url = get_mds_url()

    mds_url = mds_base_url + f'/organization?querytype=permid&permid={perm_id}'
    result = requests.get(url=mds_url)
    log.info(f'Result from MDS {mds_url} is {result.status_code} {result.text}')

    if result.status_code is requests.codes.ok:
        organization = json.loads(result.text)
        organization['perm_id'] = organization['permId']
        del organization['permId']
    else:
        log.error(f'Unable to get a successful response for organization lookup from MDS for the permID {perm_id}')

    return organization
