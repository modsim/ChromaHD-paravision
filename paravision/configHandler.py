"""

ConfigHandler class.

contract:
    - must read and store values from yaml config
    - must provide easy access to deep/nested values (deep_get -> get)

"""

from ruamel.yaml import YAML
from functools import reduce

from pathlib import Path
from paravision.log import Logger

from addict import Dict
import argparse

from typing import Any

from rich import print as rprint

class ConfigHandler:

    def __init__(self):
        self.config = {}
        self.yaml=YAML(typ='safe')
        self.logger = Logger()
        self.logger.info("Creating config.")
        self.config = Dict({
            'integrate': None,
            'project': ['none', 'Plane', 0.5, 'x'],
            'shelltype': 'EQUIDISTANT',
            'nrad': 5,
            'colormap': 'viridis',
            'colormap_fuzzy_cutoff': 70,
            'show_axis': False,
            'show_scalar_bar': False,
            'display_representation': 'Surface',
            'color_range_method': 'auto',
            'custom_color_range': None,
            'scalars': None,
            'zoom': 1,
            'view': ['-x', '-y'],
            'geometry': [2560, 1440],
            'output_prefix': None,
            'filetype': 'pvtu',
            'standalone': False,
            'append_datasets': False,
            'FILES': [],
            })

    def read(self, fname):
        """
            Read the config yaml file, save into config dict
        """
        filepath = Path(fname)
        if not filepath.is_file():
            raise RuntimeError(f"No config file found: {fname}")
        self.config.update(Dict(self.yaml.load(filepath)))

    def get(self, keys, default=None, vartype=None, choices=[], wrapper=None) -> Any:
        """
        Simpler syntax to get deep values from a dictionary
        > config.get('key1.key2.key3', defaultValue)

        - typechecking
        - value restriction
        """
        value = reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys.split("."), self.config)

        if value is None:
            if default != None:
                self.logger.warn(keys, 'not specified! Defaulting to', str(default) or 'None (empty string)')
                value = default

        if vartype:
            if not isinstance(value, vartype):
                self.logger.die(keys, 'has invalid type!', str(type(value)), 'instead of', str(vartype))

        if choices:
            if value not in choices:
                self.logger.die(keys, 'has invalid value! Must be one of ', str(choices))

        if wrapper:
            value = wrapper(value)

        return value

    def get_config_file(self):
        ap = argparse.ArgumentParser()

        ap.add_argument("-c","--config", help="YAML config file")

        print("NOTE: Only parsing known arguments!")
        args, unknown =  ap.parse_known_args()

        return args.config, unknown

    def parse_cmdline_args(self, argslist):
        """ parse commandline args and update config

        NOTE: Make sure to set the default (especially bool types) to None.
        This makes it easier to update the config with args, allowing to switch bool flags on and off using cmdline
        """

        ap = argparse.ArgumentParser()

        ap.add_argument("-c","--config", help="YAML config file")

        ap.add_argument("--integrate", choices=['Volume', 'Area', 'None'], help="Integrate and average the given Volume/Area")
        ap.add_argument("--project", nargs=4, help="Projection. <clip|slice|none> <Plane|Cylinder..> <origin> <x|y|z>" )

        ## TODO: Check feasibility of creating such a feature
        # ap.add_argument("--radial-divide", help="Divide into radial sections??" )

        ap.add_argument("-cm", "--colormap", help="Use specified colormap. Fuzzy searches within paraview and then ScientificColourMaps7. See -cfc.")
        ap.add_argument("-cfc", "--colormap-fuzzy-cutoff", type=int, help="Fuzziness cutoff score for colormap names. 100 implies exact match.")
        ap.add_argument("-crm", "--color-range-method", choices=['auto', 'startzero', 'midzero', 'custom'], help="Range method for the scalar bar (color transfer function)")
        ap.add_argument("-ccr", "--custom-color-range", nargs=2, type=float, help="Custom range for the scalar bar (color transfer function). Ensure -crm == custom")

        ap.add_argument("-sa", "--show-axis", action=argparse.BooleanOptionalAction, default=None, help="Show coordinate axis")
        ap.add_argument("-sb", "--show-scalar-bar", action=argparse.BooleanOptionalAction, default=None, help="Show scalar color bar")

        ap.add_argument("-dr", "--display-representation", choices=['Surface', 'Surface With Edges', 'Points'],  help="Show Surface, Surface With Edges, etc")
        ap.add_argument("-s", "--scalars" , nargs='*' , help="Scalars to consider. (Previously colorvars).")

        ap.add_argument("-z", "--zoom", type=float, help="Zoom (camera.dolly) value for view")
        ap.add_argument("-v", "--view", nargs=2, help="Set view: target, viewup. Use +x, -z notation.")
        ap.add_argument("-g", "--geometry", nargs=2, type=int, help="Animation geometry size")

        ap.add_argument("-o", "--output-prefix", help="prefix for output filenames")
        ap.add_argument("-f", "--filetype", choices=['xdmf', 'vtu', 'vtk', 'pvtu'], help="filetype: xdmf | vtu | vtk | pvtu")

        ap.add_argument("--standalone", action=argparse.BooleanOptionalAction, default=None, help="Read files as separate standalone objects, not part of time series.")
        ap.add_argument("--append-datasets", action=argparse.BooleanOptionalAction, default=None, help="Use AppendDatasets on standalone files before processing.")

        ap.add_argument("FILES", nargs='*', help="files..")

        ## NOTE: Specific to chromatogram
        # ap.add_argument("--flow", help="Flowfield pvtu/vtu file for use in chromatograms. May need --resample-flow.")
        # ap.add_argument("--resample-flow", action=argparse.BooleanOptionalAction, default=None, help="Flag to resample flowfield data using concentration mesh")

        ## NOTE:  Specific to radial types: grm2d and radial_shell_integrate etc
        # ap.add_argument("-st"  , "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], help="Shell discretization type. See --nrad")
        # ap.add_argument("-nr"  , "--nrad", type=int, help="Radial discretization in particular plugins")

        ## NOTE: Specific to infogeneric
        # ap.add_argument("--packedbed", help="Packed bed mesh to use with --infogeneric")
        # ap.add_argument("--interstitial", help="Interstitial mesh to use with --infogeneric")

        args =  ap.parse_args(argslist)
        args = Dict(vars(ap.parse_args()))

        self.config.update([ (k,v) for k,v in args.items() if v is not None])
        print(self.config)
        return self.config 

    def parse_config_and_cmdline_args(self):

        configfile, argslist = self.get_config_file()
        if configfile: 
            self.read(configfile)
        self.parse_cmdline_args(argslist)

        return self.config


