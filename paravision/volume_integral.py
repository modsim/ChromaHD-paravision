from paraview.simple import *

from paravision.utils import read_files, csvWriter
from paravision.integrate import integrate

# TODO: Update this with --integrate?

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json

def volume_integral(reader, args):
    """ Calculate the integral of a scalar over a volume
    """
    scalars = args['scalars'] or reader.PointArrayStatus

    # timeKeeper = GetTimeKeeper()
    # nts = len(reader.TimestepValues)
    timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')

    result = integrate(reader, scalars, normalize=args.normalize, timeArray=timeArray)

    print(result)
    for i,scalar in enumerate(scalars):
        filename = scalar + '.integrated.csv'
        print(f'Writing data to {filename}')
        csvWriter(filename, reader.TimestepValues, map(lambda x: x[i], result))


def volume_integral_parser(args, local_args_list):

    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--normalize", choices = ['NoNorm', 'Volume', 'Area'], help="files..")
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
    args = volume_integral_parser(args, local_args_list)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    volume_integral(reader, args)
