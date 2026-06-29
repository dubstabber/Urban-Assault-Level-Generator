# Backend API Reference

The supported backend API is intentionally small and centered on generator
services plus result models. Import from `ualg` for normal use:

```python
from ualg import (
    Generator1,
    Generator1CustomOptions,
    Generator2,
    GeneratedCampaign,
    GeneratedLevel,
    MSVCRTRandom,
)
```

Internal modules under `ualg.gen1` and `ualg.gen2` are implementation details.
The GUI workflow helpers are also not part of the backend API described here.

## Generator1

`Generator1(profile_registry: ProfileRegistry | None = None)`

Random UA-derived terrain and campaign generator. By default it uses the built-in
campaign profiles and improved playable output behavior.

### `generate_single`

```python
level = Generator1().generate_single(
    seed=424242,
    difficulty=5,
    skill=6,
    improved=True,
    zero_enemy_radar_budgets=False,
)
```

Signature:

```python
generate_single(
    seed: int = 0,
    difficulty: int = 5,
    skill: int = 0,
    improved: bool = True,
    *,
    zero_enemy_radar_budgets: bool = False,
) -> GeneratedLevel
```

| Parameter | Default | Description |
| --- | --- | --- |
| `seed` | `0` | Integer RNG seed. `0` uses the current time. |
| `difficulty` | `5` | Difficulty used by the difficulty-based scenario when `skill` is `0`. |
| `skill` | `0` | Scenario category selector. Nonzero values are clamped to `1` through `11`; `0` uses the difficulty-based scenario. |
| `improved` | `True` | Keep improved tileset filtering enabled. Pass `False` for strict parity behavior. |
| `zero_enemy_radar_budgets` | `False` | Set all enemy host station `rad_budget` values to `0`. |

### `generate_campaign`

```python
campaign = Generator1().generate_campaign(
    seed=13579,
    difficulty=5,
    improved=True,
    campaign_profile="original",
    zero_enemy_radar_budgets=False,
)
```

Signature:

```python
generate_campaign(
    seed: int = 0,
    difficulty: int = 5,
    improved: bool = True,
    campaign_profile: str = "original",
    *,
    zero_enemy_radar_budgets: bool = False,
) -> GeneratedCampaign
```

| Parameter | Default | Description |
| --- | --- | --- |
| `seed` | `0` | Integer RNG seed. `0` uses the current time. |
| `difficulty` | `5` | Difficulty passed into each generated level. |
| `improved` | `True` | Keep improved tileset filtering enabled. Pass `False` for strict parity behavior. |
| `campaign_profile` | `"original"` | Built-in choices are `"original"`, `"md-ghorkov"`, and `"md-taerkasten"`. |
| `zero_enemy_radar_budgets` | `False` | Set all enemy host station `rad_budget` values to `0`. |

Unknown campaign profiles raise `ValueError` and include the available choices.

### `generate_custom`

```python
options = Generator1CustomOptions(
    seed=778899,
    width=14,
    height=12,
    gate_target_level_id=70,
    gate_key_count=4,
    player_energy=600000,
    zero_enemy_radar_budgets=True,
)
level = Generator1().generate_custom(options)
```

Signature:

```python
generate_custom(options: Generator1CustomOptions) -> GeneratedLevel
```

`generate_custom` creates a single Generator1 level using explicit custom
options. It returns a `GeneratedLevel` with filename `custom_level.ldf`.

## Generator1CustomOptions

`Generator1CustomOptions` is a dataclass used by `Generator1.generate_custom`.

| Field | Default | Description |
| --- | --- | --- |
| `seed` | `0` | Integer RNG seed. `0` uses the current time. |
| `difficulty` | `5` | Difficulty used when no custom scenario fields are supplied. |
| `improved` | `True` | Keep improved tileset filtering enabled. |
| `width` / `height` | `None` | Custom map size. Both must be set to force size. Width is clamped to `4..45`; height is clamped to `3..32`. |
| `gate_target_level_id` | `0` | Target level written into the gate block, clamped to `0` or greater. |
| `gate_key_count` | `None` | Override gate key count, clamped to `0..16`. |
| `win_movie` / `lose_movie` | `False` | Emit win or lose movie markers. |
| `player_energy` | `None` | Override player energy, clamped to at least `1`. |
| `ai_slot_present` | `{}` | Mapping of faction ID to up to three booleans for active enemy host slots. |
| `ai_slot_energy` | `{}` | Mapping of faction ID to up to three energy values. Nonzero values are clamped to at least `1`. |
| `ai_host_vehicle_id` | `{}` | Mapping of faction ID to one host vehicle ID for that faction. |
| `ai_slot_host_vehicle_id` | `{}` | Mapping of faction ID to up to three per-slot host vehicle IDs. |
| `superitem_flags` | `None` | Optional list of up to two booleans selecting superitems. |
| `random_superitems` | `False` | Randomly select `0..2` superitems when `superitem_flags` is not set. |
| `superitem_countdowns` | `{}` | Mapping for superitem indexes `1` and `2`; values are clamped to `0` or greater. |
| `enabled_vehicles` | `{}` | Mapping of faction ID to vehicle IDs forced into the enable block. |
| `enabled_buildings` | `{}` | Mapping of faction ID to building IDs forced into the enable block. |
| `zero_enemy_radar_budgets` | `False` | Set all enemy host station `rad_budget` values to `0`. |

Faction IDs are defined in `ualg.constants`: `1` Resistance, `2` Sulgogars,
`3` Mykonians, `4` Taerkasten, `5` Black Sect, `6` Ghorkovs, and `7` Tutor.

## Generator2

`Generator2(profile_registry: ProfileRegistry | None = None)`

PHP-derived Generator2 implementation.

### `generate_single`

```python
level = Generator2().generate_single(
    seed=112233,
    level_id=1,
    zero_enemy_station_delays=False,
    zero_enemy_radar_budgets=False,
)
```

Signature:

```python
generate_single(
    seed: int = 0,
    level_id: int = 1,
    *,
    zero_enemy_station_delays: bool = False,
    zero_enemy_radar_budgets: bool = False,
) -> GeneratedLevel
```

| Parameter | Default | Description |
| --- | --- | --- |
| `seed` | `0` | Integer RNG seed. `0` uses the current time. |
| `level_id` | `1` | Original Generator2 campaign level ID to generate. |
| `zero_enemy_station_delays` | `False` | Set all enemy host station `*_delay` values to `0`. |
| `zero_enemy_radar_budgets` | `False` | Set all enemy host station `rad_budget` values to `0`. |

Unknown level IDs raise `ValueError`.

### `generate_campaign`

```python
campaign = Generator2().generate_campaign(
    seed=998877,
    campaign_profile="original",
    zero_enemy_station_delays=True,
    zero_enemy_radar_budgets=True,
)
```

Signature:

```python
generate_campaign(
    seed: int = 0,
    campaign_profile: str = "original",
    *,
    zero_enemy_station_delays: bool = False,
    zero_enemy_radar_budgets: bool = False,
) -> GeneratedCampaign
```

| Parameter | Default | Description |
| --- | --- | --- |
| `seed` | `0` | Integer RNG seed. `0` uses the current time. |
| `campaign_profile` | `"original"` | Built-in choices are `"original"`, `"md-ghorkov"`, and `"md-taerkasten"`. |
| `zero_enemy_station_delays` | `False` | Set all enemy host station `*_delay` values to `0`. |
| `zero_enemy_radar_budgets` | `False` | Set all enemy host station `rad_budget` values to `0`. |

Unknown campaign profiles raise `ValueError` and include the available choices.

## Generator3

`Generator3(profile_registry: ProfileRegistry | None = None)`

Corpus-driven, authored-style generator with two modes. **Remix**
(`mode="remix"`, default) reuses a hand-made original level as a skeleton
(terrain maps, entity positions, balance numbers) and swaps only faction
identities, rosters, sky and campaign wiring. **Synthesis**
(`mode="synthesis"`) learns tile-adjacency from the corpus and uses Wave
Function Collapse to generate new coherent terrain, then places fresh entities
on it. The skeleton corpus is committed package data at
`src/ualg/data/gen3_corpus.json`.

### `generate_single`

```python
level = Generator3().generate_single(
    seed=12345,
    campaign_profile="original",
    skeleton="L1515",
)
synth = Generator3().generate_single(seed=12345, mode="synthesis")
```

Signature:

```python
generate_single(
    seed: int = 0,
    *,
    campaign_profile: str = "original",
    mode: str = "remix",
    skeleton: str | None = None,
    level_id: int | None = None,
    zero_enemy_radar_budgets: bool = False,
    zero_enemy_station_delays: bool = False,
) -> GeneratedLevel
```

| Parameter | Default | Description |
| --- | --- | --- |
| `seed` | `0` | Integer RNG seed. `0` uses the current time. |
| `campaign_profile` | `"original"` | Roster/profile. `"original"` uses the vanilla corpus; `"md-ghorkov"`/`"md-taerkasten"` use Metropolis Dawn. |
| `mode` | `"remix"` | `"remix"` or `"synthesis"`. |
| `skeleton` | `None` | Remix only: force a source level by name, e.g. `"L1515"`. When omitted, a skeleton is chosen from the seed. |
| `level_id` | `None` | Remix only: use the original level with this id (e.g. `15` → `L1515`) as the skeleton. |
| `zero_enemy_radar_budgets` | `False` | Set all enemy host station `rad_budget` values to `0`. |
| `zero_enemy_station_delays` | `False` | Set all enemy host station `*_delay` values to `0`. |

The returned `GeneratedLevel.metadata` includes `"mode"` and `"warnings"`
(playability check results). Remix adds `"skeleton"` and `"faction_remap"`;
synthesis adds `"synth_method"` (`"wfc"` or `"scanline"`).

### `generate_campaign`

```python
campaign = Generator3().generate_campaign(
    seed=12345,
    campaign_profile="original",
)
```

Signature:

```python
generate_campaign(
    seed: int = 0,
    campaign_profile: str = "original",
    *,
    mode: str = "remix",
    zero_enemy_radar_budgets: bool = False,
    zero_enemy_station_delays: bool = False,
) -> GeneratedCampaign
```

In Remix mode each campaign slot reuses the matching original level as its
skeleton; in Synthesis mode each slot is generated from scratch. Gate
progression is rewired to the profile graph in both modes.

## Result Models

### `GeneratedLevel`

Fields:

| Field | Type | Description |
| --- | --- | --- |
| `filename` | `str` | Suggested campaign filename for this level. |
| `level_id` | `int` | Numeric Urban Assault level ID. |
| `seed` | `int` | Normalized seed used for generation. |
| `width` / `height` | `int` | Map dimensions in sectors. |
| `tileset` | `int` | Selected tileset ID. |
| `text` | `str` | Complete generated LDF text. |
| `maps` | `dict[str, list[list[int]]]` | Generated map rows keyed by map name. |
| `metadata` | `dict[str, Any]` | Generator-specific metadata. |

Write a level to disk:

```python
path = level.write("out/L0101.ldf")
```

`write(path: str | Path) -> Path` creates parent directories and writes UTF-8
text with the generated line endings.

### `GeneratedCampaign`

Fields:

| Field | Type | Description |
| --- | --- | --- |
| `seed` | `int` | Normalized campaign seed. |
| `levels` | `list[GeneratedLevel]` | Generated levels in campaign order. |
| `errors` | `list[str]` | Reserved for generation errors. Current successful generation returns an empty list. |
| `ok` | `bool` | `True` when `errors` is empty. |

Write all campaign levels to disk:

```python
paths = campaign.write("out/campaign")
```

`write(directory: str | Path) -> list[Path]` creates the directory and writes
each level using its `filename`.

## Campaign Profiles

Built-in profile names are available through `ProfileRegistry`:

```python
from ualg.campaign_profiles import default_profile_registry

registry = default_profile_registry()
print(registry.names("generator1"))
print(registry.names("generator2"))
```

Both generators currently expose:

```text
original, md-ghorkov, md-taerkasten
```

To use custom profile data, build a registry and inject it into a generator:

```python
from ualg.campaign_profiles import ProfileRegistry
from ualg import Generator1

registry = ProfileRegistry.from_mapping({
    "version": 1,
    "generators": {
        "generator1": {
            "tiny": {
                "data_profile": "original",
                "roster_profile": "original",
                "mission_map_profile": None,
                "mission_briefing_default": "MB_02.IFF",
                "mission_debriefing_default": "DB_02.IFF",
                "player_faction": 1,
                "level_filenames": ["l0101.ldf"],
                "target_mode": "next",
            }
        }
    },
})

campaign = Generator1(profile_registry=registry).generate_campaign(
    seed=1234,
    campaign_profile="tiny",
)
```

For the profile data shape and maintenance guidance, see
[`docs/architecture.md`](architecture.md).

## MSVCRTRandom

`MSVCRTRandom(seed: int = 1)` implements the Visual C++ 6.0 compatible
`rand`/`srand` sequence used by the generators.

```python
from ualg import MSVCRTRandom

rng = MSVCRTRandom(1)
values = [rng.rand() for _ in range(5)]
```

Common methods:

| Method | Description |
| --- | --- |
| `srand(seed=0)` | Reset the RNG state. Seed `0` uses the current time. |
| `rand()` | Return the next integer in `0..32767`. |
| `rand_mod(n)` | Return `rand() % n`; returns `0` when `n <= 0`. |
| `rand_range(min_value, max_value)` | Return an inclusive random integer. Reversed bounds are accepted. |
| `rand_float()` | Return a float in `[0.0, 1.0)`. |
| `choice(values)` | Choose one item from a non-empty sequence. |
| `state` | Property exposing the masked internal RNG state. |
