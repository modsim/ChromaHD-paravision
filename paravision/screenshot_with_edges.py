from paraview.simple import *

from paravision import ConfigHandler
from paravision.defaults import DEFAULT_CONFIG
from paravision.project import projector
from paravision.utils import configure_scalar_bar
from paravision.utils import find_files
from paravision.utils import find_preset
from paravision.utils import read_files
from paravision.utils import script_main_new
from paravision.utils import view_handler
from paravision.screenshot import screenshot

import argparse
from addict import Dict
from rich import print, print_json
from pathlib import Path

def driver(obj, **args):

    _project               = args.get('project'               , DEFAULT_CONFIG.project) 
    _geometry              = args.get('geometry'              , DEFAULT_CONFIG.geometry)
    _view                  = args.get('view'                  , DEFAULT_CONFIG.view)
    _zoom                  = args.get('zoom'                  , DEFAULT_CONFIG.zoom)
    _output_prefix         = args.get('output_prefix'         , DEFAULT_CONFIG.output_prefix)
    _linewidth = args.get('linewidth', 2.0)
    _linecolor = args.get('linecolor', [0.0, 0.0, 0.0])
    _screenshot = args.get('screenshot', True) 
    _overlay = args.get('overlay', None)
    _mode = args.get('mode', 'surfaces_projection')

    view = GetActiveViewOrCreate('RenderView')
    view.ViewSize = _geometry

    screenshotted=None
    sc_display = None
    if _screenshot:
        screenshotted = screenshot(obj, **args)

    if _overlay:
        overlay = read_files([_overlay], filetype=args['filetype'])
        print(f"Using {_overlay} to generate overlay edges")
    elif _screenshot:
        overlay = screenshotted
        print(f"Using projection (same as screenshot) to generate overlay edges")
    else: 
        overlay = obj
        print(f"Using full object to generate overlay edges")

    if _mode == 'features':
        print("Generating feature edges from screenshot...")
        edges = FeatureEdges(overlay)
    elif _mode == 'surfaces_projection' :
        print("Generating surfaces from prime object...")
        surfaces = ExtractSurface(overlay)
        print("Projecting surfaces...")
        edges = projector(surfaces, *_project)
    else:
        raise ValueError("Bad Mode")

    if _screenshot:
        sc_display = Show(screenshotted, view)
        sc_display.SetScalarBarVisibility(view, True)

    display = Show(edges, view)
    display.LineWidth = _linewidth
    display.AmbientColor = _linecolor
    display.DiffuseColor = _linecolor

    display.ColorArrayName = ['POINTS', '']
    ColorBy(display, None)

    view_handler(_view, _zoom)
    # view.Update()

    screenshot_filename = f'screenshot_withEdges_{_output_prefix}.png'
    print(f'Saving screenshot to file: {screenshot_filename}')
    SaveScreenshot(screenshot_filename, view, ImageResolution=_geometry, TransparentBackground=1)
    Hide(display, view)


def local_parser(local_args_list):

    ## Or use utils.default_parser()?
    ap = argparse.ArgumentParser()

    ap.add_argument("FILES", nargs='*', help="files..")
    ap.add_argument("-lw", "--linewidth", type=int, help="Line width for drawing edges")
    ap.add_argument("-lc", "--linecolor", type=int, nargs=3, help="Line color in [R, G, B] fraction for drawing edges")
    ap.add_argument("--screenshot", action=argparse.BooleanOptionalAction, help="Run screenshotter before drawing lines")
    ap.add_argument("--overlay", default=None, help="Object used to generate edges to use as overlay")
    ap.add_argument("--mode", choices = ['features', 'surfaces_projection'], default=None, help="Method of extracting edges from overlay object")

    print(local_args_list)

    args = ap.parse_args(local_args_list)
    args = Dict(vars(args))
    print_json(data=args)

    return args

if __name__=="__main__":
    script_main_new(local_parser, driver)
