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

The `paravision` module consists of mainly the `utils.py` file that has some helper functions with respect to paraview's python API. Paraview's python scripting is powerful, but in my case I would have preferred a slightly higher level of abstraction to interact with.

Bundled along with module this is the `pvrun` script that handles running some built-in operations such as screenshotting, generating chromatograms, and calculating mass flux along the axial length of a chromatography column The built-ins are simply paraview python scripts that are executable themselves, but use `paravision.utils` for some sugar (ease of use). Since my work is regarding chromatography columns, we currently have the built-ins regarding that. Any custom plugin can also be run using the `-p or --plugin <custom-script.py>` arguments.

Eventually, ideally, we can move the current built-ins out into a separate chromatography-specific repository, and move the helper functions into their own files based on some categorization. 

This project was initially just written into one long script `vis.py` with global commandline args to specify certain options, then a small rewrite `paravis.py`, before ultimately becoming `paravision`. Keeping conceptually disparate operations in one file was too much after a while, and having them completely separate meant a lot of verbosity and copying which did no one any good. In its current state, I find it works well for me, though I know that it's not as polished as I would like it to be.

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
