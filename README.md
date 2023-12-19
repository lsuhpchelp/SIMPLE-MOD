# CAMP (Containerized Application Modulekey Producer)

- [1. Introduction](#1-Introduction)
  - [1.1 About CAMP](#11-About-CAMP)
  - [1.2 Who is CAMP for](#12-Who-is-CAMP-for)
- [2. Installation](#2-Installation)
  - [2.1 Running with Python](#21-Running-with-Python)
  - [2.2 Running in a Singularity image](#22-Running-in-a-Singularity-image)
- [3. Contributors](#3-Contributors)

## 1. Introduction

### 1.1 About CAMP

CAMP (Containerized Application Modulekey Producer) is a QT-based GUI software tool to automatically generate module keys for container-based software packages. 

### 1.2 Who is CAMP for

CAMP is designed for HPC administrators who oversee software installation and deployment. Its purpose is to help administrators conveniently create module keys from software in Singularity container images, taking advantage of the installation-free portability. If your HPC systems use a module system (TCL or LUA-based) and Singularity/Apptainer, this may be your simple solution to deploy container-based software. This allows users to activate software with a simple ```module load``` command and use the executables as if they were installed natively, without needing to know they are using containers.

CAMP is most suitable for software accessible via a handful of executables. However, it is not suitable for all software or use cases. For example, it is not suitable for pure libraries, and may be not suitable for software that would be used as dependencies. It is at the administrators' discretion to determine which software packages can be deployed with CAMP. Administrators are also responsible for testing the deployed module keys on the clusters. The databases and templates provided with the code are for reference only, and the LSU HPC group shall not be held responsible for the installation, deployment, testing, and validation of the software.


## 2. Installation

### 2.1 Running with Python

As a QT-based Python program, CAMP is installation-free. To run CAMP, simply run it with Python:

```
python camp.py
```

It is tested with Python 3 and PyQt5 module as dependency. If PyQt5 is not installed on your system, please install it with pip:

```
pip install pyqt5
```

### 2.2 Running in a Singularity image

If for any reason you cannot run it with Python on your system (e.g., lack of dependencies and you do not have the permission to install), you may also build a CAMP container image and run it with Singularity/Apptainer. The recipe is provided in `singularity.def`. To build it with Singularity/Appatainer, please run the below command in terminal:

```
singularity build camp.sif singularity.def
```

Once the image is build, you may run it with:

```
singularity run camp.sif
```


## 3. Contributors

Main author: Dr. Jason Li ( jasonli3@lsu.edu )

