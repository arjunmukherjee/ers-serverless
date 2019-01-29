import os


def get_entity_resolution_table_name():
    return os.environ['RESOLVED_TABLE_NAME']


def get_unresolved_entities_table_name():
    return os.environ['UNRESOLVED_TABLE_NAME']
