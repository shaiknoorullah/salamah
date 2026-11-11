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
  # qmltestrunner finds QtQuick.Window and other modules only through this path.
  env.QML_IMPORT_PATH = "${pkgs.qt6.qtdeclarative}/lib/qt-6/qml";

  shellHook = ''
    git config core.hooksPath .githooks 2>/dev/null || true
  '';
}
