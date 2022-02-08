from paraview.simple import *

from paravision.utils import parse_cmdline_args, read_files, view_handler
from paravision.project import project

def column_snapshot_fast(args):

    # NOTE: This is a faster version of column snapshot for when the mesh data
    # is already split into two files: particles_volume and interstitial
    # volume. Might work for surfaces as well, but currently untested. This was
    # necessary because connectivity filter doesn't work in parallel and and
    # mixd2pvtu doesn't work for AC-poly in serial currently due to its large
    # size. (something to do with MPI_COUNT size)
    #
    # This way, the script is parallelizable, provided that the inputs are
    # PVTU, but that would require a previous decomposition step. My mesher
    # currently only generates single legacy VTK files.
    
    print("WARNING: Assumes files are passed in order <particles_volume> <interstitial_volume>")

    particles = read_files([args['FILES'][0]], filetype=args['filetype'])
    interstitial = read_files([args['FILES'][1]], filetype=args['filetype'])

    for key in args:
        print(key + ': ', args[key])

    geometry    = args['geometry']
    axisVisible = args['show_axis']
    zoom        = args['zoom']
    files       = args['FILES']
    filetype    = args['filetype']

    view = GetActiveViewOrCreate('RenderView')

    nord10 = [94, 129, 172]
    color_rgb = [ x/255 for x in nord10]

    print("Processing Particles.")
    particlesDisplay = Show(particles, view)
    print(particlesDisplay.ColorArrayName)
    particlesDisplay.ColorArrayName =  ['POINTS', '']
    ColorBy(particlesDisplay, None)
    # threshold.UpdatePipeline()
    particlesDisplay.AmbientColor = color_rgb
    particlesDisplay.DiffuseColor = color_rgb

    print("Processing Column.")
    outerShell = project(interstitial, args)

    outerShellDisplay = Show(outerShell, view)
    print(outerShellDisplay.ColorArrayName)
    outerShellDisplay.ColorArrayName =  ['POINTS', '']
    ColorBy(outerShellDisplay, None)
    # outerShell.UpdatePipeline()
    outerShellDisplay.Opacity = 0.5
    view.InteractionMode = '2D'

    view_handler(args['view'], args['zoom'])

    view.Update()
    view.ResetCamera()
    view.ViewSize = geometry

    ## NOTE: Only works on the first file provided
    SaveScreenshot('column_snapshot.png', view, ImageResolution=geometry, TransparentBackground=1)

if __name__=="__main__":
    args = parse_cmdline_args()
    column_snapshot_fast(args)
