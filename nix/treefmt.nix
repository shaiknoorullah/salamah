{
  projectRootFile = "flake.nix";

  programs = {
    nixfmt.enable = true;
    ruff-format.enable = true;
    ruff-check.enable = true;
    shfmt.enable = true;
    qmlformat.enable = true;
  };

  settings = {
    formatter = {
      ruff-format.options = [
        "--config"
        ".config/ruff.toml"
      ];
      ruff-check.options = [
        "--config"
        ".config/ruff.toml"
      ];
    };
    global.excludes = [
      "tests/golden/*"
      "*.lock"
      "LICENSE"
    ];
  };
}
