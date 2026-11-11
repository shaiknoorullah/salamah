# List the available recipes.
default:
    @just --list

# Format every file with treefmt.
fmt:
    nix fmt

# Run the unit tests.
test:
    python3 -m pytest -c .config/pytest.ini tools
    just test-qml

# Run the QML tests headless.
test-qml:
    QT_QPA_PLATFORM=offscreen qmltestrunner -input shell/tests

# Run the fast checks: format, lint and tests.
check-fast:
    treefmt --fail-on-change
    ruff check --config .config/ruff.toml tools
    just test
    python3 -m tools.hygiene.scan $(git ls-files)
    just docs
    python3 -m tools.agents.check

# Run the Nix checks, then the fast checks.
check:
    nix build --no-link .#checks.x86_64-linux.formatting .#checks.x86_64-linux.unit .#checks.x86_64-linux.docs
    just check-fast

# Check the docs: checkers, rumdl, Vale and lychee (offline).
docs:
    python3 -m tools.docs check
    rumdl check --config .config/rumdl.toml .
    vale --config .config/vale.ini docs $(ls README.md AGENTS.md 2>/dev/null)
    lychee --offline --include-fragments --config .config/lychee.toml 'docs/**/*.md' README.md

# Check the J1 screenshot, and compare it to the golden when one exists.
visual:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 -m tools.visual j1 out/j1-bar.png
    if [ -f tests/golden/j1-bar.png ]; then
        python3 -m tools.visual compare tests/golden/j1-bar.png out/j1-bar.png --name j1-bar
    else
        echo no golden yet
    fi

# Build the VM test driver, run it into out/, then check the screenshots.
e2e:
    nix build -L .#checks.x86_64-linux.desktop-e2e.driver -o .cache/e2e-driver
    mkdir -p out
    .cache/e2e-driver/bin/nixos-test-driver -o out
    just visual

# Owner only: refresh the goldens from a fresh VM run and write out/contact.png.
golden-update:
    nix build -L .#checks.x86_64-linux.desktop-e2e.driver -o .cache/e2e-driver
    mkdir -p out tests/golden
    .cache/e2e-driver/bin/nixos-test-driver -o out
    cp out/*.png tests/golden/
    python3 -m tools.visual contact out/contact.png out/*.png

# Report missing tools and uninstalled git hooks.
doctor:
    python3 -m tools.doctor

# Point git at the repo hooks.
hooks:
    git config core.hooksPath .githooks
