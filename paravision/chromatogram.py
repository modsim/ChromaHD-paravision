from paravision.utils import csvWriter, parse_cmdline_args, read_files
from paravision.integrate import integrate

from paraview.simple import *

import numpy as np

def chromatogram(reader, args):
    """
        Calculate chromatogram from 
            - Volume : Given 3D column volume -> Extracted top surface
            - Area   : Given 2D Area
    """

    args.scalars = args.scalars or reader.PointArrayStatus
    scalars = args['scalars']
    timeArray = reader.TimestepValues

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

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args)
    chromatogram(reader, args)
