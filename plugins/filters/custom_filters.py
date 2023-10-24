# custom_filters.py
import ansible.plugins.filter
from ansible.utils.display import Display
import re

display = Display()

###########################
# HELPER FUNCTIONS
###########################


def parse_key(key):
    return re.split(r'\.|\[|\]', key)


def add_key_to_all(data, key, value):
    for item in data:
        if isinstance(item, dict):
            item[key] = value


def get_nested_value(dic, keys):
    for key in keys:
        if not key:
            continue  # Skip empty strings from key split
        if re.match(r'\d+', key):  # If key is an index
            dic = dic[int(key)]
        else:
            dic = dic[key]
    return dic


def nested_set(dic, keys, value):
    for key in keys[:-1]:
        if re.match(r'.+\[\d+\]$', key):  # If key has an index e.g., b[1]
            key, index = re.match(r'(.+)\[(\d+)\]$', key).groups()
            if key not in dic or not isinstance(dic[key], list):
                dic[key] = [{} for _ in range(int(index) + 1)]  # Ensure list is long enough
            dic = dic[key][int(index)]  # Navigate to the indexed item
        else:
            if not isinstance(dic, dict):
                dic = {}
            dic = dic.setdefault(key, {})  # For non-indexed keys, ensure key exists and navigate to it
    
    last_key = keys[-1]
    if re.match(r'.+\[\d+\]$', last_key):
        last_key, index = re.match(r'(.+)\[(\d+)\]$', last_key).groups()
        if last_key not in dic or not isinstance(dic[last_key], list):
            dic[last_key] = [{} for _ in range(int(index) + 1)]  # Ensure list is long enough
        dic[last_key][int(index)] = value  # Set value at the indexed item
    else:
        if not isinstance(dic, dict):
            dic = {}
        dic[last_key] = value  # Set value for non-indexed keys


# def nested_set(dic, keys, value):
#     for key in keys[:-1]:
#         if re.match(r'.+\[\d+\]$', key):  # If key has an index e.g., b[1]
#             key, index = re.match(r'(.+)\[(\d+)\]$', key).groups()
#             dic = dic.setdefault(key, [{}])[int(index)]
#         else:
#             dic = dic.setdefault(key, {})
#     last_key = keys[-1]
#     if re.match(r'.+\[\d+\]$', last_key):
#         last_key, index = re.match(r'(.+)\[(\d+)\]$', last_key).groups()
#         dic[last_key][int(index)] = value
#     else:
#         dic[last_key] = value


def nested_merge(dic, keys, new_obj):
    for key in keys[:-1]:
        if re.match(r'.+\[\d+\]$', key):
            key, index = re.match(r'(.+)\[(\d+)\]$', key).groups()
            dic = dic.setdefault(key, [{}])[int(index)]
        else:
            dic = dic.setdefault(key, {})
    last_key = keys[-1]
    if re.match(r'.+\[\d+\]$', last_key):
        last_key, index = re.match(r'(.+)\[(\d+)\]$', last_key).groups()
        dic[last_key][int(index)].update(new_obj)
    else:
        dic[last_key].update(new_obj)


def evaluate_condition_and_set(data, condition, new_key, value):
    key, condition_value = condition.split('==')
    condition_value = condition_value.strip('`')
    for item in data:
        if isinstance(item, dict) and item.get(key) == condition_value:
            item[new_key] = value  # Use new_key variable instead of hardcoded 'new_key'


def evaluate_condition(data, condition):
    key, value = condition.split('==')
    value = value.strip('`')
    return [item for item in data if item.get(key) == value]


# def parse_query(query):
#     # Parse the query into a structured format
#     keys = []
#     for key in re.split(r'\.', query):
#         match = re.match(r'(.+)\[(\d+)\]$', key)
#         if match:
#             key, index = match.groups()
#             keys.append((key, int(index)))
#         else:
#             keys.append((key, None))
#     return keys

def parse_query(query):
    # Split the query by '.' to get the keys
    keys = query.split('.')
    return keys


def recursive_set(data, keys, value):
    if not keys:
        return
    key = keys[0]

    # Check if the key contains an index or a condition for a list item
    match = re.match(r'(.+)\[(\*|Name==`(.+)`)\]$', key, re.IGNORECASE)
    if match:
        key, star, condition_value = match.groups()
        if not isinstance(data.get(key), list):
            data[key] = []
        if star:
            for item in data[key]:
                if isinstance(item, dict):
                    recursive_set(item, keys[1:], value)
        else:
            for item in data[key]:
                if isinstance(item, dict) and item.get('Name') == condition_value:
                    recursive_set(item, keys[1:], value)
                    return
            new_item = {'Name': condition_value}
            data[key].append(new_item)
    else:
        if len(keys) == 1:
            data[key] = value
        else:
            data.setdefault(key, {})
            recursive_set(data[key], keys[1:], value)

##########################
# CORE FUNCTIONS
##########################


def get_value(data, query):
    keys = re.split(r'\.|\[|\]', query)
    for i, key in enumerate(keys):
        if not key:
            continue
        if key == '*':  # Check for wildcard operator
            # If wildcard is encountered, iterate over all items in the current array
            remaining_query = '.'.join(keys[i + 1:])
            if remaining_query:
                data = [get_value(item, remaining_query) for item in data]
            else:
                return data
            break  # Exit the loop as the remaining query will be handled in recursive calls
        elif '==' in key:
            data = evaluate_condition(data, key)
        elif re.match(r'\d+', key):
            data = data[int(key)]
        else:
            data = data.get(key, {})
    return data

# def get_value(data, query):
#     keys = re.split(r'\.|\[|\]', query)
#     for i, key in enumerate(keys):
#         if not key:
#             continue
#         if key == '*':  # Check for wildcard operator
#             # If wildcard is encountered, iterate over all items in the current array
#             remaining_query = '.'.join(keys[i + 1:])
#             data = [get_value(item, remaining_query) for item in data]
#             break  # Exit the loop as the remaining query will be handled in recursive calls
#         elif '==' in key:
#             data = evaluate_condition(data, key)
#         elif re.match(r'\d+', key):
#             data = data[int(key)]
#         else:
#             data = data.get(key, {})
#     return data


def merge_obj(current_obj, key, new_obj):
    display.vvvv("get_value: merge_obj: %s" % key)
    keys = key.split('.')
    nested_merge(current_obj, keys, new_obj)
    return current_obj


def add_key_value(data, query, value):
    # Parse the query
    keys = parse_query(query)
    # Call the recursive function to set the value
    recursive_set(data, keys, value)
    return data


##########################
# CORE CLASS
##########################


class FilterModule():
    """ Query filter """

    def filters(self):
        return {
            'merge_obj': merge_obj,
            'add_key_value': add_key_value,
            'get_value': get_value
        }
