from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import read_files
from paravision.utils import configure_scalar_bar
from paravision.utils import find_preset
from paravision.project import projector

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

from paravision.defaults import DEFAULT_CONFIG

def screenshot(object, **args):
    """ 
    Screenshot a given object with a given projection. Takes the following kwargs.

    scalars:List[str], project:List, show_axis:bool, geometry:List[float], view:List[str],
    zoom: float, show_scalar_bar:bool, colormap:str, colormap_fuzzy_cutoff:float, 
    display_representation:str, color_range_method:str, custom_color_range:List[float],
    output_prefix:str
    """

    _scalars               = args.get('scalars') or object.PointArrayStatus
    _project               = args.get('project'               , DEFAULT_CONFIG.project) 
    _show_axis             = args.get('show_axis'             , DEFAULT_CONFIG.show_axis)
    _geometry              = args.get('geometry'              , DEFAULT_CONFIG.geometry)
    _view                  = args.get('view'                  , DEFAULT_CONFIG.view)
    _zoom                  = args.get('zoom'                  , DEFAULT_CONFIG.zoom)
    _show_scalar_bar       = args.get('show_scalar_bar'       , DEFAULT_CONFIG.show_scalar_bar)
    _colormap              = args.get('colormap'              , DEFAULT_CONFIG.colormap)
    _colormap_fuzzy_cutoff = args.get('colormap_fuzzy_cutoff' , DEFAULT_CONFIG.colormap_fuzzy_cutoff)
    _display_representation= args.get('display_representation', DEFAULT_CONFIG.display_representation)
    _color_range_method    = args.get('color_range_method'    , DEFAULT_CONFIG.color_range_method)
    _custom_color_range    = args.get('custom_color_range'    , DEFAULT_CONFIG.custom_color_range)
    _output_prefix         = args.get('output_prefix'         , DEFAULT_CONFIG.output_prefix)

    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = _show_axis
    view.ViewSize = _geometry

    projection = projector(object, *_project)
    pd = projection.PointData

    for scalar in _scalars:
        print("Snapping", scalar )

        display = Show(projection, view)
        display.Representation = _display_representation

        if scalar == 'None':
            display.ColorArrayName = ['POINTS', '']
            ColorBy(display, None)
        elif scalar == 'CellEntityIds': 
            ColorBy(display, ('CELLS', 'CellEntityIds'))
        else:
            ColorBy(display, ('POINTS', scalar))

        view_handler(_view, _zoom)
        # view.Update()

        wLUT:Proxy = GetColorTransferFunction(scalar)
        wPWF = GetOpacityTransferFunction(scalar)
        # HideScalarBarIfNotNeeded(wLUT, view)

        wLUT.ApplyPreset(find_preset(_colormap, _colormap_fuzzy_cutoff), True)

        if _color_range_method == 'auto': 
            display.RescaleTransferFunctionToDataRange(False, True)
        elif _color_range_method == 'startzero': 
            crange = pd.GetArray(scalar).GetRange()
            wLUT.RescaleTransferFunction(0.0, crange[1])
        elif _color_range_method == 'midzero': 
            crange = pd.GetArray(scalar).GetRange()
            wLUT.RescaleTransferFunction(-abs(max(crange, key=abs)), abs(max(crange, key=abs)))
        elif _color_range_method == 'custom': 
            wLUT.RescaleTransferFunction(_custom_color_range[0], _custom_color_range[1])

        configure_scalar_bar(wLUT, view, config.get('ColorBar'))

        UpdateScalarBars()
        display.SetScalarBarVisibility(view, _show_scalar_bar)
        # view.Update()
        # display.UpdatePipeline()

        screenshot_filename = f'screenshot_{_output_prefix}_{scalar}.png'
        print(f'Saving screenshot to file: {screenshot_filename}')
        SaveScreenshot(screenshot_filename, view, ImageResolution=_geometry, TransparentBackground=1)
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
        screenshot(reader, **args)
