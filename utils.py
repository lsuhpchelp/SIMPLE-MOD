# ===================================================================##
# SIMPLE-MOD Utilities
#   (Singularity Integrated Module-key Producer for Loadable
#    Environment MODules)
# Developer: Jason Li (jasonli3@lsu.edu)
# Dependency: Python 3
# =====================================================================##


# =========== Software Information ===========##

TITLE = "SIMPLE-MOD "
VERSION = "1.1.0"
ABOUT = f"""{TITLE}
(Singularity Integrated Module-key Producer for Loadable Environment MODules)

SIMPLE-MOD is a QT-based GUI tool to automatically generate module keys for easy access of container-based software packages.

Version: \t{VERSION}
Author: \tJason Li
Home: \thttps://github.com/lsuhpchelp/SIMPLE-MOD
License: \tMIT License
"""


# =================== Imports ===========##


import os
import json
import copy
from string import Template


# =================== Utility Functions ===========##


def load_preferences():
    """
    Load preferences from "~/.simple-modrc". Create the file if it does not exist.
    """
    config_path = os.path.expanduser('~/.simple-modrc')

    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass

    # Default configuration
    config = {
        "defaultDatabasePath": "./database",
        "defaultImagePath": "",
        "defaultModKeyPath": "./modulekey",
        "defaultTemplate": "./template/template.tcl",
        "defaultBindingPath": "/work,/project,/usr/local/packages,/var/scratch",
        "defaultFlags": "",
    }
    try:
        with open(config_path, "w") as fw:
            json.dump(config, fw, indent=4)
    except IOError:
        pass

    return config


def ret_empty_module(config):
    """
    Return an empty module dictionary.
    """
    return {
        "conflict": "",
        "module_whatis": "",
        "singularity_image": "",
        "singularity_bindpaths": "",
        "singularity_flags": "",
        "cmds": "",
        "envs": {},
        "template": config.get("defaultTemplate", "./template/template.tcl")
    }


def list_json_files(directory):
    """List all JSON files in a directory."""
    try:
        return sorted([f for f in os.listdir(directory) if f.endswith('.json')])
    except FileNotFoundError:
        return []


def load_database(db_path):
    """Load a database JSON file."""
    try:
        with open(db_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {db_path}: {e}")
        return {}


def save_database(db_path, db):
    """Save database to a JSON file."""
    try:
        with open(db_path, 'w') as f:
            json.dump(db, f, indent=4)
        return True
    except IOError as e:
        print(f"Error saving database: {e}")
        return False
