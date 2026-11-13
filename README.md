# salamah

A public NixOS config for one home machine, built and tested in the open.

One flake, host `home`. Home-manager places the dotfiles. The first content is a Hyprland desktop with a hello-world bar, tested in a VM.

## Status

| Milestone | State |
|---|---|
| M1 Foundation | Build steps done. Closes after 3 green nightly VM runs. |
| M2 Principles | Next. The owner writes the philosophy, principles and goals. |
| M3 Home on NixOS | Later. A tested one-command install for the home PC. |

## Install

Not yet. M3 adds the install path.

## Develop

```sh
nix develop      # enter the dev shell
just --list      # every recipe
just check-fast  # format, lint, tests, hygiene and docs
just check       # Nix checks, then the fast checks
```

`make` forwards to `just`, so `make check` works too. The [develop guide](docs/guides/develop.md) has the details.

## Docs

The [docs index](docs/README.md) lists every doc. Docs follow Diataxis, and decisions use MADR.

- [Philosophy](docs/philosophy/philosophy.md)
- [Principles](docs/philosophy/principles.md)
- [Goals](docs/philosophy/goals.md)
- [Decisions](docs/decisions/README.md)
- [Layout](docs/reference/layout.md)

## How work is tracked

Every change starts as an issue, then a branch and a pull request. Types, areas, labels and milestones live in the [taxonomy](docs/reference/taxonomy.md). Issues also land on the repo's GitHub Project.

CI requires the `gate` and `hygiene` checks before a merge.

## Agents

Agents follow [AGENTS.md](AGENTS.md). They recommend, and the owner approves and merges.

## Licence

[MIT](LICENSE).
