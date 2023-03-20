#!/usr/bin/python3
import logging

def find_c_functions(root_node):
    functions = []
    for child in root_node.children:
        if is_c_function(child):
            functions.append(child)
    return functions

def is_c_function(node, log=False):
    result = (node.type == "function_definition")
    if result and log:
        func_decl = node.child_by_field_name("declarator")
        name_decl = func_decl.child_by_field_name("declarator")
        logging.debug("is_c_function found: %s", name_decl.text)
    return result

def c_function_return_type(node):
    assert(is_c_function(node))
    return_type = node.child_by_field_name('type')
    assert(return_type)
    return node.child_by_field_name('type')

def is_c_function_return_type(node, return_type):
    fn_return = c_function_return_type(node)
    if not fn_return:
        return False
    result = fn_return.text == bytes(return_type, "utf8")
    if result:
        logging.debug("  is_c_function_return_type found: %s", return_type)
    return result

def c_function_parameter_count(node):
    assert(is_c_function(node))
    func_decl = node.child_by_field_name("declarator")
    assert(func_decl)
    param_list = func_decl.child_by_field_name("parameters")
    assert(param_list)
    params = [x for x in param_list.children if x.type == "parameter_declaration"]
    return len(params)

def is_c_function_parameter_count(node, count):
    param_count = c_function_parameter_count(node)
    result = param_count == count
    if result:
        logging.debug("  is_c_function_parameter_count found: %d", count)
    return result

def c_function_parameter_type(node, param_pos):
    assert(is_c_function(node))
    func_decl = node.child_by_field_name("declarator")
    assert(func_decl)
    param_list = func_decl.child_by_field_name("parameters")
    assert(param_list)

    params = [x for x in param_list.children if x.type == "parameter_declaration"]
    assert(len(params) > param_pos)

    target_param = params[param_pos].child_by_field_name("type")
    assert(target_param)

    return target_param

def c_function_name(node):
    assert(is_c_function(node))
    func_decl = node.child_by_field_name("declarator")
    name_decl = func_decl.child_by_field_name("declarator")
    return name_decl.text

def is_c_function_parameter_type(node, param_pos, param_type):
    target_param = c_function_parameter_type(node, param_pos)
    result = target_param.text == bytes(param_type, "utf8")
    if result:
        logging.debug("  is_c_function_parameter_type found: %d -> %s", param_pos, param_type)
    return result

def is_lua_c_api_function(node):
    return is_c_function(node, log=True) and \
        is_c_function_return_type(node, "int") and \
        is_c_function_parameter_count(node, 1) and \
        is_c_function_parameter_type(node, 0, "lua_State")

def get_lua_c_api_functions(root_node):
    return [x for x in find_c_functions(root_node) if is_lua_c_api_function(x)]

# FIXME: This only finds the first item at each level, which is likely not useful in most cases
def find_item_by_type_path(node, type_path):
    logging.debug("find_item_by_type_path: %s", type_path)
    result = None

    to_search = node.children
    last_found = None
    while len(type_path) > 0:
        found = False
        target_type = type_path.pop(0)
        logging.debug("  Next in path: %s", target_type)
        for item in to_search:
            logging.debug("    checking %s", item.type)
            if item.type == target_type:
                to_search = item.children
                last_found = item
                found = True
                break
        if not found:
            logging.debug("find_item_by_type_path: Unable to find %s", target_type)
            return None
    return last_found

def is_text_in_item(item, text):
    return (item and item.text.find(bytes(text, "utf8")) != -1)

