"""Command-line interface for the Urban Assault generators."""

from __future__ import annotations

import argparse
from pathlib import Path

from .constants import GENERATOR1_CAMPAIGN_PROFILES
from .generator1 import Generator1
from .generator2 import Generator2


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
    gen1_campaign.add_argument("--output-dir", required=True)

    gen2 = subparsers.add_parser("gen2", help="PHP-derived Generator2")
    gen2_sub = gen2.add_subparsers(dest="mode", required=True)
    gen2_single = gen2_sub.add_parser("single", help="Generate one Generator2 level")
    gen2_single.add_argument("--seed", type=int, default=0)
    gen2_single.add_argument("--level-id", type=int, default=1)
    gen2_single.add_argument("--output", required=True)
    gen2_campaign = gen2_sub.add_parser("campaign", help="Generate the 42-level Generator2 campaign")
    gen2_campaign.add_argument("--seed", type=int, default=0)
    gen2_campaign.add_argument("--output-dir", required=True)

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
            )
            path = level.write(args.output)
            print(f"Wrote {path}")
            return 0
        campaign = generator.generate_campaign(
            seed=args.seed,
            difficulty=args.difficulty,
            improved=improved,
            campaign_profile=args.campaign_profile,
        )
        written = campaign.write(args.output_dir)
        print(f"Wrote {len(written)} Generator1 levels to {Path(args.output_dir)}")
        return 0

    generator = Generator2()
    if args.mode == "single":
        level = generator.generate_single(seed=args.seed, level_id=args.level_id)
        path = level.write(args.output)
        print(f"Wrote {path}")
        return 0
    campaign = generator.generate_campaign(seed=args.seed)
    written = campaign.write(args.output_dir)
    print(f"Wrote {len(written)} Generator2 levels to {Path(args.output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
