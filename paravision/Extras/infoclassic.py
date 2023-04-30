from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore
from math import pi

from addict import Dict
import json

from paraview.simple import *
from paravision import ConfigHandler
from paravision.utils import read_files
from paravision.project import projector

import argparse
from rich import print, print_json

def infoclassic(interstitial, args):
    """
    Write out information about classic xns meshes, given the interstitial mesh
    """

    ## TODO: allow cylindrical/box container shapes

    view = GetActiveViewOrCreate('RenderView')
    projection = projector(interstitial, *args['project'])

    data = Dict()

    SetActiveSource(projection)
    display = Show(projection, view)
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
    ## FIXME: Assumes cylindrical container
    csa = pi * radius * radius 
    total_volume_bounds = csa * height

    data.container.radius = radius
    data.container.height = height
    data.container.cross_section_area = csa

    print(f"---- Bounds based calculations ----")
    print(f"Container radius: {radius}")
    print(f"Container height: {height}")
    print(f"Cross section area: {csa}")
    print(f"Total volume: {total_volume_bounds}")
    print(f"-----------------------------------")

    integrated = IntegrateVariables(Input=projection)
    intdata = servermanager.Fetch(integrated)
    intdata = dsa.WrapDataObject(intdata)
    int_volume = intdata.CellData['Volume'][0]
    Delete(integrated)

    print(f"---- Mesh based volumes ----")
    print(f"Interstitial volume: {int_volume}")
    print(f"----------------------------")

    data.volumes.interstitial = int_volume
    data.volumes.total = total_volume_bounds
    data.volumes.particles = total_volume_bounds - int_volume

    data.mesh_porosity = int_volume / total_volume_bounds

    with open(f'info_{args.output_prefix}.json', 'w') as fp: 
        json.dump(data, fp, indent=4)


def infoclassic_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args

if __name__=="__main__":

    config = ConfigHandler()
    args, local_args_list = config.parse_config_and_cmdline_args()
    args = infoclassic_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    # WARNING: Assumes you read interstitial mesh
    interstitial = read_files(args['FILES'], args['filetype'])
    infoclassic(interstitial, args)
