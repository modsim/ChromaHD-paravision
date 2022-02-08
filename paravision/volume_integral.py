from paraview.simple import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

from paravision.utils import parse_cmdline_args, read_files, csvWriter
from paravision.integrate import integrate

# TODO: Update this with --integrate?

def volume_integral(reader, args):
    for key in args:
        print(key + ': ', args[key])
    scalars = args['scalars'] or reader.PointArrayStatus

    timeKeeper = GetTimeKeeper()
    nts = len(reader.TimestepValues)
    timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')

    result = integrate(reader, scalars, normalize=args['volume_integral'], timeArray=timeArray)

    print(result)
    for i,scalar in enumerate(scalars):
        csvWriter(scalar + '.integrated.csv', reader.TimestepValues, map(lambda x: x[i], result))

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    volume_integral(reader, args)
