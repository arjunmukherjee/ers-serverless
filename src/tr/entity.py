import enum


class Entity:
    def __init__(self,
                 keyword,
                 org_name,
                 confidence,
                 perm_id,
                 is_company_score='1.0'
                 ):
        self.keyword = keyword
        self.org_name = org_name
        self.confidence = confidence
        self.perm_id = perm_id
        self.is_company_score = is_company_score


class UnresolvedEntityState(enum.Enum):
    NEW = 'new'
    RESOLUTION_FAILED = 'resolution_failed'
    FAILED = 'failed'


class ResolutionAlgo(enum.Enum):
    MANUAL_OVERRIDE = 'manual_override'
    ENTITY_MATCH = 'entity_match'
    OPEN_CALAIS = 'open_calais'


def default_not_found_result(resolution_algorithm, keyword):
    default = {"perm_id": 0, "confidence": "0.1", "is_company_score": "0.1",
               "keyword": keyword, "org_name": "XXXX: UNABLE TO RESOLVE ENTITY :XXXX"}

    if resolution_algorithm is ResolutionAlgo.OPEN_CALAIS:
        return [default]
    else:
        return default
