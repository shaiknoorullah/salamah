# List the available recipes.
default:
    @just --list

# Format every file with treefmt.
fmt:
    nix fmt

# Run the unit tests.
test:
    python3 -m pytest -c .config/pytest.ini tools

# Run the fast checks: format, lint and tests.
check-fast:
    treefmt --fail-on-change
    ruff check --config .config/ruff.toml tools
    just test
    python3 -m tools.hygiene.scan $(git ls-files)

# Run the Nix checks, then the fast checks.
check:
    nix build --no-link .#checks.x86_64-linux.formatting .#checks.x86_64-linux.unit
    just check-fast

# Report missing tools and uninstalled git hooks.
doctor:
    python3 -m tools.doctor

# Point git at the repo hooks.
hooks:
    git config core.hooksPath .githooks
