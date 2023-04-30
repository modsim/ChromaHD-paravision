from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import read_files
from paravision.utils import configure_scalar_bar
from paravision.utils import find_preset
from paravision.utils import find_files
from paravision.project import projector
from paravision.chromatogram import chromatogram

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json
from pathlib import Path

from paravision.defaults import DEFAULT_CONFIG

def driver(object, **args):
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

    slices = ( projector(reader, _project[0], _project[1], i, _project[3]) for i in range(_project[2]) )
    for slice in slices:
        args.type = 'full'
        chromatogram(slice, args)

def parse_local_args(args, local_args_list):

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
    args = parse_local_args(*config.parse_config_and_cmdline_args())

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    if args['standalone']: 
        readers = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])

        if args['append_datasets']:
            appended = AppendDatasets(Input=readers)
            driver(appended, **args)
        else: 
            # Use input filenames in output using output_prefix
            files, filetype = find_files(args['FILES'], args['filetype'])
            print("FILES =", files)
            _output_prefix         = args.get('output_prefix', DEFAULT_CONFIG.output_prefix)
            for ind, ireader in enumerate(readers): 
                args['output_prefix'] = f"{Path(files[ind]).stem.strip()}_{_output_prefix}"
                driver(ireader, **args)
    else: 
        reader = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])
        driver(reader, **args)
