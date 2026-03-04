#!/usr/bin/env python3
# ==================================================================##
# SIMPLE-MOD CLI
#   (Singularity Integrated Module-key Producer for Loadable
#    Environment MODules)
# Developer: Jason Li (jasonli3@lsu.edu)
# Dependency: Python 3, prompt_toolkit
# =================================================================##


import sys
import os
import json
import copy
import argparse
from string import Template

# Check for prompt_toolkit (for interactive CLI)
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import (
        prompt, button_dialog, input_dialog,
        progress_dialog, checkboxlist_dialog, message_dialog
    )
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
    from prompt_toolkit.key_binding.defaults import load_key_bindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit
    from prompt_toolkit.widgets import Dialog, Label, RadioList
    CLI_ENABLED = True
except ImportError:
    CLI_ENABLED = False

# Constants
TITLE = "SIMPLE-MOD "
VERSION = "1.1.0"
DATABASE_DIR = "database"
MODULEKEY_DIR = "modulekey"
TEMPLATE_DIR = "template"


# =============== Customized Fullscreen Choice ============== ##

def full_screen_choice(title, options, body_text=None):
    """
    Full-screen radio list selection consistent with dialog components.

    Uses Dialog with background fill (full_screen=True) and accepts the
    selection on Enter without requiring a button click.
    Returns "esc" when Esc or Ctrl+C is pressed.

    Optional body_text is displayed as a label above the radio list.
    """
    radio_list = RadioList(values=options,select_on_focus=True)

    if body_text is not None:
        body = HSplit([Label(f"\n{body_text}\n"), radio_list])
    else:
        body = radio_list

    dialog = Dialog(
        title=title,
        body=body,
        with_background=True,
    )

    kb = KeyBindings()

    @kb.add("enter", eager=True)
    def _accept(event):
        event.app.exit(result=radio_list.current_value)

    @kb.add("escape")
    @kb.add("c-c")
    def _cancel(event):
        event.app.exit(result="esc")

    app = Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([load_key_bindings(), kb]),
        mouse_support=True,
        full_screen=True,
    )
    return app.run()


# =================== Utility Functions ================== ##

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
        "defaultBindingPath": "/work,/project,/usr/local/packages,/var/scratch",
        "defaultFlags": "",
        "defaultImagePath": "",
        "defaultTemplate": "./template/template.tcl",
        "defaultModKeyPath": "./modulekey"
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



# =================== Main CLI Application ================== ##

class SimpleModCLI:
    """Main CLI application class."""

    def __init__(self):
        self.config = load_preferences()
        self.db = {}
        self.db_original = {}
        self.current_module_name = None
        self.current_module_version = None
        self.current_module = None
        self.current_db_path = None
        self._updating_form = False

        # Ensure default directories exist
        os.makedirs(DATABASE_DIR, exist_ok=True)
        os.makedirs(MODULEKEY_DIR, exist_ok=True)

    def ret_empty_module(self):
        """Return an empty module dictionary."""
        return ret_empty_module(self.config)

    def has_unsaved_changes(self):
        """Check if there are unsaved changes."""
        return self.db != self.db_original

    def confirm_save_before_continue(self, action_name="continue"):
        """Show confirmation dialog for unsaved changes with Save/No/Cancel options."""
        choice = button_dialog(
            title="Unsaved Changes",
            text="You have unsaved changes! To avoid data loss, do you want to save before continue?",
            buttons=[
                ("Yes", "save"),
                ("No", "discard"),
                ("Cancel", "cancel")
            ]
        ).run()
        if choice == "cancel":
            return False
        if choice == "save":
            self.action_save_database()
            if self.has_unsaved_changes():
                # User canceled save or save failed
                return False
        return True

    def refresh_module_list(self):
        """Refresh the current module list and version list."""
        if not self.current_module_name:
            return [], []

        if self.current_module_name not in self.db:
            return [], []

        versions = sorted(self.db[self.current_module_name].keys(), reverse=True)
        return list(self.db.keys()), versions

    def load_current_module(self, name=None, version=None):
        """Load a module into the current working buffer."""
        if name is None:
            name = self.current_module_name
        if version is None:
            version = self.current_module_version

        if name and version and name in self.db and version in self.db[name]:
            self.current_module = copy.deepcopy(self.db[name][version])
            self.current_module_name = name
            self.current_module_version = version
        else:
            self.current_module = self.ret_empty_module()
            self.current_module_name = None
            self.current_module_version = None

    def update_db_from_form(self):
        """Update the database with current module form data."""
        if self.current_module_name and self.current_module_version:
            self.db[self.current_module_name][self.current_module_version] = copy.deepcopy(self.current_module)

    def generate_module_key(self, module_data, name, version, output_dir):
        """Generate a module key file from template."""
        if not module_data or not output_dir:
            return False

        template_path = module_data.get('template', './template/template.tcl')
        if not os.path.exists(template_path):
            print(f"Error: Template not found: {template_path}")
            return False

        # Parse environment variables
        envs_str = ""
        for key, value in module_data.get('envs', {}).items():
            envs_str += f'setenv {key} "{value}"\n'

        # Process bind paths
        default_bind = self.config.get('defaultBindingPath', '/work,/project,/usr/local/packages,/var/scratch')
        custom_bind = module_data.get('singularity_bindpaths', '')
        bind_paths = ','.join(filter(None, [default_bind, custom_bind]))

        # Process flags
        default_flags = self.config.get('defaultFlags', '')
        custom_flags = module_data.get('singularity_flags', '')
        flags = ' '.join(filter(None, [default_flags, custom_flags]))

        # Read template
        try:
            with open(template_path) as f:
                template = Template(f.read())
        except IOError as e:
            print(f"Error reading template: {e}")
            return False

        # Substitute values
        try:
            key_content = template.safe_substitute(
                modName=name,
                modVersion=version,
                conflict=module_data.get('conflict', ''),
                whatis=module_data.get('module_whatis', ''),
                singularity_image=module_data.get('singularity_image', ''),
                singularity_bindpaths=bind_paths,
                singularity_flags=flags,
                cmds_dummy=module_data.get('cmds', ''),
                envs=envs_str
            )
        except Exception as e:
            print(f"Error substituting template: {e}")
            return False

        # Write output
        output_path = os.path.join(output_dir, name, version)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with open(output_path, 'w') as f:
                f.write(key_content)
            return True
        except IOError as e:
            print(f"Error writing module key: {e}")
            return False

    # =================== Menu Actions ================== ##

    def action_new_database(self):
        """Create a new empty database."""
        if self.has_unsaved_changes():
            if not self.confirm_save_before_continue():
                return False

        self.db = {}
        self.db_original = {}
        self.current_module_name = None
        self.current_module_version = None
        self.current_module = self.ret_empty_module()
        self.current_db_path = None
        return True

    def action_open_database(self):
        """Open an existing database file."""
        if self.has_unsaved_changes():
            if not self.confirm_save_before_continue():
                return False

        json_files = list_json_files(DATABASE_DIR)
        if not json_files:
            message_dialog(
                title="Open Database",
                text=f"No JSON files found in {DATABASE_DIR}/"
            ).run()
            return False

        options = [(f, f) for f in json_files] + [('esc', 'Back (Esc)')]
        db_file = full_screen_choice(
            "Open Database",
            options=options,
        )

        if db_file == 'esc':
            return False

        db_path = os.path.join(DATABASE_DIR, db_file)
        self.db = load_database(db_path)
        self.db_original = copy.deepcopy(self.db)
        self.current_db_path = db_path

        if self.db:
            # Load first module
            first_name = sorted(self.db.keys())[0]
            first_version = sorted(self.db[first_name].keys(), reverse=True)[0]
            self.load_current_module(first_name, first_version)

        return True

    def action_save_database(self):
        """Save the current database to a file."""
        if not self.db:
            message_dialog(
                title="Save Database",
                text="Error: Database is empty. Nothing to save."
            ).run()
            return False

        if not (self.current_db_path and os.path.exists(self.current_db_path)):
            # Let user choose path
            user_path = input_dialog(
                title="Save Database As",
                text="Enter path to save database (must end with .json):"
            ).run()

            if user_path is None:
                return False

            if not user_path.endswith('.json'):
                user_path += '.json'

            self.current_db_path = user_path

        if save_database(self.current_db_path, self.db):
            self.db_original = copy.deepcopy(self.db)
            return True
        else:
            message_dialog(
                title="Save Failed",
                text="Could not save the database."
            ).run()
            return False

    def action_add_module(self):
        """Add a new module."""
        name = input_dialog(
            title="Add Module",
            text="Enter module name:",
            default=""
        ).run()

        if name is None:
            return
        name = name.strip()
        if not name:
            message_dialog(title="Error", text="Module name cannot be empty.").run()
            return

        version = input_dialog(
            title="Add Module",
            text="Enter version:",
            default=""
        ).run()

        if version is None:
            return
        version = version.strip()
        if not version:
            message_dialog(title="Error", text="Version cannot be empty.").run()
            return

        # Check if module already exists
        if name in self.db and version in self.db[name]:
            message_dialog(title="Error", text=f"Module {name} {version} already exists.").run()
            return

        # Create new module
        if name not in self.db:
            self.db[name] = {}
        self.db[name][version] = self.ret_empty_module()

        # Load the new module
        self.load_current_module(name, version)

    def action_copy_module(self):
        """Copy the current module to a new name/version."""
        if not self.current_module_name:
            message_dialog(
                title="Copy Module",
                text="Error: No module selected."
            ).run()
            return

        name = input_dialog(
            title="Copy Module",
            text="Enter new module name:",
            default=self.current_module_name
        ).run()

        if name is None:
            return
        name = name.strip()
        if not name:
            message_dialog(title="Error", text="Module name cannot be empty.").run()
            return

        version = input_dialog(
            title="Copy Module",
            text="Enter new version:",
            default=self.current_module_version
        ).run()

        if version is None:
            return
        version = version.strip()
        if not version:
            message_dialog(title="Error", text="Version cannot be empty.").run()
            return

        # Check if module already exists
        if name in self.db and version in self.db[name]:
            message_dialog(title="Error", text=f"Module {name} {version} already exists.").run()
            return

        # Create copy
        if name not in self.db:
            self.db[name] = {}
        self.db[name][version] = copy.deepcopy(self.current_module)

        # Load the copy
        self.load_current_module(name, version)

    def action_delete_module(self):
        """Delete the current module."""
        if not self.current_module_name:
            message_dialog(
                title="Delete Module",
                text="Error: No module selected."
            ).run()
            return

        choice = button_dialog(
            title="Delete Module",
            text="Are you sure you want to delete this module?",
            buttons=[
                ("Yes", "yes"),
                ("No", "no")
            ]
        ).run()
        if choice != "yes":
            return

        # Check for multiple versions
        if len(self.db[self.current_module_name]) > 1:
            # Delete only this version
            del self.db[self.current_module_name][self.current_module_version]

            # Find next version
            versions = sorted(self.db[self.current_module_name].keys(), reverse=True)
            self.load_current_module(self.current_module_name, versions[0])
        else:
            # Delete entire module
            del self.db[self.current_module_name]
            # Select first module and version if database is not empty
            if self.db:
                first_name = sorted(self.db.keys())[0]
                first_version = sorted(self.db[first_name].keys(), reverse=True)[0]
                self.load_current_module(first_name, first_version)
            else:
                self.current_module_name = None
                self.current_module_version = None
                self.current_module = self.ret_empty_module()

    def action_edit_module(self):
        """Edit the current module's details."""
        if not self.current_module_name:
            message_dialog(
                title="Edit Module",
                text="Error: No module selected."
            ).run()
            return

        while True:
            envs = self.current_module.get('envs', {})

            choice = full_screen_choice(
                    "Edit Module:",
                    options=[
                        ('1', 'Conflicts'),
                        ('2', 'Description'),
                        ('3', 'Image Path'),
                        ('4', 'Bind Paths'),
                        ('5', 'Flags'),
                        ('6', 'Commands'),
                        ('7', 'Template'),
                        ('8', 'Environment Vars'),
                        ('esc', 'Back (Esc)'),
                    ],
                )

            if choice == 'esc':
                break

            if choice == '1':
                # Conflicts
                value = input_dialog(
                    title="Edit Conflicts",
                    text="Enter conflict modules (space-separated):",
                    default=self.current_module.get('conflict', '')
                ).run()
                if value is not None:
                    self.current_module['conflict'] = value.strip()

            elif choice == '2':
                # Description
                value = input_dialog(
                    title="Edit Description",
                    text="Enter software description:",
                    default=self.current_module.get('module_whatis', '')
                ).run()
                if value is not None:
                    self.current_module['module_whatis'] = value.strip()

            elif choice == '3':
                # Image Path
                value = input_dialog(
                    title="Edit Image Path",
                    text="Enter Singularity image path:",
                    default=self.current_module.get('singularity_image', '')
                ).run()
                if value is not None:
                    self.current_module['singularity_image'] = value.strip()

            elif choice == '4':
                # Bind Paths
                default_bind = self.config.get('defaultBindingPath', '/work,/project,/usr/local/packages,/var/scratch')
                value = input_dialog(
                    title="Edit Bind Paths",
                    text=f"Enter additional paths to bind (default: {default_bind}):",
                    default=self.current_module.get('singularity_bindpaths', '')
                ).run()
                if value is not None:
                    self.current_module['singularity_bindpaths'] = value.strip()

            elif choice == '5':
                # Flags
                default_flags = self.config.get('defaultFlags', '')
                value = input_dialog(
                    title="Edit Flags",
                    text=f"Enter additional flags (default: {default_flags}):",
                    default=self.current_module.get('singularity_flags', '')
                ).run()
                if value is not None:
                    self.current_module['singularity_flags'] = value.strip()

            elif choice == '6':
                # Commands
                value = input_dialog(
                    title="Edit Commands",
                    text="Enter commands to map (space or newline separated):",
                    default=self.current_module.get('cmds', '')
                ).run()
                if value is not None:
                    self.current_module['cmds'] = value.strip()

            elif choice == '7':
                # Template
                value = input_dialog(
                    title="Edit Template",
                    text="Enter template file path:",
                    default=self.current_module.get('template', './template/template.tcl')
                ).run()
                if value is not None:
                    self.current_module['template'] = value.strip()

            elif choice == '8':
                # Environment Variables
                self.edit_environment_variables()

        # Save to database
        self.update_db_from_form()

    def edit_environment_variables(self):
        """Edit environment variables for the current module."""
        envs = copy.deepcopy(self.current_module.get('envs', {}))

        while True:
            if envs:
                # Show available variables for selection
                value_choices = [(str(i), f"{key} = {value}") for i, (key, value) in enumerate(envs.items(), 1)]
                value_choices.extend([
                    ('A', 'Add new variable'),
                    ('D', 'Delete variable'),
                    ('esc', 'Back (Esc)')
                ])
            else:
                value_choices = [
                    ('A', 'Add new variable'),
                    ('esc', 'Back (Esc)')
                ]

            choice = full_screen_choice(
                    "Edit Environment Variables:",
                    options=value_choices,
                )

            if choice == 'esc':
                self.current_module['envs'] = envs
                break
            elif choice == 'A':
                key = input_dialog(
                    title="Add Environment Variable",
                    text="Variable name:",
                ).run()
                if key:
                    value = input_dialog(
                        title="Add Environment Variable",
                        text="Variable value:",
                    ).run()
                    if value:
                        envs[key] = value
            elif choice == 'D':
                if envs:
                    del_options = [(k, k) for k in envs.keys()] + [('esc', 'Back (Esc)')]
                    key = full_screen_choice(
                            "Delete Environment Variable:",
                            options=del_options,
                        )
                    if key != 'esc':
                        del envs[key]
                else:
                    message_dialog(
                        title="No Variables",
                        text="No environment variables to delete.",
                        ok_text="OK"
                    ).run()
            else:
                try:
                    idx = int(choice) - 1
                    keys = list(envs.keys())
                    if 0 <= idx < len(keys):
                        key = keys[idx]
                        value = input_dialog(
                            title="Edit Environment Variable",
                            text=f"New value for {key}:",
                            default=envs.get(key, '')
                        ).run()
                        if value:
                            envs[key] = value
                except (ValueError, IndexError):
                    continue

            if not envs:
                # Clear empty dict
                self.current_module['envs'] = {}

    def action_select_module(self):
        """Interactive module selection dialog."""
        name_list, version_list = self.refresh_module_list()

        if not name_list:
            message_dialog(
                title="Select Module",
                text="No modules in database."
            ).run()
            return

        # Name selection
        name_options = [(n, n) for n in name_list] + [('esc', 'Back (Esc)')]
        name = full_screen_choice(
            "Select Module:",
            options=name_options,
        )

        if name == 'esc':
            return

        # Version selection
        versions = sorted(self.db[name].keys(), reverse=True)
        if len(versions) == 1:
            version = versions[0]
        else:
            ver_options = [(v, v) for v in versions] + [('esc', 'Back (Esc)')]
            version = full_screen_choice(
                    f"Select Version for {name}:",
                    options=ver_options,
                )

        if version == 'esc':
            return

        self.load_current_module(name, version)

    def action_generate_key(self):
        """Generate a module key for the current module."""
        if not self.current_module_name:
            message_dialog(
                title="Generate Module Key",
                text="Error: No module selected."
            ).run()
            return

        output_dir = self.config.get('defaultModKeyPath', MODULEKEY_DIR)

        # Ask for output directory
        custom_dir = input_dialog(
            title="Generate Module Key",
            text="Enter output directory (press Enter for default):",
            default=output_dir
        ).run()

        if custom_dir is None:
            return

        output_dir = custom_dir.strip() if custom_dir.strip() else output_dir

        # Generate the key
        if self.generate_module_key(
            self.current_module,
            self.current_module_name,
            self.current_module_version,
            output_dir
        ):
            message_dialog(
                title="Success",
                text=f"Module key generated for {self.current_module_name} {self.current_module_version}\n\nOutput: {os.path.join(output_dir, self.current_module_name, self.current_module_version)}"
            ).run()
        else:
            message_dialog(
                title="Error",
                text="Failed to generate module key. Check logs for details."
            ).run()

    def action_generate_all_keys(self):
        """Generate module keys for all modules in the database."""
        if not self.db:
            message_dialog(
                title="Generate All Module Keys",
                text="Error: Database is empty."
            ).run()
            return

        if self.has_unsaved_changes():
            if not self.confirm_save_before_continue():
                return

        output_dir = self.config.get('defaultModKeyPath', MODULEKEY_DIR)

        custom_dir = input_dialog(
            title="Generate All Module Keys",
            text="Enter output directory (press Enter for default):",
            default=output_dir
        ).run()

        if custom_dir is None:
            return

        output_dir = custom_dir.strip() if custom_dir.strip() else output_dir

        success_count = 0
        fail_count = 0

        for name in sorted(self.db.keys()):
            for version in sorted(self.db[name].keys(), reverse=True):
                if self.generate_module_key(
                    self.db[name][version],
                    name,
                    version,
                    output_dir
                ):
                    success_count += 1
                else:
                    fail_count += 1

        message_dialog(
            title="Generation Complete",
            text=f"Successfully generated: {success_count} keys\nFailed: {fail_count} keys\nOutput directory: {output_dir}"
        ).run()

    def action_preferences(self):
        """Edit preferences."""
        config = self.config

        while True:
            choice = full_screen_choice(
                    "Preferences",
                    options=[
                        ('1', 'Default binding paths'),
                        ('2', 'Default flags'),
                        ('3', 'Default image directory'),
                        ('4', 'Default template'),
                        ('5', 'Default modkey path'),
                        ('esc', 'Back (Esc)'),
                    ],
                )

            if choice == 'esc':
                break

            if choice == '1':
                value = input_dialog(
                    title="Edit Default Binding Paths",
                    text="Enter default paths to bind (comma-separated):",
                    default=config.get('defaultBindingPath', '/work,/project,/usr/local/packages,/var/scratch')
                ).run()
                if value is not None:
                    config['defaultBindingPath'] = value.strip()

            elif choice == '2':
                value = input_dialog(
                    title="Edit Default Flags",
                    text="Enter default Singularity flags:",
                    default=config.get('defaultFlags', '')
                ).run()
                if value is not None:
                    config['defaultFlags'] = value.strip()

            elif choice == '3':
                value = input_dialog(
                    title="Edit Default Image Directory",
                    text="Enter default directory for Singularity images:",
                    default=config.get('defaultImagePath', '')
                ).run()
                if value is not None:
                    config['defaultImagePath'] = value.strip()

            elif choice == '4':
                value = input_dialog(
                    title="Edit Default Template",
                    text="Enter default template file path:",
                    default=config.get('defaultTemplate', './template/template.tcl')
                ).run()
                if value is not None:
                    config['defaultTemplate'] = value.strip()

            elif choice == '5':
                value = input_dialog(
                    title="Edit Default Module Key Path",
                    text="Enter default directory for generated module keys:",
                    default=config.get('defaultModKeyPath', MODULEKEY_DIR)
                ).run()
                if value is not None:
                    config['defaultModKeyPath'] = value.strip()

        # Save preferences
        try:
            with open(os.path.expanduser('~/.simple-modrc'), 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
        except IOError as e:
            message_dialog(
                title="Error",
                text=f"Error saving preferences: {e}"
            ).run()

    # =================== Main Menu ================== ##

    def main_menu(self):
        """Display the main menu."""
        while True:
            choice = full_screen_choice(
                    "Main Menu",
                    options=[
                        ('1', 'File'),
                        ('2', 'Module'),
                        ('3', 'Generate'),
                        ('4', 'Preferences'),
                        ('esc', 'Exit (Esc)'),
                    ],
                )

            if choice == '1':
                self.file_menu()
            elif choice == '2':
                self.module_menu()
            elif choice == '3':
                self.generate_menu()
            elif choice == '4':
                self.action_preferences()
            elif choice == 'esc':
                if self.has_unsaved_changes():
                    if not self.confirm_save_before_continue():
                        continue
                    return True
                else:
                    return True

    def file_menu(self):
        """Display the file menu."""
        while True:
            choice = full_screen_choice(
                    "File Menu",
                    options=[
                        ('1', 'New Database'),
                        ('2', 'Open Database'),
                        ('3', 'Save Database'),
                        ('4', 'Save Database As...'),
                        ('esc', 'Back (Esc)'),
                    ],
                )

            if choice == '1':
                if self.action_new_database():
                    self.module_menu()
                    break
            elif choice == '2':
                if self.action_open_database():
                    self.module_menu()
                    break
            elif choice == '3':
                if self.action_save_database():
                    self.module_menu()
                    break
            elif choice == '4':
                custom_path = input_dialog(
                    title="Save Database As",
                    text="Enter path to save database (must end with .json):"
                ).run()
                if custom_path:
                    if not custom_path.endswith('.json'):
                        custom_path += '.json'
                    self.current_db_path = custom_path
                    if self.action_save_database():
                        self.module_menu()
                        break
            elif choice == 'esc':
                break

    def module_menu(self):
        """Display the module menu."""
        while True:
            db_path_display = self.current_db_path if self.current_db_path else ""
            choice = full_screen_choice(
                    "Module Menu",
                    options=[
                        ('1', 'Select Module'),
                        ('2', 'Add New Module'),
                        ('3', 'Copy Current Module'),
                        ('4', 'Delete Current Module'),
                        ('5', 'Edit Current Module'),
                        ('esc', 'Back (Esc)'),
                    ],
                    body_text=f"Opened database: {db_path_display or "(None)"}",
                )

            if choice == '1':
                self.action_select_module()
            elif choice == '2':
                self.action_add_module()
            elif choice == '3':
                self.action_copy_module()
            elif choice == '4':
                self.action_delete_module()
            elif choice == '5':
                self.action_edit_module()
            elif choice == 'esc':
                break

    def generate_menu(self):
        """Display the generate menu."""
        while True:
            choice = full_screen_choice(
                    "Generate Menu",
                    options=[
                        ('1', 'Generate Current Module Key'),
                        ('2', 'Generate All Module Keys'),
                        ('esc', 'Back (Esc)'),
                    ],
                )

            if choice == '1':
                self.action_generate_key()
            elif choice == '2':
                self.action_generate_all_keys()
            elif choice == 'esc':
                break

    def run(self):
        """Run the CLI application. Requires prompt_toolkit (CLI_ENABLED)."""
        if not CLI_ENABLED:
            return
        # Main menu loop
        while True:
            exit_app = self.main_menu()
            if exit_app:
                break


# =================== Command Line Interface ================== ##

def run_command_mode(cli, args):
    """Run in command-line mode."""
    if args.cmd == 'gen-key':
        if not args.name or not args.version:
            print("Error: --name and --version are required for gen-key")
            return False

        # Load database
        db_path = args.database
        if db_path:
            cli.db = load_database(db_path)
            cli.db_original = copy.deepcopy(cli.db)

        # Get module
        if args.name in cli.db and args.version in cli.db[args.name]:
            module = cli.db[args.name][args.version]
            output = args.output or cli.config.get('defaultModKeyPath', MODULEKEY_DIR)

            if cli.generate_module_key(module, args.name, args.version, output):
                print(f"Generated: {os.path.join(output, args.name, args.version)}")
                return True
            else:
                print("Failed to generate module key")
                return False
        else:
            print(f"Module {args.name} {args.version} not found in database")
            return False

    elif args.cmd == 'gen-all':
        db_path = args.database
        if db_path:
            cli.db = load_database(db_path)
            cli.db_original = copy.deepcopy(cli.db)

        output = args.output or cli.config.get('defaultModKeyPath', MODULEKEY_DIR)

        success = 0
        fail = 0
        for name in cli.db:
            for version in cli.db[name]:
                if cli.generate_module_key(cli.db[name][version], name, version, output):
                    success += 1
                else:
                    fail += 1

        print(f"Generated {success} keys, {fail} failed")
        return fail == 0

    return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SIMPLE-MOD CLI - Singularity Module Key Generator"
    )
    parser.add_argument(
        '-d', '--database',
        help='Path to database JSON file to open on startup'
    )
    parser.add_argument(
        '-c', '--cmd',
        choices=['gen-key', 'gen-all'],
        help='Command to execute: gen-key (generate current module), gen-all (generate all)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory for generated keys'
    )
    parser.add_argument(
        '--name',
        help='Module name for command mode'
    )
    parser.add_argument(
        '--version',
        help='Module version for command mode'
    )

    args = parser.parse_args()

    cli = SimpleModCLI()

    if args.cmd:
        # Command mode
        if not run_command_mode(cli, args):
            sys.exit(1)
    else:
        # Interactive mode
        if not CLI_ENABLED:
            print("ERROR: prompt_toolkit is not installed!")
            print("Please install it with: pip install prompt_toolkit")
            print("The application requires prompt_toolkit and cannot run without it.")
            sys.exit(1)

        try:
            cli.run()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
