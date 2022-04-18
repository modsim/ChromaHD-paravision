"""hotspots.py

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
from paravision.project import project

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

def hotspots(object, args):
    """ Screenshot a given object with a given projection"""

    args.scalars = args.scalars or object.PointArrayStatus

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']

    projection = project(object, args)

    display = Show(projection, view)
    view_handler(args['view'], args['zoom'])
    Hide(projection, view)

    for scalar in args['scalars']:
        print("Snapping", scalar )

        threshold = create_threshold(projection, scalar, 'above', 0, args.threshold_reference * args.threshold_factor)

        display = Show(threshold, view)
        display.Representation = args.display_representation

        wLUT, _ = handle_coloring(threshold, display, scalar, args)

        configure_scalar_bar(wLUT, view, config.get('ColorBar'))
        UpdateScalarBars()
        display.SetScalarBarVisibility(view, args['show_scalar_bar'])

        screenshot_filename = f'screenshot_{args.output_prefix}_{scalar}.png'
        print(f'Saving screenshot to file: {screenshot_filename}')
        SaveScreenshot(screenshot_filename, view, ImageResolution=args['geometry'], TransparentBackground=1)

        Delete(display)
        Delete(threshold)

def hotspots_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")
    ap.add_argument("--threshold-reference", type=float, help="Value above which to plot in threshold (along with threshold factor)")
    ap.add_argument("--threshold-factor", type=float, default=1.0, help="Multiplicative factor for threshold-reference")

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
            hotspots(appended, args)
        else: 
            print("ERROR: Screenshotting for pure --standalone not yet fully supported. Please use along with --append-datasets")

            # If the next two lines are uncommented, it will work, but the
            # screenshots will get overwritten because filenames aren't unique

            # for ireader in readers: 
            #     screenshot(ireader, args)
    else: 
        reader = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])
        hotspots(reader, args)

