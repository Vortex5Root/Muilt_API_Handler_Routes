from muiltapi.libs.DB import ConfigModel, Skeletons

from typing import Any, Dict, List, Optional

def check_rules(rule_list: list, row_rest: list) -> Any:
    """
    Checks if all required rules are present in the row data.

    Args:
    - rule_list (list): The list of required rules.
    - row_rest (list): The list of row data.

    Returns:
    - Any: True if all rules are present, a dictionary of missing rules otherwise.
    """
    targets = [_ for _ in row_rest]
    error = {}
    for rule in rule_list:
        if rule not in targets:
            error[rule] = "Missing"
    if error != {}:
        return error
    return True

def check_config(config_id: list) -> Any:
    """
    Checks if a config exists with the given ID.
    """
    gc_config_find = ConfigModel.find(ConfigModel.id == config_id)
    if gc_config_find.count() == 1:
        return True
    return False

def check_skeleton(skeleton_id: list) -> Any:
    """
    Checks if a skeleton exists with the given ID.
    """
    gc_skeleton_find = Skeletons.find(Skeletons.id == skeleton_id)
    if gc_skeleton_find.count() == 1:
        return True
    return False