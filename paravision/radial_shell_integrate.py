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

        values = integrate(clipInner, scalars, normalize=args.radial_shell_integrate)[0]

        print(values)
        appended.append(values)

    print("Average scalar by radius:", appended)

    for i, scalar in enumerate(scalars): 
        csvWriter(f'radial_shell_integrate_{scalar}.csv', radAvg, map(lambda x: x[i], appended))

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    radial_shell_integrate(reader, args)
