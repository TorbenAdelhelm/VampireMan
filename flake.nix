{
  description = "Pflotran flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      poetry2nix,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryEnv overrides;
        python3_env = mkPoetryEnv {
          projectDir = ./.;
          overrides = overrides.withDefaults (
            _: prev: {
              numpydantic = prev.numpydantic.override { preferWheel = true; };
            }
          );
        };
      in
      {
        packages = rec {
          default = pflotran;

          # The mpi implementation here could also be set to pkgs.mpich
          mpi = pkgs.openmpi;

          hdf5 = pkgs.hdf5.override {
            cppSupport = false;
            fortranSupport = true;
            mpiSupport = true;
            inherit mpi;
          };

          parmetis = pkgs.parmetis.override {
            inherit mpi;
          };

          petsc =
            (pkgs.petsc.override {
              hdf5-support = true;
              petsc-optimized = true;
              withParmetis = true;
              inherit parmetis hdf5 mpi;
            }).overrideAttrs
              rec {
                version = "3.21.5";
                src = pkgs.fetchzip {
                  url = "https://web.cels.anl.gov/projects/petsc/download/release-snapshots/petsc-${version}.tar.gz";
                  hash = "sha256-D/QgCcq81Ym9uF+6n2uFj+vPrXHCrIUwCtXW0E1f1FQ=";
                };
                patches = [ ./filter_mpi_warnings.patch ];
                doInstallCheck = system != "aarch64-linux";
              };

          pflotran = pkgs.stdenv.mkDerivation rec {
            pname = "pflotran";
            version = "6.0.0";
            src = pkgs.fetchFromBitbucket {
              owner = "pflotran";
              repo = "pflotran";
              rev = "v${version}";
              hash = "sha256-pIaHlAT3lMx7Uc3gIwMBnsVePIVv71fec1QYXmrj2jA=";
            };
            enableParallelBuilding = true;
            PETSC_DIR = petsc;
            nativeBuildInputs = [
              mpi
            ];
            buildInputs = [
              hdf5
              mpi
              parmetis
            ];
            strictDeps = true;
            patches = [ ./pflotran.patch ];
          };

          build_h5_file = pkgs.stdenvNoCC.mkDerivation {
            name = "buildH5File";
            src = ./.;

            nativeBuildInputs = [
              self.packages.${system}.default
              mpi
              python3_env
            ];

            buildPhase = ''
              python -m vampireman --non-interactive
            '';

            installPhase = ''
              mkdir -p $out
              mv datasets_out/*/datapoint-0/pflotran.h5 $out/pflotran.h5
            '';
          };

          inherit python3_env;
        };

        devShells = {
          default = pkgs.mkShell {
            PFLOTRAN_DIR = self.packages.${system}.default;
            buildInputs = [
              self.packages.${system}.default
              self.packages.${system}.mpi
              pkgs.poetry
              pkgs.tree
              pkgs.ruff
              pkgs.pyright
              pkgs.pylint
              pkgs.nixfmt-rfc-style
              pkgs.treefmt
              python3_env
              self.packages.${system}.hdf5
            ];
          };
        };

        checks = {
          treefmt = pkgs.stdenvNoCC.mkDerivation {
            name = "treefmtTest";
            src = ./.;

            doCheck = true;

            nativeBuildInputs = [
              pkgs.treefmt
              pkgs.nixfmt-rfc-style
              pkgs.ruff
            ];

            checkPhase = ''
              treefmt --version
              treefmt --verbose --on-unmatched=debug --no-cache --fail-on-change
            '';

            installPhase = "mkdir -p $out";
          };

          ruff = pkgs.stdenvNoCC.mkDerivation {
            name = "ruff";
            src = ./.;

            doCheck = true;

            nativeBuildInputs = [ pkgs.ruff ];

            checkPhase = ''
              ruff check .
            '';

            installPhase = "mkdir -p $out";
          };

          pyright = pkgs.stdenvNoCC.mkDerivation {
            name = "pyright";
            src = ./.;

            doCheck = true;

            nativeBuildInputs = [
              pkgs.pyright
              python3_env
            ];

            checkPhase = ''
              pyright
            '';

            installPhase = "mkdir -p $out";
          };

          check_h5_file = pkgs.stdenvNoCC.mkDerivation {
            name = "checkH5File";
            src = ./.;

            doCheck = true;

            nativeBuildInputs = [
              self.packages.${system}.default
              self.packages.${system}.mpi
              self.packages.${system}.hdf5
              pkgs.openssh
              python3_env
            ];

            checkPhase = ''
              python -m vampireman --non-interactive
              # h5diff exits with code 0 if any objects are not comparable
              h5diff -v1 datasets_out/*/datapoint-0/pflotran.h5 reference_files/pflotran.h5 | tee diff.out
              if grep -q "Some objects are not comparable" diff.out; then
                exit 1
              fi
            '';

            installPhase = "mkdir -p $out";
          };

          pytest = pkgs.stdenvNoCC.mkDerivation {
            name = "pytest";
            src = ./.;

            doCheck = true;

            nativeBuildInputs = [
              python3_env
              self.packages.${system}.default
            ];

            checkPhase = ''
              pytest
            '';

            installPhase = "mkdir -p $out";
          };
        };
      }
    );
}
