# Paravision

A rewrite of vis.py and paravis.py scripts into a more modular and reusable format. Documentation in source.

# Usage

```
pvrun --chromatogram full -np 48
```

# Design

## Top level actions
- --chromatogram ['Volume', 'Area']
- --animate
- --screenshot
- --column-snapshot 
- --volume-integral
- --bead-loading
- --radial-shell-integrate <number_of_regions>
- --shell_chromatograms <number_of_regions>
- --mass-flux <number_of_slices>

## Pipeline actions
- project
- screenshot

## Notes and references
- When colorby(none) doesn't work in some cases: https://discourse.paraview.org/t/colorby-rep-value-none-results-in-runtimeerror/6263

## TODO
- [TASK] incorporate confighandler fully. Use yaml configs, the commandline args are getting too long
    - `pvrun --chromatogram full config.yaml`
