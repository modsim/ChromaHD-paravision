from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import parse_cmdline_args, read_files
from paravision.project import project

def screenshot(object, args):
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
    pd = projection.PointData

    for scalar in args['scalars']:
        print("Snapping", scalar )

        display = Show(projection, view)
        display.Representation = args['display_representation']

        if scalar == 'None':
            ColorBy(display, None)
        else:
            ColorBy(display, ('POINTS', scalar))

        view_handler(args['view'], args['zoom'])
        # view.Update()

        wLUT = GetColorTransferFunction(scalar)
        wPWF = GetOpacityTransferFunction(scalar)
        # HideScalarBarIfNotNeeded(wLUT, view)

        wLUT.ApplyPreset(args['colormap'], True)

        if args.custom_color_range: 
            wLUT.RescaleTransferFunction(args.custom_color_range[0], args.custom_color_range[1])
        elif args.color_range_method == 'auto': 
            display.RescaleTransferFunctionToDataRange(False, True)
        elif args.color_range_method == 'startzero': 
            crange = pd.GetArray(scalar).GetRange()
            wLUT.RescaleTransferFunction(0.0, crange[1])
        elif args.color_range_method == 'midzero': 
            crange = pd.GetArray(scalar).GetRange()
            wLUT.RescaleTransferFunction(-max(crange), max(crange))
        elif args.color_range_method == 'custom': 
            wLUT.RescaleTransferFunction(args.custom_color_range[0], args.custom_color_range[1])

        configure_scalar_bar(wLUT, view, scalar)

        UpdateScalarBars()
        display.SetScalarBarVisibility(view, args['show_scalar_bar'])
        # view.Update()
        # display.UpdatePipeline()

        SaveScreenshot(f'screenshot_{args.output_prefix}_{scalar}.png', view, ImageResolution=args['geometry'], TransparentBackground=1)
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
