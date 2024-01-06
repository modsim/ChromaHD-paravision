from paraview.simple import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

import numpy as np

from paravision.utils import parse_cmdline_args, read_files, csvWriter

# TODO: Distinguish between mass flux and volume flux
def mass_flux(reader, args):
    for key in args:
        print(key + ': ', args[key])

    scalars = args['scalars'] or reader.PointArrayStatus
    nSlice = args['mass_flux'] or 1
    output_prefix = args['output_prefix']

    view = GetActiveViewOrCreate('RenderView')
    display = Show(reader, view)
    display.Representation = args['display_representation']
    # display.Representation = 'Surface With Edges'

    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    print(xmin,xmax,ymin,ymax,zmin,zmax)

    Hide(reader, view)

    ## NOTE: Only takes takes one color
    scalar = scalars[0]
    flowrate = []
    zs = []

    count = 0

    try:
        ## Set timestep to last timestep (last file in series)
        timeKeeper = GetTimeKeeper()
        timeKeeper.Time = reader.TimestepValues[-1]
    except:
        pass

    for zpos in np.linspace(zmin, zmax, nSlice):

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

        integrated = IntegrateVariables(Input=projection)
        intdata = servermanager.Fetch(integrated)
        intdata = dsa.WrapDataObject(intdata)
        value = intdata.PointData[scalar]
        print('Area:', intdata.CellData['Area'][0])
        ## TODO: FIX THIS
        try:
            value = ns.vtk_to_numpy(value)
            flowrate.append(value[0])
            zs.append(zpos)
        except:
            pass

    print(zs)
    print(flowrate)
    csvWriter(f'massFlux_{scalar}_{output_prefix}.csv', zs, flowrate)
    # plt.figure()
    # plt.plot(zs, flowrate)
    # plt.savefig('plot.pdf')
    # plt.show()

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    mass_flux(reader, args)
