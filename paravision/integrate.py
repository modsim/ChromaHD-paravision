from paraview.simple import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
import vtk.util.numpy_support as ns #type:ignore

def integrate(object, vars, normalize=None, timeArray=[]):
    ## normalize= "Volume" or "Area" or None
    choices = ['Volume', 'Area']

    timeKeeper = GetTimeKeeper()
    nts = len(timeArray) or 1

    # GetActiveViewOrCreate('RenderView')

    VolumeOrArea = []

    integrated_over_time = []
    for timestep in range(nts):
        try:
            timeKeeper.Time = timestep
            object.UpdatePipeline(timeArray[timestep])
        except IndexError:
            pass

        print(f"Integrating timestep: {timestep}")

        integrated = IntegrateVariables(Input=object)
        intdata = servermanager.Fetch(integrated)
        intdata = dsa.WrapDataObject(intdata)

        if not intdata:
            raise(AssertionError)

        volume=1
        if normalize in choices:
            if normalize in intdata.CellData.keys():
                volume = intdata.CellData[normalize][0]
            else:
                print("".join(["Cannot normalize by ", normalize, ". No such CellData!"]))

        # print("{key}: {value}".format(key=normalize, value=volume))
        # VolumeOrArea.append(volume)
        # print(VolumeOrArea)

        integrated_scalars = []
        for var in vars:
            value = intdata.PointData[var]
            value = ns.vtk_to_numpy(value)
            integrated_scalars.append(value[0]/volume)  ## Average of c, instead of integ(c.dV)

        integrated_over_time.append(integrated_scalars)

        Delete(integrated)

    return integrated_over_time
