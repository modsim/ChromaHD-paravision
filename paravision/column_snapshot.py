from paraview.simple import *
from vtk import vtkThreshold

from paravision.utils import read_files, view_handler
from paravision.project import project

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

def column_snapshot(reader, args):

    view = GetActiveViewOrCreate('RenderView')
    connectivity = Connectivity(Input=reader)
    connectivityDisplay = Show(connectivity, view)

    view.OrientationAxesVisibility = int(args.show_axis)

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
    # threshold.ThresholdRange = [0, nbeads-1]
    threshold.LowerThreshold = 0
    threshold.UpperThreshold = nbeads-1
    threshold.ThresholdMethod = vtkThreshold.THRESHOLD_BETWEEN
    thresholdDisplay = Show(threshold, view)
    ColorBy(thresholdDisplay, None)
    # threshold.UpdatePipeline()
    thresholdDisplay.AmbientColor = color_rgb
    thresholdDisplay.DiffuseColor = color_rgb
    thresholdDisplay.Representation = args.display_representation

    # thresholdDisplay.AmbientColor = [2/255, 61/255, 107/255]
    # thresholdDisplay.DiffuseColor = [2/255, 61/255, 107/255]

    print("Processing Column.")
    threshold = Threshold(Input=connectivity)
    # threshold.ThresholdRange = [nbeads, nbeads]
    threshold.LowerThreshold = nbeads
    threshold.UpperThreshold = nbeads
    threshold.ThresholdMethod = vtkThreshold.THRESHOLD_BETWEEN

    outerShell = project(
            threshold, 
            {
                'project': ['clip', 'Plane', 0.5, 'x']
            })

    outerShellDisplay = Show(outerShell, view)
    ColorBy(outerShellDisplay, None)
    # outerShell.UpdatePipeline()
    outerShellDisplay.Opacity = 0.5
    view.InteractionMode = '2D'

    view_handler(args['view'], args['zoom'])

    view.Update()
    view.ResetCamera()
    view.ViewSize = args.geometry

    ## NOTE: Only works on the first file provided
    screenshot_filename = f'column_snapshot.png'
    print(f'Saving screenshot to file: {screenshot_filename}')
    SaveScreenshot(screenshot_filename, view, ImageResolution=args.geometry, TransparentBackground=1)

def column_snapshot_parser(args, local_args_list):

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
    args = column_snapshot_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    column_snapshot(reader, args)
