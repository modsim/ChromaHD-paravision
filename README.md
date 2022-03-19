# Paravision

A rewrite of vis.py and paravis.py scripts into a more modular and reusable format. Documentation in source.

# Dependencies
- ParaView with MPI (preferrably headless)

# Installation 

## Manual

Install with pip: 
```
pip install .
```

## Nix

Just run `nix-shell /path/to/shell.nix` to install dependencies (mainly paraview) and drop into a shell with paravision.

> NOTE: A headless OSMESA version of ParaView will be built from source this way. You can also remove the paraview override in `shell.nix` to get the binary version, but that might have issues with OpenGL (it's a nix thing). If you want to use your own version of ParaView, just remove all mentions of paraview from shell.nix and ensure your environment variables are set during runtime.

# Usage
Examples: 
```
# Calculate chromatogram (optional flag to resample flow data on conc mesh)
pvrun --chromatogram full <conc.pvtu> --flow <flow.pvtu> [--flow-resample]

# Save a screenshot of the domain after projection for scalar_0
pvrun --screenshot --project clip Plane 0.5 x -s scalar_0

# In case of a parallel, pvbatch run
pvrun -np 64 --volume-integral
# The above command is equivalent to mpiexec -np 64 /path/to/volume-integral.py
```

# Design

There are some top-level flags to perform top-level actions such as taking a screenshot, calculating the chromatogram, etc. These files are written to be independently runnable python scripts. Some utility wrappers around paraview's python scripting are found in `utils.py` and can be accessed by the top-level action scripts to make life easier.

The `pvrun` script takes user input, processes the top-level flags and runs the corresponding action script in a `subprocess.run()` call, passing on the environment variables.

Every top-level script looks for `.pvtu` files in the current directory unless files are specified on the CLI.

Currently, `mpirun/mpiexec` is the only possible MPI runner.

## Top level actions
- `--chromatogram ['full', 'shells']`
- `--animate`
- `--screenshot`
- `--column-snapshot`
- `--column-snapshot_fast`
- `--volume-integral`
- `--bead-loading`
- `--radial-shell-integrate <number_of_regions>`
- `--mass-flux <number_of_slices>`
- `--shell_chromatograms <number_of_regions>`

## Pipeline actions
- project
- screenshot

## Notes and references
- When colorby(none) doesn't work in some cases: https://discourse.paraview.org/t/colorby-rep-value-none-results-in-runtimeerror/6263
- [ParaView, OpenGL, OSMESA](https://www.paraview.org/Wiki/ParaView/ParaView_And_Mesa_3D)
- [More about ParaView rendering backends](https://kitware.github.io/paraview-docs/v5.9.0/cxx/Offscreen.html)
- There's a change to the ParaView threshold range API between 5.9 and 5.10. 

## TODO
- [TASK] incorporate confighandler fully. Use yaml configs, the commandline args are getting too long
    - `pvrun --chromatogram full config.yaml`
