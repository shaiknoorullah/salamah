{
  description = "salamah: home desktop on NixOS";

  inputs = {
    nixpkgs.url = "git+https://github.com/NixOS/nixpkgs?ref=nixos-unstable&shallow=1";
    treefmt-nix = {
      url = "git+https://github.com/numtide/treefmt-nix?shallow=1";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    home-manager = {
      url = "git+https://github.com/nix-community/home-manager?shallow=1";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      treefmt-nix,
      ...
    }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      treefmtEval = treefmt-nix.lib.evalModule pkgs ./nix/treefmt.nix;
    in
    {
      devShells.${system}.default = import ./nix/devshell.nix {
        inherit pkgs;
        treefmt = treefmtEval.config.build.wrapper;
      };

      formatter.${system} = treefmtEval.config.build.wrapper;

      checks.${system} = import ./nix/checks.nix {
        inherit pkgs self inputs;
        formatting = treefmtEval.config.build.check self;
      };
    };
}
