"""Settings persistence for the Tkinter GUI."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SETTINGS_FILE = "RandomUA.ini"
RLG_SECTION = "RLG Data"
FILE_SECTION = "FileLocations"
UA_SECTION = "UA Installed Folder"
GENERATOR2_SECTION = "Generator2"



@dataclass(slots=True)
class GuiSettings:
    random_level_file: str = ""
    custom_level_file: str = ""
    campaign_directory: str = ""
    exe_location: str = ""
    use_building_scripts: bool = True
    generator2_single_level_file: str = ""
    generator2_campaign_directory: str = ""



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
        generator2_single_level_file=_get_option(parser, GENERATOR2_SECTION, "SingleLevelFile"),
        generator2_campaign_directory=_get_option(parser, GENERATOR2_SECTION, "CampaignDirectory"),
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
    parser[GENERATOR2_SECTION] = {
        "SingleLevelFile": settings.generator2_single_level_file,
        "CampaignDirectory": settings.generator2_campaign_directory,
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
