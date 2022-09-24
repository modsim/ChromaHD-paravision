{
  inputs = { nixpkgs.url = "github:nixos/nixpkgs/6361b4941a69395ebf15e6e56b142765fce850f9"; };
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
  flake-utils.lib.eachDefaultSystem (system:
  let 
    pkgs = nixpkgs.legacyPackages.${system}; 
    # dir = ''/home/jayghoshter/dev/tools/paravision/'';

    mach-nix = import (builtins.fetchGit {
      url = "https://github.com/DavHau/mach-nix";
      ref = "refs/tags/3.5.0";
    }) {};


    ## Override paraview to run headless because openGL in nix can be a pain
    ## for non-NixOS.
    paraview = pkgs.paraview.overrideAttrs ( oldAttrs: rec {

        cmakeFlags = [
            "-DCMAKE_BUILD_TYPE=Release"
            "-DPARAVIEW_ENABLE_FFMPEG=ON"
            "-DPARAVIEW_ENABLE_XDMF3=ON"
            "-DPARAVIEW_INSTALL_DEVELOPMENT_FILES=ON"
            "-DPARAVIEW_USE_MPI=ON"
            "-DPARAVIEW_USE_PYTHON=ON"
            "-DVTK_SMP_IMPLEMENTATION_TYPE=TBB"
            "-DVTK_OPENGL_HAS_OSMESA=ON"
            "-DVTK_USE_X=OFF"
            "-DVTKm_ENABLE_MPI=ON"
            "-DCMAKE_INSTALL_LIBDIR=lib"
            "-DCMAKE_INSTALL_INCLUDEDIR=include"
            "-DCMAKE_INSTALL_BINDIR=bin"
            "-GNinja"
        ];

        buildInputs = oldAttrs.buildInputs ++ [
            pkgs.mesa
            pkgs.mesa.osmesa
        ];

        });

    in 
    {

      defaultPackage = pkgs.python3Packages.buildPythonPackage{
        pname = "paravision";
        version = "0.1";

        src = ./.;

        mnpyreq = mach-nix.mkPython {
          requirements = builtins.readFile ./requirements.txt;
        };

        propagatedBuildInputs = with pkgs; [
          mnpyreq
        ];

        doCheck = false;
      };


      devShell = pkgs.mkShell rec {
            name = "paravision";

            mnpyreq = mach-nix.mkPython {
              requirements = builtins.readFile ./requirements.txt;
            };

            buildInputs = with pkgs; [
              mnpyreq
              paraview
              openssh # For something related to openmpi/MCA/ORTE
              git
              which
            ];

            shellHook = ''
              # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
              # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
              export PIP_PREFIX=$(pwd)/_build/pip_packages
              export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
              export PYTHONPATH="${paraview}/lib/python3.9/site-packages:$PYTHONPATH"
              export PYTHONPATH="$(pwd):$PYTHONPATH"
              export PATH="$(pwd):$PATH"
              export PATH="$PIP_PREFIX/bin:$PATH"
              unset SOURCE_DATE_EPOCH
            '';
                  };

      });
}
