from paravision.utils import csvWriter, parse_cmdline_args, read_files
from paravision.integrate import integrate

from paraview.simple import *

import numpy as np

from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

def chromatogram(reader, args):
    """
        Calculate chromatogram from 
            - Volume : Given 3D column volume -> Extracted top surface
            - Area   : Given 2D Area
            - ResampleFlowOutlet: Given 2D Area

        REQUIRES flowfield data.
    """

    args.scalars = args.scalars or reader.PointArrayStatus
    scalars = args['scalars']
    timeArray = reader.TimestepValues

    if not args.flow:
        raise RuntimeError("Please provide --flow <flowfield_file> args.")
    else:
        flow = read_files([args['flow']], filetype=args['filetype'])

    integrated_flowrate = integrate(flow, ['scalar_2'], normalize=None, timeArray=[])
    print("Flowrate:", integrated_flowrate)

    if args['chromatogram'] == 'Volume':

        GetActiveViewOrCreate('RenderView')

        surfaces = ExtractSurface(Input=reader)
        surfaceNormals = GenerateSurfaceNormals(Input=surfaces)

        threshold = Threshold(Input=surfaceNormals)
        threshold.ThresholdRange = [1.0, 1.0]
        threshold.Scalars = ['POINTS', 'Normals_Z']

        integratedData = integrate(threshold, scalars, normalize='Area', timeArray=timeArray)

        for scalar in scalars:
            csvWriter("".join([scalar, '.csv']), timeArray or list(range(len(integratedData))), np.array(integratedData).T[list(scalars).index(scalar)])

    elif args['chromatogram'] == 'Area':
        integratedData = integrate(reader, scalars, normalize='Area', timeArray=reader.TimestepValues)

        for scalar in scalars:
            csvWriter("".join([scalar, '.csv']), reader.TimestepValues, np.array(integratedData).T[list(scalars).index(scalar)])

    elif args['chromatogram'] == 'ResampleFlowOutlet':
        # NOTE: Assumes input is 2D output of extractRNG applied on the outlet
        # Resampling is required for it to work currently. Possibly extractRNG doing something weird.

        resampled_flow = ResampleWithDataset(registrationName='resampled_flow', SourceDataArrays=flow, DestinationMesh=reader)
        resampled_flow.CellLocator = 'Static Cell Locator'

        # conc * velocity_z
        cu = PythonCalculator(Input=[reader, resampled_flow])
        cu.Expression = "inputs[0].PointData['scalar_0'] * inputs[1].PointData['scalar_2']"

        chromatogram = integrate(cu, ['result'], normalize=None, timeArray=reader.TimestepValues)
        chromatogram = [ x[0]/integrated_flowrate[0][0] for x in chromatogram ]

        csvWriter('chromatogram', reader.TimestepValues, chromatogram)



if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args['FILES'], filetype=args['filetype'])
    chromatogram(reader, args)
