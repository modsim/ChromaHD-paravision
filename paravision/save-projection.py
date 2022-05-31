from paraview.simple import *
from paravision.utils import read_files
from paravision.project import project
from paravision.integrate import integrate

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

def saveprojection(object, args): 

    args.scalars = args.scalars or object.PointArrayStatus
    # args.scalars = args.scalars 
    # scalars = args['scalars']
    # timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')

    projection = project(object, args)

    # integrated = integrate(projection, ['scalar_0'], normalize=None, timeArray=[])
    # print(integrated)

    SaveData(f"{args.saveas}", proxy=projection, PointDataArrays=args.scalars)

def saveprojection_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")
    ap.add_argument("--saveas", help="Output filename")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args

if __name__=="__main__":

    config = ConfigHandler()
    args, local_args_list = config.parse_config_and_cmdline_args()
    args = saveprojection_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])
    saveprojection(reader, args)

