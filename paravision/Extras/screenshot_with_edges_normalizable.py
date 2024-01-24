#!/usr/bin/env python3

"""
A shorter, newer, more modular implementation of the screenshot_with_edges plugin
"""

from paraview.simple import *
from paravision.utils import script_main_new, default_parser, default_local_parser, argcheck
from paravision.utils import get_view, view_handler
from paravision.utils import handle_coloring
from paravision.utils import configure_scalar_bar
from paravision.utils import read_files
from paravision.project import projector
from addict import Dict
from rich import print, print_json
import argparse

def driver(obj, **args):
    args = Dict(args)

    # What is the purpose of all these checks?
    # What I truly need is to mention which cmdline args are NOT used in the current script.
    # The rest can just be dumped to stdout
    args.scalars = args.scalars or obj.PointArrayStatus

    view = get_view(args)
    projection = projector(obj, *args.project)

    for scalar in args.scalars:
        normed = PythonCalculator(Input=[projection])
        normed.Expression = f"inputs[0].PointData['{scalar}'] / {args.normalizing_factor}"
        normed.ArrayName = scalar

        sc_display = None
        if args.screenshot: 
            sc_display = Show(normed, view)
            sc_display.Representation = args.display_representation

            wLUT, _ = handle_coloring(normed, sc_display, scalar, args)
            # HideScalarBarIfNotNeeded(wLUT, view)
            configure_scalar_bar(wLUT, view, args.get('ColorBar'))
            sc_display.SetScalarBarVisibility(view, args.show_scalar_bar)

        # screenshot_filename = f'screenshot_with_edges_{args.output_prefix}_{scalar}.png'
        # print(f'Saving screenshot to file: {screenshot_filename}')
        # SaveScreenshot(screenshot_filename, view, ImageResolution=args.geometry, TransparentBackground=1)
        # Hide(display, view)

        if args.overlay:
            overlay = read_files([args.overlay], filetype=args['filetype'])
            print(f"Using {args.overlay} to generate overlay edges")
        elif args.screenshot:
            overlay = normed
            print(f"Using projection (same as screenshot) to generate overlay edges")
        else: 
            overlay = obj
            print(f"Using full object to generate overlay edges")

        if args.mode == 'features':
            print("Generating feature edges from screenshot...")
            edges = FeatureEdges(overlay)
        elif args.mode == 'surfaces_projection' :
            print("Generating surfaces from prime object...")
            surfaces = ExtractSurface(overlay)
            print("Projecting surfaces...")
            edges = projector(surfaces, *args.project)
        elif args.mode.lower() == 'none':
            edges = None
        else:
            raise ValueError("Bad Mode")


        edge_display = None
        if edges is not None: 
            edge_display = Show(edges, view)
            edge_display.LineWidth = args.linewidth
            edge_display.AmbientColor = args.linecolor
            edge_display.DiffuseColor = args.linecolor

            edge_display.ColorArrayName = ['POINTS', '']
            ColorBy(edge_display, None)

        view_handler(args.view, args.zoom)
        # view.Update()
        screenshot_filename = f'screenshot_with_edges_{scalar}_{args.output_prefix}.png'
        print(f'Saving screenshot to file: {screenshot_filename}')
        SaveScreenshot(screenshot_filename, view, ImageResolution=args.geometry, TransparentBackground=1)

        if edge_display:
            Hide(edge_display, view)
        if sc_display: 
            Hide(sc_display, view)

        Delete(normed)


def parser(argslist):
    ap = default_parser()
    ap.add_argument("--normalizing-factor", type=float, default=1.0, help="Value to normalize all projected scalars")
    ap.add_argument("-lw", "--linewidth", type=int, default=2.0, help="Line width for drawing edges")
    ap.add_argument("-lc", "--linecolor", type=int, nargs=3, default=[0.0, 0.0, 0.0], help="Line color in [R, G, B] fraction for drawing edges")
    ap.add_argument("--screenshot", action=argparse.BooleanOptionalAction, default=True, help="Run screenshotter before drawing lines")
    ap.add_argument("--overlay", default=None, help="Object used to generate edges to use as overlay")
    ap.add_argument("--mode", choices = ['features', 'surfaces_projection', 'none'], default='surfaces_projection', help="Method of extracting edges from overlay object")
    args = Dict(vars(ap.parse_args(argslist)))
    print_json(data=args)
    return args

if __name__ == "__main__":
    script_main_new(parser, driver)
