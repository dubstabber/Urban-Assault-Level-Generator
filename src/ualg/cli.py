"""Command-line interface for the Urban Assault generators."""

from __future__ import annotations

import argparse
from pathlib import Path

from .constants import (
    GENERATOR1_CAMPAIGN_PROFILES,
    GENERATOR2_CAMPAIGN_PROFILES,
    GENERATOR3_CAMPAIGN_PROFILES,
    GENERATOR4_CAMPAIGN_PROFILES,
)
from .generator1 import Generator1
from .generator2 import Generator2
from .generator3 import Generator3
from .generator4 import Generator4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ualg", description="Urban Assault level generator")
    subparsers = parser.add_subparsers(dest="generator", required=True)

    gen1 = subparsers.add_parser("gen1", help="Random UA-derived Generator1")
    gen1_sub = gen1.add_subparsers(dest="mode", required=True)
    gen1_single = gen1_sub.add_parser("single", help="Generate one Generator1 level")
    gen1_single.add_argument("--seed", type=int, default=0)
    gen1_single.add_argument("--difficulty", type=int, default=5)
    gen1_single.add_argument("--skill", type=int, default=0)
    gen1_single.add_argument("--strict-parity", action="store_true", help="Disable improved tileset filtering")
    gen1_single.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen1_single.add_argument("--output", required=True)
    gen1_campaign = gen1_sub.add_parser("campaign", help="Generate the 44-level Generator1 campaign")
    gen1_campaign.add_argument("--seed", type=int, default=0)
    gen1_campaign.add_argument("--difficulty", type=int, default=5)
    gen1_campaign.add_argument("--strict-parity", action="store_true", help="Disable improved tileset filtering")
    gen1_campaign.add_argument(
        "--campaign-profile",
        choices=GENERATOR1_CAMPAIGN_PROFILES,
        default="original",
        help="Generator1 campaign roster/profile to generate",
    )
    gen1_campaign.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen1_campaign.add_argument("--output-dir", required=True)

    gen2 = subparsers.add_parser("gen2", help="PHP-derived Generator2")
    gen2_sub = gen2.add_subparsers(dest="mode", required=True)
    gen2_single = gen2_sub.add_parser("single", help="Generate one Generator2 level")
    gen2_single.add_argument("--seed", type=int, default=0)
    gen2_single.add_argument("--level-id", type=int, default=1)
    gen2_single.add_argument(
        "--zero-enemy-station-delays",
        action="store_true",
        help="Set all enemy host station *_delay values to 0",
    )
    gen2_single.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen2_single.add_argument("--output", required=True)
    gen2_campaign = gen2_sub.add_parser("campaign", help="Generate the 42-level Generator2 campaign")
    gen2_campaign.add_argument("--seed", type=int, default=0)
    gen2_campaign.add_argument(
        "--campaign-profile",
        choices=GENERATOR2_CAMPAIGN_PROFILES,
        default="original",
        help="Generator2 campaign roster/profile to generate",
    )
    gen2_campaign.add_argument(
        "--zero-enemy-station-delays",
        action="store_true",
        help="Set all enemy host station *_delay values to 0",
    )
    gen2_campaign.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen2_campaign.add_argument("--output-dir", required=True)

    gen3 = subparsers.add_parser("gen3", help="Corpus-driven authored-style Generator3 (Remix)")
    gen3_sub = gen3.add_subparsers(dest="mode", required=True)
    gen3_single = gen3_sub.add_parser("single", help="Remix one authored level")
    gen3_single.add_argument("--seed", type=int, default=0)
    gen3_single.add_argument(
        "--campaign-profile",
        choices=GENERATOR3_CAMPAIGN_PROFILES,
        default="original",
        help="Generator3 roster/profile to remix with",
    )
    gen3_single.add_argument(
        "--synthesis",
        action="store_true",
        help="Synthesize new WFC terrain instead of remixing an authored level",
    )
    gen3_single.add_argument("--skeleton", default=None, help="Remix: force a source level, e.g. L1515")
    gen3_single.add_argument("--level-id", type=int, default=None, help="Remix: use the original level with this id as skeleton")
    gen3_single.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen3_single.add_argument(
        "--zero-enemy-station-delays",
        action="store_true",
        help="Set all enemy host station *_delay values to 0",
    )
    gen3_single.add_argument("--output", required=True)
    gen3_campaign = gen3_sub.add_parser("campaign", help="Remix a full authored campaign")
    gen3_campaign.add_argument("--seed", type=int, default=0)
    gen3_campaign.add_argument(
        "--campaign-profile",
        choices=GENERATOR3_CAMPAIGN_PROFILES,
        default="original",
        help="Generator3 roster/profile to remix with",
    )
    gen3_campaign.add_argument(
        "--synthesis",
        action="store_true",
        help="Synthesize new WFC terrain instead of remixing authored levels",
    )
    gen3_campaign.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen3_campaign.add_argument(
        "--zero-enemy-station-delays",
        action="store_true",
        help="Set all enemy host station *_delay values to 0",
    )
    gen3_campaign.add_argument("--output-dir", required=True)

    gen4 = subparsers.add_parser("gen4", help="Campaign-aware hybrid synthesis Generator4")
    gen4_sub = gen4.add_subparsers(dest="mode", required=True)
    gen4_single = gen4_sub.add_parser("single", help="Generate one Generator4 campaign-aware level")
    gen4_single.add_argument("--seed", type=int, default=0)
    gen4_single.add_argument(
        "--campaign-profile",
        choices=GENERATOR4_CAMPAIGN_PROFILES,
        default="original",
        help="Generator4 campaign profile/archetype set",
    )
    gen4_single.add_argument("--level-id", type=int, default=None, help="Use this campaign slot as the archetype")
    gen4_single.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen4_single.add_argument(
        "--zero-enemy-station-delays",
        action="store_true",
        help="Set all enemy host station *_delay values to 0",
    )
    gen4_single.add_argument("--output", required=True)
    gen4_campaign = gen4_sub.add_parser("campaign", help="Generate a full Generator4 campaign")
    gen4_campaign.add_argument("--seed", type=int, default=0)
    gen4_campaign.add_argument(
        "--campaign-profile",
        choices=GENERATOR4_CAMPAIGN_PROFILES,
        default="original",
        help="Generator4 campaign profile/archetype set",
    )
    gen4_campaign.add_argument(
        "--zero-enemy-radar-budgets",
        action="store_true",
        help="Set all enemy host station rad_budget values to 0",
    )
    gen4_campaign.add_argument(
        "--zero-enemy-station-delays",
        action="store_true",
        help="Set all enemy host station *_delay values to 0",
    )
    gen4_campaign.add_argument("--output-dir", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.generator == "gen1":
        generator = Generator1()
        improved = not args.strict_parity
        if args.mode == "single":
            level = generator.generate_single(
                seed=args.seed,
                difficulty=args.difficulty,
                skill=args.skill,
                improved=improved,
                zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
            )
            path = level.write(args.output)
            print(f"Wrote {path}")
            return 0
        campaign = generator.generate_campaign(
            seed=args.seed,
            difficulty=args.difficulty,
            improved=improved,
            campaign_profile=args.campaign_profile,
            zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
        )
        written = campaign.write(args.output_dir)
        print(f"Wrote {len(written)} Generator1 levels to {Path(args.output_dir)}")
        return 0

    if args.generator == "gen2":
        generator = Generator2()
        if args.mode == "single":
            level = generator.generate_single(
                seed=args.seed,
                level_id=args.level_id,
                zero_enemy_station_delays=args.zero_enemy_station_delays,
                zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
            )
            path = level.write(args.output)
            print(f"Wrote {path}")
            return 0
        campaign = generator.generate_campaign(
            seed=args.seed,
            campaign_profile=args.campaign_profile,
            zero_enemy_station_delays=args.zero_enemy_station_delays,
            zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
        )
        written = campaign.write(args.output_dir)
        print(f"Wrote {len(written)} Generator2 levels to {Path(args.output_dir)}")
        return 0

    if args.generator == "gen3":
        generator = Generator3()
        gen3_mode = "synthesis" if args.synthesis else "remix"
        if args.mode == "single":
            level = generator.generate_single(
                seed=args.seed,
                campaign_profile=args.campaign_profile,
                mode=gen3_mode,
                skeleton=args.skeleton,
                level_id=args.level_id,
                zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
                zero_enemy_station_delays=args.zero_enemy_station_delays,
            )
            path = level.write(args.output)
            origin = level.metadata.get("skeleton") or f"synthesized/{level.metadata.get('synth_method')}"
            print(f"Wrote {path} ({gen3_mode}: {origin})")
            return 0
        campaign = generator.generate_campaign(
            seed=args.seed,
            campaign_profile=args.campaign_profile,
            mode=gen3_mode,
            zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
            zero_enemy_station_delays=args.zero_enemy_station_delays,
        )
        written = campaign.write(args.output_dir)
        print(f"Wrote {len(written)} Generator3 levels ({gen3_mode}) to {Path(args.output_dir)}")
        return 0

    generator = Generator4()
    if args.mode == "single":
        level = generator.generate_single(
            seed=args.seed,
            campaign_profile=args.campaign_profile,
            level_id=args.level_id,
            zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
            zero_enemy_station_delays=args.zero_enemy_station_delays,
        )
        path = level.write(args.output)
        print(f"Wrote {path} (gen4: {level.metadata.get('level_archetype')}/{level.metadata.get('synth_method')})")
        return 0
    campaign = generator.generate_campaign(
        seed=args.seed,
        campaign_profile=args.campaign_profile,
        zero_enemy_radar_budgets=args.zero_enemy_radar_budgets,
        zero_enemy_station_delays=args.zero_enemy_station_delays,
    )
    written = campaign.write(args.output_dir)
    print(f"Wrote {len(written)} Generator4 levels to {Path(args.output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
