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
        prompt, confirm, button_dialog, input_dialog,
        progress_dialog, radiolist_dialog, checkboxlist_dialog, message_dialog
    )
    CLI_ENABLED = True
except ImportError:
    CLI_ENABLED = False

# Constants
TITLE = "SIMPLE-MOD "
VERSION = "1.1.0"
DATABASE_DIR = "database"
MODULEKEY_DIR = "modulekey"
TEMPLATE_DIR = "template"


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


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title=""):
    """Print a formatted header."""
    clear_screen()
    print("=" * 60)
    if title:
        print(f"  {title}")
    print(f"  {TITLE}CLI v{VERSION}")
    print("=" * 60)
    print()


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
            if not confirm("You have unsaved changes. Discard them?"):
                return

        self.db = {}
        self.db_original = {}
        self.current_module_name = None
        self.current_module_version = None
        self.current_module = self.ret_empty_module()
        self.current_db_path = None

        print_header("New Database")
        print("New empty database created.")
        input("Press Enter to continue...")

    def action_open_database(self):
        """Open an existing database file."""
        if self.has_unsaved_changes():
            if not confirm("You have unsaved changes. Discard them?"):
                return

        json_files = list_json_files(DATABASE_DIR)
        if not json_files:
            print_header("Open Database")
            print(f"No JSON files found in {DATABASE_DIR}/")
            input("Press Enter to continue...")
            return

        db_file = radiolist_dialog(
            title="Open Database",
            text="Select a database file to open:",
            values=[(f, f) for f in json_files],
            ok_text="Open",
            cancel_text="Back"
        ).run()

        if db_file is None:
            return

        db_path = os.path.join(DATABASE_DIR, db_file)
        self.db = load_database(db_path)
        self.db_original = copy.deepcopy(self.db)
        self.current_db_path = db_path

        if self.db:
            # Load first module
            first_name = sorted(self.db.keys())[0]
            first_version = sorted(self.db[first_name].keys(), reverse=True)[0]
            self.load_current_module(first_name, first_version)

        print_header("Database Loaded")
        print(f"Loaded: {db_path}")
        print(f"Modules: {len(self.db)}")
        input("Press Enter to continue...")

    def action_save_database(self):
        """Save the current database to a file."""
        if not self.db:
            print_header("Save Database")
            print("Error: Database is empty. Nothing to save.")
            input("Press Enter to continue...")
            return

        if self.current_db_path and os.path.exists(self.current_db_path):
            # Auto-save to current path
            confirm_save = True
        else:
            # Let user choose path
            user_path = input_dialog(
                title="Save Database As",
                text="Enter path to save database (must end with .json):",
                default="database/new-database.json"
            ).run()

            if user_path is None:
                return

            if not user_path.endswith('.json'):
                user_path += '.json'

            self.current_db_path = user_path

        if save_database(self.current_db_path, self.db):
            self.db_original = copy.deepcopy(self.db)
            print_header("Database Saved")
            print(f"Saved to: {self.current_db_path}")
            input("Press Enter to continue...")
        else:
            print_header("Save Failed")
            print("Could not save the database.")
            input("Press Enter to continue...")

    def action_add_module(self):
        """Add a new module."""
        print_header("Add New Module")

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
        self.db_original = copy.deepcopy(self.db)

        # Load the new module
        self.load_current_module(name, version)

        print_header("Module Added")
        print(f"Created: {name} {version}")
        print("Edit the module details to configure it.")
        input("Press Enter to continue...")

    def action_copy_module(self):
        """Copy the current module to a new name/version."""
        if not self.current_module_name:
            print_header("Copy Module")
            print("Error: No module selected.")
            input("Press Enter to continue...")
            return

        print_header("Copy Module")

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
        self.db_original = copy.deepcopy(self.db)

        # Load the copy
        self.load_current_module(name, version)

        print_header("Module Copied")
        print(f"Copied {self.current_module_name} {self.current_module_version}")
        print(f"To: {name} {version}")
        input("Press Enter to continue...")

    def action_delete_module(self):
        """Delete the current module."""
        if not self.current_module_name:
            print_header("Delete Module")
            print("Error: No module selected.")
            input("Press Enter to continue...")
            return

        print_header("Delete Module")
        print(f"Module: {self.current_module_name} {self.current_module_version}")
        print()

        if not confirm("Are you sure you want to delete this module?"):
            return

        # Check for multiple versions
        if len(self.db[self.current_module_name]) > 1:
            # Delete only this version
            del self.db[self.current_module_name][self.current_module_version]
            self.db_original = copy.deepcopy(self.db)

            # Find next version
            versions = sorted(self.db[self.current_module_name].keys(), reverse=True)
            self.load_current_module(self.current_module_name, versions[0])
        else:
            # Delete entire module
            del self.db[self.current_module_name]
            self.db_original = copy.deepcopy(self.db)
            self.current_module_name = None
            self.current_module_version = None
            self.current_module = self.ret_empty_module()

        print_header("Module Deleted")
        print("Module has been deleted.")
        input("Press Enter to continue...")

    def action_edit_module(self):
        """Edit the current module's details."""
        if not self.current_module_name:
            print_header("Edit Module")
            print("Error: No module selected.")
            input("Press Enter to continue...")
            return

        while True:
            print_header(f"Edit Module: {self.current_module_name} {self.current_module_version}")

            # Display current values
            print("Current settings:")
            print(f"  [1] Conflicts:        {self.current_module.get('conflict', '')}")
            print(f"  [2] Description:      {self.current_module.get('module_whatis', '')}")
            print(f"  [3] Image Path:       {self.current_module.get('singularity_image', '')}")
            print(f"  [4] Bind Paths:       {self.current_module.get('singularity_bindpaths', '')}")
            print(f"  [5] Flags:            {self.current_module.get('singularity_flags', '')}")
            print(f"  [6] Commands:         {self.current_module.get('cmds', '')}")
            print(f"  [7] Template:         {self.current_module.get('template', './template/template.tcl')}")
            envs = self.current_module.get('envs', {})
            if envs:
                print(f"  [8] Environment Vars: {', '.join(envs.keys())}")
            else:
                print(f"  [8] Environment Vars: (none)")
            print()

            choice = input_dialog(
                title="Edit Module",
                text="Select field to edit (1-8), or 'q' to return:",
                default="1"
            ).run()

            if choice is None or choice.lower() == 'q':
                break

            try:
                choice = int(choice)
            except ValueError:
                continue

            if choice == 1:
                # Conflicts
                value = input_dialog(
                    title="Edit Conflicts",
                    text="Enter conflict modules (space-separated):",
                    default=self.current_module.get('conflict', '')
                ).run()
                if value is not None:
                    self.current_module['conflict'] = value.strip()

            elif choice == 2:
                # Description
                value = input_dialog(
                    title="Edit Description",
                    text="Enter software description:",
                    default=self.current_module.get('module_whatis', '')
                ).run()
                if value is not None:
                    self.current_module['module_whatis'] = value.strip()

            elif choice == 3:
                # Image Path
                value = input_dialog(
                    title="Edit Image Path",
                    text="Enter Singularity image path:",
                    default=self.current_module.get('singularity_image', '')
                ).run()
                if value is not None:
                    self.current_module['singularity_image'] = value.strip()

            elif choice == 4:
                # Bind Paths
                default_bind = self.config.get('defaultBindingPath', '/work,/project,/usr/local/packages,/var/scratch')
                value = input_dialog(
                    title="Edit Bind Paths",
                    text=f"Enter additional paths to bind (default: {default_bind}):",
                    default=self.current_module.get('singularity_bindpaths', '')
                ).run()
                if value is not None:
                    self.current_module['singularity_bindpaths'] = value.strip()

            elif choice == 5:
                # Flags
                default_flags = self.config.get('defaultFlags', '')
                value = input_dialog(
                    title="Edit Flags",
                    text=f"Enter additional flags (default: {default_flags}):",
                    default=self.current_module.get('singularity_flags', '')
                ).run()
                if value is not None:
                    self.current_module['singularity_flags'] = value.strip()

            elif choice == 6:
                # Commands
                value = input_dialog(
                    title="Edit Commands",
                    text="Enter commands to map (space or newline separated):",
                    default=self.current_module.get('cmds', '')
                ).run()
                if value is not None:
                    self.current_module['cmds'] = value.strip()

            elif choice == 7:
                # Template
                value = input_dialog(
                    title="Edit Template",
                    text="Enter template file path:",
                    default=self.current_module.get('template', './template/template.tcl')
                ).run()
                if value is not None:
                    self.current_module['template'] = value.strip()

            elif choice == 8:
                # Environment Variables
                self.edit_environment_variables()

        # Save to database
        self.update_db_from_form()
        self.db_original = copy.deepcopy(self.db)

    def edit_environment_variables(self):
        """Edit environment variables for the current module."""
        envs = copy.deepcopy(self.current_module.get('envs', {}))

        while True:
            clear_screen()
            print_header(f"Edit Environment Variables: {self.current_module_name} {self.current_module_version}")
            print()

            if envs:
                print("Current environment variables:")
                for i, (key, value) in enumerate(envs.items(), 1):
                    print(f"  [{i}] {key} = {value}")
                print()
            else:
                print("No environment variables set.")
                print()

            print("[A] Add new variable")
            print("[D] Delete variable")
            print("[Q] Return to edit module")

            choice = input("\nSelection: ").strip().upper()

            if choice == 'Q':
                self.current_module['envs'] = envs
                break
            elif choice == 'A':
                key = input("Variable name: ").strip()
                if key:
                    value = input("Variable value: ").strip()
                    if value:
                        envs[key] = value
            elif choice == 'D':
                if envs:
                    key = input("Enter variable name to delete: ").strip()
                    if key in envs:
                        del envs[key]
            else:
                try:
                    idx = int(choice) - 1
                    keys = list(envs.keys())
                    if 0 <= idx < len(keys):
                        key = keys[idx]
                        value = input(f"New value for {key}: ").strip()
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
            print_header("Select Module")
            print("No modules in database.")
            input("Press Enter to continue...")
            return

        # Name selection
        name = radiolist_dialog(
            title="Select Module",
            text="Choose a module to work with:",
            values=[(n, n) for n in name_list],
            ok_text="Select",
            cancel_text="Back"
        ).run()

        if name is None:
            return

        # Version selection
        versions = sorted(self.db[name].keys(), reverse=True)
        if len(versions) == 1:
            version = versions[0]
        else:
            version = radiolist_dialog(
                title=f"Select Version for {name}",
                text="Choose a version:",
                values=[(v, v) for v in versions],
                ok_text="Select",
                cancel_text="Back"
            ).run()

        if version is None:
            return

        self.load_current_module(name, version)

    def action_generate_key(self):
        """Generate a module key for the current module."""
        if not self.current_module_name:
            print_header("Generate Module Key")
            print("Error: No module selected.")
            input("Press Enter to continue...")
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
            print_header("Generate All Module Keys")
            print("Error: Database is empty.")
            input("Press Enter to continue...")
            return

        if self.has_unsaved_changes():
            if not confirm("You have unsaved changes. Save before generating?"):
                return
            self.action_save_database()

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

        print_header("Generation Complete")
        print(f"Successfully generated: {success_count} keys")
        print(f"Failed: {fail_count} keys")
        print(f"Output directory: {output_dir}")
        input("Press Enter to continue...")

    def action_preferences(self):
        """Edit preferences."""
        config = self.config

        while True:
            clear_screen()
            print_header("Preferences")
            print()

            print("Current preferences:")
            print(f"  [1] Default binding paths:   {config.get('defaultBindingPath', '/work,/project,/usr/local/packages,/var/scratch')}")
            print(f"  [2] Default flags:           {config.get('defaultFlags', '')}")
            print(f"  [3] Default image directory: {config.get('defaultImagePath', '')}")
            print(f"  [4] Default template:        {config.get('defaultTemplate', './template/template.tcl')}")
            print(f"  [5] Default modkey path:     {config.get('defaultModKeyPath', MODULEKEY_DIR)}")
            print()

            choice = input_dialog(
                title="Preferences",
                text="Select setting to change (1-5), or 'q' to return:",
                default="1"
            ).run()

            if choice is None or choice.lower() == 'q':
                break

            try:
                choice = int(choice)
            except ValueError:
                continue

            if choice == 1:
                value = input_dialog(
                    title="Edit Default Binding Paths",
                    text="Enter default paths to bind (comma-separated):",
                    default=config.get('defaultBindingPath', '/work,/project,/usr/local/packages,/var/scratch')
                ).run()
                if value is not None:
                    config['defaultBindingPath'] = value.strip()

            elif choice == 2:
                value = input_dialog(
                    title="Edit Default Flags",
                    text="Enter default Singularity flags:",
                    default=config.get('defaultFlags', '')
                ).run()
                if value is not None:
                    config['defaultFlags'] = value.strip()

            elif choice == 3:
                value = input_dialog(
                    title="Edit Default Image Directory",
                    text="Enter default directory for Singularity images:",
                    default=config.get('defaultImagePath', '')
                ).run()
                if value is not None:
                    config['defaultImagePath'] = value.strip()

            elif choice == 4:
                value = input_dialog(
                    title="Edit Default Template",
                    text="Enter default template file path:",
                    default=config.get('defaultTemplate', './template/template.tcl')
                ).run()
                if value is not None:
                    config['defaultTemplate'] = value.strip()

            elif choice == 5:
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
            print(f"Error saving preferences: {e}")
            input("Press Enter to continue...")

    # =================== Main Menu ================== ##

    def main_menu(self):
        """Display the main menu."""
        while True:
            clear_screen()
            print_header("SIMPLE-MOD CLI Main Menu")
            print()

            if self.current_module_name:
                print(f"Current: {self.current_module_name} {self.current_module_version}")
            else:
                print("No module selected")
            print()

            if self.has_unsaved_changes():
                print("[!] Unsaved changes detected")
            print()

            print("  [1] File")
            print("  [2] Module")
            print("  [3] Generate")
            print("  [4] Preferences")
            print("  [5] Exit")

            choice = input("\nSelection: ").strip()

            if choice == '1':
                self.file_menu()
            elif choice == '2':
                self.module_menu()
            elif choice == '3':
                self.generate_menu()
            elif choice == '4':
                self.action_preferences()
            elif choice == '5':
                if self.has_unsaved_changes():
                    if confirm("You have unsaved changes. Exit anyway?"):
                        return True
                else:
                    return True

    def file_menu(self):
        """Display the file menu."""
        while True:
            clear_screen()
            print_header("File Menu")
            print()

            print("  [1] New Database")
            print("  [2] Open Database")
            print("  [3] Save Database")
            print("  [4] Save Database As...")
            print("  [5] Back")

            choice = input("\nSelection: ").strip()

            if choice == '1':
                self.action_new_database()
            elif choice == '2':
                self.action_open_database()
            elif choice == '3':
                self.action_save_database()
            elif choice == '4':
                custom_path = input_dialog(
                    title="Save Database As",
                    text="Enter path to save database (must end with .json):",
                    default="database/new-database.json"
                ).run()
                if custom_path:
                    if not custom_path.endswith('.json'):
                        custom_path += '.json'
                    self.current_db_path = custom_path
                    self.action_save_database()
            elif choice == '5':
                break

    def module_menu(self):
        """Display the module menu."""
        while True:
            clear_screen()
            print_header("Module Menu")
            print()

            if self.db:
                print(f"Database contains {len(self.db)} module(s)")
                print()

            print("  [1] Select Module")
            print("  [2] Add New Module")
            print("  [3] Copy Current Module")
            print("  [4] Delete Current Module")
            print("  [5] Edit Current Module")
            print("  [6] Back")

            choice = input("\nSelection: ").strip()

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
            elif choice == '6':
                break

    def generate_menu(self):
        """Display the generate menu."""
        while True:
            clear_screen()
            print_header("Generate Menu")
            print()

            if self.current_module_name:
                print(f"Current module: {self.current_module_name} {self.current_module_version}")
            else:
                print("No module selected")
            print()

            print("  [1] Generate Current Module Key")
            print("  [2] Generate All Module Keys")
            print("  [3] Back")

            choice = input("\nSelection: ").strip()

            if choice == '1':
                self.action_generate_key()
            elif choice == '2':
                self.action_generate_all_keys()
            elif choice == '3':
                break

    def run(self):
        """Run the CLI application."""
        print_header("Welcome to SIMPLE-MOD CLI")
        print()
        print("Loading configuration...")
        print()

        # Check for prompt_toolkit
        if not CLI_ENABLED:
            print("ERROR: prompt_toolkit is not installed!")
            print("Please install it with: pip install prompt_toolkit")
            print()
            print("To use basic input mode, run:")
            print("  python simple-mod-cli.py")
            print()
            print("Press Enter to exit...")
            input()
            return

        # Load existing database if available
        json_files = list_json_files(DATABASE_DIR)
        if json_files:
            print(f"Found {len(json_files)} database file(s) in {DATABASE_DIR}/")
            load_existing = confirm("Load existing database?")

            if load_existing:
                db_file = radiolist_dialog(
                    title="Load Database",
                    text="Select a database to load:",
                    values=[(f, f) for f in json_files],
                    ok_text="Load",
                    cancel_text="Skip"
                ).run()

                if db_file:
                    db_path = os.path.join(DATABASE_DIR, db_file)
                    self.db = load_database(db_path)
                    self.db_original = copy.deepcopy(self.db)
                    self.current_db_path = db_path

                    if self.db:
                        first_name = sorted(self.db.keys())[0]
                        first_version = sorted(self.db[first_name].keys(), reverse=True)[0]
                        self.load_current_module(first_name, first_version)

        print()
        print("Press Enter to continue to main menu...")
        input()

        # Main menu loop
        while True:
            exit_app = self.main_menu()
            if exit_app:
                break

        print_header("Goodbye!")

    def run_basic_mode(self):
        """Run the CLI in basic input mode (without prompt_toolkit)."""
        print_header("SIMPLE-MOD CLI - Basic Mode")
        print()
        print("Note: This is basic input mode without interactive selection.")
        print()

        while True:
            clear_screen()
            print_header("SIMPLE-MOD CLI - Basic Mode")
            print()

            print("1. New Database")
            print("2. Open Database")
            print("3. Save Database")
            print("4. Add Module")
            print("5. Edit Module")
            print("6. Generate Key")
            print("7. Generate All Keys")
            print("8. Exit")

            choice = input("\nSelection: ").strip()

            if choice == '1':
                self.action_new_database()
            elif choice == '2':
                self.action_open_database()
            elif choice == '3':
                self.action_save_database()
            elif choice == '4':
                self.action_add_module()
            elif choice == '5' and self.current_module_name:
                self.action_edit_module()
            elif choice == '6' and self.current_module_name:
                self.action_generate_key()
            elif choice == '7':
                self.action_generate_all_keys()
            elif choice == '8':
                if self.has_unsaved_changes():
                    if confirm("You have unsaved changes. Exit anyway?"):
                        break
                else:
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
            print()
            print("To use basic input mode without prompt_toolkit:")
            print("  python -c \"import simple_mod_cli; cli = simple_mod_cli.SimpleModCLI(); cli.run_basic_mode()\"")
            sys.exit(1)

        try:
            cli.run()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
