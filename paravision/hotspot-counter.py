"""hotspots-counter.py

Given a flow simulation with velocity components as scalars, 
output csv file with <threshold_factor> and <num_hotspots> as columns

Usage: pvrun -p <hotspots-counter.py> --threshold-reference <value>

NOTE: CANNOT RUN THIS IN PARALLEL DUE TO THE CONNECTIVITY FILTER FAILING IN PARALLEL.
"""

from paraview.simple import *
from paravision.utils import read_files
from paravision.utils import create_threshold
from paravision.utils import csvWriter
from paravision.utils import get_volume
from paravision.utils import save_screenshot
from paravision.utils import handle_coloring
from paravision.utils import configure_scalar_bar
from paravision.utils import view_handler

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

def hotspots(object, args):

    args.scalars = args.scalars or object.PointArrayStatus

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']

    full_volume = get_volume(object)

    display = Show(object, view)
    view_handler(args['view'], args['zoom'])
    Hide(object, view)

    for scalar in args['scalars']:
        print(f"Operating on scalar: {scalar}")

        n_hotspots_all = []
        hotspot_volumes = []

        for h_factor in range(1,args['threshold_factor_max'] + 1): 

            print(f"{h_factor = }")

            if args['threshold_type'] == 'above': 
                threshold = create_threshold(object, scalar, 'above', 0, args.threshold_reference * h_factor)
            elif args['threshold_type'] == 'below': 
                threshold = create_threshold(object, scalar, 'below', args.threshold_reference * h_factor, 0)

            if args['hotspot-count']: 
                conn = Connectivity(Input=threshold)
                conn_data = servermanager.Fetch(conn)
                n_hotspots = conn_data.GetCellData().GetArray('RegionId').GetRange()[1] + 1
                print(f"Found {n_hotspots} hotspots for threshold values above {args.threshold_reference * h_factor}")
                n_hotspots_all.append(n_hotspots)
                Delete(conn)
                csvWriter(f'{args.output_prefix}_nHotspots_factor.csv', list(range(1,h_factor+1)), n_hotspots_all)

            if args['hotspot_volume']: 
                hotspot_volumes.append(get_volume(threshold))
                csvWriter(f'{args.output_prefix}_volume_factor.csv', list(range(1,h_factor+1)), hotspot_volumes)
                csvWriter(f'{args.output_prefix}_volumefraction_factor.csv', list(range(1,h_factor+1)), [ item/full_volume for item in hotspot_volumes] )

            if args['hotspot_screenshot']:
                save_screenshot(threshold,
                                view,
                                scalar,
                                args,
                                f"screenshot_{args.output_prefix}_{scalar}_hotspot-threshold-{args.threshold_reference}-{args.threshold_type}-{h_factor:02d}.png"
                                )

            Delete(threshold)

def hotspots_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")

    ap.add_argument("--hotspot-count", action='store_true', help="Count the number of hotspots at each threshold_factor and save to csv")
    ap.add_argument("--hotspot-volume", action='store_true', default=None, help="Calculate hotspot volumes at each threshold_factor ")
    ap.add_argument("--hotspot-screenshot", action='store_true', default=None, help="Screenshot hotspot volumes at each threshold_factor ")

    ap.add_argument("--threshold-type", default=None, choices=['above', 'below'], help="'above', 'below' will be fuzzy matched to exact available options from paraview")
    ap.add_argument("--threshold-reference", type=float, help="Value above which to plot in threshold (along with hotspot factor)")
    ap.add_argument("--threshold-factor-max", type=int, help="Max value of threshold factor to loop until")

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

