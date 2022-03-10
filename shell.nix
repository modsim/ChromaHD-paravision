let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
    name = "paravision";

  buildInputs = [
    pkgs.python3
    pkgs.python3Full
    pkgs.python3Packages.setuptools
    pkgs.python3Packages.numpy
    pkgs.python3Packages.rich
    pkgs.python3Packages.ruamel-yaml
    pkgs.python3Packages.GitPython
    pkgs.python3Packages.matplotlib
    pkgs.python3Packages.addict
  ];
  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
