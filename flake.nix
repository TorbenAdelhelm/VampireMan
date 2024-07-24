{
  description = "Pflotran flake";

  inputs.nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

  outputs =
    {
      self,
      nixpkgs,
      poetry2nix,
    }:
    let
      pkgs = import nixpkgs {
        system = "x86_64-linux";
        config.allowUnfree = true;
      };

      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryEnv;
      python3_env = mkPoetryEnv { projectDir = ./.; };
    in
    {
      packages.x86_64-linux = rec {
        default = pflotran;

        hdf5 = pkgs.hdf5.override {
          cppSupport = false;
          fortranSupport = true;
          mpiSupport = true;
        };

        petsc =
          (pkgs.petsc.override {
            petsc-optimized = true;
            hdf5-support = true;
            inherit hdf5;
          }).overrideAttrs
            { patches = [ ./filter_mpi_warnings.patch ]; };

        pflotran = pkgs.stdenv.mkDerivation rec {
          name = "pflotran";
          version = "5.0.0";
          src = pkgs.fetchFromBitbucket {
            owner = "pflotran";
            repo = "pflotran";
            rev = "v${version}";
            hash = "sha256-j934pPT9zSbRgV4xgwJtycYcaq9Qs7Hgpxc5e6dKPdM=";
          };
          enableParallelBuilding = true;
          PETSC_DIR = petsc;
          nativeBuildInputs = [
            pkgs.mpi
            pkgs.pkg-config
          ];
          buildInputs = [ hdf5 ];
          patches = [ ./pflotran.patch ];
          doCheck = false;
        };

        inherit python3_env;
      };

      devShells.x86_64-linux = {
        default = pkgs.mkShell {
          PFLOTRAN_DIR = self.packages.x86_64-linux.default;
          buildInputs = [
            self.packages.x86_64-linux.default
            pkgs.mpi
            pkgs.poetry
            python3_env
          ];
        };
      };
    };
}
