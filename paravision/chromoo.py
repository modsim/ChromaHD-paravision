from paraview.simple import *

from paravision.utils import ConfigHandler, default_parser, read_files
from paravision.radial_porosity import radial_porosity_profile
from paravision.radial_shell_integrate import radial_shell_integrate

from rich import print, print_json
from addict import Dict

def local_parser(argslist):
    ap = default_parser()

    ap.add_argument('--flow', nargs='*', help='Stationary flow results')
    ap.add_argument('--bulkc', nargs='*', help='Bulk concentration')
    ap.add_argument('--bedc', nargs='*', help='Bed particle pore phase concentration input')
    ap.add_argument('--bedq', nargs='*', help='Bed solid phase concentration input')
    ap.add_argument('--nrad', type=int, default=1, help='Number of radial zones')
    ap.add_argument('--shelltype', default='EQUIDISTANT', choices = [ 'EQUIDISTANT', 'EQUIVOLUME' ], 
                    help='Radial discretization type')

    args = Dict(vars(ap.parse_args(argslist)))
    print_json(data=args)
    return args

if __name__ == "__main__":
    config = ConfigHandler()
    args = config.load_and_parse_args(local_parser)

    print("[bold yellow]Final set of args:[/bold yellow]")
    print_json(data=args)

    args = Dict(args)

    if args.flow:
        flow = read_files(args.flow)
        radial_porosity_profile(flow, args.nrad, args.shelltype, args.project, args.output_prefix)
        flow_args = args
        flow_args.output_prefix = f'{flow_args.output_prefix}_flowrate' if flow_args.output_prefix else 'flowrate'
        radial_shell_integrate(flow, **args, divide_by_length=True)

    if args.bulkc:
        bulkc = read_files(args.bulkc)
        bulk_args = args
        bulk_args.output_prefix = f'{bulk_args.output_prefix}_bulk' if bulk_args.output_prefix else 'bulkc'
        radial_shell_integrate(bulkc, **args)

    if args.bedc:
        bedc = read_files(args.bedc)
        bed_args = args
        bed_args.output_prefix = f'{bed_args.output_prefix}_bedc' if bed_args.output_prefix else 'bedc'
        radial_shell_integrate(bedc, **args, scale=0.75)

    if args.bedq:
        bedq = read_files(args.bedq)
        bed_args = args
        bed_args.output_prefix = f'{bed_args.output_prefix}_bedq' if bed_args.output_prefix else 'bedc'
        radial_shell_integrate(bedq, **args, scale=0.25)
