import logging

from src.tr.open_calais import issue_open_calais_request
from src.tr.entity_match import issue_entity_match_request
from src.dynamo.dynamo_handler import dynamo_save_entity
from src.dynamo.dynamo_handler import dynamo_lookup_entity
from src.helpers.date_helper import get_timestamp
from src.tr.entity import ResolutionAlgo

log = logging.getLogger()
log.setLevel(logging.INFO)


class ResolvedItem:
    def __init__(
            self,
            keyword,
            entity_match,
            open_calais,
            manual_override=None
    ):
        self.keyword = keyword
        self.entity_match = entity_match
        self.open_calais = open_calais
        self.manual_override = manual_override
        self.update_timestamp = get_timestamp()


def search_tr(keyword):
    entity_match_result = issue_entity_match_request(keyword_arg=keyword)
    open_calais_result = issue_open_calais_request(keyword_arg=keyword)

    if not entity_match_result and not open_calais_result:
        return None

    resolved_entity = ResolvedItem(keyword=keyword,
                                   entity_match=entity_match_result,
                                   open_calais=open_calais_result,
                                   manual_override=__get_previous_manual_override(keyword))

    if resolved_entity is not None:
        dynamo_save_entity(resolved_entity)
        return resolved_entity.__dict__
    else:
        return None


def __get_previous_manual_override(keyword):
    manual_override = None
    dynamo_result = dynamo_lookup_entity(keyword)
    try:
        if dynamo_result is not None and dynamo_result is not '':
            manual_override = dynamo_result[ResolutionAlgo.MANUAL_OVERRIDE.value]
    except:
        pass
    return manual_override
