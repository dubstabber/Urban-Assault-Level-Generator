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
	  gen3
	    single
	    campaign
	  gen4
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
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
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
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
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
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
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
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
| `--output-dir OUTPUT_DIR` | Yes | None | Directory where campaign `.ldf` files are written. The directory is created automatically. |

Built-in profile sizes:

| Profile | Output |
| --- | --- |
| `original` | 42-level original Generator2 campaign. |
| `md-ghorkov` | 16-level Metropolis Dawn Ghorkov campaign. |
| `md-taerkasten` | 15-level Metropolis Dawn Taerkasten campaign. |

## Generator3 Single Level

In the default **Remix** mode, reuse one hand-made original level: its terrain,
entity positions and balance numbers are kept, while faction identities, rosters
and sky are regenerated from the chosen profile. Pass `--synthesis` to instead
generate brand-new Wave Function Collapse terrain and place fresh entities on it.

```sh
ualg gen3 single --seed 12345 --campaign-profile original --output out/L0101.ldf
ualg gen3 single --seed 12345 --skeleton L1515 --output out/remix.ldf
ualg gen3 single --seed 12345 --synthesis --output out/synth.ldf
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--campaign-profile {original,md-ghorkov,md-taerkasten}` | No | `original` | Roster/profile used. `original` draws from the vanilla corpus; the `md-*` profiles draw from Metropolis Dawn. |
| `--synthesis` | No | Off | Synthesize new WFC terrain instead of remixing an authored level. |
| `--skeleton NAME` | No | None | Remix only: force a specific source level, e.g. `L1515`. When omitted, a skeleton is chosen from the seed. |
| `--level-id ID` | No | None | Remix only: use the original level with this id (e.g. `15` → `L1515`) as the skeleton. |
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
| `--zero-enemy-station-delays` | No | Off | Set all enemy host station `*_delay` values to `0`. |
| `--output OUTPUT` | Yes | None | Output `.ldf` file path. Parent directories are created automatically. |

## Generator3 Campaign

Remix a full authored campaign. Each campaign slot reuses the matching original
level as its skeleton, with gate progression rewired to the profile graph.

```sh
ualg gen3 campaign --seed 12345 --campaign-profile original --output-dir out/gen3
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--campaign-profile {original,md-ghorkov,md-taerkasten}` | No | `original` | Roster/profile used. |
| `--synthesis` | No | Off | Synthesize new WFC terrain for every level instead of remixing authored levels. |
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
| `--zero-enemy-station-delays` | No | Off | Set all enemy host station `*_delay` values to `0`. |
| `--output-dir OUTPUT_DIR` | Yes | None | Directory where campaign `.ldf` files are written. The directory is created automatically. |

Built-in profile sizes:

| Profile | Output |
| --- | --- |
| `original` | 44-level vanilla campaign. |
| `md-ghorkov` | 16-level Metropolis Dawn Ghorkov campaign. |
| `md-taerkasten` | 15-level Metropolis Dawn Taerkasten campaign. |

## Generator4 Single Level

Generate one campaign-aware synthesized level. The selected campaign slot
controls the tileset, map size, enemy enable pools, upgrade sectors, startup
tech, and output filename.

```sh
ualg gen4 single --seed 12345 --campaign-profile original --level-id 2 --output out/L0202.ldf
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--campaign-profile {original,md-ghorkov,md-taerkasten}` | No | `original` | Campaign profile/archetype set. |
| `--level-id ID` | No | None | Campaign slot to use as the archetype. When omitted, one profile slot is chosen from the seed. |
| `--difficulty-mode {normal,hard,extremely-hard}` | No | `normal` | Difficulty tuning. Hard reduces player ownership/stations and raises enemy energy; extremely hard also lowers player energy, expands enemy unit enables, and can add enemy hosts. |
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
| `--zero-enemy-station-delays` | No | Off | Set all enemy host station `*_delay` values to `0`. |
| `--output OUTPUT` | Yes | None | Output `.ldf` file path. Parent directories are created automatically. |

## Generator4 Campaign

Generate one campaign-aware synthesized level for every slot in a profile.

```sh
ualg gen4 campaign --seed 12345 --campaign-profile md-ghorkov --output-dir out/gen4
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--seed SEED` | No | `0` | Integer RNG seed. `0` uses the current time. |
| `--campaign-profile {original,md-ghorkov,md-taerkasten}` | No | `original` | Campaign profile/archetype set. |
| `--difficulty-mode {normal,hard,extremely-hard}` | No | `normal` | Difficulty tuning applied to every generated level. |
| `--zero-enemy-radar-budgets` | No | Off | Set all enemy host station `rad_budget` values to `0`. |
| `--zero-enemy-station-delays` | No | Off | Set all enemy host station `*_delay` values to `0`. |
| `--output-dir OUTPUT_DIR` | Yes | None | Directory where campaign `.ldf` files are written. The directory is created automatically. |

Built-in profile sizes match Generator3:

| Profile | Output |
| --- | --- |
| `original` | 44-level vanilla campaign. |
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
