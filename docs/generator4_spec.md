# Generator4 Specification: Campaign-Aware Hybrid Synthesis

This document specifies a fourth Urban Assault level generator. It is a design
specification for future implementation; the current codebase does not yet
provide `Generator4`.

Generator4 should synthesize new levels, but it must be constrained by the
rules and progression patterns inferred from the original vanilla and
Metropolis Dawn levels in `original-levels/`. It is intended to fill the gap
left by the existing generators:

- Generator1 and Generator2 generate broad random levels.
- Generator3 remixes original skeletons or synthesizes WFC terrain, but it
  still uses broad profile rosters and does not model campaign tech progression
  in a first-class way.
- Generator4 should generate new maps while preserving authored campaign
  progression: faction pools, per-level enables, upgrade sectors, stat
  upgrades, and terrain passability.

## Source Findings

The raw corpus contains 75 original LDF files:

| Corpus | Levels | Notes |
| --- | ---: | --- |
| Vanilla | 44 | Original Resistance campaign plus special/tutorial levels. |
| Metropolis Dawn | 31 | Ghorkov and Taerkasten campaigns. |

The important inferred rules are:

- `begin_enable` blocks in original levels are per-owner, per-level capability
  pools. They are not equivalent to "all units for the faction".
- Vanilla campaign levels usually do not emit a player `begin_enable` block.
  Player tech is mostly controlled by startup scripts, prototype modifications,
  and `begin_gem` upgrade sectors.
- Enemy factions vary by map. A generated level must choose enemies from the
  original level slot/archetype, not from every available faction.
- Upgrade sectors use `begin_gem` plus nested `begin_action` blocks. They can
  enable vehicles/buildings and can also modify vehicle or weapon stats.
- Adjacent `hgt_map` sectors with an absolute height difference greater than
  `4` are ground-movement barriers. Original levels use these barriers
  intentionally: roughly 7-8% of adjacent height edges in the corpus exceed
  this threshold, and several levels are split into multiple ground-passable
  components.
- Existing LDF safety limits still apply: at most 7 host stations, at most 100
  squads, at most 32 units per squad, intact energy-wall borders, valid world
  coordinates, and a Resistance/player host station appropriate to the profile.

## Public Interface

Generator4 should be exposed as a separate backend entrypoint, not as a
Generator3 mode.

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

Single-level behavior:

- `campaign_profile` accepts the same built-in profiles as Generator3:
  `original`, `md-ghorkov`, and `md-taerkasten`.
- If `level_id` is provided, Generator4 uses the matching campaign slot as the
  archetype.
- If `level_id` is omitted, Generator4 chooses a campaign slot from the selected
  profile with the seeded RNG.
- The output filename is the canonical level filename for the chosen slot, for
  example `L0202.ldf`.

Campaign behavior:

- Generate one level for every `level_id` in the selected campaign profile.
- Rewire gate targets from the profile graph, matching Generator3 campaign
  behavior.
- Use one RNG stream across the campaign so a campaign seed deterministically
  controls the whole set.

Metadata on every `GeneratedLevel` should include:

```python
{
    "generator": "generator4",
    "campaign_profile": profile_id,
    "source": "vanilla" | "metropolisDawn",
    "level_archetype": "L0202",
    "tech_phase": {
        "baseline_level_ids": [...],
        "new_unlocks": [...],
    },
    "warnings": [...],
}
```

Future CLI and GUI names:

- CLI namespace: `gen4`
- GUI tab label: `Generator4`

## Rules Dataset

Implement Generator4 from a baked rules dataset generated from
`original-levels/`, separate from `src/ualg/data/gen3_corpus.json`.

Suggested package data:

```text
src/ualg/data/gen4_rules.json
```

Suggested builder:

```text
tools/build_gen4_rules.py
```

The dataset should be deterministic and committed, so installed packages do not
need the raw `original-levels/` directory.

Top-level structure:

```json
{
  "version": 1,
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

Each level record must contain enough data to generate a new level without
looking at the original LDF again:

```json
{
  "level_id": 2,
  "name": "L0202",
  "source_name": "L0202",
  "tileset": 1,
  "width": 10,
  "height": 10,
  "header": {},
  "mission_targets": [3],
  "player_owner": 1,
  "present_owners": [1, 6],
  "enemy_owners": [6],
  "enemy_enables": {
    "6": {
      "vehicles": [24, 29],
      "buildings": []
    }
  },
  "player_baseline": {
    "include": "include data:scripts/startup2.scr",
    "prototype": []
  },
  "upgrade_gems": [],
  "placement_stats": {},
  "height_stats": {}
}
```

Required extraction details:

- Preserve raw prototype modification lines for re-emission, but also parse
  them into structured records for tests and future balancing.
- Preserve raw `begin_gem` blocks for authored action payloads, but also parse
  `sec_x`, `sec_y`, `building`, `type`, modified vehicle/weapon/building ids,
  and `enable` owners.
- Store initial enemy enables exactly as found in the source level.
- Store player unlocks and stat upgrades separately from enemy enables.
- Store height passability metrics:
  - blocked-edge ratio where `abs(hgt_a - hgt_b) > 4`;
  - connected component sizes using passable edges only;
  - host/squad/gate/component assignments;
  - maximum observed adjacent height delta.

The rules builder should use the existing `ualg.gen3.ldf_reader.parse_ldf`
reader where possible, extending it only if Generator4 needs additional
structured fields.

## Progression Rules

Generator4 must treat each generated level as a campaign slot, not just a map
shape.

### Player Tech

For a level slot, split tech into two parts:

- Baseline tech: all prototype modifications that should already be active
  before the level starts.
- New tech: upgrade sectors available inside the level.

The output should include:

- startup include selected by `startup_include_for_level(profile_id, level_id)`;
- baseline prototype modifications for the selected campaign phase;
- `begin_gem` blocks for the level's new unlocks/stat upgrades, remapped to the
  active player faction when needed.

Known first player unlocks that the dataset/tests must preserve:

| Profile | Level | Unlock |
| --- | --- | --- |
| `original` | L02 | Jaguar, vehicle `2` |
| `original` | L03 | Weasel, vehicle `1` |
| `original` | L04 | Wasp, vehicle `6` |
| `original` | L05 | Scout, vehicle `9` |
| `original` | L12 | Hornet, vehicle `15` |
| `original` | L20 | Tiger, vehicle `3` |
| `original` | L21 | Resistance Power Station 1, building `63` |
| `original` | L30 | Resistance Flak Station 1, building `28` |
| `original` | L31 | Firefly, vehicle `10` |
| `original` | L40 | Dragonfly, vehicle `14` |
| `original` | L41 | Power Station 1+, building `1`; Falcon, vehicle `4` |
| `original` | L42 | Marauder, vehicle `5` |
| `original` | L43 | Bronsteijn(Blue), vehicle `134` |
| `original` | L52 | Radar Station 1, building `3` |
| `original` | L53 | Warhammer, vehicle `7` |
| `original` | L54 | Rhino, vehicle `12` |
| `original` | L62 | Radar Station 2, building `54`; Rock Sled, vehicle `11` |
| `original` | L63 | Flak Station 2, building `2`; Power Station 2, building `11` |
| `original` | L70 | Power Station 2+, building `64` |
| `md-ghorkov` | L07 | Ghor-Scout, vehicle `29` |
| `md-ghorkov` | L14 | Ghargoil 2, vehicle `28` |
| `md-ghorkov` | L17 | Speedy, vehicle `22` |
| `md-ghorkov` | L19 | Ghorkov Power Station 1, building `52` |
| `md-ghorkov` | L28 | Tekh-Trak, vehicle `26` |
| `md-ghorkov` | L35 | Ying, vehicle `23` |
| `md-ghorkov` | L37 | Ghargoil 3, vehicle `25` |
| `md-ghorkov` | L39 | Ghorkov Power Station 2, building `12` |
| `md-ghorkov` | L46 | Yang, vehicle `130` |
| `md-ghorkov` | L48 | Ghorkov Flak Station, building `30` |
| `md-ghorkov` | L56 | Gigant, vehicle `27` |
| `md-ghorkov` | L58 | Tien-Ying 7, vehicle `31` |
| `md-ghorkov` | L67 | Ghorkov Radar Station, building `71` |
| `md-taerkasten` | L06 | Ormu-Scout, vehicle `35` |
| `md-taerkasten` | L08 | Hetzel, vehicle `33` |
| `md-taerkasten` | L13 | Mnosjetz, vehicle `38` |
| `md-taerkasten` | L16 | Leonid, vehicle `37` |
| `md-taerkasten` | L18 | Ostwind, vehicle `144` |
| `md-taerkasten` | L29 | Taerkasten Power Station 1, building `53` |
| `md-taerkasten` | L36 | Taerkasten Flak Station, building `74` |
| `md-taerkasten` | L38 | Zeppelin, vehicle `131` |
| `md-taerkasten` | L45 | Taerkasten Radar Station, building `73` |
| `md-taerkasten` | L47 | Serp, vehicle `36` |
| `md-taerkasten` | L55 | Taerkasten Power Station 2, building `17`; Thor's Hammer, vehicle `143` |
| `md-taerkasten` | L65 | Bronsteijn, vehicle `34` |
| `md-taerkasten` | L68 | Phantom, vehicle `8` |

Do not generate broad player `begin_enable` blocks for normal campaign levels
unless the source archetype explicitly contains one.

### Enemy Factions And Rosters

Enemy factions and buildable units must come from the source level slot.

Examples of early/mid/late enemy pools:

| Profile | Level | Enemy pool shape |
| --- | --- | --- |
| `original` | L98/L01 | Ghorkov only, usually `24` initially. |
| `original` | L05 | Ghorkov plus Taerkasten present. |
| `original` | L15 | Broad finale pool: Sulgogar, Mykonian, Taerkasten, Black Sect, Ghorkov. |
| `md-ghorkov` | L07 | Resistance only, limited to early units. |
| `md-ghorkov` | L79 | Resistance, Mykonian, Taerkasten, Black Sect with broad late rosters. |
| `md-taerkasten` | L06 | Resistance only, limited early roster. |
| `md-taerkasten` | L78 | Resistance, Sulgogar, Mykonian, Black Sect, Ghorkov. |

When a synthesized level remaps factions, it may only map to factions allowed by
the selected campaign profile and source level slot. A faction's emitted
`begin_enable` vehicles/buildings must be a subset of that source slot's
enable block after applying known exclusion rules already shared by Generator2
and Generator3.

## Generation Pipeline

### 1. Resolve Profile And Archetype

- Normalize `campaign_profile`.
- Resolve `level_id`, either provided or selected by RNG from the profile.
- Load the matching `gen4_rules.json` level record.
- Resolve player faction, target levels, mission maps, startup include, and
  source corpus.

### 2. Choose Terrain Frame

- Use the archetype tileset by default. Do not randomly switch tilesets because
  sector/building compatibility is fragile.
- Use the archetype size exactly for v1. Later versions may vary size within
  learned profile bands, but exact size keeps passability, density, and mission
  pacing easier to validate.
- Generate `typ_map` with the existing Generator3 WFC adjacency model for the
  archetype source and tileset.
- Preserve the standard energy-wall border tiles.

### 3. Generate Height And Passability

Generate `hgt_map` as a graph problem:

- Treat every sector as a node and four-neighbor adjacency as an edge.
- Edges with `abs(hgt_a - hgt_b) <= 4` are passable to ground units.
- Edges with `abs(hgt_a - hgt_b) > 4` are cliffs/barriers.
- Match the archetype's blocked-edge ratio approximately, with a tolerance of
  `+/- 35%` relative for v1.
- Ensure the required gameplay graph is connected:
  - player host station;
  - required enemy host stations that should be reachable by ground units;
  - beam gate;
  - gate key sectors;
  - bomb/key sectors if present;
  - required player tech gems.
- Optional isolated components are allowed only when they mirror the archetype's
  component structure and do not trap required ground gameplay objects.

If the generated map fails passability validation after a bounded retry count,
fallback to a flatter height map near the archetype median height and keep only
decorative cliff bands outside required routes.

### 4. Ownership And Buildings

- Place player and enemy host sectors first, on valid passable components.
- Build `own_map` from seeded regions grown from host sectors, while preserving
  neutral owner `0` and tutorial/power-station owner `7` semantics.
- Power stations that are predeployed but intended to be conquerable should use
  owner `7`; flak/radar buildings should be owned by their faction.
- Build `blg_map` from placed functional buildings, gates, bombs, and upgrade
  sectors.
- Keep building ids compatible with the selected profile/source data.

### 5. Host Stations And Squads

- Emit one player host station using the profile's player faction and
  player-robo override rules.
- Emit enemy host stations using the archetype's enemy factions and host-count
  distribution.
- Preserve enemy budget/delay style from the archetype distribution. Apply
  `zero_enemy_radar_budgets` and `zero_enemy_station_delays` after budget
  generation.
- Place squads from the source slot's enabled rosters. Do not pick vehicles not
  enabled for that level/faction.
- Ground squads should be placed on passable components where their intended
  owner can act. Flying squads may be placed more freely, but still inside map
  bounds and away from energy-wall borders.

### 6. Gates, Items, And Upgrade Sectors

- Emit at least one beam gate for campaign levels and write profile target
  levels.
- Place gate key sectors on reachable sectors unless the archetype has no keys.
- Re-emit authored-style `begin_gem` actions for player unlock/stat upgrades,
  but synthesize new sector positions.
- For each upgrade gem:
  - write its `building` into `blg_map`;
  - set a compatible `typ_map` value if required by the building id;
  - keep `mb_status = unknown` when the source gem had it;
  - remap `enable = <source player owner>` to the active profile player faction.

### 7. Render And Validate

- Render in the same LDF style as Generator3 unless a stronger local convention
  emerges during implementation.
- Return `GeneratedLevel` with maps and metadata.
- Run Generator4 validation and include warnings in metadata.

## Validation Rules

Generator4 validation should extend `ualg.gen3.validate` rather than replacing
it.

Required checks:

- `typ_map`, `own_map`, `hgt_map`, and `blg_map` dimensions match.
- Energy-wall border and corners are intact.
- Host stations are present and count is `<= 7`.
- Squad count is `<= 100`; squad `num` is `<= 32`.
- Host/squad coordinates are in bounds and not on the energy-wall border.
- Every emitted `begin_enable` is legal for the selected level slot.
- Every generated squad vehicle is available to its owner in that level slot.
- Required ground-route sectors are connected by edges with height delta `<= 4`.
- No required route crosses a height barrier greater than `4`.
- Functional buildings have compatible ownership:
  - power stations intended as neutral/conquerable use owner `7`;
  - flak/radar buildings use a participating faction owner.
- Upgrade gem building ids are reflected in `blg_map`.
- Generated prototype and gem action blocks are balanced and closed.

Warnings should be non-fatal for decorative issues. Illegal rosters,
out-of-bounds entities, broken maps, or disconnected required gameplay routes
should fail generation and trigger retry/fallback.

## Tests And Acceptance Criteria

Add unit tests in a future implementation for these scenarios:

- Rules builder parses all 75 original levels and produces deterministic
  `gen4_rules.json`.
- Known first unlocks listed above are extracted exactly.
- Enemy enables for generated levels are subsets of the matching source slot.
- Fixed seeds produce identical single levels and campaigns.
- Different seeds change synthesized terrain or placements.
- Campaign generation succeeds for `original`, `md-ghorkov`, and
  `md-taerkasten`.
- Generated maps round-trip through `ualg.ldf.parse_maps`.
- Passability validator rejects a required route containing any adjacent height
  delta greater than `4`.
- Passability validator accepts intentional cliffs outside required routes.
- Zero-budget options affect only enemy host station budgets/delays.
- Generated campaign levels have no validation warnings under default settings.

Initial implementation is acceptable when:

- `Generator4().generate_campaign(seed=2026, campaign_profile=profile)` returns
  `GeneratedCampaign.ok == True` for all built-in profiles.
- No generated squad uses a vehicle outside its level/faction enable pool.
- Required player progression upgrades are present at the expected campaign
  levels.
- Required ground gameplay routes obey the delta-4 height rule.
- Existing Generator1, Generator2, and Generator3 tests remain unchanged and
  passing.

## Non-Goals For V1

- Full campaign state persistence between generated levels.
- New mission briefing or debriefing image generation.
- Multiplayer/LAN/Internet-specific output.
- Arbitrary custom profile authoring UI.
- Rebalancing vehicle or weapon stat values beyond faithfully carrying inferred
  original prototype and gem modifications.
- Random tileset substitution across incompatible sector sets.

