# SIMPLE-MOD (Singularity Integrated Module-key Producer for Loadable Environment MODules)

- [1. Introduction](#1-Introduction)
  - [1.1 About SIMPLE-MOD](#11-About-SIMPLE-MOD)
  - [1.2 Who is SIMPLE-MOD for](#12-Who-is-SIMPLE-MOD-for)
- [2. Installation](#2-Installation)
  - [2.1 Dependencies](#21-Dependencies)
  - [2.2 Running with Python](#22-Running-with-Python)
  - [2.3 Running with Singularity/Apptainer](#23-Running-with-SingularityApptainer)
- [3. Running SIMPLE-MOD](#3-Running-SIMPLE-MOD)
  - [3.1 GUI Mode (Default)](#31-GUI-Mode-Default)
    - [3.1.1 Menu Bar](#311-Menu-Bar)
    - [3.1.2 Module List](#312-Module-List)
    - [3.1.3 Module Details](#313-Module-Details)
    - [3.1.4 Generate Module Key(s)](#314-Generate-Module-Keys)
  - [3.2 CLI Interactive Mode](#32-CLI-Interactive-Mode)
    - [3.2.1 Launching](#321-Launching)
    - [3.2.2 Navigation](#322-Navigation)
    - [3.2.3 Menu Tree](#323-Menu-Tree)
    - [3.2.4 Module Fields](#324-Module-Fields)
  - [3.3 CLI Command Mode](#33-CLI-Command-Mode)
    - [3.3.1 Launching](#331-Launching)
    - [3.3.2 Commands and Options](#332-Commands-and-Options)
    - [3.3.3 Examples](#333-Examples)
- [4. Contributors](#4-Contributors)
- [5. Cite this work](#5-Cite-this-work)

## 1. Introduction

### 1.1 About SIMPLE-MOD

**SIMPLE-MOD** (**S**ingularity **I**ntegrated **M**odule-key **P**roducer for **L**oadable **E**nvironment **MOD**ules) is a Python tool to automatically generate module keys for easy access of container-based software packages. It supports three operation modes:

- **GUI mode** (default) — a Qt-based graphical interface.
- **CLI interactive mode** — a full-screen terminal UI powered by `prompt_toolkit`, suitable for headless or remote environments.
- **CLI command mode** — a non-interactive command-line interface for scripting and automation.

Currently, SIMPLE-MOD supports two commonly used module systems through pre-written templates:
- ***Environment Modules*** (https://github.com/cea-hpc/modules)
- ***Lmod*** (https://github.com/TACC/Lmod)

Other support can be added by adding customized templates.

### 1.2 Who is SIMPLE-MOD for

SIMPLE-MOD is designed for HPC administrators who oversee software installation and deployment. Its purpose is to help administrators conveniently create module keys from software in Singularity/Apptainer container images, taking advantage of the installation-free portability. If your HPC systems use a module system (***Environment Modules*** or ***Lmod***) and Singularity/Apptainer, this may be your simple solution to deploy container-based software. This allows users to activate software with a simple ```module load``` command and use the executables as if they were installed natively, without needing to know they are using containers.

SIMPLE-MOD is most suitable for software accessible via a handful of executables. However, it is not suitable for all software or use cases. For example, it is not suitable for pure libraries, and may be not suitable for software that would be used as dependencies. It is at the administrators' discretion to determine which software packages can be deployed with SIMPLE-MOD. Administrators are also responsible for testing the deployed module keys on the clusters. The databases and templates provided with the code are for reference only, and the LSU HPC group shall not be held responsible for the installation, deployment, testing, and validation of the software.

SIMPLE-MOD is primarily designed for HPC administrators; however, interested users can also use it to generate customized module keys. Knowledge and permissions to set up customized module keys are required.


## 2. Installation

### 2.1 Dependencies

SIMPLE-MOD requires **Python 3**. Additional dependencies depend on the mode you want to use:

| Mode | Dependency | Install |
|------|-----------|---------|
| GUI | PyQt6 or PyQt5 | `pip install pyqt6` or `pip install pyqt5` |
| CLI interactive | prompt_toolkit | `pip install prompt_toolkit` |
| CLI command | *(none beyond Python 3)* | — |

The GUI automatically detects the available PyQt version, preferring PyQt6. If Qt libraries are not available via pip, you can use Conda:

```bash
# PyQt6 via conda
conda install pyqt6 -c conda-forge

# Or PyQt5 via conda
conda install pyqt -c conda-forge
```

### 2.2 Running with Python

SIMPLE-MOD is installation-free. The recommended way to launch it is through the unified launcher script `simple-mod`:

```bash
./simple-mod
```

The launcher automatically selects the best available mode:
- With **no arguments**: tries the GUI first; falls back to the CLI interactive mode if the GUI cannot start (e.g., no display available). `prompt_toolkit` will be installed automatically if needed.
- With **arguments**: forces CLI mode and passes all arguments to `simple-mod-cli.py`.

You can also launch each mode directly:

```bash
# GUI mode
python3 simple-mod.py

# CLI interactive mode
python3 simple-mod-cli.py

# CLI command mode (see Section 3.3 for options)
python3 simple-mod-cli.py --cmd gen-all --database database/mydb.json
```

### 2.3 Running with Singularity/Apptainer

If for any reason you cannot run it with Python on your system (e.g., lack of dependencies and you do not have the permission to install), you may also build a SIMPLE-MOD container image and run it with Singularity/Apptainer. The recipe is provided in `recipe.def`. To build it with Singularity/Apptainer, please run the below command in terminal:

```bash
singularity build simple-mod.sif recipe.def
```

Once the image is built, you may run it with:

```bash
singularity run simple-mod.sif
```

Additional path binding may be required to save module databases and generate module keys in the desired paths.


## 3. Running SIMPLE-MOD

### 3.1 GUI Mode (Default)

The GUI mode is the default when running `./simple-mod` on a system with a display. Below is the GUI of SIMPLE-MOD:

![README](https://raw.githubusercontent.com/lsuhpchelp/SIMPLE-MOD/master/README.png)

#### 3.1.1 Menu Bar

| Menu | Description |
|------|-------------|
| **File** | Create, open, and save module database (.json format). **Save Database** (`Ctrl+S`) overwrites the current file; **Save Database As...** (`Ctrl+Shift+S`) saves to a new path. |
| **Settings** | Change preferences (default paths, binding paths, flags, template, etc.). |
| **Help** | About information. |

#### 3.1.2 Module List

| Action | Description |
|--------|-------------|
| Select | Choose a module name & version to edit. |
| Create / Copy | Create a new module or copy the current module. |
| Delete | Delete the selected module. |

#### 3.1.3 Module Details

All changes are automatically saved to the in-memory database as you type. Unsaved changes (relative to the last saved file) are indicated by a `*` in the window title.

| Field | Description |
|-------|-------------|
| Conflicts | Conflicted modules that cannot be loaded together. (Itself is already added by default.) |
| Software description | Software description. |
| Singularity image path | Path to Singularity image. Can use a remote path if the host system supports it. |
| Singularity binding paths | Additional binding paths ("-B") appended to the default paths set in Preferences. |
| Additional Singularity flags | Additional flags to add (e.g., `--nv` for GPU support). |
| Commands to map | Executables inside the container that need to be mapped as wrappers outside of the container. |
| Environment variables | Set up additional environment variables for the module, if needed. |
| Module key template | Template to generate module keys. Default: `./template/template.tcl` |

#### 3.1.4 Generate Module Key(s)

| Button | Description |
|--------|-------------|
| Generate current module key | Generate one module key from the currently open module. |
| Generate all module keys from current database | Generate all module keys from the currently open database. |


### 3.2 CLI Interactive Mode

The CLI interactive mode provides a full-screen terminal UI equivalent to the GUI, suitable for headless servers or SSH sessions without X forwarding.

#### 3.2.1 Launching

```bash
# Via unified launcher (auto-selected when GUI is unavailable)
./simple-mod

# Directly
python3 simple-mod-cli.py
```

Requires `prompt_toolkit`:

```bash
pip install prompt_toolkit
```

#### 3.2.2 Navigation

All screens are full-screen radio-list dialogs. Navigation controls:

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move selection |
| `Enter` | Confirm selection |
| `Esc` / `Ctrl+C` | Go back / cancel |

Text-input dialogs accept free-form text and are dismissed with `Enter` (confirm) or `Esc` (cancel).

#### 3.2.3 Menu Tree

```
Main Menu
├── File
│   ├── New Database
│   ├── Open Database          (lists JSON files from default database directory)
│   ├── Save Database          (overwrites current file; prompts for path if new)
│   ├── Save Database As...    (always prompts for a new path)
│   └── Back (Esc)
│
├── Module
│   ├── Select Module          (radio list of all modules in the database)
│   │   └── → Module Edit Menu
│   │       ├── Edit Current Module
│   │       │   ├── Conflicts
│   │       │   ├── Description
│   │       │   ├── Image Path
│   │       │   ├── Bind Paths
│   │       │   ├── Flags
│   │       │   ├── Commands
│   │       │   ├── Template
│   │       │   ├── Environment Vars
│   │       │   │   ├── [variable name = value]  (click to edit value)
│   │       │   │   ├── Add new variable
│   │       │   │   ├── Delete variable
│   │       │   │   └── Back (Esc)
│   │       │   └── Back (Esc)
│   │       ├── Copy Current Module
│   │       ├── Delete Current Module
│   │       ├── Generate Current Module Key
│   │       └── Back (Esc)
│   │
│   ├── Add New Module         (prompts for name + version)
│   │   └── → Module Edit Menu  (same sub-tree as above)
│   │
│   ├── Generate All Module Keys from Database
│   └── Back (Esc)
│
├── Preferences
│   ├── Default database path
│   ├── Default Singularity image directory
│   ├── Default module key output directory
│   ├── Default module key template
│   ├── Always bind these paths
│   ├── Always enable these flags
│   └── Back (Esc)              (saves preferences to ~/.simple-modrc on exit)
│
├── About
└── Exit (Esc)                  (prompts to save if there are unsaved changes)
```

#### 3.2.4 Module Fields

The fields available when editing a module are the same as in the GUI:

| Field | Description |
|-------|-------------|
| Conflicts | Space-separated list of conflicting module names |
| Description | Software description (`module whatis`) |
| Image Path | Path to the Singularity/Apptainer image |
| Bind Paths | Extra paths to bind (appended to the default bind paths from Preferences) |
| Flags | Extra Singularity flags (e.g., `--nv`) |
| Commands | Executables to expose as wrappers (space or newline separated) |
| Template | Path to the Tcl template file |
| Environment Vars | Additional environment variables (`setenv KEY VALUE`) |


### 3.3 CLI Command Mode

CLI command mode is non-interactive and suitable for scripting and automation pipelines.

#### 3.3.1 Launching

```bash
python3 simple-mod-cli.py --cmd <command> [options]

# Or via the unified launcher (any argument forces CLI mode)
./simple-mod --cmd <command> [options]
```

#### 3.3.2 Commands and Options

| Option | Description |
|--------|-------------|
| `-d`, `--database FILE` | Path to database JSON file to load |
| `-c`, `--cmd COMMAND` | Command to execute: `gen-key` or `gen-all` |
| `-o`, `--output DIR` | Output directory for generated module key files |
| `--name NAME` | Module name (required for `gen-key`) |
| `--version VERSION` | Module version (required for `gen-key`) |
| `--nodisplay` | Force terminal mode instead of GUI (used internally by the launcher) |

**Commands:**

- `gen-key` — Generate a single module key for the specified name and version.
- `gen-all` — Generate module keys for every module in the database.

#### 3.3.3 Examples

```bash
# Generate a module key for a specific module
python3 simple-mod-cli.py \
    --cmd gen-key \
    --database database/mydb.json \
    --name python \
    --version 3.11.0 \
    --output modulekey/

# Generate all module keys from a database
python3 simple-mod-cli.py \
    --cmd gen-all \
    --database database/mydb.json \
    --output modulekey/

# Use the unified launcher (same arguments work)
./simple-mod --cmd gen-all --database database/mydb.json --output modulekey/
```

Output files are written to `<output>/<name>/<version>` (no extension), matching the convention expected by Environment Modules and Lmod.


## 4. Contributors

Main author: Dr. Jason Li ( jasonli3@lsu.edu )

## 5. Cite this work

Jianxiong Li. 2024. "_Transforming Container Experience: Turning Singularity Images into Loadable Environment Modules_". In Practice and Experience in Advanced Research Computing 2024: Human Powered Computing (PEARC '24). Association for Computing Machinery, New York, NY, USA, Article 98, 1–2. https://doi.org/10.1145/3626203.3670551

