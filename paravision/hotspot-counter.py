"""hotspots-counter.py

Given a flow simulation with velocity components as scalars, 
output csv file with <threshold_factor> and <num_hotspots> as columns

Usage: pvrun -p <hotspots-counter.py> --threshold-reference <value>

NOTE: CANNOT RUN THIS IN PARALLEL DUE TO THE CONNECTIVITY FILTER FAILING IN PARALLEL.
"""

from paraview.simple import *
from paravision.utils import read_files
from paravision.utils import create_threshold
from paravision.project import project
from paravision.utils import csvWriter

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

    for scalar in args['scalars']:
        print("Snapping", scalar )

        n_hotspots_all = []

        for h_factor in range(1,11): 

            threshold = create_threshold(object, scalar, 'above', 0, args.threshold_reference * h_factor)

            conn = Connectivity(Input=threshold)
            conn_data = servermanager.Fetch(conn)
            n_hotspots = conn_data.GetCellData().GetArray('RegionId').GetRange()[1] + 1
            print(f"Found {n_hotspots} hotspots for threshold values above {args.threshold_reference * h_factor}")

            n_hotspots_all.append(n_hotspots)

            Delete(threshold)
            Delete(conn)

        csvWriter('nHotspots_factor.csv', list(range(1,11)), n_hotspots_all)

def hotspots_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")
    ap.add_argument("--threshold-reference", type=float, help="Value above which to plot in threshold (along with hotspot factor)")

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

