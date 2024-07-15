# SIMPLE-MOD (Singularity Integrated Module-key Producer for Loadable Environment MODules)

- [1. Introduction](#1-Introduction)
  - [1.1 About SIMPLE-MOD](#11-About-SIMPLE-MOD)
  - [1.2 Who is SIMPLE-MOD for](#12-Who-is-SIMPLE-MOD-for)
- [2. Installation](#2-Installation)
  - [2.1 Running with Python](#21-Running-with-Python)
  - [2.2 Running in a Singularity image](#22-Running-in-a-Singularity-image)
- [3. User Interface](#3-User-Interface)
  - [3.1 Menu Bar](#31-Menu-Bar)
  - [3.2 Module List](#32-Module-List)
  - [3.3 Module Details](#33-Module-Details)
  - [3.4 Generate Module Keys](#34-Generate-Module-Keys)
- [4. Contributors](#4-Contributors)

## 1. Introduction

### 1.1 About SIMPLE-MOD

**SIMPLE-MOD** (**S**ingularity **I**ntegrated **M**odule-key **P**roducer for **L**oadable **E**nvironment **MOD**ules) is a QT-based GUI tool to automatically generate module keys for easy access of container-based software packages.

Currently, SIMPLE-MOD supports two commonly used module systems through pre-written templates: 
- ***Environment Modules*** (https://github.com/cea-hpc/modules) 
- ***Lmod*** (https://github.com/TACC/Lmod)

Other support can be added by adding customized templates.

### 1.2 Who is SIMPLE-MOD for

SIMPLE-MOD is designed for HPC administrators who oversee software installation and deployment. Its purpose is to help administrators conveniently create module keys from software in Singularity/Apptainer container images, taking advantage of the installation-free portability. If your HPC systems use a module system (***Environment Modules*** or ***Lmod***) and Singularity/Apptainer, this may be your simple solution to deploy container-based software. This allows users to activate software with a simple ```module load``` command and use the executables as if they were installed natively, without needing to know they are using containers.

SIMPLE-MOD is most suitable for software accessible via a handful of executables. However, it is not suitable for all software or use cases. For example, it is not suitable for pure libraries, and may be not suitable for software that would be used as dependencies. It is at the administrators' discretion to determine which software packages can be deployed with SIMPLE-MOD. Administrators are also responsible for testing the deployed module keys on the clusters. The databases and templates provided with the code are for reference only, and the LSU HPC group shall not be held responsible for the installation, deployment, testing, and validation of the software.

SIMPLE-MOD is primarily designed for HPC administrators; however, interested users can also use it to generate customized module keys. Knowledge and permissions to set up customized module keys are required.


## 2. Installation

### 2.1 Running with Python (Recommended)

As a QT-based Python program, SIMPLE-MOD is installation-free. To run SIMPLE-MOD, simply run it with Python:

```
python simple-mod.py
```

It is tested with Python 3 and PyQt5 module as dependency. If PyQt5 is not installed on your system, please install it with pip:

```
pip install pyqt5
```

### 2.2 Running in a Singularity image

If for any reason you cannot run it with Python on your system (e.g., lack of dependencies and you do not have the permission to install), you may also build a SIMPLE-MOD container image and run it with Singularity/Apptainer. The recipe is provided in `singularity.def`. To build it with Singularity/Appatainer, please run the below command in terminal:

```
singularity build simple-mod.sif recipe.def
```

Once the image is build, you may run it with:

```
singularity run simple-mod.sif
```

Additional path binding may be required to save module databases and generate module keys in the desired paths. 


## 3. User Interface

The usage of SIMPLE-MOD shoul be straightforward and self-explanatory. Below is the GUI of SIMPLE-MOD:

![README](https://raw.githubusercontent.com/lsuhpchelp/SIMPLE-MOD/master/README.png)

### 3.1 Menu Bar

Menu Bar contains 3 menus:

- **_File_**: Create, open, and save module database (.json format).
- **_Settings_**: Change preferences.
- **_Help_**: About information.

### 3.2 Module List

- Select module name & version to edit.
- Create a new module or copy current module.
- Delete selected module.

### 3.3 Module Details

- **_Conflicts_**: Conflicted modules that cannot be loaded together. (Itself is already added by default)
- **_Software description_**: Software description.
- **_Singularity image path_**: Path to Singularity image. Can use remote path if the host system supports.
- **_Singularity binding paths_**: Binding paths ("-B"). Bound by default (can be changed in Settings): /home,/tmp,/work,/project,/usr/local/packages,/var/scratch.
- **_Additional Singularity flags_**: Additional flags to add (e.g., "--nv").
- **_Commands to map_**: Executables inside the container that need to be mapped as wrappers outside of the container. 
- **_Set up environmental variable_**: Set up additional environmental variable for the module, if needed.
- **_Module key template_**: Template to generate module keys. Default: ./template/template.tcl

### 3.4 Generate Module Keys

- **_Generate current module key_**: Generate one module key from the current open module.
- **_Generate all module keys from current database_**: Generate all module keys from the current open database. Database needs to be saved first.


## 4. Contributors

Main author: Dr. Jason Li ( jasonli3@lsu.edu )

