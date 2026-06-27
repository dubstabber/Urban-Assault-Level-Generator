"""Tkinter desktop GUI for the Urban Assault generators."""

from __future__ import annotations

import sys
from typing import Sequence

import tkinter as tk

from .gui_support.app import APP_TITLE, Generator1GUI
from .gui_support.backups import backup_campaign_ldfs, backup_existing_file
from .gui_support.custom_options import (
    BLACK_SECT_NEW_BUILDING_IDS,
    BUILDING_LABELS,
    CUSTOM_BUILD_FACTIONS,
    CUSTOM_WIZARD_FACTIONS,
    CUSTOM_WIZARD_PAGE_TITLES,
    GHORKOV_HOST_VEHICLE_ALIASES,
    GHORKOV_HOST_VEHICLES,
    NEW_BUILDING_IDS,
    RESISTANCE_NEW_BUILDING_IDS,
    VEHICLE_LABELS,
    CustomGenerationOptions,
    CustomWizardState,
    _active_custom_build_factions,
    _bool_slots,
    _building_options_for_faction,
    _collect_build_options_from_state,
    _default_faction_random_build_options,
    _default_host_energy_slots,
    _default_host_slots,
    _faction_label,
    _ghorkov_host_vehicle_id,
    _int_slots,
    _int_value,
    _leading_int,
    _legacy_energy_value,
    _option_label,
    _ordered_selected,
    _vehicle_options_for_faction,
    custom_wizard_options_from_state,
)
from .gui_support.custom_wizard import CustomLevelDialog, CustomWizardDialog
from .gui_support.legacy_dialogs import (
    DLU_X,
    DLU_Y,
    ENABLE_ALL_CONTROL_IDS,
    LEGACY_CAMPAIGN_DIALOG,
    LEGACY_CREDITS_DIALOG,
    LEGACY_FONT_FAMILY,
    LEGACY_FONT_SIZE,
    LEGACY_LICENSE_DIALOG,
    LEGACY_MAIN_DIALOG,
    LEGACY_SEED_DIALOG,
    LEGACY_SKILL_DIALOG,
    LEGACY_TUTORIAL_DIALOG,
    UNIT_ENABLE_MAP,
    UNIT_RANDOM_CONTROL_BY_FACTION,
    WIZARD_PAGE_IDS,
    BLACK_SECT_BUILDING_MAP,
    BLACK_SECT_NEW_BUILDING_MAP,
    BLACK_SECT_VEHICLE_MAP,
    RESISTANCE_NEW_BUILDING_MAP,
    RESISTANCE_VEHICLE_CONTROLS,
    LegacyDialogRenderer,
    LegacyModal,
    LegacyWizard,
    _checked,
    _control_map,
    _int_from_var,
    _legacy_energy,
    _unit_enable_values,
)
from .gui_support.settings import (
    DEFAULT_SETTINGS_FILE,
    FILE_SECTION,
    GENERATOR1_SECTION,
    GENERATOR2_SECTION,
    RLG_SECTION,
    UA_SECTION,
    GuiSettings,
    _get_option,
    _new_parser,
    _truthy,
    default_settings_path,
    load_settings,
    save_settings,
)

__all__ = [
    "APP_TITLE",
    "BLACK_SECT_BUILDING_MAP",
    "BLACK_SECT_NEW_BUILDING_IDS",
    "BLACK_SECT_NEW_BUILDING_MAP",
    "BLACK_SECT_VEHICLE_MAP",
    "BUILDING_LABELS",
    "CUSTOM_BUILD_FACTIONS",
    "CUSTOM_WIZARD_FACTIONS",
    "CUSTOM_WIZARD_PAGE_TITLES",
    "CustomGenerationOptions",
    "CustomLevelDialog",
    "CustomWizardDialog",
    "CustomWizardState",
    "DEFAULT_SETTINGS_FILE",
    "DLU_X",
    "DLU_Y",
    "ENABLE_ALL_CONTROL_IDS",
    "FILE_SECTION",
    "GENERATOR1_SECTION",
    "GENERATOR2_SECTION",
    "GHORKOV_HOST_VEHICLE_ALIASES",
    "GHORKOV_HOST_VEHICLES",
    "Generator1GUI",
    "GuiSettings",
    "LEGACY_CAMPAIGN_DIALOG",
    "LEGACY_CREDITS_DIALOG",
    "LEGACY_FONT_FAMILY",
    "LEGACY_FONT_SIZE",
    "LEGACY_LICENSE_DIALOG",
    "LEGACY_MAIN_DIALOG",
    "LEGACY_SEED_DIALOG",
    "LEGACY_SKILL_DIALOG",
    "LEGACY_TUTORIAL_DIALOG",
    "LegacyDialogRenderer",
    "LegacyModal",
    "LegacyWizard",
    "NEW_BUILDING_IDS",
    "RESISTANCE_NEW_BUILDING_IDS",
    "RESISTANCE_NEW_BUILDING_MAP",
    "RESISTANCE_VEHICLE_CONTROLS",
    "RLG_SECTION",
    "UA_SECTION",
    "UNIT_ENABLE_MAP",
    "UNIT_RANDOM_CONTROL_BY_FACTION",
    "VEHICLE_LABELS",
    "WIZARD_PAGE_IDS",
    "backup_campaign_ldfs",
    "backup_existing_file",
    "custom_wizard_options_from_state",
    "default_settings_path",
    "load_settings",
    "main",
    "save_settings",
]


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        raise SystemExit("ualg-gui does not accept command-line arguments")
    root = tk.Tk()
    Generator1GUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
