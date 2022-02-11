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

from typing import Any

class ConfigHandler:

    def __init__(self):
        self.config = {}
        self.yaml=YAML(typ='safe')
        self.logger = Logger()
        self.logger.info("Creating config.")

    def read(self, fname):
        """
            Read the config yaml file, save into config dict
        """
        self.config = Dict(self.yaml.load(Path(fname)))

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
