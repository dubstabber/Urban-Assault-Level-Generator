# CLI Reference

The installed command-line entry point is `ualg`. When running directly from a
source checkout, set `PYTHONPATH=src` and use `python -m ualg.cli`.

```sh
PYTHONPATH=src python -m ualg.cli --help
```

All generation commands write Urban Assault `.ldf` text files. A seed value of
`0` means "use the current time"; use any nonzero integer seed for repeatable
output.

## Command Tree

```text
ualg
  gen1
    single
    campaign
  gen2
    single
    campaign
```

Every command supports `-h` or `--help`.

## Generator1 Single Level

Generate one Random UA-derived Generator1 level.

```sh
ualg gen1 single --seed 12345 --difficulty 5 --skill 6 --output out/L0101.ldf
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--difficulty DIFFICULTY` | No | `5` | Integer difficulty used by the difficulty scenario when `--skill` is `0`. |
| `--skill SKILL` | No | `0` | Scenario category selector. Nonzero values are clamped to categories `1` through `11`; `0` uses the difficulty-based scenario. |
| `--strict-parity` | No | Off | Disable improved tileset filtering and use the stricter recovered parity behavior. |
| `--output OUTPUT` | Yes | None | Output `.ldf` file path. Parent directories are created automatically. |

## Generator1 Campaign

Generate a Generator1 campaign into a directory.

```sh
ualg gen1 campaign --seed 12345 --campaign-profile original --output-dir out/gen1
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--difficulty DIFFICULTY` | No | `5` | Integer difficulty passed into each generated level. |
| `--strict-parity` | No | Off | Disable improved tileset filtering and use the stricter recovered parity behavior. |
| `--campaign-profile {original,md-ghorkov,md-taerkasten}` | No | `original` | Campaign roster/profile to generate. |
| `--output-dir OUTPUT_DIR` | Yes | None | Directory where campaign `.ldf` files are written. The directory is created automatically. |

Built-in profile sizes:

| Profile | Output |
| --- | --- |
| `original` | 44-level original Generator1 campaign. |
| `md-ghorkov` | 16-level Metropolis Dawn Ghorkov campaign. |
| `md-taerkasten` | 15-level Metropolis Dawn Taerkasten campaign. |

## Generator2 Single Level

Generate one PHP-derived Generator2 level.

```sh
ualg gen2 single --seed 12345 --level-id 1 --output out/L0101.ldf
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--level-id LEVEL_ID` | No | `1` | Original Generator2 campaign level ID to generate. |
| `--zero-enemy-station-delays` | No | Off | Set all enemy host station `*_delay` values to `0`. |
| `--output OUTPUT` | Yes | None | Output `.ldf` file path. Parent directories are created automatically. |

Valid `--level-id` values are the original Generator2 campaign IDs:

```text
1, 2, 3, 4, 5, 10, 11, 12, 15, 20, 21, 22, 23, 25, 26, 30,
31, 32, 33, 34, 40, 41, 42, 43, 44, 50, 51, 52, 53, 54, 60,
61, 62, 63, 64, 66, 70, 71, 72, 73, 74, 75
```

Unknown level IDs fail with `ValueError: unknown Generator2 level id: ...`.

## Generator2 Campaign

Generate a Generator2 campaign into a directory.

```sh
ualg gen2 campaign --seed 12345 --campaign-profile original --output-dir out/gen2
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--campaign-profile {original,md-ghorkov,md-taerkasten}` | No | `original` | Campaign roster/profile to generate. |
| `--zero-enemy-station-delays` | No | Off | Set all enemy host station `*_delay` values to `0`. |
| `--output-dir OUTPUT_DIR` | Yes | None | Directory where campaign `.ldf` files are written. The directory is created automatically. |

Built-in profile sizes:

| Profile | Output |
| --- | --- |
| `original` | 42-level original Generator2 campaign. |
| `md-ghorkov` | 16-level Metropolis Dawn Ghorkov campaign. |
| `md-taerkasten` | 15-level Metropolis Dawn Taerkasten campaign. |

## GUI Command

The package also installs `ualg-gui`, equivalent to running:

```sh
python -m ualg.gui
```

`ualg-gui` does not accept command-line arguments. The repository also includes
double-click launchers:

| Platform | Launcher |
| --- | --- |
| Windows | `launch-gui.cmd` |
| Linux | `launch-gui.sh` |

On Linux, make the launcher executable once:

```sh
chmod +x launch-gui.sh
```
