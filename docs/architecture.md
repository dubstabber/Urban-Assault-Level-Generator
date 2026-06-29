# Backend Architecture

The public backend API is intentionally small:

- `ualg.generator1.Generator1`
- `ualg.generator2.Generator2`
- `ualg.generator3.Generator3`
- `ualg.generator4.Generator4`
- `GeneratedLevel` and `GeneratedCampaign`

CLI and GUI code should keep using those entrypoints. Generator internals are composed from explicit collaborators instead of inherited mixins.

## Generation Pipeline

Generator1 resolves a campaign profile, applies scenario/custom options, builds maps and placements, then serializes LDF text.

Generator2 resolves a campaign profile, chooses layout, places gates/stations/bombs/squads, builds maps, applies special map rules, then serializes LDF text.

Generator3 has two modes. **Remix** resolves a campaign profile, selects a skeleton from the baked original-level corpus, copies its terrain maps, relabels ownership/buildings through a seeded faction remap, swaps host/squad identities and rosters while preserving authored balance numbers, then serializes LDF text. **Synthesis** learns 4-neighbour tile adjacency from the corpus (per source + tileset) and collapses a fresh `typ_map` via Wave Function Collapse (`synthesis.py`), then builds ownership (Voronoi from host positions), height, buildings and entities (`synth_builder.py`) before serializing with the same renderer. Its modules live under `ualg.gen3` (`ldf_reader`, `corpus`, `corpus_builder`, `profiles`, `placement`, `remix`, `synthesis`, `synth_builder`, `renderer`, `validate`, `service`). The skeleton corpus (`src/ualg/data/gen3_corpus.json`) is committed package data derived from the original levels, so Generator3 works without the gitignored `original-levels/` tree. `tools/build_gen3_corpus.py` refreshes it, and `corpus.py` can still auto-build it on demand via `corpus_builder.build_corpus()` in a source checkout if the baked file is missing.

Generator4 resolves a campaign slot from a baked rules dataset (`src/ualg/data/gen4_rules.json`), keeps the archetype tileset and dimensions, synthesizes new WFC `typ_map` terrain, and rebuilds ownership, height, buildings, hosts, squads, gates, items, and upgrade sectors while constraining enemy rosters and tech progression to the source slot. Its modules live under `ualg.gen4`; `tools/build_gen4_rules.py` refreshes the baked rules from `original-levels/`.

The service classes are orchestration only. Profile lookup, scenario policy, placement, map construction, and rendering each live in focused classes under `ualg.gen1`, `ualg.gen2`, `ualg.gen3`, or `ualg.gen4`.

## Campaign Profiles

Built-in campaign/profile definitions live in `src/ualg/data/campaign_profiles.json` and are loaded by `ualg.campaign_profiles.ProfileRegistry`.

A profile defines:

- supported generator namespace: `generator1`, `generator2`, `generator3`, or `generator4`
- level IDs or level filenames
- target graph or `target_mode: "next"`
- player faction
- roster source or explicit rosters
- mission map policy
- optional per-level player robo overrides

`constants.py` still exposes legacy constant names for compatibility, but those values are derived from the registry where practical.

## Adding A Profile

Add a new entry under the relevant generator in `campaign_profiles.json`. Prefer `roster_profile` when using an existing `UAdata.json` roster; use explicit rosters only when a generator needs custom string-keyed faction data.

For tests or external experiments, construct `ProfileRegistry.from_mapping(...)` and inject it with:

```python
Generator1(profile_registry=registry)
Generator2(profile_registry=registry)
Generator4(profile_registry=registry)
```

This keeps new profile work out of generator orchestration.
