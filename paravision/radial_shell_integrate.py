from paraview.simple import *

from paravision.utils import csvWriter, read_files
from paravision.integrate import integrate

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

from math import sqrt

def radial_shell_integrate(reader, args):
    for key in args:
        print(key + ': ', args[key])

    scalars = args['scalars'] or reader.PointArrayStatus
    nRegions = args.nrad
    shellType = args.shelltype


    ## Calc bounding box. Requires show
    view = GetActiveViewOrCreate('RenderView')
    display = Show(reader, view)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    Hide(reader, view)

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

    appended = []
    radAvg = []

    for radIn, radOut in zip(rShells[:-1], rShells[1:]+rShells[:0]):

        radAvg.append( (radIn + radOut) / 2 )

        clipOuter = Clip(Input=reader)
        clipOuter.ClipType = 'Cylinder'
        clipOuter.ClipType.Axis = [0.0, 0.0, 1.0]
        clipOuter.ClipType.Radius = radOut
        Hide3DWidgets(proxy=clipOuter.ClipType)

        clipInner = Clip(Input=clipOuter)
        clipInner.ClipType = 'Cylinder'
        clipInner.ClipType.Axis = [0.0, 0.0, 1.0]
        clipInner.ClipType.Radius = radIn
        clipInner.Invert = 0

        values = integrate(clipInner, scalars, normalize=args.normalize)[0]

        Delete(clipInner)
        Delete(clipOuter)

        print(values)
        appended.append(values)

    print("Average scalar by radius:", appended)

    for i, scalar in enumerate(scalars): 
        csvWriter(f'radial_shell_integrate_{scalar}_{nRegions}_{args.output_prefix}.csv', radAvg, map(lambda x: x[i], appended))


def radial_shell_integrate_parser(args, local_args_list):
    ap = argparse.ArgumentParser()

    ap.add_argument("-nr", "--nrad", type=int, help="Radial discretization size for shell chromatograms. Also see --shelltype")
    ap.add_argument("-st", "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], help="Radial shell discretization type. See --nrad")
    ap.add_argument("-n", "--normalize", choices = ['NoNorm', 'Volume', 'Area'], help="Normalization for integration. Divides integrated result by Volume or Area")

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
    args = radial_shell_integrate_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    radial_shell_integrate(reader, args)
