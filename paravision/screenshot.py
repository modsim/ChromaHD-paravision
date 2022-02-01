from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import parse_cmdline_args, read_files
from paravision.project import project

def screenshot(object, args, suffix=''):
    """ Screenshot a given object with a given projection"""
    for key in args:
        print(key + ': ', args[key])

    # args.scalars = args.scalars or reader.PointArrayStatus
    args.scalars = args.scalars 
    # scalars = args['scalars']
    # timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')

    projection = project(object, args)

    for scalar in args['scalars']:
        print("Snapping", scalar )

        display = Show(projection, view)
        display.Representation = args['display_representation']
        view.OrientationAxesVisibility = args['show_axis']
        display.RescaleTransferFunctionToDataRange()
        display.UpdatePipeline()

        view_handler(args['view'], args['zoom'])
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
        SaveScreenshot('screenshot_' + scalar + '_' + suffix + '.png', view, ImageResolution=args['geometry'], TransparentBackground=1)
        Hide(display, view)

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    screenshot(reader, args)
