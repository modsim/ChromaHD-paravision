from paravision.utils import csvWriter, read_files
from paravision.integrate import integrate
from paravision.project import projector

from paraview.simple import *
from paravision import ConfigHandler

import argparse
from addict import Dict
from rich import print, print_json

## TODO: Test with parallel meshes

def chromatogram(reader, args):
    """
        Calculate chromatogram from given 2D concentration field and flowfield
        Resampling is necessary when using flowfield that wasn't generated from the exact same mesh.
        Resampling is extremely slow.
    """

    # for key in args:
    #     print(key + ': ', args[key])

    args.scalars = args.scalars or reader.PointArrayStatus
    timeArray = reader.TimestepValues

    if not args.flow:
        raise RuntimeError("Please provide --flow <flowfield_file> args.")
    else:
        flow = read_files([args['flow']], filetype=args['filetype'])

    if args.resample_flow: 
        # NOTE: Resampling is only required when the flowfield information is taken from the FLOW mesh instead of the MASS mesh mapping of the flowfield.
        print("Resampling the flowfield...")
        flow = ResampleWithDataset(registrationName='resampled_flow', SourceDataArrays=flow, DestinationMesh=reader)
        flow.CellLocator = 'Static Cell Locator'

    integrated_flowrate = integrate(flow, ['scalar_2'], normalize=None, timeArray=[])
    print("Flowrate:", integrated_flowrate)

    if args['type'] == 'full':
        # NOTE: Assumes input is 2D output of extractRNG applied on the outlet
        # conc * velocity_z
        cu = PythonCalculator(Input=[reader, flow])
        cu.Expression = "inputs[0].PointData['scalar_0'] * inputs[1].PointData['scalar_2']"

        chromatogram = integrate(cu, ['result'], normalize=None, timeArray=reader.TimestepValues)
        chromatogram = [ x[0]/integrated_flowrate[0][0] for x in chromatogram ]

        csvWriter('chromatogram.csv', reader.TimestepValues, chromatogram)

    elif args.type == 'shells': 

        get_shell_chromatograms(reader, flow, args, timeArray=timeArray)

    elif args.type == 'shells_at_slice': 

        args.project[0] = 'slice'

        mass_slice = projector(reader, *args.project)
        flow_slice = projector(flow, *args.project)

        get_shell_chromatograms(mass_slice, flow_slice, args, timeArray=timeArray)

        
def get_shell_chromatograms(mass, flow, args, timeArray): 
        nRegions = args.nrad
        shellType = args.shelltype

        timeKeeper = GetTimeKeeper()
        # timeArray = mass.TimestepValues
        nts = len(timeArray) or 1

        # conc * velocity_z
        cu = PythonCalculator(Input=[mass, flow])
        cu.Expression = "inputs[0].PointData['scalar_0'] * inputs[1].PointData['scalar_2']"
        
        view = GetActiveViewOrCreate('RenderView')
        ## Calc bounding box. Requires show
        display = Show(cu, view)
        # SetActiveSource(cu)
        (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
        Hide(cu, view)

        nShells = nRegions + 1 #Including r = 0
        rShells = []

        R = (xmax - xmin + ymax - ymin)/4
        print("R:", R)

        if shellType == 'EQUIVOLUME':
            for n in range(nShells):
                rShells.append(R * sqrt(n/nRegions))
        elif shellType == 'EQUIDISTANT':
            for n in range(nShells):
                rShells.append(R * (n/nRegions))

        print("rShells:", rShells)

        radAvg = []
        integrated_over_time = [ [] for region in range(nRegions) ]

        flowrates = []

        print("Calculating Flowrates")
        # NOTE: Flowrate: u * dA
        for radIn, radOut in zip(rShells[:-1], rShells[1:]):

            rIndex = rShells.index(radIn)

            radAvg.append( (radIn + radOut) / 2 )

            clipOuter = Clip(Input=flow)
            clipOuter.ClipType = 'Cylinder'
            clipOuter.ClipType.Axis = [0.0, 0.0, 1.0]
            clipOuter.ClipType.Radius = radOut
            Hide3DWidgets(proxy=clipOuter.ClipType)

            clipInner = Clip(Input=clipOuter)
            clipInner.ClipType = 'Cylinder'
            clipInner.ClipType.Axis = [0.0, 0.0, 1.0]
            clipInner.ClipType.Radius = radIn
            clipInner.Invert = 0

            ## Since we handle time outside the integrate function, the
            ## only entry in the outer list is the list of integrated scalars
            ## at the given time
            integratedData = integrate(clipInner, ['scalar_2'], normalize=None, timeArray=[])
            flowrates.append(integratedData[0][0])

            Delete(clipInner)
            Delete(clipOuter)

        print(f"{flowrates = }")
        print('flowrates sum:', sum(flowrates))

        for timestep in range(nts):

            timeKeeper.Time = timestep
            cu.UpdatePipeline(timeArray[timestep])

            print("its:", timestep)

            for radIn, radOut in zip(rShells[:-1], rShells[1:]):
                rIndex = rShells.index(radIn)

                radAvg.append( (radIn + radOut) / 2 )

                clipOuter = Clip(Input=cu)
                clipOuter.ClipType = 'Cylinder'
                clipOuter.ClipType.Axis = [0.0, 0.0, 1.0]
                clipOuter.ClipType.Radius = radOut
                Hide3DWidgets(proxy=clipOuter.ClipType)

                clipInner = Clip(Input=clipOuter)
                clipInner.ClipType = 'Cylinder'
                clipInner.ClipType.Axis = [0.0, 0.0, 1.0]
                clipInner.ClipType.Radius = radIn
                clipInner.Invert = 0

                ## Since we handle time outside the integrate function, the
                ## only entry in the outer list is the list of integrated scalars
                ## at the given time
                integratedData = integrate(clipInner, ['result'], normalize=None)
                integrated_over_time[rIndex].extend( [ x[0]/flowrates[rIndex] for x in integratedData ] )

                Delete(clipInner)
                Delete(clipOuter)

        print(integrated_over_time)

        for region in range(nRegions):
            csvWriter("chromatogram_{op}_shell_{i}.csv".format(op=args.output_prefix, i=region), timeArray, integrated_over_time[region])

        csvWriter(f'flowrates_{nRegions}_{args.output_prefix}.csv', radAvg, flowrates)

def chromatogram_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument("--type", choices=['full', 'shells', 'shells_at_slice'], help="Chromatogram for full area or shells")
    ap.add_argument("--flow", help="Flowfield pvtu/vtu file for use in chromatograms. May need --resample-flow.")
    ap.add_argument("--resample-flow", action=argparse.BooleanOptionalAction, default=None, help="Flag to resample flowfield data using concentration mesh")
    ap.add_argument("-nr", "--nrad", type=int, help="Radial discretization size for shell chromatograms. Also see --shelltype")
    ap.add_argument("-st", "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], help="Radial shell discretization type. See --nrad")

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
    args = chromatogram_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    chromatogram(reader, args)


