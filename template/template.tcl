#%Module

# =====================================================================
# Generated by CAMP (Containerized Application Modulekey Producer)
# Developer: Jason Li (jasonli3@lsu.edu)
# =====================================================================

# ---------------------------------------------------------------------
# Software specific information
# ---------------------------------------------------------------------

# Conflicts
conflict $modName $conflict

# Module information
module-whatis $whatis
module-version $modVersion

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
# Module key setup template
# ---------------------------------------------------------------------

# Combine Singularity exec command
set singularity_exec "singularity exec -B $SINGULARITY_BINDPATHS $SINGULARITY_FLAGS $SINGULARITY_IMAGE"

# Overwrite the list of commands upon loading
if { [ module-info mode load ] } {
    foreach cmd $cmds {
        if { [ module-info shelltype csh ] } {
            puts "alias $cmd $singularity_exec $cmd $*; "
        } elseif { [ module-info shelltype sh ] } {
            puts "$cmd () {"
            puts "    $singularity_exec $cmd $@"
            puts "}"
            #puts "export -f $cmd"
        }
    }
}

# Unset commands upon unloading
if { [ module-info mode unload ] } {
    foreach cmd $cmds {
        if { [ module-info shelltype csh ] } {
            puts "unalias $cmd"
        } elseif { [ module-info shelltype sh ] } {
            puts "unset -f $cmd"
        }
    }
}

# For "module help" and "module load"
if { [ module-info mode help ] || [ module-info mode load ] || [ module-info mode display ] } {
    puts stderr "
\[ Help information \]

1. You may use below commands as normal:
$cmds
2. Those commands may only run on computing nodes (not available on head nodes). Make sure you start a job!
"
}
proc ModulesHelp {} {
}
