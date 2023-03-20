#!/usr/bin/python3

import os
import fnmatch
import logging
import argparse
from tree_sitter import Language, Parser
from tsa_utils import *

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tree_sitter_module_path', type=str, required=True)
    parser.add_argument('--scan_file', type=str)
    parser.add_argument('--scan_path', type=str)

    return parser.parse_args()

def build_languages(module_path):
    Language.build_library(
        'build/langs.so',
        [
            module_path + '/tree-sitter-c',
            module_path + '/tree-sitter-objc'
        ]
    )

    C_LANG = Language('build/langs.so', 'c')
    OBJC_LANG = Language('build/langs.so', 'objc')

    parser = Parser()
    parser.set_language(OBJC_LANG)
    return parser

def validate_checkArgs(parser, file_data):
    tree = parser.parse(bytes(file_data, "utf8"))
    root = tree.root_node

    lua_c_api_functions = get_lua_c_api_functions(root)

    logging.info("Found %d Lua API implementations", len(lua_c_api_functions))
    for api in lua_c_api_functions:
        logging.debug("Examining Lua API function: %s %s", c_function_name(api), api.start_point)
        body = api.child_by_field_name("body")

        contains_checkArgs = False
        for expr in body.children:
            if expr.type == "expression_statement":
                msg = expr.children[0]
                if msg.type == "message_expression":
                    if msg.text.find(b" checkArgs:") != -1:
                        contains_checkArgs = True
        if not contains_checkArgs:
            logging.warning("%s is missing checkArgs", c_function_name(api))


def validate_file(parser, filepath):
    logging.info("Checking: %s", filepath)
    fp = open(filepath)
    file_data = fp.read()
    fp.close()
    validate_checkArgs(parser, file_data)

if __name__ == "__main__":
    opts = parse_args()

    parser = build_languages(opts.tree_sitter_module_path)

    if opts.scan_file:
        validate_file(parser, opts.scan_file)

    if opts.scan_path:
        for root, dirs, files in os.walk(opts.scan_path):
            for file in fnmatch.filter(files, "*.[cm]"):
                validate_file(parser, root + "/" + file)
