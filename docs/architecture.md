# Backend Architecture

The public backend API is intentionally small:

- `ualg.generator1.Generator1`
- `ualg.generator2.Generator2`
- `GeneratedLevel` and `GeneratedCampaign`

CLI and GUI code should keep using those entrypoints. Generator internals are composed from explicit collaborators instead of inherited mixins.

## Generation Pipeline

Generator1 resolves a campaign profile, applies scenario/custom options, builds maps and placements, then serializes LDF text.

Generator2 resolves a campaign profile, chooses layout, places gates/stations/bombs/squads, builds maps, applies special map rules, then serializes LDF text.

The service classes are orchestration only. Profile lookup, scenario policy, placement, map construction, and rendering each live in focused classes under `ualg.gen1` or `ualg.gen2`.

## Campaign Profiles

Built-in campaign/profile definitions live in `src/ualg/data/campaign_profiles.json` and are loaded by `ualg.campaign_profiles.ProfileRegistry`.

A profile defines:

- supported generator namespace: `generator1` or `generator2`
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
```

This keeps new profile work out of generator orchestration.

