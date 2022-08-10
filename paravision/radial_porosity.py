from paraview.simple import *

from paravision.utils import csvWriter, read_files, get_bounds, get_volume
from paravision.integrate import integrate
from paravision.project import project

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

from math import sqrt, pi

def radial_porosity_profile(reader, nrad, shelltype, projectargs, output_prefix=None):
    nRegions = nrad
    shellType = shelltype

    projection = project(reader, *projectargs)

    ## Calc bounding box. Requires show
    view = GetActiveViewOrCreate('RenderView')
    HideAll(view)
    SetActiveSource(projection)
    view.Update()

    display = Show(projection, view)

    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    print('Bounds: ',*(xmin,xmax,ymin,ymax,zmin,zmax))
    Hide(projection, view)

    nShells = nRegions + 1 #Including r = 0
    rShells = []

    R = (xmax - xmin + ymax - ymin)/4
    print("R:", R)

    if shellType == 'EQUIVOLUME':
        for n in range(nShells):
            rShells.append(R * sqrt(n/nRegions))
    elif shellType == 'EQUIDISTANT':
        for n in range(nShells):
            rShells.append(R * (n/nRegions))

    print("rShells:", rShells)

    radAvg = []
    for radIn, radOut in zip(rShells[:-1], rShells[1:]+rShells[:0]):
        radAvg.append( (radIn + radOut) / 2 )

    porosity_profile = []

    for radIn, radOut in zip(rShells[:-1], rShells[1:]+rShells[:0]):

        # radAvg.append( (radIn + radOut) / 2 )

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

        int_volume = get_volume(clipInner)
        ## WARNING: Assumes cylinder
        full_volume = (zmax - zmin) * pi * (radOut**2 - radIn**2)

        porosity_profile.append( int_volume/ full_volume )

        Delete(clipInner)
        Delete(clipOuter)

    print(porosity_profile)
    csvWriter(f'porosity_profile_{shelltype}_{nrad}_{output_prefix}.csv', radAvg, porosity_profile)


def radial_porosity_parser(args, local_args_list):
    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")

    ap.add_argument("-nr", "--nrad", type=int, help="Radial discretization size for shell chromatograms. Also see --shelltype")
    ap.add_argument("-st", "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], help="Radial shell discretization type. See --nrad")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args


if __name__=="__main__":
    config = ConfigHandler()
    args, local_args_list = config.parse_config_and_cmdline_args()
    args = radial_porosity_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    radial_porosity_profile(reader, args.nrad, args.shelltype, args.project, args.output_prefix )
