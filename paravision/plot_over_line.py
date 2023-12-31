from paraview.simple import *

from paravision.defaults import DEFAULT_CONFIG
from paravision.project import projector
from paravision.utils import script_main_new
from paravision.utils import default_parser

import argparse
from addict import Dict
from rich import print, print_json
from pathlib import Path

def driver(obj, **args):

    _scalars               = args.get('scalars') or obj.PointArrayStatus
    _project               = args.get('project'               , DEFAULT_CONFIG.project) 
    _view                  = args.get('view'                  , DEFAULT_CONFIG.view)
    _output_prefix         = args.get('output_prefix'         , DEFAULT_CONFIG.output_prefix)
    _p1 = args.get('point_1', [0.0, 0.0, 0.0])
    _p2 = args.get('point_2', [0.0, 0.0, 0.0])

    # view = GetActiveViewOrCreate('RenderView')
    # view.ViewSize = _geometry

    projected = projector(obj, *_project)
    plotOverLine = PlotOverLine(obj)
    plotOverLine.Point1 = _p1
    plotOverLine.Point2 = _p2

    SaveData(f"plotOverLine_{_output_prefix}.csv", proxy=plotOverLine, PointDataArrays=_scalars, WriteTimeSteps=0) 

def local_parser(local_args_list):

    ## Or use utils.default_parser()?
    ap = default_parser()

    # ap.add_argument("FILES", nargs='*', help="files..")
    ap.add_argument("-p1", "--point-1", nargs=3, type=float, help="Point 1 coords")
    ap.add_argument("-p2", "--point-2", nargs=3, type=float, help="Point 2 coords")

    print(local_args_list)

    args = ap.parse_args(local_args_list)
    args = Dict(vars(args))
    print_json(data=args)

    return args

if __name__=="__main__":
    script_main_new(local_parser, driver)
