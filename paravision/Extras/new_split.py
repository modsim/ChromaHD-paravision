from paravision.utils import csvWriter, read_files
from paravision.integrate import integrate
from paravision.project import projector

from paraview.simple import *
from paravision import ConfigHandler

from paravision.radial_porosity import radial_porosity_profile
from paravision.radial_shell_integrate import radial_shell_integrate
from paravision.screenshot import screenshot

import argparse
from addict import Dict
from rich import print, print_json

def new_split(reader, args):

    args.scalars = args.scalars or reader.PointArrayStatus
    timeArray = reader.TimestepValues

    void_inlet  = projector(reader, 'clip', 'Plane', f'{args.split[0]}'                , 'z')
    column_bed  = projector(reader, 'clip', 'twice', f'{args.split[0]}-{args.split[1]}', 'z')
    void_outlet = projector(reader, 'clip', 'Plane', f'{args.split[1]}'                , '-z')

    if args.savedata:
        SaveData(f"void_inlet.pvd" , proxy=void_inlet , PointDataArrays=args.scalars, WriteTimeSteps=1) 
        SaveData(f"void_outlet.pvd", proxy=void_outlet, PointDataArrays=args.scalars, WriteTimeSteps=1) 
        SaveData(f"column.pvd"     , proxy=column     , PointDataArrays=args.scalars, WriteTimeSteps=1) 

    radial_porosity_profile(void_inlet , args.nrad, args.shelltype, args.project, 'void_inlet')
    radial_porosity_profile(column_bed , args.nrad, args.shelltype, args.project, 'column_bed' )
    radial_porosity_profile(void_outlet, args.nrad, args.shelltype, args.project, 'void_outlet' )

    radial_shell_integrate(void_inlet , args.nrad, args.shelltype, [None]*4, 'Volume', ['w'], 'void_inlet_rsa', timeArray=timeArray)
    radial_shell_integrate(column_bed , args.nrad, args.shelltype, [None]*4, 'Volume', ['w'], 'column_bed_rsa', timeArray=timeArray)
    radial_shell_integrate(void_outlet, args.nrad, args.shelltype, [None]*4, 'Volume', ['w'], 'void_outlet_rsa', timeArray=timeArray)
    

def new_split_parser(args, local_args_list):

    ap = argparse.ArgumentParser()

    ap.add_argument('--split', nargs=2, type=float, help='0-1 positions for splitting the column into void-bed-void regions')
    ap.add_argument('--savedata', action='store_true', help='Flag to save projections data')

    # ap.add_argument("--type", choices=['full', 'shells', 'shells_at_slice'], help="Chromatogram for full area or shells")

    # ap.add_argument("--flow", help="Flowfield pvtu/vtu file for use in chromatograms. May need --resample-flow.")
    # ap.add_argument("--resample-flow", action=argparse.BooleanOptionalAction, default=None, help="Flag to resample flowfield data using concentration mesh")

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
    args = new_split_parser(args, local_args_list)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    reader = read_files(args['FILES'], filetype=args['filetype'])
    new_split(reader, args)


