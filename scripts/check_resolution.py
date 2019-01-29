import requests
import urllib
import os
import logging

from src.tr.open_calais import issue_open_calais_request
from src.tr.entity_match import issue_entity_match_request

logging.getLogger().setLevel(logging.ERROR)

###### KEYWORD #########
keyword_arg = "Panasonic"
force_resolve = True
quoted_keyword = urllib.parse.quote(keyword_arg, safe='')
########################

base_url = 'https://entityresolution-prod.defaulttest.com/api/v1'
lookup_ers_url = f'{base_url}/lookup/keyword'
smart_ers_url = f'{base_url}/smartresolve/keyword'
force_ers_url = f'{base_url}/resolve/force/keyword'

tr_url = 'https://api.thomsonreuters.com/permid'
tr_api_key = "'hWRwzOxar9YGo0A0BnhqKvxF5s5CpwNS', 'hWRwzOxar9YGo0A0BnhqKvxF5s5CpwNS'"

os.environ['TR_URL'] = tr_url
os.environ['TR_API_KEY'] = tr_api_key

# Lookup
result = requests.get(url=f'{lookup_ers_url}/{quoted_keyword}')
print(f'LOOKUP: {result.status_code}, {result.text}\n')

# Force Resolve
if force_resolve:
    result = requests.post(url=f'{smart_ers_url}/{quoted_keyword}/0')
    if result.status_code is not requests.codes.ok:
        result = requests.post(url=f'{force_ers_url}/{quoted_keyword}')
        print(f'FORCE-RESOLVE: {result.status_code}, {result.text}\n')

# Smart Resolve
result = requests.post(url=f'{smart_ers_url}/{quoted_keyword}/0')
print(f'SMART-RESOLVE: {result.status_code}, {result.text}\n')

# Entity Match
result = issue_entity_match_request(keyword_arg=keyword_arg)
print(f'ENTITY-MATCH: {result}')

# Open Calais
result = issue_open_calais_request(keyword_arg=keyword_arg, max_retry=10)
print(f'OPEN-CALAIS: {result}')
