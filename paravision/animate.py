from paraview.simple import *

from paravision.utils import parse_cmdline_args, read_files, view_handler
from paravision.project import project

def animate(reader, args):
    projectionType = args['projectionType']
    colorVars = args['colorVars'] or reader.PointArrayStatus
    scalarBarVisible = not args['no_scalar_bar']
    geometry = args['geometry']
    axisVisible = not args['no_coordinate_axis']
    zoom = args['zoom']

    animationScene1 = GetAnimationScene()
    timeKeeper1 = GetTimeKeeper()
    animationScene1.UpdateAnimationUsingDataTimeSteps()

    ## TODO: Animate using constant scalarbar range
    ## TODO: Fix animation for one timestep

    # try:
    #     ## Use last timestep as reference for creating color map
    #     animationScene1.AnimationTime = reader.TimestepValues[-1]
    #     timeKeeper1.Time = reader.TimestepValues[-1]
    # except:
    #     ## for files without time data
    #     animationScene1.AnimationTime = 0
    #     animationScene1.StartTime = 0
    #     animationScene1.EndTime = 0
    #     timeKeeper1.Time = 0

    # projection = Projection(reader, projectionType)
    projection = project(reader, args)

    view = GetActiveViewOrCreate('RenderView')
    projectionDisplay = Show(projection, view)
    projectionDisplay.Representation = args['display_representation']
    view.OrientationAxesVisibility = int(axisVisible)
    projectionDisplay.RescaleTransferFunctionToDataRange()
    view.ViewSize = geometry
    view.Update()

    # setCameraOrientation(zoom)
    view_handler(args['view'], args['zoom'])

    for colorVar in colorVars:
        print("Animating", colorVar )

        if colorVar == 'None':
            ColorBy(projectionDisplay, None)
        else:
            ColorBy(projectionDisplay, ('POINTS', colorVar))

        ## NOTE: Removing this should HELP fix the varying scalar bar range for every frame
        projectionDisplay.RescaleTransferFunctionToDataRange()

        wLUT = GetColorTransferFunction(colorVar)
        wPWF = GetOpacityTransferFunction(colorVar)
        HideScalarBarIfNotNeeded(wLUT, view)

        wLUT.ApplyPreset('Rainbow Uniform', True)

        view.Update()
        UpdateScalarBars()

        projectionDisplay.SetScalarBarVisibility(view, scalarBarVisible)
        SaveAnimation(colorVar + '.png', view, ImageResolution=geometry, TransparentBackground=1, SuffixFormat='.%04d')

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    animate(reader, args)
