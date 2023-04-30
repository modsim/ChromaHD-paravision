from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import read_files
from paravision.utils import configure_scalar_bar
from paravision.utils import find_preset
from paravision.project import projection

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

def stream_tracer(object, args):
    """Calculate a flowfield stream trace"""

    args.scalars = args.scalars or object.PointArrayStatus

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']

    projection = projection(object, *args.project)
    pd = projection.PointData
    
    calculator = Calculator(Input=projection)
    calculator.ResultArrayName = 'velocity'
    calculator.Function = 'iHat * scalar_0 + jHat * scalar_1 + kHat * scalar_2'
    calculator.ResultArrayType = 'Double'



def stream_tracer_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args

if __name__=="__main__":

    config = ConfigHandler()
    args, local_args_list = config.parse_config_and_cmdline_args()
    args = stream_tracer_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    stream_tracer(reader, args)
