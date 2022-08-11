from paravision.utils import csvWriter, parse_cmdline_args, read_files
from paravision.utils import view_handler
from paravision.project import projector

from paraview.simple import *

## FIXME: Check if savedata is correct for parallel meshes. The number of data points might not correspond to number of nodes
def velocity_divergence(reader, args):
    """ 
    Calculate velocity divergence on the flowfield. 
    Assumes data is in u,v,w,p scalars. Creates vector field and then calculates divergence. 
    Assumes scalars are named: scalar_0, scalar_1, scalar_2
    """

    for key in args:
        print(key + ': ', args[key])

    args.scalars = args.scalars or reader.PointArrayStatus

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']
    
    calculator = Calculator(Input=reader)
    calculator.ResultArrayName = 'velocity'
    calculator.Function = 'iHat * scalar_0 + jHat * scalar_1 + kHat * scalar_2'
    calculator.ResultArrayType = 'Double'

    grads = GradientOfUnstructuredDataSet(Input=calculator)
    grads.ScalarArray = ['POINTS', 'velocity']
    grads.ComputeDivergence = 1
    grads.ComputeVorticity = 1
    print(f"Divergence Range: {grads.PointData.GetArray('Divergence').GetRange()}")

    ## This prints point data and coordinates
    SaveData('divergence.csv', proxy=grads, ChooseArraysToWrite=1, PointDataArrays=['Divergence'], UseScientificNotation=1)
    # OR
    # spreadSheetView1 = GetActiveViewOrCreate('SpreadSheetView')
    # spreadSheetView1.HiddenColumnLabels = ['Block Number', 'Points_Magnitude', 'Points', 'Point ID']
    # ExportView('output.csv', view=spreadSheetView1)

    projection = projector(grads, *args.project)
    projection_datarange = projection.PointData.GetArray('Divergence').GetRange()
    print(f"Divergence Range after projection: {projection_datarange}")

    display = Show(projection, view)
    display.Representation = args['display_representation']
    display.Opacity = 0.4

    ColorBy(display, ('POINTS', 'Divergence'))
    view_handler(args['view'], args['zoom'])

    wLUT = GetColorTransferFunction('Divergence')
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

    UpdateScalarBars()
    display.SetScalarBarVisibility(view, args['show_scalar_bar'])

    SaveScreenshot(f'velocity_div_{args.output_prefix}.png', view, ImageResolution=args['geometry'], TransparentBackground=1)
    HideAll(view)

    threshold = Threshold(Input=projection)
    threshold.Scalars = ['POINTS', 'Divergence']
    threshold.ThresholdRange = [10, projection_datarange[1]]

    # SetActiveSource(threshold)
    thresholdDisplay = Show(threshold, view)
    thresholdDisplay.Representation = args['display_representation']
    # thresholdDisplay.Opacity = 0.4
    ColorBy(thresholdDisplay, ('POINTS', 'Divergence'))

    thresholdDisplay.SetScalarBarVisibility(view, args['show_scalar_bar'])

    wLUT = GetColorTransferFunction('Divergence')
    wLUT.ApplyPreset(args['colormap'], True)

    if args.custom_color_range: 
        wLUT.RescaleTransferFunction(args.custom_color_range[0], args.custom_color_range[1])
    elif args.color_range_method == 'auto': 
        thresholdDisplay.RescaleTransferFunctionToDataRange(False, True)
    elif args.color_range_method == 'startzero': 
        crange = pd.GetArray(scalar).GetRange()
        wLUT.RescaleTransferFunction(0.0, crange[1])
    elif args.color_range_method == 'midzero': 
        crange = pd.GetArray(scalar).GetRange()
        wLUT.RescaleTransferFunction(-abs(max(crange, key=abs)), abs(max(crange, key=abs)))
    elif args.color_range_method == 'custom': 
        wLUT.RescaleTransferFunction(args.custom_color_range[0], args.custom_color_range[1])

    UpdateScalarBars()
    thresholdDisplay.SetScalarBarVisibility(view, args['show_scalar_bar'])
    thresholdDisplay.UpdatePipeline()

    SaveScreenshot(f'velocity_div_threshold_{args.output_prefix}.png', view, ImageResolution=args['geometry'], TransparentBackground=1)

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    velocity_divergence(reader, args)
