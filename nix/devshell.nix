{ pkgs, treefmt }:
pkgs.mkShell {
  packages = [
    treefmt
    (pkgs.python3.withPackages (ps: [
      ps.pytest
      ps.pillow
    ]))
  ]
  ++ (with pkgs; [
    just
    gh
    git
    go
    ruff
    pyright
    golangci-lint
    gofumpt
    shellcheck
    shfmt
    nixfmt
    statix
    deadnix
    typos
    gitleaks
    lychee
    vale
    rumdl
    qt6.qtdeclarative
    quickshell
    tesseract
    pinact
  ]);

  env.PYTHONDONTWRITEBYTECODE = "1";

  shellHook = ''
    git config core.hooksPath .githooks 2>/dev/null || true
  '';
}
