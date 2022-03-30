from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import read_files
from paravision.utils import configure_scalar_bar
from paravision.utils import find_preset
from paravision.project import project

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

def screenshot(object, args):
    """ Screenshot a given object with a given projection"""

    args.scalars = args.scalars or object.PointArrayStatus
    # args.scalars = args.scalars 
    # scalars = args['scalars']
    # timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']

    projection = project(object, args)
    pd = projection.PointData

    for scalar in args['scalars']:
        print("Snapping", scalar )

        display = Show(projection, view)
        display.Representation = args['display_representation']

        if scalar == 'None':
            ColorBy(display, None)
        else:
            ColorBy(display, ('POINTS', scalar))

        view_handler(args['view'], args['zoom'])
        # view.Update()

        wLUT:Proxy = GetColorTransferFunction(scalar)
        wPWF = GetOpacityTransferFunction(scalar)
        # HideScalarBarIfNotNeeded(wLUT, view)

        wLUT.ApplyPreset(find_preset( args['colormap'] , args['colormap_fuzzy_cutoff']), True)

        if args.color_range_method == 'auto': 
            display.RescaleTransferFunctionToDataRange(False, True)
        elif args.color_range_method == 'startzero': 
            crange = pd.GetArray(scalar).GetRange()
            wLUT.RescaleTransferFunction(0.0, crange[1])
        elif args.color_range_method == 'midzero': 
            crange = pd.GetArray(scalar).GetRange()
            wLUT.RescaleTransferFunction(-abs(max(crange, key=abs)), abs(max(crange, key=abs)))
        elif args.color_range_method == 'custom': 
            wLUT.RescaleTransferFunction(args.custom_color_range[0], args.custom_color_range[1])

        configure_scalar_bar(wLUT, view, config.get('ColorBar'))

        UpdateScalarBars()
        display.SetScalarBarVisibility(view, args['show_scalar_bar'])
        # view.Update()
        # display.UpdatePipeline()

        screenshot_filename = f'screenshot_{args.output_prefix}_{scalar}.png'
        print(f'Saving screenshot to file: {screenshot_filename}')
        SaveScreenshot(screenshot_filename, view, ImageResolution=args['geometry'], TransparentBackground=1)
        Hide(display, view)

def screenshot_parser(args, local_args_list):

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
    args = screenshot_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    if args['standalone']: 
        readers = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])

        if args['append_datasets']:
            appended = AppendDatasets(Input=readers)
            screenshot(appended, args)
        else: 
            print("ERROR: Screenshotting for pure --standalone not yet fully supported. Please use along with --append-datasets")

            # If the next two lines are uncommented, it will work, but the
            # screenshots will get overwritten because filenames aren't unique

            # for ireader in readers: 
            #     screenshot(ireader, args)
    else: 
        reader = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])
        screenshot(reader, args)
