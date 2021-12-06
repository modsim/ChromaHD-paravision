from paravision.utils import parse_cmdline_args, read_files, appendToBin
from paravision.integrate import integrate

from paraview.simple import *

from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

import numpy as np

def bead_loading(reader, args):
    scalars = args['scalars'] or reader.PointArrayStatus
    files = args['FILES']

    try:
        timeKeeper = GetTimeKeeper()
        nts = len(reader.TimestepValues)
    except:
        nts = 1
        pass

    if nts == 0:
        nts = 1
    ncv = len(scalars)

    print("nts:", nts)
    print("ncv:", ncv)

    view = GetActiveViewOrCreate('RenderView')

    connectivity = Connectivity(Input=reader)
    connectivityDisplay = Show(connectivity, view)
    Hide(connectivity, view)

    # NOTE: Threshold  range will be (0, n) where n is number of beads.
    # Typically, the interstitial domain is the last, n+1th region.
    # Here, we ignore the interstitial region by setting nbeads = n, and not n+1.
    nbeads = int(connectivity.PointData.GetArray("RegionId").GetRange()[1])
    print("Number of Objects:", nbeads)

    appendToBin([nts, nbeads, ncv],'bead_loading.inf', '=i')
    dataArr = np.zeros((nts, nbeads, ncv))
    # coordArr = np.zeros((nbeads,4))


    for timestep in range(nts):
        timeKeeper.Time = timestep
        # print("Processing timestep: ", timestep, end="\r")

        for index in range(nbeads):

            print("Processing timestep: {timestep:3d} | bead: {index:5d} | file: {file}".format(timestep=timestep, index=index, file=files[timestep]), end="\r")
            threshold = Threshold(Input=connectivity)
            threshold.ThresholdRange = [index, index]
            thresholdDisplay = Show(threshold, view)
            # threshold.UpdatePipeline()

            if timestep == 0:
                (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
                # print("Threshold coordinate bounds:",xmin,xmax,ymin,ymax,zmin,zmax)
                x = (xmax + xmin)/2
                y = (ymax + ymin)/2
                z = (zmax + zmin)/2
                r = (xmax - xmin + ymax - ymin + zmax - zmin)/6
                # print("xyzr:",x, y, z, r)
                # coordArr[index,:] = np.array([x, y, z, r])
                appendToBin([x,y,z,r],'bead_loading.xyzr', '=d')

            integrated = IntegrateVariables(Input=threshold)
            intdata = servermanager.Fetch(integrated)
            intdata = dsa.WrapDataObject(intdata)

            values = []
            for scalar in scalars:
                value = intdata.PointData[scalar]
                value = ns.vtk_to_numpy(value)
                values.append(value[0])

            dataArr[timestep,index,:] = np.array(values)
            Hide(threshold, view)

            Delete(integrated)
            Delete(thresholdDisplay)
            Delete(threshold)

        # TODO: this only works with one scalar currently, which is okay for now
        # appendToBin(dataArr[timestep,:,:], 'ts_' + str(timestep) + '.dat', "=d")
        appendToBin(dataArr[timestep,:,:], files[timestep].replace('.pvtu', '.dat'), "=d")

if __name__=="__main__":
    args = parse_cmdline_args()
    reader = read_files(args)
    bead_loading(reader, args)
