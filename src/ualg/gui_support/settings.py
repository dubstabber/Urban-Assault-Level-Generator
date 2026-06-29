"""Settings persistence for the Tkinter GUI."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SETTINGS_FILE = "RandomUA.ini"
RLG_SECTION = "RLG Data"
FILE_SECTION = "FileLocations"
UA_SECTION = "UA Installed Folder"
GENERATOR1_SECTION = "Generator1"
GENERATOR2_SECTION = "Generator2"
GENERATOR3_SECTION = "Generator3"
GENERATOR4_SECTION = "Generator4"



@dataclass(slots=True)
class GuiSettings:
    random_level_file: str = ""
    custom_level_file: str = ""
    campaign_directory: str = ""
    exe_location: str = ""
    use_building_scripts: bool = True
    generator2_single_level_file: str = ""
    generator2_campaign_directory: str = ""
    generator2_zero_enemy_station_delays: bool = False
    generator1_zero_enemy_radar_budgets: bool = False
    generator2_zero_enemy_radar_budgets: bool = False
    generator3_single_level_file: str = ""
    generator3_campaign_directory: str = ""
    generator3_zero_enemy_station_delays: bool = False
    generator3_zero_enemy_radar_budgets: bool = False
    generator4_single_level_file: str = ""
    generator4_campaign_directory: str = ""
    generator4_difficulty_mode: str = "normal"
    generator4_zero_enemy_station_delays: bool = False
    generator4_zero_enemy_radar_budgets: bool = False



def default_settings_path() -> Path:
    return Path.cwd() / DEFAULT_SETTINGS_FILE


def load_settings(path: str | Path | None = None) -> GuiSettings:
    settings_path = Path(path) if path is not None else default_settings_path()
    if not settings_path.exists():
        return GuiSettings()

    parser = _new_parser()
    parser.read(settings_path, encoding="utf-8")
    return GuiSettings(
        random_level_file=_get_option(parser, FILE_SECTION, "RandomLevelFile"),
        custom_level_file=_get_option(parser, FILE_SECTION, "CustomLevelFile"),
        campaign_directory=_get_option(parser, UA_SECTION, "CampaignDirectory"),
        exe_location=_get_option(parser, UA_SECTION, "EXELocation"),
        use_building_scripts=_truthy(_get_option(parser, RLG_SECTION, "Data3-DO NOT CHANGE", default="1")),
        generator1_zero_enemy_radar_budgets=_truthy(
            _get_option(parser, GENERATOR1_SECTION, "ZeroEnemyRadarBudgets", default="0")
        ),
        generator2_single_level_file=_get_option(parser, GENERATOR2_SECTION, "SingleLevelFile"),
        generator2_campaign_directory=_get_option(parser, GENERATOR2_SECTION, "CampaignDirectory"),
        generator2_zero_enemy_station_delays=_truthy(
            _get_option(parser, GENERATOR2_SECTION, "ZeroEnemyStationDelays", default="0")
        ),
        generator2_zero_enemy_radar_budgets=_truthy(
            _get_option(parser, GENERATOR2_SECTION, "ZeroEnemyRadarBudgets", default="0")
        ),
        generator3_single_level_file=_get_option(parser, GENERATOR3_SECTION, "SingleLevelFile"),
        generator3_campaign_directory=_get_option(parser, GENERATOR3_SECTION, "CampaignDirectory"),
        generator3_zero_enemy_station_delays=_truthy(
            _get_option(parser, GENERATOR3_SECTION, "ZeroEnemyStationDelays", default="0")
        ),
        generator3_zero_enemy_radar_budgets=_truthy(
            _get_option(parser, GENERATOR3_SECTION, "ZeroEnemyRadarBudgets", default="0")
        ),
        generator4_single_level_file=_get_option(parser, GENERATOR4_SECTION, "SingleLevelFile"),
        generator4_campaign_directory=_get_option(parser, GENERATOR4_SECTION, "CampaignDirectory"),
        generator4_difficulty_mode=_get_option(parser, GENERATOR4_SECTION, "DifficultyMode", default="normal"),
        generator4_zero_enemy_station_delays=_truthy(
            _get_option(parser, GENERATOR4_SECTION, "ZeroEnemyStationDelays", default="0")
        ),
        generator4_zero_enemy_radar_budgets=_truthy(
            _get_option(parser, GENERATOR4_SECTION, "ZeroEnemyRadarBudgets", default="0")
        ),
    )


def save_settings(settings: GuiSettings, path: str | Path | None = None) -> Path:
    settings_path = Path(path) if path is not None else default_settings_path()
    parser = _new_parser()
    parser[RLG_SECTION] = {
        "Data-DO NOT CHANGE": "1",
        "Data3-DO NOT CHANGE": "1" if settings.use_building_scripts else "0",
        "Data2-DO NOT CHANGE": "0",
    }
    parser[FILE_SECTION] = {
        "RandomLevelFile": settings.random_level_file,
        "CustomLevelFile": settings.custom_level_file,
    }
    parser[UA_SECTION] = {
        "CampaignDirectory": settings.campaign_directory,
        "EXELocation": settings.exe_location,
    }
    parser[GENERATOR1_SECTION] = {
        "ZeroEnemyRadarBudgets": "1" if settings.generator1_zero_enemy_radar_budgets else "0",
    }
    parser[GENERATOR2_SECTION] = {
        "SingleLevelFile": settings.generator2_single_level_file,
        "CampaignDirectory": settings.generator2_campaign_directory,
        "ZeroEnemyStationDelays": "1" if settings.generator2_zero_enemy_station_delays else "0",
        "ZeroEnemyRadarBudgets": "1" if settings.generator2_zero_enemy_radar_budgets else "0",
    }
    parser[GENERATOR3_SECTION] = {
        "SingleLevelFile": settings.generator3_single_level_file,
        "CampaignDirectory": settings.generator3_campaign_directory,
        "ZeroEnemyStationDelays": "1" if settings.generator3_zero_enemy_station_delays else "0",
        "ZeroEnemyRadarBudgets": "1" if settings.generator3_zero_enemy_radar_budgets else "0",
    }
    parser[GENERATOR4_SECTION] = {
        "SingleLevelFile": settings.generator4_single_level_file,
        "CampaignDirectory": settings.generator4_campaign_directory,
        "DifficultyMode": settings.generator4_difficulty_mode,
        "ZeroEnemyStationDelays": "1" if settings.generator4_zero_enemy_station_delays else "0",
        "ZeroEnemyRadarBudgets": "1" if settings.generator4_zero_enemy_radar_budgets else "0",
    }
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w", encoding="utf-8", newline="") as handle:
        parser.write(handle, space_around_delimiters=False)
    return settings_path


def _new_parser() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    return parser


def _get_option(
    parser: configparser.ConfigParser,
    section: str,
    option: str,
    default: str = "",
) -> str:
    if not parser.has_section(section):
        return default
    values = parser[section]
    if option in values:
        return values.get(option, default)
    lowered = option.lower()
    for key in values:
        if key.lower() == lowered:
            return values.get(key, default)
    return default


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
