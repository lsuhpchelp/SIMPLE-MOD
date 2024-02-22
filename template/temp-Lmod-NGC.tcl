#%Module

# =====================================================================
# Generated by CAMP (Containerized Application Modulekey Producer)
# Developer: Jason Li (jasonli3@lsu.edu)
# Description: 
#       1) This module template is tested with Lmod
#           >= 8.7.34. See https://github.com/TACC/Lmod
#          May not be compatible with different module systems.
#       2) This template generates wrapper scripts in users' /work
#          directory, and works with MPI-enabled software packages.
# =====================================================================

# ---------------------------------------------------------------------
# Software specific information
# ---------------------------------------------------------------------

# Conflicts
conflict $modName $conflict

# Module information
module-whatis Description: $whatis
module-whatis Version: $modVersion

# Singularity options
set SINGULARITY_IMAGE "$singularity_image"
set SINGULARITY_BINDPATHS "$singularity_bindpaths"
set SINGULARITY_FLAGS "$singularity_flags"

# List of commands to overwrite
set cmds {
$cmds_dummy
}

# Set environment varialbles
$envs

# ---------------------------------------------------------------------
# Module key setup
# ---------------------------------------------------------------------

# Combine Singularity exec command
set singularity_exec "singularity run -B $SINGULARITY_BINDPATHS $SINGULARITY_FLAGS --pwd \$PWD $SINGULARITY_IMAGE"

# Set wrapper directory
file mkdir /work/$env(USER)/.modulebin/$modName/$modVersion
prepend-path PATH /work/$env(USER)/.modulebin/$modName/$modVersion

# Create wrappers when the module is loaded
if { [ module-info mode load ] } {

    # If it is csh type shell
    if { [module-info shelltype] == "csh" } {
    
        # Find shell header
        #puts "setenv shellheader '#\\!/bin/'`ps -p \$\$ -o comm=`;"
        #puts "if ( ! \$?prompt ) setenv shellheader `head -n1 \$0`;"
    
        # Create wrappers for each command
        foreach cmd $cmds {
            puts "echo '#\\!/bin/bash' > /work/\$USER/.modulebin/$modName/$modVersion/$cmd;"
            puts "echo '$singularity_exec $cmd $@' >> /work/\$USER/.modulebin/$modName/$modVersion/$cmd;"
            puts "chmod u+x /work/\$USER/.modulebin/$modName/$modVersion/$cmd;"
        }
        
        # Refresh cache (only for csh type shell)
        puts "rehash;"
        
        # Unset shell header variable
        #puts "unsetenv shellheader;"
        
    # If it is sh type shell
    } elseif { [module-info shelltype] == "sh" } {
    
        # Find shell header
        #puts "\[\[ -t 0 \]\] && shellheader='#!/bin/'`ps -p \$\$ -o comm=` || shellheader=`head -n1 \$0`;"
    
        # Create wrappers for each command
        foreach cmd $cmds {
            puts "echo '#!/bin/bash' > /work/\$USER/.modulebin/$modName/$modVersion/$cmd;"
            puts "echo '$singularity_exec $cmd $@' >> /work/\$USER/.modulebin/$modName/$modVersion/$cmd;"
            puts "chmod u+x /work/\$USER/.modulebin/$modName/$modVersion/$cmd;"
        }
        
        # Unset shell header variable
        #puts "unset shellheader;"
    }
}

# Currently, wrappers will not be deleted to avoid unwanted issues.

# For "module help" and "module load"
proc ModulesHelp {} {
    global cmds
    puts stderr "
    
\[ Help information \]

1. This module only works on computing nodes (not available on head nodes). Make sure you start a job!

2. Below executables are available:
$cmds"
}
if { [ module-info mode load ]} {
    ModulesHelp
}
