from paraview.simple import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

from paravision.utils import parse_cmdline_args, read_files, csvWriter

# TODO: Update this with --integrate?

def volume_integral(reader, args):
    for key in args:
        print(key + ': ', args[key])
    scalars = args['scalars'] or reader.PointArrayStatus

    timeKeeper = GetTimeKeeper()
    nts = len(reader.TimestepValues)

    view = GetActiveViewOrCreate('RenderView')

    # cellSize1 = CellSize(Input=reader)
    # cellSize1.ComputeVolume= 1
    # cellSize1.ComputeSum = 1
    # volume = servermanager.Fetch(cellSize1)
    # volume = dsa.WrapDataObject(volume)
    # volume = volume.FieldData['Volume'][0]
    # print("volume:", volume)

    intOutput = {}
    for scalar in scalars:
        intOutput.update({scalar: []})
        print(type(intOutput[scalar]))

    for timestep in range(nts):

        timeKeeper.Time = timestep
        # print("Processing timestep: ", timestep, end="\r")
        reader.UpdatePipeline(reader.TimestepValues[timestep])

        integrated = IntegrateVariables(Input=reader)
        intdata = servermanager.Fetch(integrated)
        intdata = dsa.WrapDataObject(intdata)

        volume = intdata.CellData['Volume'][0]

        for scalar in scalars:
            value = intdata.PointData[scalar]
            value = ns.vtk_to_numpy(value)[0]/volume
            intOutput[scalar].append(value)

        Delete(integrated)

    print(intOutput)
    for scalar in scalars:
        csvWriter(scalar + '.integrated.csv', reader.TimestepValues, intOutput[scalar])

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    volume_integral(reader, args)
