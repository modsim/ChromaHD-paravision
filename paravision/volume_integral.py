from paraview.simple import *

from paravision.utils import read_files, csvWriter
from paravision.integrate import integrate
from paravision.project import projector

# TODO: Update this with --integrate?

from paravision import ConfigHandler
import argparse
from addict import Dict

from rich import print, print_json
from paravision.defaults import DEFAULT_CONFIG

def volume_integral(reader, args):
    """ Calculate the integral of a scalar over a volume
    """
    scalars = args['scalars'] or reader.PointArrayStatus
    output_prefix = args.get('output_prefix', DEFAULT_CONFIG.output_prefix)
    _project               = args.get('project'               , DEFAULT_CONFIG.project) 

    # timeKeeper = GetTimeKeeper()
    # nts = len(reader.TimestepValues)
    timeArray = reader.TimestepValues

    view = GetActiveViewOrCreate('RenderView')
    projection = projector(reader, *_project)

    result = integrate(projection, scalars, normalize=args.normalize, timeArray=timeArray)

    print(result)
    for i,scalar in enumerate(scalars):
        filename = f"volume_integral_scalar_{i}_{output_prefix}.csv"
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

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    if args['standalone']: 
        readers = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])

        if args['append_datasets']:
            appended = AppendDatasets(Input=readers)
            volume_integral(appended, args)
        else: 
            # Use input filenames in output using output_prefix
            files, filetype = find_files(args['FILES'], args['filetype'])
            print("FILES =", files)
            _output_prefix         = args.get('output_prefix', DEFAULT_CONFIG.output_prefix)
            for ind, ireader in enumerate(readers): 
                args['output_prefix'] = f"{Path(files[ind]).stem.strip()}_{_output_prefix}"
                volume_integral(ireader, args)
    else: 
        reader = read_files(args['FILES'], filetype=args['filetype'], standalone=args['standalone'])
        volume_integral(reader, args)
