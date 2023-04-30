#!/usr/bin/env bash
a=(0.04 0.05 0.06 0.08 0.1)
for i in "${a[@]}" ; do
    pvrun screenshot -s CellEntityIds --view z y --display-representation 'Surface With Edges' --colormap 'rainbow uni' -o "$i" test_2d_$i.vtk 
done
