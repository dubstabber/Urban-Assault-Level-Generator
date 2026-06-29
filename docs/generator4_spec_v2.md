# Generator4 Specification v2: Authored Terrain And Strategic Infrastructure

This document specifies the next Generator4 iteration. Generator4 already
exists as a campaign-aware synthesis backend; v2 keeps the public API stable
and improves the generated levels so they look more like authored Urban
Assault campaign maps while still creating new layouts.

The v2 focus is narrow and measurable:

- add authored-style pre-placed power, flak, and radar infrastructure;
- replace mostly flat height maps and isolated cliff dots with terrain forms
  learned from original levels;
- preserve campaign-slot progression, legal rosters, gate wiring, map safety,
  and ground passability.

## Current Defects And Corpus Signals

The original-level corpus contains 75 LDF files. The current parser sees 71
map-bearing levels with complete map blocks. These levels show two patterns
that Generator4 v1 does not reproduce well enough.

### Infrastructure

Authored levels frequently deploy functional buildings directly in `blg_map`:

| Station category | Authored levels containing category | Authored station cells |
| --- | ---: | ---: |
| Power | 67 | 538 |
| Flak | 53 | 817 |
| Radar | 29 | 89 |

Current Generator4 campaigns emit power-station buildings through host-building
placement only, so generated maps lack authored-style flak and radar layers.
This is a major visual and gameplay difference from the original maps.

### Terrain

Authored `hgt_map` data has real terrain variety:

| Metric | Authored median | Authored min | Authored max |
| --- | ---: | ---: | ---: |
| Unique height values | 10 | 1 | 29 |
| Height range | 10 | 0 | 35 |
| Height standard deviation | 2.31 | 0.00 | 7.26 |
| Blocked-edge ratio, `abs(delta) > 4` | 0.059 | 0.000 | 0.304 |
| Maximum adjacent delta | 7 | 0 | 22 |

Current Generator4 usually produces one or two height values. It can match a
blocked-edge ratio numerically, but it does so with isolated cliff cells instead
of authored-looking plateaus, ramps, ridges, and barriers.

## Public Interface

Keep the existing Generator4 API unchanged:

```python
class Generator4:
    def __init__(self, profile_registry: ProfileRegistry | None = None) -> None: ...

    def generate_single(
        self,
        seed: int = 0,
        *,
        campaign_profile: str = "original",
        level_id: int | None = None,
        zero_enemy_radar_budgets: bool = False,
        zero_enemy_station_delays: bool = False,
    ) -> GeneratedLevel: ...

    def generate_campaign(
        self,
        seed: int = 0,
        campaign_profile: str = "original",
        *,
        zero_enemy_radar_budgets: bool = False,
        zero_enemy_station_delays: bool = False,
    ) -> GeneratedCampaign: ...
```

Metadata should remain backward compatible and may add these fields:

```python
{
    "generator": "generator4",
    "campaign_profile": profile_id,
    "source": "vanilla" | "metropolisDawn",
    "level_archetype": "L0202",
    "rules_version": 2,
    "tech_phase": {...},
    "terrain_profile": {
        "source_unique_heights": 10,
        "generated_unique_heights": 9,
        "source_blocked_edge_ratio": 0.059,
        "generated_blocked_edge_ratio": 0.052
    },
    "infrastructure_profile": {
        "source_counts": {"power": 2, "flak": 4, "radar": 1},
        "generated_counts": {"power": 2, "flak": 3, "radar": 1}
    },
    "synth_method": "wfc" | "scanline",
    "warnings": []
}
```

Do not add new user-facing options for v2. Generator4 should apply the improved
terrain and infrastructure behavior by default.

## Rules Dataset v2

Version the baked dataset as `version: 2`. Installed packages must still work
without access to `original-levels/`.

```json
{
  "version": 2,
  "profiles": {
    "original": {
      "source": "vanilla",
      "levels": []
    },
    "md-ghorkov": {
      "source": "metropolisDawn",
      "levels": []
    },
    "md-taerkasten": {
      "source": "metropolisDawn",
      "levels": []
    }
  }
}
```

Each level record should keep all v1 fields and add the following v2 fields.

### Infrastructure Placements

Extract every `blg_map` cell whose building id is known in `UAdata.json` as a
`power_station`, `flak_station`, or `radar_station`.

```json
{
  "infrastructure_placements": [
    {
      "category": "flak",
      "building": 30,
      "typ": 207,
      "owner": 6,
      "expected_owner": 6,
      "x": 5,
      "y": 1,
      "component": 0,
      "cluster": 2,
      "near_host_owner": 6,
      "distance_to_nearest_host": 4,
      "distance_to_gate": 18,
      "distance_to_required_object": 6,
      "height": 131,
      "local_height_delta_max": 5,
      "edge_role": "front"
    }
  ]
}
```

Field rules:

- `category` is one of `power`, `flak`, or `radar`.
- `building` is the raw `blg_map` id.
- `typ` is the compatible `typ_map` id from `UAdata.json`/`BUILDING_TYP_BY_ID`.
- `owner` is the actual `own_map` owner at that cell.
- `expected_owner` is the faction owner implied by `UAdata.json`, or `0` for
  neutral/other buildings.
- `component` is the height-passability component id.
- `cluster` groups same-category station cells connected within Chebyshev
  distance 2.
- `edge_role` is a coarse derived label: `base`, `front`, `choke`, `remote`,
  or `decorative`. It is for weighting only and need not be perfect.

### Infrastructure Profile

Summarize source placement patterns for synthesis:

```json
{
  "infrastructure_profile": {
    "counts": {"power": 2, "flak": 4, "radar": 1},
    "counts_by_owner": {
      "6": {"power": 1, "flak": 4, "radar": 1},
      "7": {"power": 1}
    },
    "cluster_sizes": {"power": [1, 1], "flak": [4], "radar": [1]},
    "neutral_or_tutor_power_count": 1,
    "has_radar": true,
    "has_flak": true,
    "max_station_density": 0.08
  }
}
```

`max_station_density` is source station cells divided by interior map cells,
clamped during generation so small maps do not become saturated.

### Terrain Profile

Replace the loose v1 `height_stats` shape with explicit terrain targets:

```json
{
  "terrain_profile": {
    "median": 128,
    "min": 121,
    "max": 137,
    "range": 16,
    "unique_count": 13,
    "stdev": 3.4,
    "histogram": {"121": 3, "122": 9, "123": 18},
    "quantiles": {"p10": 124, "p25": 126, "p50": 128, "p75": 131, "p90": 134},
    "blocked_edge_ratio": 0.07,
    "max_adjacent_delta": 9,
    "component_sizes": [212, 18],
    "assignments": {
      "robos": [],
      "squads": [],
      "gates": [],
      "items": [],
      "gems": [],
      "infrastructure": []
    },
    "feature_counts": {
      "plateaus": 3,
      "ramps": 4,
      "cliff_bands": 2,
      "isolated_peaks": 0,
      "basins": 1
    }
  }
}
```

Feature extraction may be heuristic. It only needs to provide stable targets
for synthesis and regression tests.

## Generation Pipeline

### 1. Resolve Profile And Archetype

- Normalize `campaign_profile`.
- Resolve the campaign slot by `level_id` or seeded selection.
- Load the matching v2 archetype record.
- Keep the archetype tileset and dimensions.
- Preserve startup include, prototype progression, upgrade gems, enemy enables,
  host/squad source records, gate targets, and mission map behavior from v1.

### 2. Synthesize `typ_map`

- Use the current Generator3-derived adjacency/WFC model for the source corpus
  and tileset.
- Preserve standard energy-wall borders and corners.
- Treat generated functional cells as overrides: host buildings, stations,
  gates, items, and upgrade gems may replace synthesized `typ_map` values with
  required compatible values.

### 3. Place Hosts, Gates, Items, And Upgrade Gems

- Place host stations first, using the existing source-cell jitter behavior and
  host cap of 7.
- Reserve every occupied gameplay sector: hosts, gates, gate keys, items, item
  keys, and upgrade gems.
- Build the required route set from all sectors needed for ground progression:
  player host, required enemy hosts, gates, keys, items, item keys, and required
  player tech gems.
- Do not place infrastructure until these reserved cells are known.

### 4. Synthesize Authored Terrain

Generate `hgt_map` as a constrained terrain field, not as isolated random
barriers.

Required behavior:

- Match the archetype `terrain_profile` within tolerant bands:
  - blocked-edge ratio within `+/- 35%` relative when the source ratio is above
    `0.02`;
  - unique height count at least `50%` of source unique count for non-flat
    sources, with a minimum of 4 when source range is at least 6;
  - generated height range at least `50%` of source range for non-flat sources,
    unless validation fallback is required.
- Build multi-cell terrain forms:
  - plateaus: contiguous areas with small internal deltas;
  - ramps: paths where each adjacent step stays `<= 4`;
  - cliff bands/ridges: connected barrier edges with `delta > 4`;
  - basins or highlands for large maps when the source has broad height spread.
- Keep all required route cells in one passable component unless the archetype
  explicitly places required objects in separate components and there is a
  known non-ground gameplay reason.
- Keep fallback terrain more varied than v1 when possible: if full terrain
  synthesis fails, use broad smooth variation around the median and remove only
  barriers that disconnect required routes.

Recommended implementation:

1. Seed several plateau centers from source component and station/host patterns.
2. Grow smooth height regions by random walks or weighted flood fill.
3. Draw ridge/cliff bands from source blocked-edge ratio and feature counts.
4. Carve passable ramps between required route cells.
5. Smooth local noise while respecting the `delta <= 4` passability corridors.
6. Validate required connectivity and retry with lower barrier strength if
   needed.

### 5. Synthesize Strategic Infrastructure

Use the extracted infrastructure profile as weighted guidance rather than exact
copying.

Count rules:

- If a source archetype has a station category, generated output should include
  at least one station of that category unless there is no valid sector.
- Target count per category is a seeded value around the source count, normally
  `65%..135%` of source count.
- Clamp total station cells by available interior cells and
  `max_station_density`.
- Never exceed map safety limits or occupy reserved gameplay sectors.

Placement rules:

- Power stations prefer base-adjacent territory, secondary control points, or
  neutral/tutor-owner conquerable sectors when the source used owner `7`.
- Flak stations prefer approaches to bases, ridges, chokepoints, and front
  lines between ownership regions.
- Radar stations prefer defended territory behind fronts, near important host
  clusters, or near late-level strategic areas.
- Clusters should mimic source cluster sizes loosely; avoid placing all
  stations as isolated singletons when the source had clusters.
- Stations must be inside map bounds, away from energy-wall borders, and on
  passable cells unless the source clearly used decorative unreachable cells.

Ownership and compatibility rules:

- Write the station building id to `blg_map`.
- Write `BUILDING_TYP_BY_ID[building]` to `typ_map` when available.
- Write a participating faction owner to `own_map` for faction-owned flak,
  radar, and power stations.
- Preserve owner `7` for conquerable/tutorial power-station patterns when the
  source used owner `7`.
- Do not imply new build permissions. Pre-placed stations may exist even when
  the faction's `begin_enable` does not allow constructing them.
- Pick station ids from the source archetype first. If a category must be
  generated but the source id is incompatible with the active profile, use the
  same category from the active profile's roster.

### 6. Build Ownership Regions

- Grow `own_map` from player/enemy hosts and infrastructure seeds.
- Keep borders neutral owner `0`.
- Preserve explicit owner `7` infrastructure cells.
- Ensure every functional non-neutral building has a participating owner.
- Keep ownership coherent around station clusters; a station should not be an
  isolated owner cell unless the source pattern was isolated.

### 7. Place Squads

- Continue deriving squads from the source slot.
- Do not emit squad vehicles outside the owner's legal level enable pool.
- Ground squads should be placed on their owner's passable component or a
  contested component reachable from relevant objectives.
- Flying squads may be placed more freely, but still in bounds, off borders,
  and away from occupied sectors.

### 8. Render And Validate

- Render in the current Generator4 LDF style.
- Include v2 terrain and infrastructure summaries in metadata.
- Retry generation on fatal validation failures. If all attempts fail, return
  the least-bad level with warnings, as current Generator4 does.

## Validation Rules

Generator4 v2 validation should extend current `ualg.gen4.validate`.

Fatal checks:

- `typ_map`, `own_map`, `hgt_map`, and `blg_map` dimensions match.
- Energy-wall borders and corners are intact.
- Host station count is `1..7`.
- Squad count is `<= 100`; squad `num` is `<= 32`.
- Host, squad, gate, item, gem, and infrastructure coordinates are in bounds
  and not on the border.
- No two functional placements occupy the same sector unless the LDF format
  intentionally represents them in different blocks with one map cell.
- Every emitted enemy `begin_enable` remains a subset of the source slot after
  existing exclusion rules.
- Every generated enemy squad uses a vehicle available to its owner in that
  level slot.
- Required ground-route cells are connected through height edges with
  `abs(delta) <= 4`.
- Every generated upgrade gem building appears in `blg_map`.
- Every generated infrastructure building appears in `blg_map` and has a
  compatible `typ_map` value when known.
- Faction-owned flak/radar/power stations have a participating owner; owner
  `7` is allowed only for source-derived conquerable/tutorial power patterns.
- Rendered prototype, gem, and LDF blocks are balanced and parseable.

Warning-only checks:

- Generated station counts fall outside the target count band after clamping.
- Generated terrain misses a non-fatal profile target but required routes are
  valid.
- A source decorative unreachable component could not be recreated.
- A station category requested by a sparse source pattern could not be placed
  because all valid sectors were occupied.

## Test And Acceptance Criteria

### Rules Builder Tests

- Building category extraction uses `UAdata.json` `icon_type` values and
  recognizes all power/flak/radar ids used by both original and Metropolis Dawn
  data.
- Rules builder produces deterministic v2 JSON from the same `original-levels/`
  input.
- Known station-heavy levels include extracted infrastructure profiles:
  `L1515`, `L5252`, `L6363`, `L7979`, and `L7878`.
- Known low-variation terrain levels remain classified as flat or near-flat:
  examples include `L0303`, `L2525`, and `L2626`.
- Known varied terrain levels expose high range/feature targets:
  examples include `L5252`, `L6363`, `L6161`, `L5151`, and `L6262`.

### Generation Tests

- Fixed seeds produce identical single levels and campaigns.
- Different seeds change terrain or placement.
- Campaign generation succeeds for `original`, `md-ghorkov`, and
  `md-taerkasten`.
- For archetypes with source flak/radar infrastructure, generated output
  includes those categories under default settings when valid sectors exist.
- Generated campaigns no longer contain only power-station infrastructure.
- Non-flat archetypes generate at least 4 unique heights and multi-cell terrain
  features unless fallback warnings are emitted.
- Required route validation rejects a generated route crossing a height barrier
  greater than 4.
- Decorative cliffs outside required routes are accepted.
- All station cells have coherent `blg_map`, `typ_map`, and `own_map` values.
- Existing Generator1, Generator2, Generator3, and Generator4 tests remain
  passing.

### Acceptance

The v2 implementation is acceptable when:

- `Generator4().generate_campaign(seed=2026, campaign_profile=profile)` returns
  `GeneratedCampaign.ok == True` for all built-in profiles.
- Generated campaigns include authored-style power, flak, and radar layers
  where the matching original campaign slots support them.
- Non-flat source archetypes produce visibly varied, connected terrain rather
  than mostly flat maps with isolated raised dots.
- Player tech progression, enemy roster legality, gate targets, and startup
  includes remain consistent with current Generator4 behavior.

## Non-Goals

- Changing the public Generator4 API.
- New CLI or GUI controls for terrain/infrastructure tuning.
- Rebalancing vehicle, weapon, or building stat values.
- Random tileset substitution.
- Full mission scripting changes or new briefing/debriefing assets.
- Exact cloning of original station counts or height maps.
