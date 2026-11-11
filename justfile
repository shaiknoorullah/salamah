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

# Report missing tools and uninstalled git hooks.
doctor:
    python3 -m tools.doctor

# Point git at the repo hooks.
hooks:
    git config core.hooksPath .githooks
