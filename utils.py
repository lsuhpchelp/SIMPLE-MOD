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
    except Exception as e:
        print(f"Error loading database: {e}")
        return {}


def save_database(db_path, db):
    """Save database to a JSON file."""
    try:
        with open(db_path, 'w') as f:
            json.dump(db, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving database: {e}")
        return False


def generate_module_key(module_data, name, version, config):
    """
    Generate a module key string from template.

    Args:
        module_data: Dictionary containing module configuration data
        name: Module name
        version: Module version
        config: Configuration dictionary with default settings

    Returns:
        Formatted module key string, or None if template not found or on error
    """
    if not module_data:
        return None

    template_path = module_data.get('template')
    if not template_path or not os.path.exists(template_path):
        return None

    # Parse environment variables
    envs_str = ""
    for key, value in module_data['envs'].items():
        envs_str += f"setenv {key} \"{value}\"\n"

    # Process bind paths using config's default
    bind_paths = ','.join(filter(None, [config['defaultBindingPath'], module_data['singularity_bindpaths']]))

    # Process flags using config's default
    flags = ' '.join(filter(None, [config['defaultFlags'], module_data['singularity_flags']]))

    # Read template
    try:
        with open(template_path) as f:
            template = Template(f.read())
    except IOError:
        return None

    # Substitute values
    try:
        key_content = template.safe_substitute(
            modName=name,
            modVersion=version,
            conflict=module_data['conflict'],
            whatis=module_data['module_whatis'],
            singularity_image=module_data['singularity_image'],
            singularity_bindpaths=bind_paths,
            singularity_flags=flags,
            cmds_dummy=module_data['cmds'],
            envs=envs_str
        )
        return key_content
    except Exception:
        return None
