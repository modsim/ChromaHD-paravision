"""copied from hotspots.py
Given a flow simulation with velocity components as scalars, 
calculate and save screenshot for hotspots in the flowfield.

Usage: pvrun -np 48 -p <hotspots.py> --threshold-reference <value> --threshold-factor <value>

Notes: 
- Consider using --color-range-method 'custom' --custom-color-range <value_low> <value_high> to further enhance the plot. 
- Also use --colors-logscale --opacity-mapping --opacity-logscale for great visuals

"""

from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import read_files
from paravision.utils import configure_scalar_bar
from paravision.utils import create_threshold
from paravision.utils import handle_coloring
from paravision.project import projector
from vtk import vtkThreshold

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

from paravision.defaults import DEFAULT_CONFIG

def hotspots(object, **args):
    """ Screenshot a given object with a given projection"""

    _scalars               = args.get('scalars') or object.PointArrayStatus
    _threshold_reference   = args.get('threshold_reference'   , DEFAULT_CONFIG.threshold_reference) 
    _threshold_factor   = args.get('threshold_factor'   , DEFAULT_CONFIG.threshold_factor) 

    _project               = args.get('project'               , DEFAULT_CONFIG.project) 
    _show_axis             = args.get('show_axis'             , DEFAULT_CONFIG.show_axis)
    _geometry              = args.get('geometry'              , DEFAULT_CONFIG.geometry)
    _view                  = args.get('view'                  , DEFAULT_CONFIG.view)
    _zoom                  = args.get('zoom'                  , DEFAULT_CONFIG.zoom)
    _show_scalar_bar       = args.get('show_scalar_bar'       , DEFAULT_CONFIG.show_scalar_bar)
    _display_representation= args.get('display_representation', DEFAULT_CONFIG.display_representation)
    _output_prefix         = args.get('output_prefix'         , DEFAULT_CONFIG.output_prefix)

    # These aren't directly used here, but passed as args in handle_coloring
    _colormap              = args.get('colormap'              , DEFAULT_CONFIG.colormap)
    _colormap_fuzzy_cutoff = args.get('colormap_fuzzy_cutoff' , DEFAULT_CONFIG.colormap_fuzzy_cutoff)
    _color_range_method    = args.get('color_range_method'    , DEFAULT_CONFIG.color_range_method)
    _custom_color_range    = args.get('custom_color_range'    , DEFAULT_CONFIG.custom_color_range)

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = _show_axis
    view.ViewSize = _geometry

    projection = projector(object, *_project)

    display = Show(projection, view)
    view_handler(_view, _zoom)
    Hide(projection, view)

    for scalar in _scalars:
        print("Snapping", scalar )

        normed = PythonCalculator(Input=[projection])
        normed.Expression = f"inputs[0].PointData['{scalar}'] / {args.get('normalizing_factor')}"
        normed.ArrayName = scalar

        normedrange = normed.PointData.GetArray(scalar).GetRange()
        print(f"Normed range = {normedrange}")

        threshold = create_threshold(normed, scalar, 'above', 0, _threshold_reference * _threshold_factor)

        display = Show(threshold, view)
        display.Representation = _display_representation

        wLUT, _ = handle_coloring(threshold, display, scalar, args)

        configure_scalar_bar(wLUT, view, config.get('ColorBar'))
        UpdateScalarBars()
        display.SetScalarBarVisibility(view, _show_scalar_bar)

        screenshot_filename = f'hotspot_{_threshold_factor}x{_threshold_reference}_{_output_prefix}_{scalar}.png'
        print(f'Saving screenshot to file: {screenshot_filename}')
        SaveScreenshot(screenshot_filename, view, ImageResolution=_geometry, TransparentBackground=1)

        args = Dict(args)

        if args.overlay:
            overlay = read_files([args.overlay], filetype=args['filetype'])
            print(f"Using {args.overlay} to generate overlay edges")
        else: 
            overlay = object
            print(f"Using full object to generate overlay edges")

        # view = GetActiveViewOrCreate('RenderView')
        surfaces = ExtractSurface(Input=overlay)
        connectivity = Connectivity(Input=surfaces)
        connectivityDisplay = Show(connectivity, view)

        view.OrientationAxesVisibility = int(args.show_axis)

        nord10 = [94, 129, 172]
        color_rgb = [ x/255 for x in nord10]

        Hide(connectivity, view)

        # NOTE: Threshold  range will be (0, n) where n is number of beads.
        # Typically, the interstitial domain is the last, n+1th region.
        # Here, we ignore the interstitial region by setting nbeads = n, and not n+1.
        nbeads = int(connectivity.PointData.GetArray("RegionId").GetRange()[1])
        print("Number of Objects:", nbeads)

        ## TODO: just use 0..n as threshold range instead of this nonsense
        # for index in range(nbeads):
        # print("Processing bead: {index}".format(index=index))
        print("Processing beads: {nbeads}".format(nbeads=nbeads))
        bead_threshold = Threshold(Input=connectivity)
        # threshold.ThresholdRange = [0, nbeads-1]
        # bead_threshold.LowerThreshold = 0
        # bead_threshold.UpperThreshold = nbeads-1
        bead_threshold.LowerThreshold = 0
        bead_threshold.UpperThreshold = nbeads
        bead_threshold.ThresholdMethod = vtkThreshold.THRESHOLD_BETWEEN
        bead_threshold_display = Show(bead_threshold, view)
        bead_threshold_display.ColorArrayName = ['POINTS', '']
        ColorBy(bead_threshold_display, None)
        # threshold.UpdatePipeline()
        bead_threshold_display.AmbientColor = color_rgb
        bead_threshold_display.DiffuseColor = color_rgb
        bead_threshold_display.Representation = args.display_representation
        bead_threshold_display.Opacity = 0.4

        Show(bead_threshold, view)

        screenshot_filename = f'hotspot_overlaid_{_threshold_factor}x{_threshold_reference}_{_output_prefix}_{scalar}.png'
        print(f'Saving screenshot to file: {screenshot_filename}')
        SaveScreenshot(screenshot_filename, view, ImageResolution=_geometry, TransparentBackground=1)

        Delete(display)
        Delete(threshold)

def hotspots_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")
    ap.add_argument("--normalizing-factor", type=float, default=1.0, help="Value to normalize all projected scalars")
    ap.add_argument("--threshold-reference", type=float, help="Value above which to plot in threshold (along with threshold factor)")
    ap.add_argument("--threshold-factor", type=float, default=1.0, help="Multiplicative factor for threshold-reference")
    ap.add_argument("--overlay", default=None, help="Object used to generate edges to use as overlay")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args

if __name__=="__main__":

    config = ConfigHandler()
    args, local_args_list = config.parse_config_and_cmdline_args()
    args = hotspots_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    if args['standalone']: 
        readers = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])

        if args['append_datasets']:
            appended = AppendDatasets(Input=readers)
            hotspots(appended, **args)
        else: 
            print("ERROR: Screenshotting for pure --standalone not yet fully supported. Please use along with --append-datasets")

            # If the next two lines are uncommented, it will work, but the
            # screenshots will get overwritten because filenames aren't unique

            # for ireader in readers: 
            #     screenshot(ireader, args)
    else: 
        reader = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])
        hotspots(reader, **args)

