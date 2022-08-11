from paraview.simple import *
from paravision import ConfigHandler
import argparse
from addict import Dict
from paravision.utils import find_preset

from rich import print, print_json

from paravision.utils import parse_cmdline_args, read_files, view_handler
from paravision.project import projector

from paravision.defaults import DEFAULT_CONFIG

def animate(reader, **kwargs):

    config = DEFAULT_CONFIG
    config.update(kwargs)

    scalars = config.get('scalars') or reader.PointArrayStatus
    scalarBarVisible = config.get('show_scalar_bar', False)
    geometry = config.get('geometry', [2560, 1440])
    axisVisible = config.get('show_axis', False)
    zoom = config.get('zoom', 1)

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
    projection = projector(reader, *config.get('project', [None, None, None, None]))

    view = GetActiveViewOrCreate('RenderView')
    projectionDisplay = Show(projection, view)
    projectionDisplay.Representation = config.get( 'display_representation' )
    view.OrientationAxesVisibility = int(axisVisible)
    projectionDisplay.RescaleTransferFunctionToDataRange()
    view.ViewSize = geometry
    view.Update()

    # setCameraOrientation(zoom)
    view_handler(config['view'], config['zoom'])

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

        wLUT.ApplyPreset(find_preset( config['colormap'] , config['colormap_fuzzy_cutoff']), True)

        wLUT.RescaleTransferFunction(pd_range_min, pd_range_max)

        view.Update()
        UpdateScalarBars()
        projectionDisplay.SetScalarBarVisibility(view, scalarBarVisible)

        SaveAnimation(scalar + '.png', view, ImageResolution=geometry, TransparentBackground=1, SuffixFormat='.%04d')

def animate_parser(args, local_args_list): 

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args

if __name__=="__main__":
    config = ConfigHandler()
    args, local_args_list = config.parse_config_and_cmdline_args()
    args = animate_parser(args, local_args_list)
    reader = read_files(args['FILES'], filetype=args['filetype'])

    animate(reader, **args)
