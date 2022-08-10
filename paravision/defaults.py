from addict import Dict

DEFAULT_CONFIG = Dict({
            'integrate': None,
            'project': ['none', 'Plane', 0.5, 'x'],
            'colormap': 'viridis',
            'colormap_fuzzy_cutoff': 70,
            'show_axis': False,
            'show_scalar_bar': False,
            'display_representation': 'Surface',
            'color_range_method': 'auto',
            'custom_color_range': None,
            'colors_logscale': False,
            'opacity_logscale': False,
            'opacity_mapping': False,
            'scalars': None,
            'zoom': 1,
            'view': ['-x', '-y'],
            'geometry': [2560, 1440],
            'output_prefix': None,
            'filetype': 'pvtu',
            'standalone': False,
            'append_datasets': False,
            'FILES': [],

            'type': None,
            'flow': None,
            'resample_flow': False,
            'shelltype': 'EQUIDISTANT',
            'nrad': 5,
            'ncol': 10,
            'normalize': None,
            'packedbed': None,
            'interstitial': None

            })
