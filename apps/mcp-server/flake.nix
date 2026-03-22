{
  description = "pokemon-mcp dev environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system:
          let
            pkgs = import nixpkgs { inherit system; };
          in
          f pkgs
        );
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.python314
            pkgs.uv
            pkgs.git
          ];

          shellHook = ''
            export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
            echo "pokemon-mcp dev shell ready"
            echo "Python: $(python --version)"
            echo "uv: $(uv --version)"
            echo "PYTHONPATH=$PYTHONPATH"
          '';
        };
      });
    };
}