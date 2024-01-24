from paraview.simple import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

import numpy as np

from paravision.utils import parse_cmdline_args, read_files, csvWriter, default_parser, script_main_new, default_local_parser
from addict import Dict
from rich import print_json

# TODO: Distinguish between mass flux and volume flux
def cross_section_dump(reader, **args):
    for key in args:
        print(key + ': ', args[key])

    _scalars = args['scalars'] or reader.PointArrayStatus
    _nslices = args['nslices'] or 1
    _output_prefix = args['output_prefix']

    view = GetActiveViewOrCreate('RenderView')
    display = Show(reader, view)
    display.Representation = args['display_representation']
    # display.Representation = 'Surface With Edges'

    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    print(xmin,xmax,ymin,ymax,zmin,zmax)

    Hide(reader, view)

    count = 0
    try:
        ## Set timestep to last timestep (last file in series)
        timeKeeper = GetTimeKeeper()
        timeKeeper.Time = reader.TimestepValues[-1]
    except:
        pass

    for zpos in np.linspace(zmin, zmax, _nslices):

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
        SaveData(f"cross_section_dump_{_output_prefix}_{_nslices:03d}_{count:03d}.csv", proxy=projection, PointDataArrays=_scalars)
        Delete(projection)

def local_parser(argslist):
    ap = default_parser()
    ap.add_argument('--nslices', type=int, help="Number of slices along length at which to dump data.")
    args = Dict(vars(ap.parse_args(argslist)))
    print_json(data=args)
    return args

if __name__=="__main__":
    script_main_new(local_parser, cross_section_dump)
