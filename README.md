# Entity Resolution Service 
The Entity Resolution Service (ERS) is responsible for resolving arbitrary string queries to a best-match parent company 
that is at the root of its organization tree. It uses a combination of the "entity match" service from Thomson Reuters 
(TR) as well as the "Open Calais" service also from TR, to find "permIDs". 

Using the [Serverless Framework](https://serverless.com/)

## Install
- Ensure you have [AWS credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) 
for the account you are trying to deploy to pre-set in your environment
- `brew install npm`
- [Install docker ](https://docs.docker.com/install/)
- `npm install serverless -g`
- `npm install --save serverless-python-requirements`
- `npm install serverless-domain-manager --save-dev`
- `pip3 install -r requirements.txt`

## Commands
- `sls` is the same as `serverless`
- DEPLOY SINGLE FUNCTION ONLY: `sls deploy --region us-east-1 -f hello --verbose --env <environment>`
- LOGS: `serverless logs -f resolveEntity -t --env <environment>`
- LOCAL INVOKE: `sls invoke -f resolveEntity -l`
- INFO: `sls info --env <environment>`

## Deploy
- `sls create_domain --env <environment> --region <regionName>` [**Note : You only need to do this once.** 
This could take ~40 mins to propagate across the DNS hierarchy]
- `sls deploy --env <environment> --region <regionName> --verbose`

## Remove
- `sls delete_domain --env <environment> --region <regionName>`
- `sls remove --env <environment> --region <regionName>`

## Command line options
- `env` to deploy lambda functions (and api gateway endpoints) differentiated by the env value 
- `account` to deploy the stack to a specific aws account
- `region` to deploy the stack to a specific aws region (default = `us-west-2`)
- `domain` which domain to use for the deployment
- `tr-api-key` The ThompsonReuters api key to use (default = `<PersonalKey>`)
- `tr-url` The ThompsonReuters api url to use (default = `https://api.thomsonreuters.com/permid`)

## Testing
- `python3 -m unittest -h` (see help)
- `python3 -m unittest -v` (run all tests)
- `python3 -m unittest test/test_dynamo.py` (to test a specific file/module/test)

## TODO
- Setup an end to end integration test
- Retrieve results by time i.e. `as of`
- Validate json body
- Test dropping error events into SNS
- Write tests for the helper utilities
- Authenticate requests (by api keys)
- Figure out how `score`, `confidence`, `match level` are calculated and then use the correct field
- Validate the `--env` argument
- The dynamo tables have been set to autoscale. However, this has been done via the console, need to move to yaml within
this repo
- Refactor `entity_handler.py` and `smart_entity_handler.py` (to many if/else conditions and repeated code, making it difficult to read)
- Setup a deployment pipeline (CI/CD)
- Added some code for spell checking (levenshtein) and phonetic similarity (nyiis), but not being used in core modules 
(in the short term the best use case is probably one off [scripts](scripts/spell_check_resolution.py) that attempt to resolve previously unresolved entities) 

## Considerations
- AWS `Concurrent Requests` limit (the total number of concurrent lambdas executing at the same time)
    - `Concurrent Requests (Expected Duration * Expected Requests per Second)`
- DynamoDB provisioned throughput: manually set to autoscale, but unsure as to how long the increased scale takes to come into effect
- TR API limits: there are daily concurrent limits as well as daily quotas per key (attempt to batch requests, [scripts](scripts) have been written to do this)
- If you notice a spike in latency due to [cold start times](https://hackernoon.com/cold-starts-in-aws-lambda-f9e3432adbf0), you might consider keeping some/all functions warm. Check this [`README`](src/README.md) 

## Obtaining a TR Api Key
- Click on `Register` (top right) on `https://permid.org/`
- Use your email address, enter in all the other relevant details and submit
- Check your inbox a few minutes later for the verification email, click on the link to verify the email address
- Go back to `https://permid.org/`, `Login` (top right), from the dropdown that says `WELCOME BACK, <USER>@DOMAIN.COM`
    - Select `Display my API token`

## Error Handling
All errors will be printed to the logs/console and the corresponding event will be sent to an SNS topic, requiring explicit handling.

## Environments
| Environment   |   base url                                     |
|:--------------|:-----------------------------------------------|
| dev           |  not deployed                                  |
| staging       |  not deployed                                  |

## API Documentation
#### V1 `/api/v1`
| resource                                                      |   type    |   description                 |
|:--------------                                                |:----------|----------------------------  |
| [/resolve/keyword/{keyword}](#resolve)                        | POST      |   attempts to resolve {keyword} first from the cache, if miss, then from TR 
| [/smartresolve/keyword/{keyword}/{confidence}](#smartresolve) | POST      |   attempts to resolve {keyword} first from the cache, if miss, then from TR (sends back a result from a single methodology by precedence (manual override > entity match > open calais), and only if the confidence level is > {confidence})
| [/resolve/force/keyword/{keyword}](#force)                    | POST      |   attempts to resolve {keyword} from TR, if successful, updates the cache
| [/override](#override)                                        | POST      |   attempts to add a manual override as specified by the data on the post request
| [/lookup/keyword/{keyword}](#lookup)                          | GET       |   attempts to lookup {keyword} from the cache only
| [/smartlookup/keyword/{keyword}/{confidence}](#smartlookup)   | GET       |   attempts to lookup {keyword} from the cache only, sends back a result from a single methodology by precedence (manual override > entity match > open calais), and only if the confidence level is > {confidence} 

## Examples
- `confidence` = a decimal number between 0 and 1 e.g. `0.4`
- `keyword` = Url encoded string representation of the entity you wish to attempt to resolve e.g. `keyword = urllib.parse.quote(keyword_arg, safe='')`

___

<a name="resolve"/>
### Lookup or Resolve
- **REQUEST**: `curl -XPOST https://entityresolution-<ENV>.<domain>.com/api/v1/resolve/keyword/somebadcompany`
- **RESPONSE**: 
    - _SUCCESS_: `Same response as Force Resolution (below)`, Status code: `200`
    - _FAILURE_: `{"status": "failed", "message": "Could not successfully resolve entity for keyword Somebadcompany"}`, Status code: `404`

___

<a name="smartresolve"/>
### Smart Lookup or Resolve
- **REQUEST**: `curl -XPOST https://entityresolution-<ENV>.<domain>.com/api/v1/smartresolve/keyword/somebadcompany/0.8`
- **RESPONSE**: 
    - Status code: `200` (success), Status code: `404` (failure)
    - 
        ```
        {
            "perm_id": 5036210547,
            "confidence": "0.9",
            "keyword": "Abb Corporate Research",
            "org_name": "ABB Research Ltd",
            "resolution_algorithm": "entity_match"
        }  
        ```   

___

<a name="force"/>
### Force Resolution
- **REQUEST**: `curl -XPOST https://entityresolution-<ENV>.<domain>.com/api/v1/resolve/force/keyword/linkedin`
- **RESPONSE**:
    - Status code: `200` (success), Status code: `404` (failure) 
    - 
        ```
        {
            "keyword": "Linkedin",
            "entity_match": {
                "keyword": "Linkedin",
                "org_name": "LinkedIn Corp",
                "perm_id": 4296977663,
                "confidence": "0.89"
            },
            "open_calais": [{
                "keyword": "Linkedin",
                "org_name": "LINKEDIN CORPORATION",
                "perm_id": 4296977663,
                "confidence": "1.0"
            }],
            "manual_override": null,
            "update_timestamp": "2018-09-26 18:39:01.004431"
        }
        ```
        
___

<a name="lookup"/> 
### Lookup
- **REQUEST**: `curl -XGET https://entityresolution-<ENV>.<domain>.com/api/v1/lookup/keyword/linkedin`
- **RESPONSE**: 
    - Status code: `200` (success), Status code: `404` (failure)
    - Response same as above       

___

<a name="smartlookup"/>
### Smart Lookup
- **REQUEST**: `curl -XGET https://entityresolution-<ENV>.<domain>.com/api/v1/smartlookup/keyword/linkedin/0.8`
- **RESPONSE**: 
    - Status code: `200` (success), Status code: `404` (failure)
    - 
        ```
        {
            "keyword": "Linkedin",
            "org_name": "LinkedIn Corp",
            "perm_id": 4296977663,
            "confidence": "0.89"
            "resolution_algorithm": "entity_match"
        }  
        ```       

___

<a name="override"/>
### Manual override
#### To add data to resolve to 
- **REQUEST**: `curl -XPOST https://entityresolution-<ENV>.<domain>.com/api/v1/override --data @manual_override.template`
    - Please see the template file [`manual_override.template`](manual_override.template) 
- **RESPONSE**:
    - Status code: `200` 
    - `Successfully added manual override for <keyword>`
     
#### To prevent resolution 
- **REQUEST**: `curl -XPOST https://entityresolution-<ENV>.<domain>.com/api/v1/override --data @manual_override_prevent_resolution.template`
    - Please see the template file [`manual_override_prevent_resolution.template`](manual_override_prevent_resolution.template) 
- **RESPONSE**:
    - Status code: `200` 
    - `Successfully added manual override for <keyword>` 
