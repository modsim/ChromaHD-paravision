from paravision.utils import csvWriter, parse_cmdline_args, read_files
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore
from math import pi

from addict import Dict
import json

from paraview.simple import *

def infogeneric(args):
    """
    Write out information about generic field 3D xns meshes

    """

    ## TODO: allow cylindrical/box container shapes

    packedbed = read_files([args['packedbed']], args['filetype'])
    interstitial = read_files([args['interstitial']], args['filetype'])

    view = GetActiveViewOrCreate('RenderView')

    data = Dict()

    SetActiveSource(interstitial)
    display = Show(interstitial, view)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()

    print(f"---- Interstitial bounds ----")
    print(f"bounds x: {xmin}, {xmax}")
    print(f"bounds y: {ymin}, {ymax}")
    print(f"bounds z: {zmin}, {zmax}")
    print(f"-----------------------------")

    data.bounds.interstitial.xmin = xmin
    data.bounds.interstitial.xmax = xmax
    data.bounds.interstitial.ymin = ymin
    data.bounds.interstitial.ymax = ymax
    data.bounds.interstitial.zmin = zmin
    data.bounds.interstitial.zmax = zmax

    radius = (xmax - xmin + ymax - ymin) / 4
    height = zmax - zmin
    csa = pi * radius * radius 
    total_volume_bounds = csa * height

    data.container.radius = radius
    data.container.height = height
    data.container.cross_section_area = csa

    SetActiveSource(packedbed)
    display = Show(packedbed, view)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()

    print(f"---- Packed bed bounds ----")
    print(f"bounds x: {xmin}, {xmax}")
    print(f"bounds y: {ymin}, {ymax}")
    print(f"bounds z: {zmin}, {zmax}")
    print(f"---------------------------")

    data.bounds.packedbed.xmin = xmin
    data.bounds.packedbed.xmax = xmax
    data.bounds.packedbed.ymin = ymin
    data.bounds.packedbed.ymax = ymax
    data.bounds.packedbed.zmin = zmin
    data.bounds.packedbed.zmax = zmax

    bed_height_bounds = zmax - zmin

    data.packedbed.height = bed_height_bounds

    print(f"---- Bounds based calculations ----")
    print(f"Container radius: {radius}")
    print(f"Container height: {height}")
    print(f"Cross section area: {csa}")
    print(f"Bed height: {bed_height_bounds}")
    print(f"Total volume: {total_volume_bounds}")
    print(f"-----------------------------------")

    integrated = IntegrateVariables(Input=interstitial)
    intdata = servermanager.Fetch(integrated)
    intdata = dsa.WrapDataObject(intdata)
    int_volume = intdata.CellData['Volume'][0]
    Delete(integrated)

    ## It's possible that savedata is faster than servermanager.Fetch and the subsequent conversions
    # SaveData('volume.csv', proxy=integrated, ChooseArraysToWrite=1, CellDataArrays=['Volume'], UseScientificNotation=1, FieldAssociation='Cell Data')

    integrated = IntegrateVariables(Input=packedbed)
    intdata = servermanager.Fetch(integrated)
    intdata = dsa.WrapDataObject(intdata)
    bed_volume = intdata.CellData['Volume'][0]
    Delete(integrated)

    porosity = int_volume / (int_volume + bed_volume)

    print(f"---- Mesh based volumes ----")
    print(f"Interstitial volume: {int_volume}")
    print(f"Packed bed volume: {bed_volume}")
    print(f"Porosity: {porosity}")
    print(f"----------------------------")

    data.volumes.interstitial = int_volume
    data.volumes.packedbed = bed_volume

    data.porosity = porosity

    with open('dump.json', 'w') as fp: 
        json.dump(data, fp, indent=4)


if __name__=="__main__":
    args = parse_cmdline_args()
    infogeneric(args)
