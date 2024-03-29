from paraview.simple import *
import struct
from fuzzywuzzy import process, fuzz
from pathlib import Path
import importlib.util
import csv
import os
import argparse
from addict import Dict
from rich import print, print_json

from vtkmodules.numpy_interface import dataset_adapter as dsa

from rich import print

from paravision import ConfigHandler

def appendToBin(arr, filename, f):
    with(open(filename, 'ab')) as output:
        for i in arr:
            output.write(struct.pack(f, i))

def csvWriter(filename, x, y):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(zip(x, y))

def arr_to_bin(arr, filename, dataformat):
    # NOTE: see https://docs.python.org/3/library/struct.html
    with(open(filename, 'wb')) as output:
        for i in arr:
            output.write(struct.pack(dataformat, i))

def arr_to_bin_unpacked(arr, filename, vartype, mode:str='w'):
    ## vartype = d, f etc
    ## NOTE: uses native by default endianness
    ## Probably faster than the default one
    with(open(filename, mode+'b')) as output:
        output.write(struct.pack(str(len(arr)) + vartype, *arr))

def reference_axisNormal(input:str):
    if input.lower() == "x":
        return [1, 0, 0]
    elif input.lower() == "y":
        return [0, 1, 0]
    elif input.lower() == "z":
        return [0, 0, 1]

def default_origin_normal(reader, origin, normal):
    """
    Input origin and normal parameters for --project should be <float> <string>
    This function takes those values and returns sane vectors to be used in the project() function

    Uses origin as float factor to bounding box limits in the normal direction (unsigned).
    Uses normal direction string to get vectors using direction_handler.

    """
    view = GetActiveViewOrCreate('RenderView')
    HideAll()
    display = Show(reader, view)
    SetActiveSource(reader)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    print('bbox: ', xmin,xmax,ymin,ymax,zmin,zmax)
    Hide(reader, view)
    Delete(display)

    new_normal, value_format = direction_handler(normal)
    print(f"VALUE_FORMAT: {value_format}")
    if value_format == '%': 
        origin_mask = [ xmin + float(origin) * (xmax - xmin), ymin + float(origin) * (ymax - ymin), zmin + float(origin) * (zmax - zmin)]
        new_origin = [abs(x) * y for x,y in zip(new_normal, origin_mask)]
    elif value_format == '#':
        origin_mask = [float(origin)]*3
        new_origin = [abs(x) * y for x,y in zip(new_normal, origin_mask)]
    else:
        raise ValueError

    print(new_origin)
    return new_origin, new_normal

def get_bounds(reader): 
    SetActiveSource(reader)
    view = GetActiveViewOrCreate('RenderView')
    display = Show(reader, view)
    bounds = GetActiveSource().GetDataInformation().GetBounds()
    Hide(reader, view)
    return bounds

# WARNING: stuck with stupid defaults due to backward compatibility. Feel free to break it when you need to update.
def direction_handler(dir:str):
    """
    Convert from "+x" notation to [1, 0, 0] notation

    Full input spec: [+,-][x,y,z][%,#]
    Examples: +x% , -z#

    The symbols % and # are used to describe whether the the accompanying input
    values in `default_origin_normal` are in percentages of the bounding box or
    full coordinate values.
    """
    dir = dir.strip()

    if dir[0] not in ['-', '+']:
        dir = "+".join(["", dir])

    if dir[1] == "x":
        target = [1, 0, 0]
    elif dir[1] == "y":
        target = [0, 1, 0]
    elif dir[1] == "z":
        target = [0, 0, 1]
    else:
        raise(ValueError)

    if dir[0] == "-":
        target = [-x for x in target]
    elif dir[0] != "+":
        raise(ValueError)

    if len(dir) == 3: 
        assert dir[2] in ['%', '#']
        value_format = dir[2]
    else:
        value_format = '%'

    return target, value_format

def view_handler(viewopts:list, zoom:float):
    """
    Set camera view to viewopts ["+x", "-y"]  and zoom
    """
    target, _ = direction_handler(viewopts[0])
    viewup, _ = direction_handler(viewopts[1])

    print("Target:", target)
    print("viewup:", viewup)

    pos = [-x for x in target]

    camera = GetActiveCamera()
    camera.SetFocalPoint(target[0],target[1],target[2])
    camera.SetPosition(pos[0], pos[1], pos[2])
    camera.SetViewUp(viewup[0], viewup[1], viewup[2])
    ResetCamera()

    camera.Dolly(zoom)
    Render()

def get_cross_sections(reader, nSlice=1):
    ## Should return list of cross sections of a geometry

    view = GetActiveViewOrCreate('RenderView')
    display = Show(reader, view)
    display.Representation = args['display_representation']
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    Hide(reader, view)

    slices = []

    for zpos in np.linspace(zmin, zmax, nSlice):
        projection = project(reader, 'Slice', geometry='Plane', origin=[0,0,zpos], normal=[0,0,-1])
        slices.append(projection)

    return slices

def get_volume(object):
    integrated = IntegrateVariables(Input=object)
    intdata = servermanager.Fetch(integrated)
    intdata = dsa.WrapDataObject(intdata)
    int_volume = intdata.CellData['Volume'][0]
    Delete(integrated)
    return int_volume

# TODO: remove dependence on args. See also handle_coloring()
def save_screenshot(object, view, scalar, args, filename:str='screenshot.png' ): 
    display = Show(object, view)
    display.Representation = args.display_representation

    wLUT, _ = handle_coloring(object, display, scalar, args)

    configure_scalar_bar(wLUT, view, args.get('ColorBar'))
    UpdateScalarBars()
    display.SetScalarBarVisibility(view, args.show_scalar_bar)

    print(f'Saving screenshot to file: {filename}')
    SaveScreenshot(filename, view, ImageResolution=args['geometry'], TransparentBackground=1)

    Delete(display)


def find_preset(name, score_cutoff=70.0):
    """ Fuzzy find routine for presets. 
    Look in ScientificColourMaps7 if not found in ParaView and import
    Because the exact string for paraview preset colormap names is not easy to find
    """
    # TODO: Doesn't work great when you have, e.g., batlow and batlowW outside ParaView. 
    # whichever is loaded the other will always match the first one loaded, and
    # not find the second one outside paraview.

    presets = servermanager.vtkSMTransferFunctionPresets()
    presetNames = [ presets.GetPresetName(i) for i in range(presets.GetNumberOfPresets())]
    result = process.extractOne(name, presetNames, scorer=fuzz.token_set_ratio, score_cutoff=score_cutoff)
    if result: 
        print(f"Fuzzy found preset {result} for input '{name}' in ParaView")
        return result[0]
    else: 
        # return None
        print(f"Could not find the requested colormap preset ({name}) in ParaView. Looking in ScientificColourMaps7")
        # NOTE: probably a better way to do this
        root = Path(importlib.util.find_spec('paravision').submodule_search_locations[0])
        dir = root / "ScientificColourMaps7"
        files = list(dir.glob('*.xml'))
        filenames = [ x.stem for x in files ]
        result = process.extractOne(name, filenames, scorer=fuzz.token_set_ratio, score_cutoff=score_cutoff)
        if result:
            print(f"Fuzzy found preset {result} for input '{name}' in ScientificColourMaps7")
            print(f"Importing preset into ParaView for use")
            ImportPresets(filename=str(dir / (result[0] + ".xml") ))
            return result[0]
        else: 
            print(f"Could not find the requested colormap preset ({name}) in ParaView or ScientificColourMaps7")
            return None

def load_scientific_colormaps():
    """ Load all presets in ScientificColourMaps7
    
    Using this should avoid all the misses thanks to fuzziness in the above function
    """
    root = Path(importlib.util.find_spec('paravision').submodule_search_locations[0])
    dir = root / "ScientificColourMaps7"
    files = list(dir.glob('*.xml'))
    filenames = [ x.stem for x in files ]
    for filename in filenames:
        preset = find_preset(filename, score_cutoff=100)

def read_files(files, filetype='pvtu', standalone=False):
    """ Read the given list of files 

    standalone: bool => if true, reads files individually instead of serially
    filetype: default filetype to read. If files is [], look for files of this extension in current dir.
    """
    assert isinstance(files, list)
    files, filetype = find_files(files, filetype)

    if standalone:
        readers = [ read_files_inner(ifile, filetype) for ifile in files ]
        return readers
    else:
        reader =  read_files_inner(files, filetype)
        return reader

def find_files(files, filetype='pvtu'):
    if len(files) == 0:
        try:
            files = sorted([ file for file in os.listdir(".") if file.endswith(filetype) ], key=lambda x: int(x.split('.')[0].split('_')[-1]))
        except:
            print("Not sorting files.")
            files = [ file for file in os.listdir(".") if file.endswith(filetype) ]

        if len(files) == 0:
            print("Didn't find", filetype, "files in current folder.")
            sys.exit(-1)
    else:
        fileExtensions = set([os.path.splitext(infile)[1] for infile in files])
        if len(fileExtensions) > 1:
            print(f"Mixed File Formats Given! {fileExtensions}")
            print(f"files: {files}")
            sys.exit(-1)
        filetype = fileExtensions.pop().replace('.', '')

    print("Reading files: ", files)
    print("with filetype: ", filetype)

    return files, filetype

def read_files_inner(files, filetype):
    reader=None

    if filetype == 'xdmf':
        reader = XDMFReader(FileNames=files)
    elif filetype == 'vtu':
        reader = XMLUnstructuredGridReader(FileName=files)
    elif filetype == 'pvtu':
        reader = XMLPartitionedUnstructuredGridReader(FileName=files)
    elif filetype == 'vtk':
        reader = LegacyVTKReader(FileNames=files)
    elif filetype == 'pvd':
        reader = PVDReader(FileName=files)
    else:
        print(f"Unsupported File Format! ({filetype})")
        raise(ValueError)
    
    return reader

# TODO: remove plugin names from args
# TODO: remove plugin specific args (like --flow)
def parse_cmdline_args():
    """ Parser for individual module commands

    To parse commandline args for a generic visualization job (e.g., screenshot.py). 
    Using/implementing them is the responsibility of the plugin itself.
    """
    ap = argparse.ArgumentParser()

    ap.add_argument("-c","--config", help="YAML config file")

    ap.add_argument("-cg", "--chromatogram", choices=['full', 'shells'], help="Calculate chromatogram from given flat 2D surface of column. Requires --flow. See --shelltype.")
    ap.add_argument("--grm2d", nargs=2, type=int, help="Split into axial and radial sections and integrate scalars for fitting with 2D GRM. args: <ncol> <nrad>")
    ap.add_argument("--screenshot", action='store_true', help="Screenshot the given object")
    ap.add_argument("--bead-loading", action='store_true', help="Screenshot the given object")
    ap.add_argument("--radial-shell-integrate", choices=['Volume', 'Area', 'NoNorm'], const='NoNorm', nargs='?', help="Divide object radially and integrate. Choices indicate normalization method. See --nrad, --shelltype")
    ap.add_argument("--column-snapshot", action='store_true', help="Snapshot the column with a semi-transparent container")
    ap.add_argument("--column-snapshot-fast", action='store_true', help="Snapshot the column with a semi-transparent container")
    ap.add_argument("--volume-integral", choices=['Volume', 'Area', 'NoNorm'], help="Calculate AVERAGES using the volume integral. EXPERIMENTAL. TO BE REPLACED")
    ap.add_argument("--mass-flux", type=int, help="Calculate mass flux (or volume flux) at n slices")
    ap.add_argument("--animate", action='store_true', help="Create animation as series of pngs")
    ap.add_argument("--infogeneric", action='store_true', help="Dump mesh info for generic field meshes")
    ap.add_argument("--infoclassic", action='store_true', help="Dump mesh info for classic interstitial meshes")

    ap.add_argument("-np", "--nproc", type=int, default=1, help="Screenshot the given object")

    ap.add_argument("--integrate", choices=['Volume', 'Area', 'None'], help="Integrate and average the given Volume/Area")
    # ap.add_argument("--project", nargs=4, default=['clip', 'Plane', 0.5, "x"], help="Projection. <clip|slice> <Plane|Cylinder..> <origin> <x|y|z>" )
    ap.add_argument("--project", nargs=4, default=['none', 'Plane', 0.5, "x"], help="Projection. <clip|slice|none> <Plane|Cylinder..> <origin> <x|y|z>" )

    ap.add_argument("-st"  , "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], default='EQUIDISTANT', help="Shell discretization type. See --nrad")
    ap.add_argument("-nr"  , "--nrad", type=int, default=5, help="Radial discretization in particular plugins")

    ap.add_argument("-cm", "--colormap", default='Viridis (matplotlib)', help="Show coordinate axis")
    ap.add_argument("-sa", "--show-axis", action='store_true', help="Show coordinate axis")
    ap.add_argument("-sb", "--show-scalar-bar", action='store_true', help="Show scalar color bar")
    ap.add_argument("-dr", "--display-representation", default='Surface', choices=['Surface', 'Surface With Edges', 'Points'],  help="Show Surface, Surface With Edges, etc")
    ap.add_argument("-crm", "--color-range-method", choices=['auto', 'startzero', 'midzero', 'custom', 'custom_bottom', 'custom_top'], default='auto', help="Range method for the scalar bar (color transfer function)")
    ap.add_argument("-ccr", "--custom-color-range", nargs=2, type=float, help="Custom range for the scalar bar (color transfer function). Ensure -crm == custom")


    ap.add_argument("-s", "--scalars" , nargs='*' , help="Scalars to consider. (Previously colorvars).")

    ap.add_argument("-z", "--zoom", type=float, default=1, help="Zoom (camera.dolly) value for view")
    ap.add_argument("-v", "--view", nargs=2, default=["-x",  "-y"], help="Set view: target, viewup. Use +x, -z notation.")
    ap.add_argument("-g", "--geometry", nargs=2, type=int, default=[1024, 768], help="Animation geometry size")

    ap.add_argument("--flow", help="Flowfield pvtu/vtu file for use in chromatograms. May need --resample-flow.")
    ap.add_argument("--resample-flow", action='store_true', default=False, help="Flag to resample flowfield data using concentration mesh")

    ap.add_argument("--packedbed", help="Packed bed mesh to use with --infogeneric")
    ap.add_argument("--interstitial", help="Interstitial mesh to use with --infogeneric")

    ap.add_argument("-o", "--output-prefix", help="prefix for output filenames")

    ap.add_argument("-f", "--filetype", default='pvtu', choices=['xdmf', 'vtu', 'vtk', 'pvtu', 'pvd'], help="filetype: xdmf | vtu | vtk | pvtu")
    ap.add_argument("--standalone", action='store_true', help="Read files as separate standalone objects, not part of time series.")

    ap.add_argument("--append-datasets", action='store_true', help="Use AppendDatasets on standalone files before processing.")

    ap.add_argument("-cfc", "--colormap-fuzzy-cutoff", default=70, type=int, help="Fuzziness cutoff score for colormap names. 100 implies exact match.")

    ap.add_argument("FILES", nargs='*', help="files..")

    args =  ap.parse_args()
    args = Dict(vars(ap.parse_args()))

    # print("NOTE: Only parsing known arguments!")
    # args, _ =  ap.parse_known_args()
    # args = Dict(vars(args))

    return args


def configure_scalar_bar(LUT, view, colorbar_config):
    """
    Given a colorbar_config args Dict, configure the ParaView ColorBar
    """

    if not colorbar_config: 
        print("No colorbar config provided...")
        UpdateScalarBars()
        return

    ColorBar:Proxy = GetScalarBar(LUT, view)
    for prop in colorbar_config.keys():
        ColorBar.SetPropertyWithName(prop, colorbar_config[prop])

    UpdateScalarBars()

def create_threshold(object, scalar, method, lower_threshold=0.0, upper_threshold=0.0):
    methodChoices = ['Between', 'Below Lower Threshold', 'Above Upper Threshold']
    method = process.extractOne(method, methodChoices, scorer=fuzz.token_set_ratio)

    if not method: 
        raise RuntimeError("Bad thresholding method!")

    threshold = Threshold(Input=object)
    threshold.Scalars = ['POINTS', scalar]
    # For paraview > 5.10
    threshold.LowerThreshold = lower_threshold
    threshold.UpperThreshold = upper_threshold
    threshold.ThresholdMethod = method[0]
    # For paraview < 5.10 
    # threshold.ThresholdRange = [0, nbeads-1]

    return threshold

# TODO: Remove args
# Potentially just pass a dict to reduce args list bloat
# Would require heirarchical configuration. 
def handle_coloring(object, display, scalar, args): 

    args = Dict(args)

    if scalar == 'None':
        display.ColorArrayName = ['POINTS', '']
        ColorBy(display, None)
    elif scalar == 'CellEntityIds': 
        ColorBy(display, ('CELLS', 'CellEntityIds'))
    else:
        ColorBy(display, ('POINTS', scalar))

    wLUT:Proxy = GetColorTransferFunction(scalar)
    wPWF:Proxy = GetOpacityTransferFunction(scalar)

    pd = object.PointData

    if args.colors_logscale: 
        # convert to log space
        wLUT.MapControlPointsToLogSpace()
        # Properties modified on wLUT
        wLUT.UseLogScale = 1

    if args.opacity_mapping: 
        # Properties modified on wLUT
        wLUT.EnableOpacityMapping = 1

    if args.opacity_logscale: 
        # convert to log space
        wPWF.MapControlPointsToLogSpace()
        # Properties modified on wPWF
        wPWF.UseLogScale = 1

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
    elif args.color_range_method == 'custom_bottom': 
        crange = pd.GetArray(scalar).GetRange()
        wLUT.RescaleTransferFunction(args.custom_color_range[0], crange[1])
    elif args.color_range_method == 'custom_top': 
        crange = pd.GetArray(scalar).GetRange()
        wLUT.RescaleTransferFunction(crange[0], args.custom_color_range[1])

    return wLUT, wPWF

def script_main_new(parser, driver):
    """ A wrapper function to make it easy to write individual scripts"""
    config = ConfigHandler()
    args = config.load_and_parse_args(parser)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    read_and_execute(args, driver)

def script_main(local_parser, local_driver):
    """ A wrapper function to make it easy to write individual scripts"""
    config = ConfigHandler()
    args, local_args_list = config.parse_config_and_cmdline_args()
    args = local_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    read_and_execute(args, local_driver)

def read_and_execute(args, driver):
    if args['standalone']: 
        readers = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])

        if args['append_datasets']:
            appended = AppendDatasets(Input=readers)
            driver(appended, **args)
        else: 
            # Use input filenames in output using output_prefix
            files, filetype = find_files(args['FILES'], args['filetype'])
            print("FILES =", files)
            _output_prefix = args.output_prefix
            for ind, ireader in enumerate(readers): 
                args['output_prefix'] = f"{Path(files[ind]).stem.strip()}_{_output_prefix}"
                driver(ireader, **args)
    else: 
        reader = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])
        driver(reader, **args)

def extract_surface_with_aligned_normal(object, normal_dir:str='Z', value:float=1.0):
    assert normal_dir in 'xyzXYZ'
    normal_dir = normal_dir.upper()

    all_surfaces = ExtractSurface(Input=object)
    all_normals = GenerateSurfaceNormals(Input=all_surfaces)
    threshold = Threshold(Input=all_normals)

    threshold.Scalars = ['POINTS', f'Normals_{normal_dir}']
    threshold.LowerThreshold = value
    threshold.UpperThreshold = value

    return threshold

def default_parser():
    """
    Copied from confighandler

    NOTE: Make sure to set the default (especially bool types) to None.
    This makes it easier to update the config with args, allowing to switch
    bool flags on and off using cmdline

    NOTE: Make sure that there are no positional args. Since we parse some
    stuff later, unknowns may get mixed up with positionals.
    """
    ap = argparse.ArgumentParser()

    ap.add_argument("-c","--config", help="YAML config file")

    ap.add_argument("--integrate", choices=['Volume', 'Area', 'None'], help="Integrate and average the given Volume/Area")
    ap.add_argument("--project", nargs=4, help="Projection. <clip|slice|none> <Plane|Cylinder..> <origin> <x|y|z>" )

    ## TODO: Check feasibility of creating such a feature
    # ap.add_argument("--radial-divide", help="Divide into radial sections??" )

    ap.add_argument("-cm", "--colormap", help="Use specified colormap. Fuzzy searches within paraview and then ScientificColourMaps7. See -cfc.")
    ap.add_argument("-cfc", "--colormap-fuzzy-cutoff", type=int, help="Fuzziness cutoff score for colormap names. 100 implies exact match.")
    ap.add_argument("-crm", "--color-range-method", choices=['auto', 'startzero', 'midzero', 'custom', 'custom_bottom', 'custom_top'], help="Range method for the scalar bar (color transfer function)")
    ap.add_argument("-ccr", "--custom-color-range", nargs=2, type=float, help="Custom range for the scalar bar (color transfer function). Ensure -crm == custom")

    ap.add_argument("-clog", "--colors-logscale", action='store_true', default=None, help="Plot colors in log scale")
    ap.add_argument("-omap", "--opacity-mapping", action='store_true', default=None, help="Object opacity by scalar value")
    ap.add_argument("-olog", "--opacity-logscale", action='store_true', default=None, help="Object opacity in log scale")

    ap.add_argument("-sa", "--show-axis", action=argparse.BooleanOptionalAction, default=None, help="Show coordinate axis")
    ap.add_argument("-sb", "--show-scalar-bar", action=argparse.BooleanOptionalAction, default=None, help="Show scalar color bar")

    ap.add_argument("-dr", "--display-representation", choices=['Surface', 'Surface With Edges', 'Points'],  help="Show Surface, Surface With Edges, etc")
    ap.add_argument("-s", "--scalars" , nargs='*' , help="Scalars to consider. (Previously colorvars).")

    ap.add_argument("-z", "--zoom", type=float, help="Zoom (camera.dolly) value for view")
    ap.add_argument("-v", "--view", nargs=2, help="Set view: target, viewup. Use +x, -z notation.")
    ap.add_argument("-g", "--geometry", nargs=2, type=int, help="Animation geometry size")

    ap.add_argument("-o", "--output-prefix", help="prefix for output filenames")
    ap.add_argument("-f", "--filetype", choices=['xdmf', 'vtu', 'vtk', 'pvtu', 'pvd'], help="filetype: xdmf | vtu | vtk | pvtu")

    ap.add_argument("--standalone", action=argparse.BooleanOptionalAction, default=None, help="Read files as separate standalone objects, not part of time series.")
    ap.add_argument("--append-datasets", action=argparse.BooleanOptionalAction, default=None, help="Use AppendDatasets on standalone files before processing.")

    ap.add_argument("FILES", nargs='*', help="files..")

    return ap

def default_local_parser(argslist):
    ap = default_parser()
    args = Dict(vars(ap.parse_args(argslist)))
    print_json(data=args)
    return args

def argcheck(obj, func=None, strict=False, msg=None):
    if func is not None: 
        result = func(obj)
    else: 
        result = obj

    if result is None:
        if strict:
            raise AssertionError(msg)
        else:
            print(msg)

## Some util functions are guaranteed to be passed args from within a driver function
def get_view(args):
    view = GetActiveViewOrCreate('RenderView')
    view.OrientationAxesVisibility = args['show_axis']
    view.ViewSize = args['geometry']
    return view
