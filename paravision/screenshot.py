from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import parse_cmdline_args, read_files
from paravision.project import project

from paravision import ConfigHandler

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
            wLUT.RescaleTransferFunction(-abs(max(crange, key=abs)), abs(max(crange, key=abs)))
        elif args.color_range_method == 'custom': 
            wLUT.RescaleTransferFunction(args.custom_color_range[0], args.custom_color_range[1])

        if args['config']: 
            config = ConfigHandler()
            config.read(args['config'])
            configure_scalar_bar(wLUT, view, config.config.ColorBar)

        UpdateScalarBars()
        display.SetScalarBarVisibility(view, args['show_scalar_bar'])
        # view.Update()
        # display.UpdatePipeline()

        SaveScreenshot(f'screenshot_{args.output_prefix}_{scalar}.png', view, ImageResolution=args['geometry'], TransparentBackground=1)
        Hide(display, view)

def configure_scalar_bar(LUT, view, colorbar_config):
    ColorBar                      = GetScalarBar(LUT, view)
    ColorBar.AutoOrient           = colorbar_config.AutoOrient
    ColorBar.Orientation          = colorbar_config.Orientation
    ColorBar.WindowLocation       = colorbar_config.WindowLocation
    ColorBar.Position             = colorbar_config.Position
    ColorBar.Title                = colorbar_config.Title
    ColorBar.ComponentTitle       = colorbar_config.ComponentTitle
    ColorBar.TitleJustification   = colorbar_config.TitleJustification
    ColorBar.HorizontalTitle      = colorbar_config.HorizontalTitle
    ColorBar.TitleOpacity         = colorbar_config.TitleOpacity
    ColorBar.TitleFontFamily      = colorbar_config.TitleFontFamily
    ColorBar.TitleFontFile        = colorbar_config.TitleFontFile
    ColorBar.TitleBold            = colorbar_config.TitleBold
    ColorBar.TitleItalic          = colorbar_config.TitleItalic
    ColorBar.TitleShadow          = colorbar_config.TitleShadow
    ColorBar.TitleFontSize        = colorbar_config.TitleFontSize
    ColorBar.TitleColor           = colorbar_config.TitleColor
    ColorBar.LabelOpacity         = colorbar_config.LabelOpacity
    ColorBar.LabelFontFamily      = colorbar_config.LabelFontFamily
    ColorBar.LabelFontFile        = colorbar_config.LabelFontFile
    ColorBar.LabelBold            = colorbar_config.LabelBold
    ColorBar.LabelItalic          = colorbar_config.LabelItalic
    ColorBar.LabelShadow          = colorbar_config.LabelShadow
    ColorBar.LabelFontSize        = colorbar_config.LabelFontSize
    ColorBar.LabelColor           = colorbar_config.LabelColor
    ColorBar.AutomaticLabelFormat = colorbar_config.AutomaticLabelFormat
    ColorBar.LabelFormat          = colorbar_config.LabelFormat
    ColorBar.DrawTickMarks        = colorbar_config.DrawTickMarks
    ColorBar.DrawTickLabels       = colorbar_config.DrawTickLabels
    ColorBar.UseCustomLabels      = colorbar_config.UseCustomLabels
    ColorBar.CustomLabels         = colorbar_config.CustomLabels
    ColorBar.AddRangeLabels       = colorbar_config.AddRangeLabels
    ColorBar.RangeLabelFormat     = colorbar_config.RangeLabelFormat
    ColorBar.DrawAnnotations      = colorbar_config.DrawAnnotations
    ColorBar.AddRangeAnnotations  = colorbar_config.AddRangeAnnotations
    ColorBar.AutomaticAnnotations = colorbar_config.AutomaticAnnotations
    ColorBar.DrawNanAnnotation    = colorbar_config.DrawNanAnnotation
    ColorBar.NanAnnotation        = colorbar_config.NanAnnotation
    ColorBar.TextPosition         = colorbar_config.TextPosition
    ColorBar.ReverseLegend        = colorbar_config.ReverseLegend
    ColorBar.ScalarBarThickness   = colorbar_config.ScalarBarThickness
    ColorBar.ScalarBarLength      = colorbar_config.ScalarBarLength


if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    screenshot(reader, args)
