from paraview.simple import *
from paravision.utils import script_main, get_bounds, get_volume

import argparse
from addict import Dict
from rich import print, print_json
import json

def mesh_info(object, **args):
    bounds = get_bounds(object)
    print(bounds)
    x0,x1,y0,y1,z0,z1 = bounds
    print(f"x => [{x0}, {x1}] | delta = {x1-x0}")
    print(f"y => [{y0}, {y1}] | delta = {y1-y0}")
    print(f"z => [{z0}, {z1}] | delta = {z1-z0}")

    volume = get_volume(object)
    print(f"Volume = {volume}")

    data = {
            "bounds": {
                "xmin": x0,
                "xmax": x1,
                "ymin": y0,
                "ymax": y1,
                "zmin": z0,
                "zmax": z1,
                },
            "deltas": {
                "x": x1-x0,
                "y": y1-y0,
                "z": z1-z0
                },
            "volume": volume
            }

    with open('mesh_info.json', 'w') as fp:
        json.dump(data, fp, indent=4)

def mesh_info_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args

if __name__=="__main__":
    script_main(mesh_info_parser, mesh_info)
