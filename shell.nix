{
    pkgs ? import (builtins.fetchTarball {

      name = "nixpkgs-unstable-2022-04-14";
      url = "https://github.com/nixos/nixpkgs/archive/6361b4941a69395ebf15e6e56b142765fce850f9.tar.gz";
      sha256 = "1lzi51c5a2wrhvmv255qajlkba5f6j4pfvidlrh9r004snpw5ikj";
    
    }) {}
}:

let

    name = "paravision";


    my-python = pkgs.python3;
    python-with-my-packages = my-python.withPackages (p: with p; [
        numpy
        rich
        ruamel-yaml
        GitPython
        matplotlib
        addict
        fuzzywuzzy
    ]);

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

in pkgs.mkShell rec {
    inherit name;

    # paravision = pkgs.python3Packages.buildPythonPackage{
    #     pname = name;
    #     version = "0.1";
    #
    #     src = ./.;
    #
    #     propagatedBuildInputs = with pkgs; [
    #             python3Packages.numpy
    #             python3Packages.rich
    #             python3Packages.ruamel-yaml
    #             python3Packages.GitPython
    #             python3Packages.matplotlib
    #             python3Packages.addict
    #             python3Packages.fuzzywuzzy
    #             which
    #         ];
    #
    #     doCheck = false;
    # };

    buildInputs = with pkgs; [
        # paravision
        python-with-my-packages
        paraview
        openssh # For something related to openmpi/MCA/ORTE
    ];

  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PYTHONPATH="${paraview}/lib/python3.9/site-packages:$PYTHONPATH"
    PYTHONPATH=${python-with-my-packages}/${python-with-my-packages.sitePackages}:$PYTHONPATH
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    export PATH="$(pwd):$PATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
