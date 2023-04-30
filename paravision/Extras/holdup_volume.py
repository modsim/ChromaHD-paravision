from paraview.simple import *
from paravision.utils import view_handler
from paravision.utils import read_files
from paravision.utils import configure_scalar_bar
from paravision.utils import find_preset
from paravision.utils import find_files
from paravision.utils import create_threshold
from paravision.project import projector
from paravision.integrate import integrate
from paravision.screenshot import screenshot

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json
from pathlib import Path

from paravision.defaults import DEFAULT_CONFIG
from paravision.utils import script_main
from paravision.utils import extract_surface_with_aligned_normal

def holdup_volume(object, **args):
    """ 

    scalars:List[str], project:List, show_axis:bool, geometry:List[float], view:List[str],
    zoom: float, show_scalar_bar:bool, colormap:str, colormap_fuzzy_cutoff:float, 
    display_representation:str, color_range_method:str, custom_color_range:List[float],
    output_prefix:str
    """
    _project               = args.get('project'               , DEFAULT_CONFIG.project) 
    _output_prefix         = args.get('output_prefix'         , DEFAULT_CONFIG.output_prefix)

    timeArray = object.TimestepValues

    ## TODO: Could potentially append_datasets

    if not args.get('flow'):
        raise RuntimeError("Please provide --flow <flowfield_file> args.")
    else:
        flow = read_files([args['flow']], filetype=args['filetype'])

    if args.get('resample_flow'):
        # NOTE: Resampling is only required when the flowfield information is taken from the FLOW mesh instead of the MASS mesh mapping of the flowfield.
        print("Resampling the flowfield...")
        flow = ResampleWithDataset(registrationName='resampled_flow', SourceDataArrays=flow, DestinationMesh=object)
        flow.CellLocator = 'Static Cell Locator'

    if _project[0] != 'none':
        raise NotImplementedError('Projection not implemented yet')
    else: 

        ## NOTE: 
        # This is extremely inefficient. I assume it's because we have SOOO
        # MANY particles and each of their surfaces gets extracted. And normals
        # are generated for them.  
        #
        # Alternate strat: Clip it before packed-bed begins

        print("Clipping flow mesh")
        flow_left = projector(flow, 'clip', 'Plane', 0.0120, 'z')
        flow_right= projector(flow, 'clip', 'Plane', 0.9880, '-z')

        print("Extracting flow surfaces")
        flow_in = extract_surface_with_aligned_normal(flow_left, 'Z', -1.0)
        flow_out = extract_surface_with_aligned_normal(flow_right, 'Z', 1.0)

        print("Screenshotting flow surfaces")
        screenshot(flow_in, view = ['z', 'y'], scalars=['None'], output_prefix='flow_in_xy')
        screenshot(flow_out, view = ['z', 'y'], scalars=['None'], output_prefix='flow_out_xy')
        screenshot(flow_in, view = ['x', 'y'], scalars=['None'], output_prefix='flow_in_yz')
        screenshot(flow_out, view = ['x', 'y'], scalars=['None'], output_prefix='flow_out_yz')

        print("Clipping mass mesh")
        mass_left = projector(object, 'clip', 'Plane', 0.0120, 'z')
        mass_right= projector(object, 'clip', 'Plane', 0.9880, '-z')

        print("Extracting mass surfaces")
        mass_in = extract_surface_with_aligned_normal(mass_left, 'Z', -1.0)
        mass_out = extract_surface_with_aligned_normal(mass_right, 'Z', 1.0)

        print("Screenshotting mass surfaces")
        screenshot(mass_in, view = ['z', 'y'], scalars=['None'], output_prefix='mass_in_xy')
        screenshot(mass_out, view = ['z', 'y'], scalars=['None'], output_prefix='mass_out_xy')
        screenshot(mass_in, view = ['x', 'y'], scalars=['None'], output_prefix='mass_in_yz')
        screenshot(mass_out, view = ['x', 'y'], scalars=['None'], output_prefix='mass_out_yz')

        # uda_in = integrate(flow_in, ['scalar_2'], normalize=None, timeArray=[])
        # uda_out = integrate(flow_out, ['scalar_2'], normalize=None, timeArray=[])
        # print("Flowrate in:", uda_in)
        # print("Flowrate out:", uda_out)
        #
        # cuda_in = calc_cuda(flow_in, mass_in, timeArray)
        # cuda_out = calc_cuda(flow_out, mass_out, timeArray)
        #
        # print(cuda_in)
        # print(cuda_out)
        #
        # csvWriter('chromatogram.csv', timeArray, chromatogram)

def calc_cuda(flow_slice, mass_slice, timeArray):
    # NOTE: Assumes input is 2D output of extractRNG applied on the outlet
    # conc * velocity_z
    cu = PythonCalculator(Input=[mass_slice, flow_slice])
    cu.Expression = "inputs[0].PointData['scalar_0'] * inputs[1].PointData['scalar_2']"
    c_u_dA = integrate(cu, ['result'], normalize=None, timeArray=timeArray)
    return c_u_dA

def holdup_volume_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("--flow", help="Flowfield pvtu/vtu file for use in chromatograms. May need --resample-flow.")
    ap.add_argument("--resample-flow", action=argparse.BooleanOptionalAction, default=None, help="Flag to resample flowfield data using concentration mesh")

    ap.add_argument("FILES", nargs='*', help="files..")

    print(local_args_list)

    local_args = ap.parse_args(local_args_list)
    local_args = Dict(vars(local_args))

    print_json(data=local_args)

    args.update([ (k,v) for k,v in local_args.items() if v is not None])

    return args

if __name__=="__main__":
    script_main(holdup_volume_parser, holdup_volume)
