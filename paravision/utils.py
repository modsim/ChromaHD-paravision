from paraview.simple import *
import struct

def appendToBin(arr, filename, f):
    with(open(filename, 'ab')) as output:
        for i in arr:
            output.write(struct.pack(f, i))

def csvWriter(filename, x, y):
    import csv
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
    display = Show(reader, view)
    (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    # print('bbox: ', xmin,xmax,ymin,ymax,zmin,zmax)
    Hide(reader, view)

    new_normal = direction_handler(normal)
    origin_mask = [ xmin + float(origin) * (xmax - xmin), ymin + float(origin) * (ymax - ymin), zmin + float(origin) * (zmax - zmin)]
    new_origin = [abs(x) * y for x,y in zip(new_normal, origin_mask)]

    return new_origin, new_normal

def direction_handler(dir:str):
    """
    Convert from "+x" notation to [1, 0, 0] notation
    """
    dir = dir.strip()
    if len(dir) == 1:
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

    return target

def view_handler(viewopts:list, zoom:float):
    """
    Set camera view to viewopts ["+x", "-y"]  and zoom
    """
    target = direction_handler(viewopts[0])
    viewup = direction_handler(viewopts[1])

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

def read_files(files, filetype='pvtu'):
    import os

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
            print("Mixed File Formats Given!")
            sys.exit(-1)
        filetype = fileExtensions.pop().replace('.', '')

    print("Reading files: ", files)

    reader=None
    if filetype == 'xdmf':
        reader = XDMFReader(FileNames=files)
    elif filetype == 'vtu':
        reader = XMLUnstructuredGridReader(FileName=files)
    elif filetype == 'pvtu':
        reader = XMLPartitionedUnstructuredGridReader(FileName=files)
    elif filetype == 'vtk':
        reader = LegacyVTKReader(FileNames=files)
    else:
        print("Unsupported File Format!")
        raise(ValueError)
    
    return reader

def parse_cmdline_args():
    """
        Parser for individual module commands
    """
    import argparse 
    from addict import Dict

    ap = argparse.ArgumentParser()

    ap.add_argument("-cg", "--chromatogram", choices=['full', 'shells'], help="Calculate chromatogram from given flat 2D surface of column. Requires --flow. See --shelltype.")
    ap.add_argument("--grm2d", nargs=2, type=int, help="Split into axial and radial sections and integrate scalars for fitting with 2D GRM. args: <ncol> <nrad>")
    ap.add_argument("--screenshot", action='store_true', help="Screenshot the given object")
    ap.add_argument("--bead-loading", action='store_true', help="Screenshot the given object")
    ap.add_argument("--radial-shell-integrate", choices=['Volume', 'Area', 'NoNorm'], const='NoNorm', nargs='?', help="Divide object radially and integrate. Choices indicate normalization method. See --nrad, --shelltype")
    ap.add_argument("--column-snapshot", action='store_true', help="Snapshot the column with a semi-transparent container")
    ap.add_argument("--volume-integral", action='store_true', help="Calculate AVERAGES using the volume integral. EXPERIMENTAL. TO BE REPLACED")
    ap.add_argument("--mass-flux", type=int, help="Calculate mass flux (or volume flux) at n slices")
    ap.add_argument("--animate", action='store_true', help="Create animation as series of pngs")

    ap.add_argument("-np", "--nproc", type=int, default=1, help="Screenshot the given object")

    ap.add_argument("--integrate", choices=['Volume', 'Area', 'None'], help="Integrate and average the given Volume/Area")
    # ap.add_argument("--project", nargs=4, default=['clip', 'Plane', 0.5, "x"], help="Projection. <clip|slice> <Plane|Cylinder..> <origin> <x|y|z>" )
    ap.add_argument("--project", nargs=4, default=['none', 'Plane', 0.5, "x"], help="Projection. <clip|slice|none> <Plane|Cylinder..> <origin> <x|y|z>" )
    ap.add_argument("--pipeline", nargs='+', help="Operations to be performed in pipe. NOT PARALLELIZED." )

    ap.add_argument("-st"  , "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], default='EQUIDISTANT', help="Shell discretization type. See --nrad")
    ap.add_argument("-nr"  , "--nrad", type=int, default=5, help="Radial discretization in particular plugins")

    ap.add_argument("-sa", "--show-axis", action='store_true', help="Show coordinate axis")
    ap.add_argument("-sb", "--show-scalar-bar", action='store_true', help="Show scalar color bar")
    ap.add_argument("-dr", "--display-representation", default='Surface', choices=['Surface', 'Surface With Edges', 'Points'],  help="Show Surface, Surface With Edges, etc")
    ap.add_argument("-s", "--scalars" , nargs='*' , help="Scalars to consider. (Previously colorvars).")
    ap.add_argument("-z", "--zoom", type=float, default=1, help="Zoom (camera.dolly) value for view")
    ap.add_argument("-v", "--view", nargs=2, default=["-x",  "+y"], help="Set view: target, viewup. Use +x, -z notation.")
    ap.add_argument("-g", "--geometry", nargs=2, type=int, default=[3840, 2160], help="Animation geometry size")
    ap.add_argument("-f", "--filetype", default='pvtu', choices=['xdmf', 'vtu', 'vtk', 'pvtu'], help="filetype: xdmf | vtu | vtk | pvtu")

    ap.add_argument("--flow", help="Flowfield pvtu/vtu file for use in chromatograms. May need --resample-flow.")
    ap.add_argument("--resample-flow", action='store_true', default=False, help="Flag to resample flowfield data using concentration mesh")

    ap.add_argument("FILES", nargs='*', help="files..")

    args = Dict(vars(ap.parse_args()))

    return args

