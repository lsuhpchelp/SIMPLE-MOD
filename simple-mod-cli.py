# ==================================================================##
# SIMPLE-MOD CLI
#   (Singularity Integrated Module-key Producer for Loadable
#    Environment MODules)
# Developer: Jason Li (jasonli3@lsu.edu)
# Dependency: prompt_toolkit
# =================================================================##


import sys
import os
import json
import copy
import argparse
import textwrap
from string import Template

# Import shared utilities
from utils import *

# CLI-specific imports
# Check for prompt_toolkit (for interactive CLI)
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import (
        prompt, button_dialog, input_dialog as input_dialog_origin,
        progress_dialog, checkboxlist_dialog, message_dialog
    )
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
    from prompt_toolkit.key_binding.defaults import load_key_bindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit
    from prompt_toolkit.widgets import Dialog, Label, RadioList, TextArea, Button
    CLI_ENABLED = True

except ImportError:

    CLI_ENABLED = False


# =============== Customized Fullscreen Choice ============== ##

def add_esc_to_dialog(app, esc_result):
    """
    Helper: attach Esc and Ctrl+C bindings to any dialog Application,
    exiting with the given esc_result (mimics full_screen_choice behaviour).
    """
    kb = KeyBindings()
    @kb.add("escape", eager=True)
    @kb.add("c-c", eager=True)
    def _cancel(event):
        event.app.exit(result=esc_result)
    app.key_bindings = merge_key_bindings([app.key_bindings, kb])
    return app

def input_dialog(*args, **kwargs):
    """Wrap input_dialog so that Esc and Ctrl+C always trigger Cancel (→ None)"""
    return add_esc_to_dialog(input_dialog_origin(*args, **kwargs), None)

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

    def ret_empty_module(self):
        """Return an empty module dictionary."""
        return ret_empty_module(self.config)

    def has_unsaved_changes(self):
        """Check if there are unsaved changes."""
        return self.db != self.db_original

    def confirm_save_before_continue(self, action_name="continue"):
        """Show confirmation dialog for unsaved changes with Save/No/Cancel options."""
        choice = add_esc_to_dialog(button_dialog(
            title="Unsaved Changes",
            text="You have unsaved changes! To avoid data loss, do you want to save before continue?",
            buttons=[
                ("Yes", "save"),
                ("No", "discard"),
                ("Cancel", "cancel")
            ]
        ), "cancel").run()
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

        key_content = generate_module_key(module_data, name, version, self.config)
        if not key_content:
            print(f"Error: Failed to generate module key content")
            return False

        # Write output
        output_path = os.path.join(output_dir, name, version)
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
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

        database_path = self.config.get('defaultDatabasePath')
        json_files = list_json_files(database_path)
        if not json_files:
            message_dialog(
                title="Open Database",
                text=f"No JSON files found in {database_path}/"
            ).run()
            return False

        options = [(f, f) for f in json_files] + [('esc', 'Back (Esc)')]
        db_file = full_screen_choice(
            "Open Database",
            options=options,
        )

        if db_file == 'esc':
            return False

        db_path = os.path.join(database_path, db_file)
        self.db = load_database(db_path)
        self.db_original = copy.deepcopy(self.db)
        self.current_db_path = db_path

        if self.db:
            # Load first module
            first_name = sorted(self.db.keys())[0]
            first_version = sorted(self.db[first_name].keys(), reverse=True)[0]
            self.load_current_module(first_name, first_version)

        return True

    def action_save_database(self, save_as=False):
        """Save the current database to a file.

        When save_as is True, always prompt for a new file path (Save As
        behaviour), pre-filling with the current path when available.
        When save_as is False, prompt only if no valid path is already set.
        """
        if not self.db:
            message_dialog(
                title="Save Database",
                text="Error: Database is empty. Nothing to save."
            ).run()
            return False

        if save_as or not (self.current_db_path and os.path.exists(self.current_db_path)):
            # Prompt user for a (new) path
            user_path = input_dialog(
                title="Save Database As",
                text="Enter path to save database (must end with .json):",
                default=self.current_db_path or "database/new-database.json"
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
            return False
        name = name.strip()
        if not name:
            message_dialog(title="Error", text="Module name cannot be empty.").run()
            return False

        version = input_dialog(
            title="Add Module",
            text="Enter version:",
            default=""
        ).run()

        if version is None:
            return False
        version = version.strip()
        if not version:
            message_dialog(title="Error", text="Version cannot be empty.").run()
            return False

        # Check if module already exists
        if name in self.db and version in self.db[name]:
            message_dialog(title="Error", text=f"Module {name} {version} already exists.").run()
            return False

        # Create new module
        if name not in self.db:
            self.db[name] = {}
        self.db[name][version] = self.ret_empty_module()

        # Load the new module
        self.load_current_module(name, version)
        return True

    def action_copy_module(self):
        """Copy the current module to a new name/version."""
        if not self.current_module_name:
            message_dialog(
                title="Copy Module",
                text="Error: No module selected."
            ).run()
            return False

        name = input_dialog(
            title="Copy Module",
            text="Enter new module name:",
            default=self.current_module_name
        ).run()

        if name is None:
            return False
        name = name.strip()
        if not name:
            message_dialog(title="Error", text="Module name cannot be empty.").run()
            return False

        version = input_dialog(
            title="Copy Module",
            text="Enter new version:",
            default=self.current_module_version
        ).run()

        if version is None:
            return False
        version = version.strip()
        if not version:
            message_dialog(title="Error", text="Version cannot be empty.").run()
            return False

        # Check if module already exists
        if name in self.db and version in self.db[name]:
            message_dialog(title="Error", text=f"Module {name} {version} already exists.").run()
            return False

        # Create copy
        if name not in self.db:
            self.db[name] = {}
        self.db[name][version] = copy.deepcopy(self.current_module)

        # Load the copy
        self.load_current_module(name, version)
        return True

    def action_delete_module(self):
        """Delete the current module."""
        if not self.current_module_name:
            message_dialog(
                title="Delete Module",
                text="Error: No module selected."
            ).run()
            return False

        choice = add_esc_to_dialog(button_dialog(
            title="Delete Module",
            text="Are you sure you want to delete this module?",
            buttons=[
                ("Yes", "yes"),
                ("No", "no")
            ]
        ), "no").run()
        if choice != "yes":
            return False

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

        return True

    def action_edit_module(self):
        """Edit the current module's details."""
        if not self.current_module_name:
            message_dialog(
                title="Edit Module",
                text="Error: No module selected."
            ).run()
            return False

        # Format display values with space alignment
        # Find the longest label for consistent alignment
        label_width = max(len("Conflicts"), len("Description"), len("Image Path"),
                        len("Bind Paths"), len("Flags"), len("Commands"),
                        len("Template"), len("Environment Vars")) + 4

        # Wrap long values for display (limit to 60 chars per line
        def wrap_value(val):
            if len(val) > 60:
                return '\n'.join(textwrap.wrap(val, width=60, replace_whitespace=False))
            return val
        
        # Format each option and its content
        def format_option(label, value):
            wrapped = wrap_value(value)
            # If wrapped has multiple lines, indent them
            if '\n' in wrapped:
                lines = [f"{label:<{label_width}}{wrapped.split(chr(10))[0]}"]
                lines.extend([' ' * (label_width + 4) + line for line in wrapped.split(chr(10))[1:]])
                return '\n'.join(lines)
            return f"{label:<{label_width}}{wrapped}"

        while True:
            envs = self.current_module.get('envs')

            # Get current values for display
            disp_conflicts = self.current_module.get('conflict')
            disp_description = self.current_module.get('module_whatis')
            disp_image_path = self.current_module.get('singularity_image')
            disp_bind_paths = self.current_module.get('singularity_bindpaths')
            disp_flags = self.current_module.get('singularity_flags')
            disp_commands = self.current_module.get('cmds')
            disp_template = self.current_module.get('template')

            # Format environment variables display
            if envs:
                disp_env_vars = ', '.join(f"{k}={v}" for k, v in envs.items())
                disp_env_vars = wrap_value(disp_env_vars)
            else:
                disp_env_vars = '(none)'

            choice = full_screen_choice(
                    "Edit Module:",
                    options=[
                        ('1', format_option("Conflicts", disp_conflicts)),
                        ('2', format_option("Description", disp_description)),
                        ('3', format_option("Image Path", disp_image_path)),
                        ('4', format_option("Bind Paths", disp_bind_paths)),
                        ('5', format_option("Flags", disp_flags)),
                        ('6', format_option("Commands", disp_commands)),
                        ('7', format_option("Template", disp_template)),
                        ('8', format_option("Environment Vars", disp_env_vars)),
                        ('esc', 'Back (Esc)'),
                    ],
                    body_text="Select a field to edit:",
                )

            if choice == 'esc':
                break

            if choice == '1':
                # Conflicts
                value = input_dialog(
                    title="Edit Conflicts",
                    text="Enter conflict modules (space-separated):",
                    default=self.current_module.get('conflict')
                ).run()
                if value is not None:
                    self.current_module['conflict'] = value.strip()

            elif choice == '2':
                # Description
                value = input_dialog(
                    title="Edit Description",
                    text="Enter software description:",
                    default=self.current_module.get('module_whatis')
                ).run()
                if value is not None:
                    self.current_module['module_whatis'] = value.strip()

            elif choice == '3':
                # Image Path
                value = input_dialog(
                    title="Edit Image Path",
                    text="Enter Singularity image path:",
                    default=self.current_module.get('singularity_image')
                ).run()
                if value is not None:
                    self.current_module['singularity_image'] = value.strip()

            elif choice == '4':
                # Bind Paths
                default_bind = self.config.get('defaultBindingPath')
                value = input_dialog(
                    title="Edit Bind Paths",
                    text=f"Enter additional paths to bind (default: {default_bind}):",
                    default=self.current_module.get('singularity_bindpaths')
                ).run()
                if value is not None:
                    self.current_module['singularity_bindpaths'] = value.strip()

            elif choice == '5':
                # Flags
                default_flags = self.config.get('defaultFlags')
                value = input_dialog(
                    title="Edit Flags",
                    text=f"Enter additional flags (default: {default_flags}):",
                    default=self.current_module.get('singularity_flags')
                ).run()
                if value is not None:
                    self.current_module['singularity_flags'] = value.strip()

            elif choice == '6':
                # Commands
                value = input_dialog(
                    title="Edit Commands",
                    text="Enter commands to map (space or newline separated):",
                    default=self.current_module.get('cmds')
                ).run()
                if value is not None:
                    self.current_module['cmds'] = value.strip()

            elif choice == '7':
                # Template
                value = input_dialog(
                    title="Edit Template",
                    text="Enter template file path:",
                    default=self.current_module.get('template')
                ).run()
                if value is not None:
                    self.current_module['template'] = value.strip()

            elif choice == '8':
                # Environment Variables
                self.edit_environment_variables()

        # Save to database
        self.update_db_from_form()
        return True

    def edit_environment_variables(self):
        """Edit environment variables for the current module."""
        envs = copy.deepcopy(self.current_module.get('envs'))

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
                            default=envs.get(key)
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
            return False

        # Name selection
        name_options = [(n, n) for n in sorted(name_list)] + [('esc', 'Back (Esc)')]
        name = full_screen_choice(
            "Select Module:",
            options=name_options,
        )

        if name == 'esc':
            return False

        # Version selection
        versions = sorted(self.db[name].keys(), reverse=True)
        ver_options = [(v, v) for v in versions] + [('esc', 'Back (Esc)')]
        version = full_screen_choice(
                f"Select Version for {name}:",
                options=ver_options,
            )

        if version == 'esc':
            return False

        self.load_current_module(name, version)
        return True

    def action_generate_key(self):
        """Generate a module key for the current module."""
        if not self.current_module_name:
            message_dialog(
                title="Generate Module Key",
                text="Error: No module selected."
            ).run()
            return False

        output_dir = self.config.get('defaultModKeyPath')

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

        output_dir = self.config.get('defaultModKeyPath')

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
        return fail_count == 0

    def action_preferences(self):
        """Edit preferences."""
        config = self.config

        while True:
            choice = full_screen_choice(
                    "Preferences",
                    options=[
                        ('1', 'Default database path'),
                        ('2', 'Default Singularity image directory'),
                        ('3', 'Default module key output directory'),
                        ('4', 'Default module key template'),
                        ('5', 'Always bind these paths'),
                        ('6', 'Always enable these flags'),
                        ('esc', 'Back (Esc)'),
                    ],
                )

            if choice == 'esc':
                break

            if choice == '1':
                value = input_dialog(
                    title="Edit Default Database Path",
                    text="Enter default directory for database files:",
                    default=config.get('defaultDatabasePath')
                ).run()
                if value is not None:
                    config['defaultDatabasePath'] = value.strip()

            elif choice == '2':
                value = input_dialog(
                    title="Edit Default Singularity Image Directory",
                    text="Enter default directory for Singularity images:",
                    default=config.get('defaultImagePath')
                ).run()
                if value is not None:
                    config['defaultImagePath'] = value.strip()

            elif choice == '3':
                value = input_dialog(
                    title="Edit Default Module Key Output Directory",
                    text="Enter default directory for generated module keys:",
                    default=config.get('defaultModKeyPath')
                ).run()
                if value is not None:
                    config['defaultModKeyPath'] = value.strip()

            elif choice == '4':
                value = input_dialog(
                    title="Edit Default Module Key Template",
                    text="Enter default module key template file path:",
                    default=config.get('defaultTemplate')
                ).run()
                if value is not None:
                    config['defaultTemplate'] = value.strip()

            elif choice == '5':
                value = input_dialog(
                    title="Always Bind These Paths",
                    text="Always bind these paths (comma-separated):",
                    default=config.get('defaultBindingPath')
                ).run()
                if value is not None:
                    config['defaultBindingPath'] = value.strip()

            elif choice == '6':
                value = input_dialog(
                    title="Always Enable These Flags",
                    text="Always enable these Singularity flags:",
                    default=config.get('defaultFlags')
                ).run()
                if value is not None:
                    config['defaultFlags'] = value.strip()

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

    def action_about(self):
        """Display the About dialog."""
        message_dialog(
            title="About",
            text=ABOUT
        ).run()

    # =================== Main Menu ================== ##

    def menu_main(self):
        """Display the main menu."""
        while True:
            choice = full_screen_choice(
                    "Main Menu",
                    options=[
                        ('1', 'File'),
                        ('2', 'Module'),
                        ('3', 'Preferences'),
                        ('4', 'About'),
                        ('esc', 'Exit (Esc)'),
                    ],
                )

            if choice == '1':
                self.menu_file()
            elif choice == '2':
                self.menu_module()
            elif choice == '3':
                self.action_preferences()
            elif choice == '4':
                self.action_about()
            elif choice == 'esc':
                if self.has_unsaved_changes():
                    if not self.confirm_save_before_continue():
                        continue
                    return True
                else:
                    return True

    def menu_file(self):
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
                    self.menu_module()
                    break
            elif choice == '2':
                if self.action_open_database():
                    self.menu_module()
                    break
            elif choice == '3':
                if self.action_save_database():
                    self.menu_module()
                    break
            elif choice == '4':
                if self.action_save_database(save_as=True):
                    self.menu_module()
                    break
            elif choice == 'esc':
                break

    def menu_module(self):
        """Display the module database menu (first level)."""
        while True:
            current_db_display = self.current_db_path if self.current_db_path else "(None)"
            choice = full_screen_choice(
                    "Module Menu",
                    options=[
                        ('1', 'Select Module'),
                        ('2', 'Add New Module'),
                        ('3', 'Generate All Module Keys from Database'),
                        ('esc', 'Back (Esc)'),
                    ],
                    body_text=f"Current database: {current_db_display}"
                )

            if choice == '1':
                if self.action_select_module():
                    self.menu_module_edit()
            elif choice == '2':
                if self.action_add_module():
                    self.menu_module_edit()
            elif choice == '3':
                self.action_generate_all_keys()
            elif choice == 'esc':
                break

    def menu_module_edit(self):
        """Display the module edit menu (second level, shown after selecting/adding a module)."""
        if not self.current_module_name:
            return False

        while True:
            module_display = f"{self.current_module_name} ({self.current_module_version})"
            choice = full_screen_choice(
                    "Module Edit Menu",
                    options=[
                        ('1', 'Edit Current Module'),
                        ('2', 'Copy Current Module'),
                        ('3', 'Delete Current Module'),
                        ('4', 'Generate Current Module Key'),
                        ('esc', 'Back (Esc)'),
                    ],
                    body_text=f"Current module: {module_display}"
                )

            if choice == '1':
                self.action_edit_module()
            elif choice == '2':
                self.action_copy_module()
            elif choice == '3':
                self.action_delete_module()
                # After deletion, return to module database menu
                return False
            elif choice == '4':
                self.action_generate_key()
            elif choice == 'esc':
                return False
        return True

    def run(self):
        """Run the CLI application. Requires prompt_toolkit (CLI_ENABLED)."""
        if not CLI_ENABLED:
            return
        # Main menu loop
        while True:
            exit_app = self.menu_main()
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
            output = args.output or cli.config.get('defaultModKeyPath')

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

        output = args.output or cli.config.get('defaultModKeyPath')

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
        description=f"{TITLE} (Singularity Integrated Module-key Producer for Loadable Environment MODules)"
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
    parser.add_argument(
        '--nodisplay',
        action='store_true',
        help='Force to run in terminal instead of GUI.'
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
