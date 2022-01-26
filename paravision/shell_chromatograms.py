from paraview.simple import *

from paravision.utils import csvWriter, parse_cmdline_args, read_files
from paravision.integrate import integrate

import math
import numpy as np

def shell_chromatograms(reader, args):
    """ Generate shell chromatograms from a given 2D surface """

    args.scalars = args.scalars or reader.PointArrayStatus
    scalars = args['scalars']
    shellType = args.shelltype

    timeKeeper = GetTimeKeeper()
    timeArray = reader.TimestepValues
    nts = len(timeArray) or 1

    print("Running shell_chromatograms on provided SURFACE!")

    nRegions = int(args['shell_chromatograms'])

    view = GetActiveViewOrCreate('RenderView')
    ## Calc bounding box. Requires show
    display = Show(reader, view)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    Hide(reader, view)

    nShells = nRegions + 1 #Including r = 0
    rShells = []

    R = (xmax - xmin + ymax - ymin)/4
    print("R:", R)

    # shellType = 'EQUIDISTANT'
    # shellType = 'EQUIVOLUME'
    if shellType == 'EQUIVOLUME':
        for n in range(nShells):
            rShells.append(R * sqrt(n/nRegions))
    elif shellType == 'EQUIDISTANT':
        for n in range(nShells):
            rShells.append(R * (n/nRegions))

    print("rShells:", rShells)

    radAvg = []
    integrated_over_time = [ [] for region in range(nRegions) ]
    for timestep in range(nts):

        timeKeeper.Time = timestep
        reader.UpdatePipeline(reader.TimestepValues[timestep])

        print("its:", timestep)

        for radIn, radOut in zip(rShells[:-1], rShells[1:]):

            index = rShells.index(radIn)

            radAvg.append( (radIn + radOut) / 2 )

            shell_area = math.pi * (radOut**2 - radIn**2)

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

            ## Since we handle time outside the integrate function, the
            ## only entry in the outer list is the list of integrated scalars
            ## at the given time
            integratedData = integrate(clipInner, scalars, normalize='Area')
            integrated_over_time[index].extend(integratedData)

            Delete(clipInner)
            Delete(clipOuter)

    for region in range(nRegions):
        for scalar in scalars:
            csvWriter("shell_{i}_{s}.cg".format(i=region, s=scalar), timeArray, np.array(integrated_over_time[region]).T[list(scalars).index(scalar)])

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    shell_chromatograms(reader, args)
