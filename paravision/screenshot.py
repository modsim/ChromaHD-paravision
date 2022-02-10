from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import parse_cmdline_args, read_files
from paravision.project import project

def screenshot(object, args, suffix=''):
    """ Screenshot a given object with a given projection"""
    for key in args:
        print(key + ': ', args[key])

    args.scalars = args.scalars or object.PointArrayStatus
    # args.scalars = args.scalars 
    # scalars = args['scalars']
    # timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']

    projection = project(object, args)

    for scalar in args['scalars']:
        print("Snapping", scalar )

        display = Show(projection, view)
        display.Representation = args['display_representation']
        display.RescaleTransferFunctionToDataRange(False, True)
        # RescaleTransferFunction(0.0, 0.007428335025126975)

        view_handler(args['view'], args['zoom'])
        # view.Update()

        if scalar == 'None':
            ColorBy(display, None)
        else:
            ColorBy(display, ('POINTS', scalar))

        wLUT = GetColorTransferFunction(scalar)
        wPWF = GetOpacityTransferFunction(scalar)
        # HideScalarBarIfNotNeeded(wLUT, view)

        wLUT.ApplyPreset(args['colormap'], True)

        configure_scalar_bar(wLUT, view, scalar)

        UpdateScalarBars()
        display.SetScalarBarVisibility(view, args['show_scalar_bar'])
        # view.Update()
        # display.UpdatePipeline()

        SaveScreenshot('screenshot_' + scalar + '_' + suffix + '.png', view, ImageResolution=args['geometry'], TransparentBackground=1)
        Hide(display, view)

def configure_scalar_bar(wLUT, view, title, fontfamily='Times', fontsize=18 ):
    ColorBar = GetScalarBar(wLUT, view)
    ColorBar.Orientation = 'Horizontal'
    ColorBar.WindowLocation = 'LowerCenter'
    ColorBar.Title = title
    ColorBar.ComponentTitle = ''
    ColorBar.TitleJustification = 'Centered'
    ColorBar.HorizontalTitle = 1
    ColorBar.TitleColor = [0.0, 0.0, 0.0]
    ColorBar.TitleOpacity = 1.0
    ColorBar.TitleFontFamily = fontfamily
    ColorBar.TitleBold = 0
    ColorBar.TitleItalic = 0
    ColorBar.TitleShadow = 0
    ColorBar.TitleFontSize = fontsize
    ColorBar.LabelColor = [0.0, 0.0, 0.0]
    ColorBar.LabelOpacity = 1.0
    ColorBar.LabelFontFamily = fontfamily
    ColorBar.LabelFontFile = ''
    ColorBar.LabelBold = 0
    ColorBar.LabelItalic = 0
    ColorBar.LabelShadow = 0
    ColorBar.LabelFontSize = fontsize
    ColorBar.AutomaticLabelFormat = 1
    ColorBar.LabelFormat = '%-#6.3g'
    ColorBar.ScalarBarThickness = 20
    ColorBar.ScalarBarLength = 0.50

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    screenshot(reader, args)
