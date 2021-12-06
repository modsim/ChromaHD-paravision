from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import parse_cmdline_args, read_files

def screenshot(object, args, suffix=''):
    """ Screenshot a given object """

    args.scalars = args.scalars or reader.PointArrayStatus
    scalars = args['scalars']
    timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')

    display = Show(object, view)
    display.Representation = args['display_representation']
    view.OrientationAxesVisibility = args['show_axis']

    # view.Update()
    # view.ResetCamera()
    # view.ViewSize = args['geometry']

    view_handler(args['view'], args['zoom'])

    for scalar in args['scalars']:
        print("Snapping", scalar )

        display = Show(object, view)
        display.Representation = args['display_representation']
        view.OrientationAxesVisibility = args['show_axis']
        display.RescaleTransferFunctionToDataRange()
        display.UpdatePipeline()

        view.Update()
        view.ViewSize = args['geometry']
        view.ResetCamera()
        UpdateScalarBars()

        if scalar == 'None':
            ColorBy(display, None)
        else:
            ColorBy(display, ('POINTS', scalar))


        wLUT = GetColorTransferFunction(scalar)
        wPWF = GetOpacityTransferFunction(scalar)
        HideScalarBarIfNotNeeded(wLUT, view)

        wLUT.ApplyPreset('Rainbow Uniform', True)

        view.Update()
        UpdateScalarBars()

        display.SetScalarBarVisibility(view, args['show_scalar_bar'])
        SaveScreenshot('screenshot_' + scalar + '_' + suffix + args['FILES'][0].replace(args['filetype'], 'png'), view, ImageResolution=args['geometry'], TransparentBackground=1)
        Hide(display, view)

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args)
    screenshot(reader, args)
