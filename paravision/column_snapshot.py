from paraview.simple import *

from paravision.utils import parse_cmdline_args, read_files, view_handler
from paravision.project import project

def column_snapshot(reader, args):

    geometry    = args['geometry']
    axisVisible = args['show_axis']
    zoom        = args['zoom']
    files       = args['FILES']
    filetype    = args['filetype']

    view = GetActiveViewOrCreate('RenderView')
    connectivity = Connectivity(Input=reader)
    connectivityDisplay = Show(connectivity, view)

    connectivityDisplay.Representation = args['display_representation']
    view.OrientationAxesVisibility = int(axisVisible)

    nord10 = [94, 129, 172]
    color_rgb = [ x/255 for x in nord10]

    Hide(connectivity, view)

    # NOTE: Threshold  range will be (0, n) where n is number of beads.
    # Typically, the interstitial domain is the last, n+1th region.
    # Here, we ignore the interstitial region by setting nbeads = n, and not n+1.
    nbeads = int(connectivity.PointData.GetArray("RegionId").GetRange()[1])
    print("Number of Objects:", nbeads)

    ## TODO: just use 0..n as threshold range instead of this nonsense
    # for index in range(nbeads):
    # print("Processing bead: {index}".format(index=index))
    print("Processing beads: {nbeads}".format(nbeads=nbeads))
    threshold = Threshold(Input=connectivity)
    threshold.ThresholdRange = [0, nbeads-1]
    thresholdDisplay = Show(threshold, view)
    ColorBy(thresholdDisplay, None)
    # threshold.UpdatePipeline()
    thresholdDisplay.AmbientColor = color_rgb
    thresholdDisplay.DiffuseColor = color_rgb

    # thresholdDisplay.AmbientColor = [2/255, 61/255, 107/255]
    # thresholdDisplay.DiffuseColor = [2/255, 61/255, 107/255]

    print("Processing Column.")
    threshold = Threshold(Input=connectivity)
    threshold.ThresholdRange = [nbeads, nbeads]
    # outerShell = Projection(threshold, 'clip')
    outerShell = project(threshold, args)

    outerShellDisplay = Show(outerShell, view)
    ColorBy(outerShellDisplay, None)
    # outerShell.UpdatePipeline()
    outerShellDisplay.Opacity = 0.5
    view.InteractionMode = '2D'

    view_handler(args['view'], args['zoom'])

    view.Update()
    view.ResetCamera()
    view.ViewSize = geometry

    ## NOTE: Only works on the first file provided
    SaveScreenshot(files[0].replace(filetype, 'png'), view, ImageResolution=geometry, TransparentBackground=1)

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args)
    column_snapshot(reader, args)
