from paraview.simple import *

from paravision.utils import parse_cmdline_args, read_files, view_handler
from paravision.project import project

def animate(reader, args):
    for key in args:
        print(key + ': ', args[key])
    projectionType = args['projectionType']
    scalars = args['scalars'] or reader.PointArrayStatus
    scalarBarVisible = not args['no_scalar_bar']
    geometry = args['geometry']
    axisVisible = not args['no_coordinate_axis']
    zoom = args['zoom']

    animationScene = GetAnimationScene()
    timekeeper = GetTimeKeeper()
    animationScene.UpdateAnimationUsingDataTimeSteps()
    timeArray = reader.TimestepValues
    nts = len(timeArray) or 1

    ## TODO: Animate using constant scalarbar range
    ## TODO: Fix animation for one timestep

    # try:
    #     ## Use last timestep as reference for creating color map
    #     animationScene.AnimationTime = reader.TimestepValues[-1]
    #     timekeeper.Time = reader.TimestepValues[-1]
    # except:
    #     ## for files without time data
    #     animationScene.AnimationTime = 0
    #     animationScene.StartTime = 0
    #     animationScene.EndTime = 0
    #     timekeeper.Time = 0

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

    for scalar in scalars:
        print("Animating", scalar )

        if scalar == 'None':
            ColorBy(projectionDisplay, None)
        else:
            ColorBy(projectionDisplay, ('POINTS', scalar))

        # ## NOTE: Removing this should HELP fix the varying scalar bar range for every frame
        # projectionDisplay.RescaleTransferFunctionToDataRange()

        ## Find the min/max range of data over all timesteps
        pd_ranges_t = []
        for timestep in range(nts):
            projection.UpdatePipeline(timeArray[timestep])
            pd = projection.PointData
            pd_ranges_t.append(pd.GetArray(scalar).GetRange())

        pd_range_min = min(pd_ranges_t)[0]
        pd_range_max = max(pd_ranges_t)[1]

        print(f"Setting color bar range to min/max over all timesteps: {(pd_range_min, pd_range_max)}")

        wLUT = GetColorTransferFunction(scalar)
        wPWF = GetOpacityTransferFunction(scalar)
        HideScalarBarIfNotNeeded(wLUT, view)

        wLUT.ApplyPreset('Rainbow Uniform', True)

        wLUT.RescaleTransferFunction(pd_range_min, pd_range_max)

        view.Update()
        UpdateScalarBars()

        projectionDisplay.SetScalarBarVisibility(view, scalarBarVisible)
        SaveAnimation(scalar + '.png', view, ImageResolution=geometry, TransparentBackground=1, SuffixFormat='.%04d')

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    animate(reader, args)
