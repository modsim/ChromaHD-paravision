# Paravision

A rewrite of vis.py and paravis.py scripts into a more modular and reusable format. 

# Usage

```
paravision --chromatogram Volume -np 48
paravision --grm-2d --nrad --ncol
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
