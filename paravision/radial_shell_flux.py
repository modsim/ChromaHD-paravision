"""
Calculate the (axially) average flux (flowrate) at various radial shells
    - Axially slice
    - Radially slice
    - Integrate
    - Average the values axially
"""

from paraview.simple import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

from paravision.utils import csvWriter, read_files
from paravision.integrate import integrate
from paravision import ConfigHandler

import numpy as np
import argparse
from addict import Dict
from rich import print, print_json

def radial_shell_flux(object, args): 
    args.scalars = args.scalars or object.PointArrayStatus

    nRegions = args.nrad
    shellType = args.shelltype

    nShells = nRegions + 1 #Including r = 0
    rShells = []

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']

    display = Show(object, view)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    print(xmin,xmax,ymin,ymax,zmin,zmax)

    Hide(reader, view)

    R = (xmax - xmin + ymax - ymin)/4
    print("R:", R)

    if shellType == 'EQUIVOLUME':
        for n in range(nShells):
            rShells.append(R * sqrt(n/nRegions))
    elif shellType == 'EQUIDISTANT':
        for n in range(nShells):
            rShells.append(R * (n/nRegions))

    print("rShells:", rShells)

    # WARNING: This is because clip/slice at the end of the column doesn't work as intended
    print("Slicing from 1.01 * zmin to 0.99 * zmax!!")
    z_slice_locations = np.linspace(zmin + args.xyoffset, zmax - args.xyoffset, args['naxial'])

    radAvg = []
    count = 0
    accumulated_values = []
    for zpos in z_slice_locations:

        count = count + 1
        print("Loop: ", count, zpos)
        projection = Slice(Input=reader)
        Hide3DWidgets(proxy=projection.SliceType)

        projection.SliceType = 'Plane'
        projection.HyperTreeGridSlicer = 'Plane'
        projection.SliceOffsetValues = [0.0]

        projection.SliceType.Origin = [0.0, 0.0, zpos]
        projection.SliceType.Normal = [0.0, 0.0, -1.0]
        projection.UpdatePipeline()

        radAvg = []
        values_current_plane = []
        for radIn, radOut in zip(rShells[:-1], rShells[1:]+rShells[:0]):

            radAvg.append( (radIn + radOut) / 2 )

            clipOuter = Clip(Input=projection)
            clipOuter.ClipType = 'Cylinder'
            clipOuter.ClipType.Axis = [0.0, 0.0, 1.0]
            clipOuter.ClipType.Radius = radOut
            Hide3DWidgets(proxy=clipOuter.ClipType)

            clipInner = Clip(Input=clipOuter)
            clipInner.ClipType = 'Cylinder'
            clipInner.ClipType.Axis = [0.0, 0.0, 1.0]
            clipInner.ClipType.Radius = radIn
            clipInner.Invert = 0

            # WARNING: Takes only the first scalar into account
            values = integrate(clipInner, args.scalars, normalize=args.normalize)[0][0]

            Delete(clipInner)
            Delete(clipOuter)

            values_current_plane.append(values)

            # print(values)
            # print(values_current_plane)

        accumulated_values.append(values_current_plane)

        Delete(projection)

    final_average = np.average(accumulated_values, axis=0)
    print(final_average)
    csvWriter(f'averaged_radial_flux_{args.naxial}_{args.nrad}_{args.shelltype}_{args.normalize}_{args.xyoffset}.csv', radAvg, final_average)


def radial_shell_flux_parser(args, local_args_list):
    ap = argparse.ArgumentParser()

    ap.add_argument("-nax", "--naxial", type=int, help="Axial discretization.")
    ap.add_argument("-nr", "--nrad", type=int, help="Radial discretization size for shell chromatograms. Also see --shelltype")
    ap.add_argument("-st", "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], help="Radial shell discretization type. See --nrad")
    ap.add_argument("-n", "--normalize", choices = ['NoNorm', 'Area'], help="Normalization for integration. Divides integrated result by Area")
    ap.add_argument("-xyo", "--xyoffset", type=float, help="Subtract/Add offset to zmin/zmax while calculating slice locations")

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
    args = radial_shell_flux_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    radial_shell_flux(reader, args)
