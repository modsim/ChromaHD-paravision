from paraview.simple import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

from paravision.utils import csvWriter, parse_cmdline_args, read_files
from paravision.integrate import integrate


from math import sqrt

def radial_shell_integrate(reader, args):
    for key in args:
        print(key + ': ', args[key])

    scalars = args['scalars'] or reader.PointArrayStatus
    nRegions = int(args['radial_shell_integrate'])

    ## Calc bounding box. Requires show
    view = GetActiveViewOrCreate('RenderView')
    display = Show(reader, view)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    Hide(reader, view)

    # nRegions = 3
    nShells = nRegions + 1 #Including r = 0
    rShells = []

    R = (xmax - xmin + ymax - ymin)/4
    print("R:", R)

    shellType = 'EQUIDISTANT'
    # shellType = 'EQUIVOLUME'
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

        # renderView1 = GetActiveViewOrCreate('RenderView')
        # projectionDisplay = Show(clipOuter, renderView1)
        # projectionDisplay.Representation = 'Surface'
        # # projectionDisplay.Representation = 'Surface With Edges'
        # renderView1.OrientationAxesVisibility = int(axisVisible)
        # projectionDisplay.RescaleTransferFunctionToDataRange()

        clipInner = Clip(Input=clipOuter)
        clipInner.ClipType = 'Cylinder'
        clipInner.ClipType.Axis = [0.0, 0.0, 1.0]
        clipInner.ClipType.Radius = radIn
        clipInner.Invert = 0

        # TODO: Remove this
        cellSize1 = CellSize(Input=clipInner)
        cellSize1.ComputeVolume = 1
        cellSize1.ComputeSum = 1

        volume = servermanager.Fetch(cellSize1)
        volume = dsa.WrapDataObject(volume)
        volume = volume.FieldData['Volume'][0]
        print("VOLUME:", volume)

        integrated = IntegrateVariables(Input=clipInner)
        intdata = servermanager.Fetch(integrated)
        intdata = dsa.WrapDataObject(intdata)

        values = []
        for scalar in scalars:
            value = intdata.PointData[scalar]
            value = ns.vtk_to_numpy(value)
            values.append(value[0]/volume) ## Average of velocity, instead of integ(v.dV)

        print(values)
        appended.extend(values)

    print("Average scalar by radius:", appended)
    csvWriter('radial_shell_integrate', radAvg, appended)

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    radial_shell_integrate(reader, args)
