from paraview.simple import *

from paravision.utils import csvWriter, parse_cmdline_args, read_files, arr_to_bin_unpacked, arr_to_bin
from paravision.integrate import integrate

import numpy as np

def GRM2D(object, args):
    ## Split into axial columns
    ## Split into cylindrical columns
    ## Integrate

    args.scalars = args.scalars or reader.PointArrayStatus

    view = GetActiveViewOrCreate('RenderView')
    display = Show(object, view)
    display.Representation = args['display_representation']
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    radius = ((xmax-xmin) + (ymax-ymin)) / 4
    length = zmax - zmin
    print("Length: {}, Radius: {}".format(length, radius))

    # nCol = 10              # Number of axial regions
    # nRad = 5               # Number of radial regions
    nCol = args['grm2d'][0]
    nRad = args['grm2d'][1]

    print(f"{nCol = } ")
    print(f"{nRad = } ")

    # dx = length/nCol
    # dr = radius/nRad

    colEdges = np.linspace(zmin, zmax, nCol+1)
    radEdges = np.linspace(0,radius,nRad+1) if args['shelltype'] == 'EQUIDISTANT' else list(x/nRad * radius for x in range(nRad+1))


    # Hide(object, view)
    nColEdgeFractions = np.linspace(0,1,nCol+1)
    nRadEdgeFractions = np.linspace(0,1,nRad+1)

    print(radEdges)
    print(nColEdgeFractions)

    ## TODO: Make these function arguments
    timeKeeper = GetTimeKeeper()
    timeArray = object.TimestepValues
    nts = len(timeArray) or 1

    # ## NOTE: Object must be reader
    # timeArray = object.TimestepValues

    ## Output vector. Should contain (nts X nCol X nRad X nScalar)
    grm2d_output = []

    grm2d_output_filename = 'grm2d_output.bin'

    ## Hack to remove previous file
    arr_to_bin([], grm2d_output_filename, 'd')

    for timestep in range(nts):

        timeKeeper.Time = timestep
        # object.UpdatePipeline(reader.TimestepValues[timestep])
        object.UpdatePipeline(timeArray[timestep])
        # object.UpdatePipeline()

        grm2d_timestep_output = []

        print("--> TS: {}".format(timestep))

        # for leftEdge, rightEdge in zip(colEdges[:-1], colEdges[1:]):
        for leftEdge, rightEdge in zip(nColEdgeFractions[:-1], nColEdgeFractions[1:]):
            print("  |--> Col: {}/{}".format(np.where(nColEdgeFractions == rightEdge)[0][0],nCol))
            SetActiveSource(object)
            print('[{}, {}]'.format(leftEdge, rightEdge))

            # clipLeftArgs = { 'project' : ['clip', 'Plane', leftEdge , '-z'] }
            # clipRightArgs = { 'project' : ['clip', 'Plane', rightEdge, '+z'] }
            # clipLeft = project(object, clipLeftArgs)
            # clipRight = project(clipLeft, clipRightArgs)
            ## screenshot(clipRight, args, suffix=str(leftEdge) + '_')

            clipBox = Clip(Input=object)
            clipBox.ClipType = 'Box'
            clipBox.Exact = 1
            clipBox.ClipType.UseReferenceBounds = 1
            clipBox.ClipType.Bounds = [0.0, 1.0, 0.0, 1.0, leftEdge, rightEdge]
            # clipBox.UpdatePipeline()

            # Hide(object, view)
            # screenshot(clipBox, args, suffix=str(leftEdge) + '_')

            radAvg = []

            for radIn, radOut in zip(radEdges[:-1], radEdges[1:]):
                radAvg.append( (radIn + radOut) / 2 )
                # print('--> [{}, {}]: {}'.format(radIn, radOut, (radIn+radOut)/2))

                print('    |--> Rad: {}/{}'.format(np.where(radEdges == radOut)[0][0], nRad))

                # clipOuter = Clip(Input=clipRight)
                clipOuter = Clip(Input=clipBox)
                clipOuter.ClipType = 'Cylinder'
                clipOuter.ClipType.Axis = [0.0, 0.0, 1.0]
                clipOuter.ClipType.Radius = radOut
                Hide3DWidgets(proxy=clipOuter.ClipType)

                # renderView1 = GetActiveViewOrCreate('RenderView')
                # projectionDisplay = Show(clipOuter, renderView1)
                # projectionDisplay.Representation = 'Surface'
                # # projectionDisplay.Representation = 'Surface With Edges'
                # renderView1.OrientationAxesVisibility = int(args['show_axis'])
                # projectionDisplay.RescaleTransferFunctionToDataRange()

                clipInner = Clip(Input=clipOuter)
                clipInner.ClipType = 'Cylinder'
                clipInner.ClipType.Axis = [0.0, 0.0, 1.0]
                clipInner.ClipType.Radius = radIn
                clipInner.Invert = 0

                # renderView1 = GetActiveViewOrCreate('RenderView')
                # projectionDisplay = Show(clipInner, renderView1)
                # projectionDisplay.Representation = 'Surface'
                # # projectionDisplay.Representation = 'Surface With Edges'
                # renderView1.OrientationAxesVisibility = int(args['show_axis'])
                # projectionDisplay.RescaleTransferFunctionToDataRange()

                # screenshot(clipInner, args, suffix=str(radIn) + "_")

                integrated_scalars = integrate(clipInner, args['scalars'], normalize='Volume')
                # print('---->', integrated_scalars[0])
                grm2d_timestep_output.extend(integrated_scalars[0])

                Delete(clipInner)
                Delete(clipOuter)

            # Delete(clipLeft)
            # Delete(clipRight)
            Delete(clipBox)

        grm2d_output.extend(grm2d_timestep_output)
        # print(grm2d_timestep_output)
        arr_to_bin_unpacked(grm2d_timestep_output, 'grm2d_appended.bin', 'd', mode='a')

    # print(grm2d_output)
    ## NOTE: Uncomment one of the below to save from RAM to disk
    # arr_to_bin(grm2d_output, grm2d_output_filename, 'd')
    # arr_to_bin_unpacked(grm2d_output, grm2d_output_filename, 'd')
    print("DONE!")

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args)
    GRM2D(reader, args)
