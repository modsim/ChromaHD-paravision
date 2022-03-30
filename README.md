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
pvrun --chromatogram <conc.pvtu> --flow <flow.pvtu> [--flow-resample] --type full

# Save a screenshot of the domain after projection for scalar_0
pvrun --screenshot --project clip Plane 0.5 x -s scalar_0

# In case of a parallel, pvbatch run
pvrun -np 64 --volume-integral
# The above command is equivalent to mpiexec -np 64 /path/to/volume-integral.py

pvrun -np64 --column-snapshot <pvtu>
```

# Design

There are some top-level flags to perform top-level actions such as taking a screenshot, calculating the chromatogram, etc. These files are written to be independently runnable python scripts. Some utility wrappers around paraview's python scripting are found in `utils.py` and can be accessed by the top-level action scripts to make life easier.

The `pvrun` script takes user input, processes the top-level flags and runs the corresponding action script in a `subprocess.run()` call, passing on the environment variables.

Currently, `mpirun/mpiexec` is the only possible MPI runner.

## Configuration
- Defaults are specified in the app (configHandler.py)
- if `--config config.yaml` is passed, the file is loaded
- then commandline args are processed. If any are passed, they overwrite the previous args from config/default.
- CLI args parsing is done in 3 steps:
    - pvrun: top level args
    - plugin: general args parsing
    - plugin: specific args parsing

Here plugin refers to the top-level scripts that perform some action.

## Top level actions
- `--chromatogram`
- `--animate`
- `--screenshot`
- `--column-snapshot`
- `--column-snapshot_fast`
- `--volume-integral`
- `--bead-loading`
- `--radial-shell-integrate`
- `--mass-flux`
- `--shell_chromatograms`

## Pipeline actions
- project
- screenshot

# Notes and references
- When colorby(none) doesn't work in some cases: https://discourse.paraview.org/t/colorby-rep-value-none-results-in-runtimeerror/6263
- [ParaView, OpenGL, OSMESA](https://www.paraview.org/Wiki/ParaView/ParaView_And_Mesa_3D)
- [More about ParaView rendering backends](https://kitware.github.io/paraview-docs/v5.9.0/cxx/Offscreen.html)
- There's a change to the ParaView threshold range API between 5.9 and 5.10. 
- pvpython 5.10.0 messes with passed short args. Makes `-sb` into `--sb` and ruins things. Pass the long args to circumvent.
- `--colormap` accepts a string that will be fuzzymatched to existing colormaps in ParaView, and then in ScientificColourMaps7

# Colormaps
For chromatography, we need a colormap that has dark colors representing higher concentration. Usual colormaps go with increasing lightness. Also, for x-y flow, we need a diverging map, and then linear maps for everything else. So in publication, we need matching diverging and linear maps.

- `vik` (diverging) and `bilbao` (linear) match
- `BrBG` (div) and `Linear YGB` (lin) match
- `Rainbow Uniform` is a diverging map around yellow. It looks good for our flow sims because it shows hotspots clearly thanks to having multiple hues. Similarly, for our mass transfer sims it shows the concentration fronts very well.
