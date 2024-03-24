
from paraview.simple import *
from paravision import ConfigHandler
from paravision.integrate import integrate
from paravision.project import projector
from paravision.utils import csvWriter, read_files, get_bounds, script_main_new, default_parser
from paravision.defaults import DEFAULT_CONFIG

from addict import Dict
from math import sqrt
from rich import print, print_json
import argparse
import numpy as np
import csv

def radial_shell_integrate(reader, **args):

    scalars = args.get('scalars') or reader.PointArrayStatus
    nRegions = args.get('nrad', 1)
    shellType = args.get('shelltype', 'EQUIDISTANT')
    normalize = args.get('normalize', DEFAULT_CONFIG.normalize)
    output_prefix = args.get('output_prefix', DEFAULT_CONFIG.output_prefix)
    _project = args.get('project', DEFAULT_CONFIG.project) 

    timeKeeper = GetTimeKeeper()
    timeArray = reader.TimestepValues
    nts = len(timeArray) or 1

    print(f"{timeArray = }")
    print(f"{nts = }")

    projection = projector(reader, *_project)

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
    print("zdelta:", zmax - zmin)

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

    final = []
    for timestep in range(nts):

        try: 
            timeKeeper.Time = timestep
            projection.UpdatePipeline(timeArray[timestep])
        except IndexError: 
            print(f"INDEX ERROR WITH TIMESTEP: {timestep}. Ignore this if we only have 1 timestep.")
            pass

        print("its:", timestep)

        appended = []
        # radAvg = []

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

            values = integrate(clipInner, scalars, normalize=normalize)[0]

            Delete(clipInner)
            Delete(clipOuter)

            appended.append(values)
        final.append(appended)

    final = np.array(final) * args.get('scale', 1.0)

    if args.get('divide_by_length', None):
        final = final / (zmax - zmin)

    if nts == 1: 
        for i, scalar in enumerate(scalars):
            csvWriter(f'radial_shell_integrate_{scalar}_{nRegions}_{output_prefix}.csv', radAvg, map(lambda x: x[i], final[0]))
    else: 
        # We have the shape of final as (nts, nrad, nscalar). Here we reshape it to the way cadet shapes arrays. This can be used as a "meta objective" in chromoo, so that we don't have to define every radial zone individually in the chromoo config.
        final_reshaped_as_cadet = np.moveaxis(final, 2, 0)
        for i, scalar in enumerate(scalars): 
            np.savetxt(f'serialized_radial_shell_integrate_time_{scalar}_{output_prefix}.dat', np.reshape(final_reshaped_as_cadet[i], (-1,)))
        for rad in range(nRegions): 
            for i, scalar in enumerate(scalars): 
                csvWriter(f'radial_shell_integrate_time_{scalar}_{rad}_{output_prefix}.csv', timeArray, map(lambda x: x[rad][i], final))

def radial_shell_integrate_parser(local_args_list):
    ap = default_parser()

    # ap.add_argument("FILES", nargs='*', help="files..") # Adding this would mask the default 'FILES' arg and always trigger reading all files in the dir.
    ap.add_argument("-nr", "--nrad", type=int, help="Radial discretization size for shell chromatograms. Also see --shelltype")
    ap.add_argument("-st", "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], help="Radial shell discretization type. See --nrad")
    ap.add_argument("-n", "--normalize", default='NoNorm', choices = ['NoNorm', 'Volume', 'Area'], help="Normalization for integration. Divides integrated result by Volume or Area")
    ap.add_argument("--scale", type=float, default=1.0, help="Scale factor applied after integration.")
    ap.add_argument("--divide-by-length", action="store_true", help="Divide result by object length in z-direction. To calculate average flux in z-dir.")

    print(local_args_list)
    args = ap.parse_args(local_args_list)
    args = Dict(vars(args))
    print_json(data=args)
    return args

if __name__=="__main__":
    script_main_new(radial_shell_integrate_parser, radial_shell_integrate)
