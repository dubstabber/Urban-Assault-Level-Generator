"""Tkinter desktop GUI for the Urban Assault generators."""

from __future__ import annotations

import configparser
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence

import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox, simpledialog, ttk

from .constants import (
    FACTION_BLACK_SECT,
    FACTION_GHORKOVS,
    FACTION_MYKONIANS,
    FACTION_PLAYER,
    FACTION_SULGOGARS,
    FACTION_TAERKASTEN,
    FACTION_TUTOR,
    GENERATOR1_CAMPAIGN_FILENAMES,
    GENERATOR2_LEVELS,
    BUILDINGS_BY_FACTION,
    VEHICLES_BY_FACTION,
    level_id_from_filename,
    level_filename,
)
from .generator1 import Generator1, Generator1CustomOptions
from .generator2 import Generator2
from .legacy_resources import LegacyControl, LegacyDialog


APP_TITLE = "Urban Assault Level Generator"
DEFAULT_SETTINGS_FILE = "RandomUA.ini"
RLG_SECTION = "RLG Data"
FILE_SECTION = "FileLocations"
UA_SECTION = "UA Installed Folder"
GENERATOR2_SECTION = "Generator2"
DLU_X = 1.5
DLU_Y = 1.72
LEGACY_FONT_FAMILY = "MS Sans Serif"
LEGACY_FONT_SIZE = 8
LEGACY_MAIN_DIALOG = 141
LEGACY_LICENSE_DIALOG = 131
LEGACY_CREDITS_DIALOG = 134
LEGACY_TUTORIAL_DIALOG = 140
LEGACY_SKILL_DIALOG = 129
LEGACY_SEED_DIALOG = 138
LEGACY_CAMPAIGN_DIALOG = 130
WIZARD_PAGE_IDS = [137, 139, 135, 136, 142]
CUSTOM_WIZARD_FACTIONS = [
    FACTION_GHORKOVS,
    FACTION_TAERKASTEN,
    FACTION_MYKONIANS,
    FACTION_SULGOGARS,
    FACTION_BLACK_SECT,
    FACTION_TUTOR,
]
CUSTOM_BUILD_FACTIONS = [FACTION_PLAYER, *CUSTOM_WIZARD_FACTIONS]
CUSTOM_WIZARD_PAGE_TITLES = [
    "Level Size",
    "Host Stations",
    "Beam Gate",
    "Stoudson Bombs",
    "Build Options",
]
GHORKOV_HOST_VEHICLES = {"Tarantul 1": 59, "Tarantul 2": 57}
RESISTANCE_NEW_BUILDING_IDS = tuple(range(38, 50)) + tuple(range(90, 94))
BLACK_SECT_NEW_BUILDING_IDS = tuple(range(38, 50)) + tuple(range(90, 97))
NEW_BUILDING_IDS = set(BLACK_SECT_NEW_BUILDING_IDS)

VEHICLE_LABELS = {
    1: "Weasel",
    2: "Jaguar",
    3: "Tiger",
    4: "Falcon",
    5: "Warhammer",
    6: "Wasp",
    7: "Mosquito",
    8: "Hetzel",
    9: "Dragonfly",
    10: "Firefly",
    11: "Rock-Sled",
    12: "Rhino",
    14: "Eagle",
    15: "Hornet",
    16: "Fox",
    22: "Bronsteijn",
    23: "Ghorkov Host",
    24: "Giant",
    25: "Shark",
    26: "Tekh-Trak",
    27: "Rokh",
    28: "Gorokhov",
    29: "Ghargoil",
    30: "Ghok",
    31: "Minenleger",
    32: "Pamir",
    33: "Eisenhans",
    34: "Flammenwerfer",
    35: "Leopard",
    36: "Tiger II",
    37: "Marder",
    38: "Jaguar II",
    57: "Tarantul 2",
    59: "Tarantul 1",
    63: "Myko 1",
    64: "Myko 2",
    65: "Myko 3",
    66: "Myko 4",
    67: "Myko 5",
    68: "Myko 6",
    69: "Myko 7",
    70: "Myko 8",
    71: "Sulgogar 2",
    72: "Sulgogar 3",
    73: "Sulgogar 1",
    74: "Sulgogar 4",
    130: "Ghorkov Special",
    131: "Taerkast Special",
    133: "Resistance Special 1",
    134: "Resistance Special 2",
    142: "Tutorial Drone",
}

BUILDING_LABELS = {
    1: "Resistance Power",
    2: "Resistance Radar",
    3: "Resistance Flak",
    10: "Mykonian Power",
    11: "Resistance Station",
    12: "Ghorkov Power",
    13: "Mykonian Flak",
    17: "Taerkast Power",
    18: "Black Sect Flak",
    28: "Resistance Beam",
    30: "Ghorkov Flak",
    31: "Taerkast Flak",
    38: "New Building 38",
    39: "New Building 39",
    40: "New Building 40",
    41: "New Building 41",
    42: "New Building 42",
    43: "New Building 43",
    44: "New Building 44",
    45: "New Building 45",
    46: "New Building 46",
    47: "New Building 47",
    48: "New Building 48",
    49: "New Building 49",
    52: "Ghorkov Station",
    53: "Taerkast Station",
    54: "Resistance Defense",
    63: "Resistance Base",
    64: "Resistance Power 2",
    71: "Black Sect Station",
    72: "Mykonian Station",
    73: "Taerkast Station 2",
    90: "New Building 90",
    91: "New Building 91",
    92: "New Building 92",
    93: "New Building 93",
    94: "New Building 94",
    95: "New Building 95",
    96: "New Building 96",
}


@dataclass(slots=True)
class GuiSettings:
    random_level_file: str = ""
    custom_level_file: str = ""
    campaign_directory: str = ""
    exe_location: str = ""
    use_building_scripts: bool = True
    generator2_single_level_file: str = ""
    generator2_campaign_directory: str = ""


@dataclass(slots=True)
class CustomGenerationOptions:
    seed: int = 0
    difficulty: int = 5
    skill: int = 0
    improved: bool = True


def _default_host_slots(value: bool = False) -> dict[int, list[bool]]:
    return {faction: [value, value, value] for faction in CUSTOM_WIZARD_FACTIONS}


def _default_host_energy_slots() -> dict[int, list[int]]:
    return {faction: [1500, 1500, 1500] for faction in CUSTOM_WIZARD_FACTIONS}


def _default_faction_random_build_options() -> dict[int, bool]:
    return {faction: True for faction in CUSTOM_BUILD_FACTIONS}


@dataclass(slots=True)
class CustomWizardState:
    random_size: bool = True
    width: int = 20
    height: int = 20
    player_energy: int = 1500
    host_present: dict[int, list[bool]] = field(default_factory=_default_host_slots)
    host_energy: dict[int, list[int]] = field(default_factory=_default_host_energy_slots)
    ghorkov_host_types: list[str] = field(default_factory=lambda: ["Tarantul 1", "Tarantul 1", "Tarantul 1"])
    gate_target_level_id: int = 0
    random_gate_keys: bool = True
    gate_key_count: int = 0
    win_movie: bool = False
    lose_movie: bool = False
    random_bombs: bool = True
    bomb_included: list[bool] = field(default_factory=lambda: [False, False])
    bomb_custom_countdown: list[bool] = field(default_factory=lambda: [False, False])
    bomb_countdown_seconds: list[int] = field(default_factory=lambda: [600, 1200])
    random_build_options: bool = True
    faction_random_build_options: dict[int, bool] = field(default_factory=_default_faction_random_build_options)
    enabled_vehicles: dict[int, set[int]] = field(default_factory=dict)
    enabled_buildings: dict[int, set[int]] = field(default_factory=dict)


def custom_wizard_options_from_state(
    state: CustomWizardState,
    *,
    allow_new_buildings: bool = True,
) -> Generator1CustomOptions:
    options = Generator1CustomOptions()

    if not state.random_size:
        width = _int_value(state.width, "horizontal level size")
        height = _int_value(state.height, "vertical level size")
        if not 4 <= width <= 43:
            raise ValueError("Horizontal level size must be between 4 and 43.")
        if not 4 <= height <= 30:
            raise ValueError("Vertical level size must be between 4 and 30.")
        options.width = width + 2
        options.height = height + 2

    options.player_energy = _legacy_energy_value(state.player_energy, "player host station energy")

    any_host = False
    for faction in CUSTOM_WIZARD_FACTIONS:
        present = _bool_slots(state.host_present.get(faction, []))
        if not any(present):
            continue
        any_host = True
        options.ai_slot_present[faction] = present
        energies = _int_slots(state.host_energy.get(faction, []), 1500)
        options.ai_slot_energy[faction] = [
            _legacy_energy_value(energies[slot], f"{_faction_label(faction)} host #{slot + 1} energy")
            if present[slot]
            else 0
            for slot in range(3)
        ]
        if faction == FACTION_GHORKOVS:
            host_types = (state.ghorkov_host_types + ["Tarantul 1", "Tarantul 1", "Tarantul 1"])[:3]
            vehicles = []
            for slot, host_type in enumerate(host_types):
                if present[slot] and host_type not in GHORKOV_HOST_VEHICLES:
                    raise ValueError(f"Ghorkov host #{slot + 1} must use a valid Tarantul host type.")
                vehicles.append(GHORKOV_HOST_VEHICLES.get(host_type, 0) if present[slot] else 0)
            options.ai_slot_host_vehicle_id[faction] = vehicles

    if not any_host:
        raise ValueError("You must have at least 1 enemy host station.")

    options.gate_target_level_id = max(0, _int_value(state.gate_target_level_id, "beam gate target level"))
    options.win_movie = bool(state.win_movie)
    options.lose_movie = bool(state.lose_movie)
    if not state.random_gate_keys:
        gate_key_count = _int_value(state.gate_key_count, "beam gate key sector count")
        if not 0 <= gate_key_count <= 16:
            raise ValueError("Beam gate key sector count must be between 0 and 16.")
        options.gate_key_count = gate_key_count

    if state.random_bombs:
        options.random_superitems = True
    else:
        bomb_flags = _bool_slots(state.bomb_included, count=2)
        if bomb_flags[1] and not bomb_flags[0]:
            raise ValueError("Bomb 2 requires Bomb 1.")
        options.superitem_flags = bomb_flags
        countdowns = _int_slots(state.bomb_countdown_seconds, 600, count=2)
        custom_countdowns = _bool_slots(state.bomb_custom_countdown, count=2)
        for index, enabled in enumerate(bomb_flags, start=1):
            if not enabled or not custom_countdowns[index - 1]:
                continue
            seconds = countdowns[index - 1]
            if not 1 <= seconds <= 3601:
                raise ValueError("Bomb countdowns must be between 1 and 3601 seconds.")
            options.superitem_countdowns[index] = seconds * 1000

    _collect_build_options_from_state(state, options, allow_new_buildings=allow_new_buildings)
    return options


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


def backup_existing_file(path: str | Path, timestamp: str | None = None) -> Path | None:
    source = Path(path)
    if not source.is_file():
        return None
    stamp = timestamp or _timestamp()
    target = _unique_path(source.with_name(f"{source.name}.bak_{stamp}"))
    shutil.copy2(source, target)
    return target


def backup_campaign_ldfs(directory: str | Path, timestamp: str | None = None) -> tuple[Path | None, list[Path]]:
    source_dir = Path(directory)
    if not source_dir.is_dir():
        return None, []

    ldf_files = sorted(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() == ".ldf")
    if not ldf_files:
        return None, []

    stamp = timestamp or _timestamp()
    backup_dir = _unique_path(source_dir / f"Backup_{stamp}")
    backup_dir.mkdir(parents=True, exist_ok=False)
    moved: list[Path] = []
    for source in ldf_files:
        target = backup_dir / source.name
        shutil.move(str(source), str(target))
        moved.append(target)
    return backup_dir, moved


class CustomLevelDialog(simpledialog.Dialog):
    def __init__(self, parent: tk.Misc, title: str = "Custom Random Level Generator Wizard") -> None:
        self.seed_var: tk.StringVar
        self.difficulty_var: tk.StringVar
        self.skill_var: tk.StringVar
        self.strict_var: tk.BooleanVar
        self.result: CustomGenerationOptions | None = None
        super().__init__(parent, title)

    def body(self, master: tk.Frame) -> tk.Widget:
        self.seed_var = tk.StringVar(value="")
        self.difficulty_var = tk.StringVar(value="5")
        self.skill_var = tk.StringVar(value="0")
        self.strict_var = tk.BooleanVar(value=False)

        tk.Label(master, text="Seed (blank for random):", anchor="w").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        seed_entry = tk.Entry(master, textvariable=self.seed_var, width=18)
        seed_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        tk.Label(master, text="Difficulty (1-10):", anchor="w").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        tk.Spinbox(master, from_=1, to=10, textvariable=self.difficulty_var, width=6).grid(
            row=1, column=1, sticky="w", padx=4, pady=4
        )

        tk.Label(master, text="Skill preset (0=random, 1-11):", anchor="w").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        tk.Spinbox(master, from_=0, to=11, textvariable=self.skill_var, width=6).grid(
            row=2, column=1, sticky="w", padx=4, pady=4
        )

        tk.Checkbutton(master, text="Strict original tileset parity", variable=self.strict_var).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=4, pady=6
        )

        master.columnconfigure(1, weight=1)
        return seed_entry

    def validate(self) -> bool:
        try:
            seed_text = self.seed_var.get().strip()
            seed = int(seed_text) if seed_text else 0
            difficulty = int(self.difficulty_var.get())
            skill = int(self.skill_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Options", "Seed, difficulty, and skill must be whole numbers.", parent=self)
            return False
        if not 1 <= difficulty <= 10:
            messagebox.showwarning("Invalid Options", "Difficulty must be between 1 and 10.", parent=self)
            return False
        if not 0 <= skill <= 11:
            messagebox.showwarning("Invalid Options", "Skill must be 0 or between 1 and 11.", parent=self)
            return False
        self.result = CustomGenerationOptions(
            seed=seed,
            difficulty=difficulty,
            skill=skill,
            improved=not self.strict_var.get(),
        )
        return True


class LegacyDialogRenderer:
    def __init__(
        self,
        parent: tk.Misc,
        dialog: LegacyDialog,
        *,
        command_map: dict[int, object] | None = None,
        entry_vars: dict[int, tk.StringVar] | None = None,
        check_vars: dict[int, tk.BooleanVar] | None = None,
        combo_values: dict[int, list[str]] | None = None,
        disabled_ids: set[int] | None = None,
    ) -> None:
        self.dialog = dialog
        self.command_map = command_map or {}
        self.entry_vars = entry_vars or {}
        self.check_vars = check_vars or {}
        self.combo_vars: dict[int, tk.StringVar] = {}
        self.widgets: dict[int, list[tk.Widget]] = {}
        self.combo_values = combo_values or {}
        self.disabled_ids = disabled_ids or set()
        self.font = tkfont.Font(root=parent, family=LEGACY_FONT_FAMILY, size=LEGACY_FONT_SIZE)
        self.frame = tk.Frame(parent, width=self.px(dialog.width), height=self.py(dialog.height))
        self.frame.pack_propagate(False)
        self._build()

    @staticmethod
    def px(value: int) -> int:
        return max(1, int(round(value * DLU_X)))

    @staticmethod
    def py(value: int) -> int:
        return max(1, int(round(value * DLU_Y)))

    def _build(self) -> None:
        for control in self.dialog.controls:
            if control.is_groupbox:
                self._place_control(control)
        for control in self.dialog.controls:
            if not control.is_groupbox:
                self._place_control(control)

    def _place_control(self, control: LegacyControl) -> None:
        x, y = self.px(control.x), self.py(control.y)
        width, height = self.px(control.width), self.py(control.height)
        widget = self._make_widget(control, width, height)
        if widget is None:
            return
        widget.place(x=x, y=y, width=width, height=height)
        self.widgets.setdefault(control.control_id, []).append(widget)

    def _make_widget(self, control: LegacyControl, width: int, height: int) -> tk.Widget | None:
        state = "disabled" if control.control_id in self.disabled_ids else "normal"
        text = control.text or ""
        if control.is_groupbox:
            return tk.LabelFrame(self.frame, text=text, font=self.font)
        if control.class_name == "STATIC":
            if text.startswith("#"):
                return tk.Label(self.frame, text="", relief="sunken", borderwidth=1)
            return tk.Label(
                self.frame,
                text=text,
                anchor="nw",
                justify="left",
                wraplength=max(20, width - 2),
                font=self.font,
                padx=0,
                pady=0,
            )
        if control.class_name == "EDIT":
            variable = self.entry_vars.setdefault(control.control_id, tk.StringVar())
            readonly = bool(control.style & 0x0800)
            if control.style & 0x0004:
                container = tk.Frame(self.frame, borderwidth=1, relief="sunken")
                text_widget = tk.Text(container, wrap="word", borderwidth=0, highlightthickness=0, font=self.font)
                scrollbar = tk.Scrollbar(container, orient="vertical", command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side="right", fill="y")
                text_widget.pack(side="left", fill="both", expand=True)
                text_widget.insert("1.0", variable.get())
                if state == "disabled" or readonly:
                    text_widget.configure(state="disabled")
                return container
            entry_state = "readonly" if readonly and state != "disabled" else state
            return tk.Entry(self.frame, textvariable=variable, state=entry_state, font=self.font)
        if control.class_name == "COMBOBOX":
            variable = self.entry_vars.setdefault(control.control_id, tk.StringVar())
            self.combo_vars[control.control_id] = variable
            values = self.combo_values.get(control.control_id, [])
            combo = ttk.Combobox(
                self.frame,
                textvariable=variable,
                values=values,
                state="readonly" if values else state,
                font=self.font,
            )
            if values and not variable.get():
                combo.current(0)
            return combo
        if control.class_name == "LISTBOX":
            return tk.Listbox(self.frame, font=self.font)
        if control.class_name and "progress" in control.class_name.lower():
            return ttk.Progressbar(self.frame, maximum=44)
        if control.class_name == "BUTTON":
            if control.is_checkbox:
                variable = self.check_vars.setdefault(control.control_id, tk.BooleanVar(value=False))
                return tk.Checkbutton(
                    self.frame,
                    text=text,
                    variable=variable,
                    anchor="w",
                    state=state,
                    font=self.font,
                    padx=0,
                    pady=0,
                    borderwidth=0,
                    highlightthickness=0,
                )
            command = self.command_map.get(control.control_id)
            if command is None:
                command = lambda: None
            return tk.Button(self.frame, text=text, command=command, state=state, font=self.font, padx=0, pady=0)
        return tk.Label(self.frame, text=text, font=self.font, padx=0, pady=0)


class LegacyModal:
    def __init__(
        self,
        parent: tk.Tk,
        dialog: LegacyDialog,
        *,
        combo_values: dict[int, list[str]] | None = None,
        entry_defaults: dict[int, str] | None = None,
        check_defaults: dict[int, bool] | None = None,
        disabled_ids: set[int] | None = None,
    ) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title(dialog.title)
        self.window.resizable(False, False)
        self.accepted = False
        self.entry_vars = {control_id: tk.StringVar(value=value) for control_id, value in (entry_defaults or {}).items()}
        self.check_vars = {control_id: tk.BooleanVar(value=value) for control_id, value in (check_defaults or {}).items()}
        command_map = {
            1: self.accept,
            1094: self.accept,
            1161: self.accept,
            1169: self.accept,
            1162: self.cancel,
            1170: self.cancel,
            2: self.cancel,
            1167: self.cancel,
            1166: self.accept,
            1173: self.accept,
        }
        self.renderer = LegacyDialogRenderer(
            self.window,
            dialog,
            command_map=command_map,
            entry_vars=self.entry_vars,
            check_vars=self.check_vars,
            combo_values=combo_values,
            disabled_ids=disabled_ids,
        )
        self.renderer.frame.pack(padx=6, pady=6)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

    def run(self) -> bool:
        self.window.grab_set()
        self.window.wait_window()
        return self.accepted

    def accept(self) -> None:
        self.accepted = True
        self.window.destroy()

    def cancel(self) -> None:
        self.accepted = False
        self.window.destroy()


class LegacyWizard:
    def __init__(self, parent: tk.Tk, dialogs: dict[int, LegacyDialog], *, allow_new_buildings: bool = True) -> None:
        self.parent = parent
        self.dialogs = dialogs
        self.allow_new_buildings = allow_new_buildings
        self.window = tk.Toplevel(parent)
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self.index = 0
        self.result: Generator1CustomOptions | None = None
        self.page_renderers: dict[int, LegacyDialogRenderer] = {}
        self.unit_renderers: dict[int, LegacyDialogRenderer] = {}
        self.page_frame = tk.Frame(self.window)
        self.page_frame.pack(padx=6, pady=6)
        self.show_page(0)

    def run(self) -> Generator1CustomOptions | None:
        self.window.grab_set()
        self.window.wait_window()
        return self.result

    def show_page(self, index: int) -> None:
        self.index = max(0, min(index, len(WIZARD_PAGE_IDS) - 1))
        dialog_id = WIZARD_PAGE_IDS[self.index]
        dialog = self.dialogs[dialog_id]
        self.window.title(dialog.title)
        for child in self.page_frame.winfo_children():
            child.destroy()
        command_map = self._page_command_map(dialog_id)
        renderer = LegacyDialogRenderer(
            self.page_frame,
            dialog,
            command_map=command_map,
            combo_values=self._combo_values(dialog_id),
            entry_vars=self._entry_defaults(dialog_id),
            check_vars=self._check_defaults(dialog_id),
        )
        self.page_renderers[dialog_id] = renderer
        renderer.frame.pack()

    def _page_command_map(self, dialog_id: int) -> dict[int, object]:
        commands: dict[int, object] = {
            1006: self.next_page,
            1020: self.next_page,
            1015: self.previous_page,
            1009: self.previous_page,
            1016: self.finish,
            1021: self.finish,
            1010: self.finish,
            1000: self.cancel,
            1025: self.cancel,
            1011: self.show_test_note,
        }
        if dialog_id == 142:
            commands.update({
                1035: lambda: self.open_unit_dialog(143),
                1036: lambda: self.open_unit_dialog(144),
                1037: lambda: self.open_unit_dialog(145),
                1038: lambda: self.open_unit_dialog(146),
                1039: lambda: self.open_unit_dialog(148),
                1040: lambda: self.open_unit_dialog(147),
                1046: lambda: self.open_unit_dialog(150),
            })
        return commands

    def _combo_values(self, dialog_id: int) -> dict[int, list[str]]:
        if dialog_id == 135:
            choices = ["0 ; No Target"]
            seen: set[int] = {0}
            for filename in GENERATOR1_CAMPAIGN_FILENAMES:
                level_id = level_id_from_filename(filename)
                if level_id not in seen:
                    seen.add(level_id)
                    choices.append(f"{level_id} ; {filename}")
            return {1017: choices}
        if dialog_id == 139:
            return {1003: ["Tarantul 1", "Tarantul 2"], 1004: ["Tarantul 1", "Tarantul 2"], 1005: ["Tarantul 1", "Tarantul 2"]}
        return {}

    def _entry_defaults(self, dialog_id: int) -> dict[int, tk.StringVar]:
        existing = self.page_renderers.get(dialog_id)
        if existing:
            return existing.entry_vars
        defaults: dict[int, str] = {}
        if dialog_id == 137:
            defaults = {1007: "20", 1008: "20"}
        elif dialog_id == 139:
            defaults = {1049: "1500"}
        elif dialog_id == 135:
            defaults = {1007: ""}
        elif dialog_id == 136:
            defaults = {1018: "600", 1022: "1200"}
        return {control_id: tk.StringVar(value=value) for control_id, value in defaults.items()}

    def _check_defaults(self, dialog_id: int) -> dict[int, tk.BooleanVar]:
        existing = self.page_renderers.get(dialog_id)
        if existing:
            return existing.check_vars
        defaults = {1009: True} if dialog_id == 137 else {}
        return {control_id: tk.BooleanVar(value=value) for control_id, value in defaults.items()}

    def next_page(self) -> None:
        self.show_page(self.index + 1)

    def previous_page(self) -> None:
        self.show_page(self.index - 1)

    def cancel(self) -> None:
        self.result = None
        self.window.destroy()

    def finish(self) -> None:
        try:
            self.result = self.collect_options()
        except ValueError as exc:
            messagebox.showerror("Insufficient/Incorrect Data", str(exc), parent=self.window)
            return
        self.window.destroy()

    def show_test_note(self) -> None:
        messagebox.showinfo("Test", "The Python reimplementation validates options when you click Finish.", parent=self.window)

    def open_unit_dialog(self, dialog_id: int) -> None:
        if dialog_id not in self.dialogs:
            return
        modal = tk.Toplevel(self.window)
        modal.title(self.dialogs[dialog_id].title)
        modal.resizable(False, False)
        entry_vars: dict[int, tk.StringVar] = {}
        check_vars: dict[int, tk.BooleanVar] = {}
        existing = self.unit_renderers.get(dialog_id)
        if existing:
            check_vars = existing.check_vars
        renderer = LegacyDialogRenderer(
            modal,
            self.dialogs[dialog_id],
            command_map={1094: modal.destroy, 1: modal.destroy, 1118: lambda: self.open_unit_dialog(149)},
            entry_vars=entry_vars,
            check_vars=check_vars,
        )
        self.unit_renderers[dialog_id] = renderer
        renderer.frame.pack(padx=6, pady=6)
        modal.grab_set()
        modal.wait_window()

    def collect_options(self) -> Generator1CustomOptions:
        options = Generator1CustomOptions()
        self._collect_size(options)
        self._collect_hosts(options)
        self._collect_gate(options)
        self._collect_bombs(options)
        self._collect_unit_enables(options)
        return options

    def _collect_size(self, options: Generator1CustomOptions) -> None:
        page = self.page_renderers.get(137)
        if not page or page.check_vars.get(1009, tk.BooleanVar(value=True)).get():
            return
        width = _int_from_var(page.entry_vars.get(1007), "horizontal level size")
        height = _int_from_var(page.entry_vars.get(1008), "vertical level size")
        if not 4 <= width <= 45 or not 3 <= height <= 32:
            raise ValueError("Level size must be within the legacy generator limits.")
        options.width = width
        options.height = height

    def _collect_hosts(self, options: Generator1CustomOptions) -> None:
        page = self.page_renderers.get(139)
        if not page:
            return
        slot_map = {
            FACTION_GHORKOVS: ([1018, 1019, 1020], [1012, 1013, 1014], [1003, 1004, 1005]),
            FACTION_TAERKASTEN: ([1021, 1022, 1023], [1015, 1016, 1024], []),
            FACTION_MYKONIANS: ([1025, 1026, 1027], [1028, 1029, 1030], []),
            FACTION_SULGOGARS: ([1031, 1032, 1033], [1034, 1035, 1036], []),
            FACTION_BLACK_SECT: ([1037, 1038, 1039], [1040, 1041, 1042], []),
            FACTION_TUTOR: ([1043, 1044, 1045], [1046, 1047, 1048], []),
        }
        for faction, (checks, energies, combos) in slot_map.items():
            present = [page.check_vars.get(control_id, tk.BooleanVar(value=False)).get() for control_id in checks]
            if any(present):
                options.ai_slot_present[faction] = present
                options.ai_slot_energy[faction] = [
                    _legacy_energy(page.entry_vars.get(control_id)) if present[index] else 0
                    for index, control_id in enumerate(energies)
                ]
            if faction == FACTION_GHORKOVS:
                for index, combo_id in enumerate(combos):
                    combo_value = page.entry_vars.get(combo_id)
                    if present[index] and combo_value and combo_value.get() == "Tarantul 2":
                        options.ai_host_vehicle_id[FACTION_GHORKOVS] = 59
                    elif present[index]:
                        options.ai_host_vehicle_id.setdefault(FACTION_GHORKOVS, 57)
        player_energy = _legacy_energy(page.entry_vars.get(1049))
        if player_energy:
            options.player_energy = player_energy
        if not any(any(slots) for slots in options.ai_slot_present.values()):
            raise ValueError("You must have at least 1 enemy host station.")

    def _collect_gate(self, options: Generator1CustomOptions) -> None:
        page = self.page_renderers.get(135)
        if not page:
            return
        target_var = page.entry_vars.get(1017)
        if target_var:
            options.gate_target_level_id = _leading_int(target_var.get())
        options.win_movie = page.check_vars.get(1024, tk.BooleanVar(value=False)).get()
        options.lose_movie = page.check_vars.get(1018, tk.BooleanVar(value=False)).get()
        random_keys = page.check_vars.get(1005, tk.BooleanVar(value=True)).get()
        if not random_keys:
            key_text = page.entry_vars.get(1007).get().strip() if page.entry_vars.get(1007) else ""
            if key_text:
                options.gate_key_count = max(0, min(16, int(key_text)))

    def _collect_bombs(self, options: Generator1CustomOptions) -> None:
        page = self.page_renderers.get(136)
        if not page:
            return
        random_bombs = page.check_vars.get(1017, tk.BooleanVar(value=False)).get()
        if random_bombs:
            return
        flags = [
            page.check_vars.get(1023, tk.BooleanVar(value=False)).get(),
            page.check_vars.get(1026, tk.BooleanVar(value=False)).get(),
        ]
        options.superitem_flags = flags
        for index, (custom_id, entry_id) in enumerate(((1027, 1018), (1028, 1022)), start=1):
            if flags[index - 1] and page.check_vars.get(custom_id, tk.BooleanVar(value=False)).get():
                seconds = _int_from_var(page.entry_vars.get(entry_id), f"bomb #{index} countdown")
                if not 1 <= seconds <= 3601:
                    raise ValueError("Bomb countdowns must be between 1 and 3601 seconds.")
                options.superitem_countdowns[index] = seconds * 1000

    def _collect_unit_enables(self, options: Generator1CustomOptions) -> None:
        page = self.page_renderers.get(142)
        if page and _checked(page.check_vars, 1017):
            return
        for dialog_id, renderer in self.unit_renderers.items():
            vehicles, buildings, faction = _unit_enable_values(dialog_id, renderer.check_vars)
            if page and _checked(page.check_vars, UNIT_RANDOM_CONTROL_BY_FACTION.get(faction, -1)):
                continue
            if not self.allow_new_buildings:
                buildings = [building for building in buildings if building not in NEW_BUILDING_IDS]
            if vehicles:
                options.enabled_vehicles[faction] = vehicles
            if buildings:
                options.enabled_buildings[faction] = buildings


class CustomWizardDialog:
    def __init__(self, parent: tk.Misc, *, allow_new_buildings: bool = True) -> None:
        self.parent = parent
        self.allow_new_buildings = allow_new_buildings
        self.result: Generator1CustomOptions | None = None
        self.page_index = 0

        self.window = tk.Toplevel(parent)
        self.window.title("Custom Random Level Generator Wizard")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

        self._init_variables()

        outer = tk.Frame(self.window, padx=10, pady=8)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)

        self.title_var = tk.StringVar()
        tk.Label(outer, textvariable=self.title_var, anchor="w", font=("TkDefaultFont", 10, "bold")).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        self.page_frame = tk.Frame(outer)
        self.page_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 8))

        nav = tk.Frame(outer)
        nav.grid(row=2, column=0, sticky="ew")
        nav.columnconfigure(0, weight=1)
        self.cancel_button = tk.Button(nav, text="Cancel", command=self.cancel, width=12)
        self.cancel_button.grid(row=0, column=0, sticky="w")
        self.back_button = tk.Button(nav, text="< Back", command=self.previous_page, width=10)
        self.back_button.grid(row=0, column=1, padx=(0, 6))
        self.next_button = tk.Button(nav, text="Next >", command=self.next_page, width=10)
        self.next_button.grid(row=0, column=2, padx=(0, 6))
        self.finish_button = tk.Button(nav, text="Finish", command=self.finish, width=10)
        self.finish_button.grid(row=0, column=3)

        self.show_page(0)

    def _init_variables(self) -> None:
        self.random_size_var = tk.BooleanVar(value=True)
        self.width_var = tk.StringVar(value="20")
        self.height_var = tk.StringVar(value="20")

        self.player_energy_var = tk.StringVar(value="1500")
        self.host_vars = {
            faction: [tk.BooleanVar(value=False) for _ in range(3)]
            for faction in CUSTOM_WIZARD_FACTIONS
        }
        self.host_energy_vars = {
            faction: [tk.StringVar(value="1500") for _ in range(3)]
            for faction in CUSTOM_WIZARD_FACTIONS
        }
        self.ghorkov_type_vars = [tk.StringVar(value="Tarantul 1") for _ in range(3)]

        self.gate_target_var = tk.StringVar(value="0 ; No Target")
        self.random_gate_keys_var = tk.BooleanVar(value=True)
        self.gate_key_count_var = tk.StringVar(value="0")
        self.win_movie_var = tk.BooleanVar(value=False)
        self.lose_movie_var = tk.BooleanVar(value=False)

        self.random_bombs_var = tk.BooleanVar(value=True)
        self.bomb_include_vars = [tk.BooleanVar(value=False), tk.BooleanVar(value=False)]
        self.bomb_custom_vars = [tk.BooleanVar(value=False), tk.BooleanVar(value=False)]
        self.bomb_countdown_vars = [tk.StringVar(value="600"), tk.StringVar(value="1200")]

        self.random_build_options_var = tk.BooleanVar(value=True)
        self.faction_random_build_vars = {
            faction: tk.BooleanVar(value=True)
            for faction in CUSTOM_BUILD_FACTIONS
        }
        self.vehicle_vars = {
            faction: {vehicle: tk.BooleanVar(value=False) for vehicle in _vehicle_options_for_faction(faction)}
            for faction in CUSTOM_BUILD_FACTIONS
        }
        self.building_vars = {
            faction: {
                building: tk.BooleanVar(value=False)
                for building in _building_options_for_faction(faction, allow_new_buildings=True)
            }
            for faction in CUSTOM_BUILD_FACTIONS
        }

        self.size_widgets: list[tk.Widget] = []
        self.host_energy_entries: dict[tuple[int, int], tk.Widget] = {}
        self.ghorkov_type_combos: dict[int, tk.Widget] = {}
        self.gate_key_widgets: list[tk.Widget] = []
        self.bomb_widgets: list[tuple[int, tk.Widget, str]] = []
        self.build_option_widgets: list[tuple[int, tk.Widget]] = []
        self.faction_random_widgets: dict[int, tk.Widget] = {}

    def run(self) -> Generator1CustomOptions | None:
        self.window.grab_set()
        self.window.wait_window()
        return self.result

    def show_page(self, index: int) -> None:
        self.page_index = max(0, min(index, len(CUSTOM_WIZARD_PAGE_TITLES) - 1))
        self.title_var.set(CUSTOM_WIZARD_PAGE_TITLES[self.page_index])
        for child in self.page_frame.winfo_children():
            child.destroy()
        builders = [
            self._build_size_page,
            self._build_hosts_page,
            self._build_gate_page,
            self._build_bombs_page,
            self._build_build_options_page,
        ]
        builders[self.page_index](self.page_frame)
        self._update_nav()

    def next_page(self) -> None:
        if self._validate_current_page():
            self.show_page(self.page_index + 1)

    def previous_page(self) -> None:
        self.show_page(self.page_index - 1)

    def finish(self) -> None:
        try:
            self.result = custom_wizard_options_from_state(
                self._state_from_vars(),
                allow_new_buildings=self.allow_new_buildings,
            )
        except ValueError as exc:
            messagebox.showerror("Insufficient/Incorrect Data", str(exc), parent=self.window)
            return
        self.window.destroy()

    def cancel(self) -> None:
        self.result = None
        self.window.destroy()

    def _update_nav(self) -> None:
        last_page = self.page_index == len(CUSTOM_WIZARD_PAGE_TITLES) - 1
        self.back_button.configure(state="disabled" if self.page_index == 0 else "normal")
        self.next_button.configure(state="disabled" if last_page else "normal")
        self.finish_button.configure(state="normal" if last_page else "disabled")

    def _validate_current_page(self) -> bool:
        try:
            if self.page_index == 0:
                self._validate_size_page()
            elif self.page_index >= 1:
                custom_wizard_options_from_state(
                    self._state_from_vars(),
                    allow_new_buildings=self.allow_new_buildings,
                )
        except ValueError as exc:
            messagebox.showerror("Insufficient/Incorrect Data", str(exc), parent=self.window)
            return False
        return True

    def _validate_size_page(self) -> None:
        if self.random_size_var.get():
            return
        width = _int_value(self.width_var.get(), "horizontal level size")
        height = _int_value(self.height_var.get(), "vertical level size")
        if not 4 <= width <= 43:
            raise ValueError("Horizontal level size must be between 4 and 43.")
        if not 4 <= height <= 30:
            raise ValueError("Vertical level size must be between 4 and 30.")

    def _build_size_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        tk.Checkbutton(
            parent,
            text="Random level size",
            variable=self.random_size_var,
            command=self._refresh_size_controls,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(parent, text="Horizontal sectors:", anchor="w").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        width_spin = tk.Spinbox(parent, from_=4, to=43, textvariable=self.width_var, width=8)
        width_spin.grid(row=1, column=1, sticky="w", pady=3)
        tk.Label(parent, text="Vertical sectors:", anchor="w").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
        height_spin = tk.Spinbox(parent, from_=4, to=30, textvariable=self.height_var, width=8)
        height_spin.grid(row=2, column=1, sticky="w", pady=3)
        self.size_widgets = [width_spin, height_spin]
        self._refresh_size_controls()

    def _refresh_size_controls(self) -> None:
        state = "disabled" if self.random_size_var.get() else "normal"
        for widget in self.size_widgets:
            widget.configure(state=state)

    def _build_hosts_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        top = tk.Frame(parent)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(top, text="Player host station energy:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 8))
        tk.Entry(top, textvariable=self.player_energy_var, width=10).grid(row=0, column=1, sticky="w")

        grid = tk.Frame(parent)
        grid.grid(row=1, column=0, sticky="nsew")
        self.host_energy_entries = {}
        self.ghorkov_type_combos = {}
        for index, faction in enumerate(CUSTOM_WIZARD_FACTIONS):
            box = tk.LabelFrame(grid, text=_faction_label(faction), padx=6, pady=5)
            box.grid(row=index // 2, column=index % 2, sticky="nsew", padx=4, pady=4)
            for slot in range(3):
                tk.Checkbutton(
                    box,
                    text=f"Host {slot + 1}",
                    variable=self.host_vars[faction][slot],
                    command=self._refresh_host_controls,
                    anchor="w",
                ).grid(row=slot, column=0, sticky="w", padx=(0, 6), pady=2)
                entry = tk.Entry(box, textvariable=self.host_energy_vars[faction][slot], width=9)
                entry.grid(row=slot, column=1, sticky="w", pady=2)
                self.host_energy_entries[(faction, slot)] = entry
                if faction == FACTION_GHORKOVS:
                    combo = ttk.Combobox(
                        box,
                        textvariable=self.ghorkov_type_vars[slot],
                        values=list(GHORKOV_HOST_VEHICLES),
                        state="readonly",
                        width=12,
                    )
                    combo.grid(row=slot, column=2, sticky="w", padx=(6, 0), pady=2)
                    self.ghorkov_type_combos[slot] = combo
        self._refresh_host_controls()

    def _refresh_host_controls(self) -> None:
        for (faction, slot), entry in self.host_energy_entries.items():
            entry.configure(state="normal" if self.host_vars[faction][slot].get() else "disabled")
        for slot, combo in self.ghorkov_type_combos.items():
            combo.configure(state="readonly" if self.host_vars[FACTION_GHORKOVS][slot].get() else "disabled")

    def _build_gate_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        tk.Label(parent, text="Target level:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        target_combo = ttk.Combobox(
            parent,
            textvariable=self.gate_target_var,
            values=self._gate_target_choices(),
            state="readonly",
            width=24,
        )
        target_combo.grid(row=0, column=1, sticky="w", pady=4)
        tk.Checkbutton(
            parent,
            text="Random key sectors",
            variable=self.random_gate_keys_var,
            command=self._refresh_gate_controls,
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 2))
        tk.Label(parent, text="Key sectors:", anchor="w").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        key_spin = tk.Spinbox(parent, from_=0, to=16, textvariable=self.gate_key_count_var, width=8)
        key_spin.grid(row=2, column=1, sticky="w", pady=4)
        self.gate_key_widgets = [key_spin]
        tk.Checkbutton(parent, text="Play losing movie", variable=self.lose_movie_var, anchor="w").grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 2),
        )
        tk.Checkbutton(parent, text="Play winning movie", variable=self.win_movie_var, anchor="w").grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=2,
        )
        self._refresh_gate_controls()

    def _gate_target_choices(self) -> list[str]:
        choices = ["0 ; No Target"]
        seen = {0}
        for filename in GENERATOR1_CAMPAIGN_FILENAMES:
            level_id = level_id_from_filename(filename)
            if level_id not in seen:
                seen.add(level_id)
                choices.append(f"{level_id} ; {filename}")
        return choices

    def _refresh_gate_controls(self) -> None:
        state = "disabled" if self.random_gate_keys_var.get() else "normal"
        for widget in self.gate_key_widgets:
            widget.configure(state=state)

    def _build_bombs_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        tk.Checkbutton(
            parent,
            text="Random number of bombs and countdowns",
            variable=self.random_bombs_var,
            command=self._refresh_bomb_controls,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.bomb_widgets = []
        for index in range(2):
            box = tk.LabelFrame(parent, text=f"Bomb {index + 1}", padx=6, pady=5)
            box.grid(row=index + 1, column=0, sticky="ew", pady=4)
            include = tk.Checkbutton(
                box,
                text="Include",
                variable=self.bomb_include_vars[index],
                command=self._refresh_bomb_controls,
                anchor="w",
            )
            include.grid(row=0, column=0, sticky="w", padx=(0, 8))
            custom = tk.Checkbutton(
                box,
                text="Custom countdown",
                variable=self.bomb_custom_vars[index],
                command=self._refresh_bomb_controls,
                anchor="w",
            )
            custom.grid(row=0, column=1, sticky="w", padx=(0, 8))
            spin = tk.Spinbox(box, from_=1, to=3601, textvariable=self.bomb_countdown_vars[index], width=8)
            spin.grid(row=0, column=2, sticky="w")
            tk.Label(box, text="seconds").grid(row=0, column=3, sticky="w", padx=(4, 0))
            self.bomb_widgets.extend([(index, include, "include"), (index, custom, "custom"), (index, spin, "countdown")])
        self._refresh_bomb_controls()

    def _refresh_bomb_controls(self) -> None:
        random_bombs = self.random_bombs_var.get()
        for index, widget, kind in self.bomb_widgets:
            if random_bombs:
                widget.configure(state="disabled")
                continue
            if index == 1 and not self.bomb_include_vars[0].get():
                widget.configure(state="disabled")
                continue
            if kind == "include":
                widget.configure(state="normal")
            elif kind == "custom":
                widget.configure(state="normal" if self.bomb_include_vars[index].get() else "disabled")
            else:
                enabled = self.bomb_include_vars[index].get() and self.bomb_custom_vars[index].get()
                widget.configure(state="normal" if enabled else "disabled")

    def _build_build_options_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        tk.Checkbutton(
            parent,
            text="Choose everything randomly",
            variable=self.random_build_options_var,
            command=self._refresh_build_controls,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        notebook = ttk.Notebook(parent)
        notebook.grid(row=1, column=0, sticky="nsew")
        self.build_option_widgets = []
        self.faction_random_widgets = {}
        for faction in self._active_build_factions_from_vars():
            tab = tk.Frame(notebook, padx=6, pady=6)
            notebook.add(tab, text=_faction_label(faction))
            random_check = tk.Checkbutton(
                tab,
                text=f"Random {_faction_label(faction)} build options",
                variable=self.faction_random_build_vars[faction],
                command=self._refresh_build_controls,
                anchor="w",
            )
            random_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
            self.faction_random_widgets[faction] = random_check
            vehicles = _vehicle_options_for_faction(faction)
            buildings = _building_options_for_faction(
                faction,
                allow_new_buildings=self.allow_new_buildings,
            )
            vehicle_box = tk.LabelFrame(tab, text="Vehicles", padx=5, pady=5)
            vehicle_box.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
            building_box = tk.LabelFrame(tab, text="Buildings", padx=5, pady=5)
            building_box.grid(row=1, column=1, sticky="nsew")
            self._check_grid(vehicle_box, faction, "vehicle", vehicles, self.vehicle_vars[faction])
            self._check_grid(building_box, faction, "building", buildings, self.building_vars[faction])
        self._refresh_build_controls()

    def _check_grid(
        self,
        parent: tk.Frame,
        faction: int,
        kind: str,
        values: Sequence[int],
        variables: dict[int, tk.BooleanVar],
    ) -> None:
        if not values:
            tk.Label(parent, text="None", anchor="w").grid(row=0, column=0, sticky="w")
            return
        columns = 3
        for index, value in enumerate(values):
            check = tk.Checkbutton(parent, text=_option_label(kind, value), variable=variables[value], anchor="w")
            check.grid(row=index // columns, column=index % columns, sticky="w", padx=(0, 8), pady=1)
            self.build_option_widgets.append((faction, check))

    def _refresh_build_controls(self) -> None:
        random_all = self.random_build_options_var.get()
        for faction, widget in self.faction_random_widgets.items():
            widget.configure(state="disabled" if random_all else "normal")
        for faction, widget in self.build_option_widgets:
            disabled = random_all or self.faction_random_build_vars[faction].get()
            widget.configure(state="disabled" if disabled else "normal")

    def _active_build_factions_from_vars(self) -> list[int]:
        active = [FACTION_PLAYER]
        for faction in CUSTOM_WIZARD_FACTIONS:
            if any(var.get() for var in self.host_vars[faction]):
                active.append(faction)
        return active

    def _state_from_vars(self) -> CustomWizardState:
        return CustomWizardState(
            random_size=self.random_size_var.get(),
            width=self.width_var.get(),
            height=self.height_var.get(),
            player_energy=self.player_energy_var.get(),
            host_present={
                faction: [var.get() for var in self.host_vars[faction]]
                for faction in CUSTOM_WIZARD_FACTIONS
            },
            host_energy={
                faction: [var.get() for var in self.host_energy_vars[faction]]
                for faction in CUSTOM_WIZARD_FACTIONS
            },
            ghorkov_host_types=[var.get() for var in self.ghorkov_type_vars],
            gate_target_level_id=_leading_int(self.gate_target_var.get()),
            random_gate_keys=self.random_gate_keys_var.get(),
            gate_key_count=self.gate_key_count_var.get(),
            win_movie=self.win_movie_var.get(),
            lose_movie=self.lose_movie_var.get(),
            random_bombs=self.random_bombs_var.get(),
            bomb_included=[var.get() for var in self.bomb_include_vars],
            bomb_custom_countdown=[var.get() for var in self.bomb_custom_vars],
            bomb_countdown_seconds=[var.get() for var in self.bomb_countdown_vars],
            random_build_options=self.random_build_options_var.get(),
            faction_random_build_options={
                faction: var.get()
                for faction, var in self.faction_random_build_vars.items()
            },
            enabled_vehicles={
                faction: {value for value, var in variables.items() if var.get()}
                for faction, variables in self.vehicle_vars.items()
            },
            enabled_buildings={
                faction: {value for value, var in variables.items() if var.get()}
                for faction, variables in self.building_vars.items()
            },
        )


class Generator1GUI:
    def __init__(self, root: tk.Tk, settings_path: str | Path | None = None) -> None:
        self.root = root
        self.settings_path = Path(settings_path) if settings_path is not None else default_settings_path()
        settings = load_settings(self.settings_path)
        self.legacy_dialogs: dict[int, LegacyDialog] = {}
        self.legacy_license_text = ""

        self.random_file_var = tk.StringVar(value=settings.random_level_file)
        self.custom_file_var = tk.StringVar(value=settings.custom_level_file)
        self.exe_var = tk.StringVar(value=settings.exe_location)
        self.campaign_dir_var = tk.StringVar(value=settings.campaign_directory)
        self.generator2_single_file_var = tk.StringVar(value=settings.generator2_single_level_file)
        self.generator2_campaign_dir_var = tk.StringVar(value=settings.generator2_campaign_directory)
        self.generator2_level_id_var = tk.StringVar(value="1")
        self.generator2_seed_var = tk.StringVar(value="")
        self.generator2_campaign_seed_var = tk.StringVar(value="")
        self.building_scripts_var = tk.BooleanVar(value=settings.use_building_scripts)
        self.status_var = tk.StringVar(value="Ready.")

        self.root.title(APP_TITLE)
        self.root.resizable(False, False)
        self._build()

    def _build(self) -> None:
        outer = tk.Frame(self.root, padx=10, pady=8)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        notebook = ttk.Notebook(outer)
        notebook.grid(row=0, column=0, sticky="nsew")

        generator1_tab = tk.Frame(notebook, padx=8, pady=8)
        generator2_tab = tk.Frame(notebook, padx=8, pady=8)
        notebook.add(generator1_tab, text="Generator1")
        notebook.add(generator2_tab, text="Generator2")
        self._build_generator1_tab(generator1_tab)
        self._build_generator2_tab(generator2_tab)

        bottom = tk.Frame(outer)
        bottom.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        bottom.columnconfigure(0, weight=1)
        tk.Label(bottom, textvariable=self.status_var, anchor="w").grid(row=0, column=0, sticky="ew")
        tk.Button(bottom, text="Save Settings", command=self._save_settings).grid(row=0, column=1, sticky="e")

    def _build_generator1_tab(self, outer: tk.Frame) -> None:
        outer.columnconfigure(0, weight=1)
        menu = tk.LabelFrame(outer, text="Main Menu", padx=8, pady=8)
        menu.grid(row=0, column=0, sticky="ew")
        menu.columnconfigure(0, weight=1)
        menu.columnconfigure(1, weight=1)

        tk.Button(menu, text="Make One Level, Totally Random", command=self._make_random_single).grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=2
        )
        tk.Button(menu, text="Make One Level at a Certain Skill Level", command=self._make_skill_single).grid(
            row=1, column=0, sticky="ew", padx=(0, 2), pady=2
        )
        tk.Button(menu, text="Make One Level From a Random Seed Number", command=self._make_seed_single).grid(
            row=1, column=1, sticky="ew", padx=(2, 0), pady=2
        )
        tk.Button(menu, text="Custom Random Level Generator Wizard", command=self._make_custom_single).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=2
        )
        tk.Button(menu, text="Create a WHOLE CAMPAIGN", command=self._make_campaign).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=2
        )
        tk.Button(menu, text="Credits", command=self._show_credits).grid(row=4, column=0, sticky="ew", padx=(0, 2), pady=2)
        tk.Button(menu, text="Read The License Agreement", command=self._show_license).grid(
            row=4, column=1, sticky="ew", padx=(2, 0), pady=2
        )
        tk.Button(menu, text="Create Backup", command=self._create_backup).grid(
            row=5, column=0, sticky="ew", padx=(0, 2), pady=2
        )
        tk.Button(menu, text="Exit", command=self._exit).grid(row=5, column=1, sticky="ew", padx=(2, 0), pady=2)

        notice = (
            "YOU ARE BOUND TO THE TERMS AND CONDITIONS IN THE LICENSE AGREEMENT IF YOU USE\n"
            "THIS PROGRAM, WHETHER OR NOT YOU READ IT!"
        )
        tk.Label(outer, text=notice, justify="left", anchor="w").grid(row=1, column=0, sticky="ew", pady=(6, 0))
        tk.Label(
            outer,
            text="Python reimplementation of the legacy Urban Assault Random UA generator.",
            justify="left",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew")
        tk.Checkbutton(
            outer,
            text="Click here to enable AOE_Danny's new building scripts. It won't automatically use them w/o it.",
            variable=self.building_scripts_var,
            anchor="w",
        ).grid(row=3, column=0, sticky="ew")

        paths = tk.Frame(outer)
        paths.grid(row=4, column=0, sticky="ew", pady=(4, 0))
        paths.columnconfigure(0, weight=1)
        self._path_row(
            paths,
            0,
            "For single levels, it puts it in the file:",
            self.random_file_var,
            self._browse_random_file,
        )
        self._path_row(
            paths,
            1,
            "For partly random levels made OR TESTED with the wizard, it puts it in the file:",
            self.custom_file_var,
            self._browse_custom_file,
        )
        self._path_row(paths, 2, "The Location of the Urban Assault .EXE file:", self.exe_var, self._browse_exe)
        self._path_row(
            paths,
            3,
            "If you make a whole campaign, it puts it in the folder:",
            self.campaign_dir_var,
            self._browse_campaign_dir,
        )

    def _build_generator2_tab(self, outer: tk.Frame) -> None:
        outer.columnconfigure(0, weight=1)

        single = tk.LabelFrame(outer, text="Single Level", padx=8, pady=8)
        single.grid(row=0, column=0, sticky="ew")
        single.columnconfigure(1, weight=1)

        tk.Label(single, text="Level ID:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        level_ids = [str(level_id) for level_id in sorted(GENERATOR2_LEVELS)]
        level_combo = ttk.Combobox(
            single,
            textvariable=self.generator2_level_id_var,
            values=level_ids,
            state="readonly",
            width=8,
        )
        level_combo.grid(row=0, column=1, sticky="w", pady=2)
        if self.generator2_level_id_var.get() not in level_ids:
            self.generator2_level_id_var.set(level_ids[0])

        tk.Label(single, text="Seed (blank for random):", anchor="w").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        tk.Entry(single, textvariable=self.generator2_seed_var, width=18).grid(row=1, column=1, sticky="w", pady=2)

        self._path_row(
            single,
            2,
            "Single level output file:",
            self.generator2_single_file_var,
            self._browse_generator2_single_file,
        )
        tk.Button(single, text="Generate Single Level", command=self._make_generator2_single).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        campaign = tk.LabelFrame(outer, text="Campaign", padx=8, pady=8)
        campaign.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        campaign.columnconfigure(1, weight=1)

        tk.Label(campaign, text="Seed (blank for random):", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(campaign, textvariable=self.generator2_campaign_seed_var, width=18).grid(
            row=0, column=1, sticky="w", pady=2
        )
        self._path_row(
            campaign,
            1,
            "Campaign output folder:",
            self.generator2_campaign_dir_var,
            self._browse_generator2_campaign_dir,
        )
        tk.Button(campaign, text="Generate Campaign", command=self._make_generator2_campaign).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_legacy_main(self) -> None:
        self.root.title(self.legacy_dialogs[LEGACY_MAIN_DIALOG].title)
        entry_vars = {
            1003: self.random_file_var,
            1017: self.custom_file_var,
            1014: self.exe_var,
            1018: self.campaign_dir_var,
        }
        check_vars = {1152: self.building_scripts_var}
        command_map = {
            1002: self._make_random_single,
            1015: self._make_skill_single,
            1001: self._make_seed_single,
            1000: self._make_custom_single,
            1011: self._make_campaign,
            1012: self._show_license,
            1013: self._show_credits,
            1004: self._exit,
            1154: self._browse_random_file,
            1155: self._browse_custom_file,
            1157: self._browse_exe,
            1159: self._create_backup,
            1160: self._save_settings,
        }
        renderer = LegacyDialogRenderer(
            self.root,
            self.legacy_dialogs[LEGACY_MAIN_DIALOG],
            command_map=command_map,
            entry_vars=entry_vars,
            check_vars=check_vars,
        )
        renderer.frame.grid(row=0, column=0, padx=8, pady=8)
        tk.Label(self.root, textvariable=self.status_var, anchor="w").grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))

    def _path_row(
        self,
        parent: tk.Frame,
        index: int,
        label: str,
        variable: tk.StringVar,
        browse_command: object,
    ) -> None:
        base_row = index * 2
        tk.Label(parent, text=label, anchor="w").grid(row=base_row, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        tk.Entry(parent, textvariable=variable, width=66).grid(row=base_row + 1, column=0, sticky="ew", pady=(0, 2))
        tk.Button(parent, text="Browse...", command=browse_command, width=10).grid(
            row=base_row + 1, column=1, sticky="e", padx=(6, 0), pady=(0, 2)
        )

    def _make_random_single(self) -> None:
        target = self._ensure_file_path(self.random_file_var, "Select single level output file")
        if target is None:
            return
        self._generate_single(target, seed=0, difficulty=5, skill=0, improved=True)

    def _make_skill_single(self) -> None:
        if LEGACY_SKILL_DIALOG in self.legacy_dialogs:
            dialog = LegacyModal(self.root, self.legacy_dialogs[LEGACY_SKILL_DIALOG], entry_defaults={1012: "6"})
            if not dialog.run():
                return
            try:
                skill = _int_from_var(dialog.entry_vars.get(1012), "skill level")
            except ValueError as exc:
                messagebox.showerror("Insufficient/Incorrect Data", str(exc), parent=self.root)
                return
            if not 1 <= skill <= 11:
                messagebox.showerror("Insufficient/Incorrect Data", "Skill level must be between 1 and 11.", parent=self.root)
                return
        else:
            skill = simpledialog.askinteger(
                "Skill Level",
                "Enter a skill level from 1 to 11:",
                parent=self.root,
                initialvalue=6,
                minvalue=1,
                maxvalue=11,
            )
        if skill is None:
            return
        target = self._ensure_file_path(self.random_file_var, "Select single level output file")
        if target is None:
            return
        self._generate_single(target, seed=0, difficulty=5, skill=skill, improved=True)

    def _make_seed_single(self) -> None:
        if LEGACY_SEED_DIALOG in self.legacy_dialogs:
            dialog = LegacyModal(self.root, self.legacy_dialogs[LEGACY_SEED_DIALOG], entry_defaults={1171: "12345"})
            if not dialog.run():
                return
            try:
                seed = _int_from_var(dialog.entry_vars.get(1171), "seed number")
            except ValueError as exc:
                messagebox.showerror("Insufficient/Incorrect Data", str(exc), parent=self.root)
                return
        else:
            seed = simpledialog.askinteger("Random Seed Number", "Enter the seed number:", parent=self.root, initialvalue=12345)
        if seed is None:
            return
        target = self._ensure_file_path(self.random_file_var, "Select single level output file")
        if target is None:
            return
        self._generate_single(target, seed=seed, difficulty=5, skill=0, improved=True)

    def _make_custom_single(self) -> None:
        options = CustomWizardDialog(
            self.root,
            allow_new_buildings=self.building_scripts_var.get(),
        ).run()
        if options is None:
            return
        target = self._ensure_file_path(self.custom_file_var, "Select custom level output file")
        if target is None:
            return
        self._generate_custom(target, options)

    def _make_campaign(self) -> None:
        seed = self._ask_optional_seed("Campaign Seed", "Enter campaign seed, or leave blank for a random seed:")
        if seed is None:
            return
        directory = self._ensure_directory_path(self.campaign_dir_var, "Select campaign output folder")
        if directory is None:
            return
        if LEGACY_CAMPAIGN_DIALOG in self.legacy_dialogs:
            dialog = LegacyModal(self.root, self.legacy_dialogs[LEGACY_CAMPAIGN_DIALOG])
            if not dialog.run():
                return
        self._generate_campaign(directory, seed=seed)

    def _make_generator2_single(self) -> None:
        level_id = self._generator2_level_id()
        if level_id is None:
            return
        seed = self._parse_optional_seed_entry(self.generator2_seed_var, "Generator2 Single Level")
        if seed is None:
            return
        target = self._ensure_file_path(
            self.generator2_single_file_var,
            "Select Generator2 single level output file",
            level_filename(level_id),
        )
        if target is None:
            return
        self._generate_generator2_single(target, seed=seed, level_id=level_id)

    def _make_generator2_campaign(self) -> None:
        seed = self._parse_optional_seed_entry(self.generator2_campaign_seed_var, "Generator2 Campaign")
        if seed is None:
            return
        directory = self._ensure_directory_path(self.generator2_campaign_dir_var, "Select Generator2 campaign output folder")
        if directory is None:
            return
        self._generate_generator2_campaign(directory, seed=seed)

    def _generate_single(self, target: Path, seed: int, difficulty: int, skill: int, improved: bool) -> None:
        try:
            self._set_status("Generating level...")
            backup_path = backup_existing_file(target)
            level = Generator1().generate_single(seed=seed, difficulty=difficulty, skill=skill, improved=improved)
            written = level.write(target)
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status("Generation failed.")
            messagebox.showerror("Generation Failed", str(exc), parent=self.root)
            return

        lines = [
            f"Wrote {written}",
            f"Seed: {level.seed}",
            f"Map: {level.width}x{level.height}",
            f"Tileset: {level.tileset}",
        ]
        if backup_path is not None:
            lines.append(f"Backup: {backup_path}")
        self._set_status(f"Wrote {written}")
        messagebox.showinfo("Level Created", "\n".join(lines), parent=self.root)

    def _generate_custom(self, target: Path, options: Generator1CustomOptions) -> None:
        try:
            self._set_status("Generating custom level...")
            backup_path = backup_existing_file(target)
            level = Generator1().generate_custom(options)
            written = level.write(target)
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status("Custom generation failed.")
            messagebox.showerror("Generation Failed", str(exc), parent=self.root)
            return

        lines = [
            f"Wrote {written}",
            f"Seed: {level.seed}",
            f"Map: {level.width}x{level.height}",
            f"Tileset: {level.tileset}",
        ]
        if backup_path is not None:
            lines.append(f"Backup: {backup_path}")
        self._set_status(f"Wrote {written}")
        messagebox.showinfo("Level Created", "\n".join(lines), parent=self.root)

    def _generate_campaign(self, directory: Path, seed: int) -> None:
        try:
            self._set_status("Generating campaign...")
            backup_dir, moved = backup_campaign_ldfs(directory)
            campaign = Generator1().generate_campaign(seed=seed, difficulty=5, improved=True)
            written = campaign.write(directory)
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status("Campaign generation failed.")
            messagebox.showerror("Campaign Generation Failed", str(exc), parent=self.root)
            return

        lines = [f"Wrote {len(written)} Generator1 levels to {directory}", f"Seed: {campaign.seed}"]
        if backup_dir is not None:
            lines.append(f"Backed up {len(moved)} existing LDF files to {backup_dir}")
        self._set_status(f"Wrote {len(written)} campaign levels.")
        messagebox.showinfo("Campaign Created", "\n".join(lines), parent=self.root)

    def _generate_generator2_single(self, target: Path, seed: int, level_id: int) -> None:
        try:
            self._set_status("Generating Generator2 level...")
            backup_path = backup_existing_file(target)
            level = Generator2().generate_single(seed=seed, level_id=level_id)
            written = level.write(target)
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status("Generator2 generation failed.")
            messagebox.showerror("Generation Failed", str(exc), parent=self.root)
            return

        lines = [
            f"Wrote {written}",
            f"Level ID: {level.level_id}",
            f"Seed: {level.seed}",
            f"Map: {level.width}x{level.height}",
            f"Tileset: {level.tileset}",
        ]
        if backup_path is not None:
            lines.append(f"Backup: {backup_path}")
        self._set_status(f"Wrote {written}")
        messagebox.showinfo("Generator2 Level Created", "\n".join(lines), parent=self.root)

    def _generate_generator2_campaign(self, directory: Path, seed: int) -> None:
        try:
            self._set_status("Generating Generator2 campaign...")
            backup_dir, moved = backup_campaign_ldfs(directory)
            campaign = Generator2().generate_campaign(seed=seed)
            written = campaign.write(directory)
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status("Generator2 campaign generation failed.")
            messagebox.showerror("Campaign Generation Failed", str(exc), parent=self.root)
            return

        lines = [f"Wrote {len(written)} Generator2 levels to {directory}", f"Seed: {campaign.seed}"]
        if backup_dir is not None:
            lines.append(f"Backed up {len(moved)} existing LDF files to {backup_dir}")
        self._set_status(f"Wrote {len(written)} Generator2 campaign levels.")
        messagebox.showinfo("Generator2 Campaign Created", "\n".join(lines), parent=self.root)

    def _create_backup(self) -> None:
        created: list[Path] = []
        seen_files: set[Path] = set()
        for raw_path in (self.random_file_var.get(), self.custom_file_var.get(), self.generator2_single_file_var.get()):
            if not raw_path.strip():
                continue
            path = Path(raw_path)
            if path in seen_files:
                continue
            seen_files.add(path)
            backup_path = backup_existing_file(path)
            if backup_path is not None:
                created.append(backup_path)

        seen_dirs: set[Path] = set()
        for campaign_dir_text in (self.campaign_dir_var.get().strip(), self.generator2_campaign_dir_var.get().strip()):
            if not campaign_dir_text:
                continue
            campaign_dir = Path(campaign_dir_text)
            if campaign_dir in seen_dirs:
                continue
            seen_dirs.add(campaign_dir)
            backup_dir, moved = backup_campaign_ldfs(campaign_dir)
            if backup_dir is not None:
                created.append(backup_dir)
                created.extend(moved)

        if not created:
            self._set_status("No existing generated files found to back up.")
            messagebox.showinfo("Create Backup", "No existing generated files found to back up.", parent=self.root)
            return
        self._set_status(f"Created backup for {len(created)} item(s).")
        messagebox.showinfo("Create Backup", "Backup created.", parent=self.root)

    def _browse_random_file(self) -> None:
        path = self._ask_save_file("Select single level output file", self.random_file_var.get(), "level_01.ldf")
        if path is not None:
            self.random_file_var.set(str(path))

    def _browse_custom_file(self) -> None:
        path = self._ask_save_file("Select custom level output file", self.custom_file_var.get(), "custom_level.ldf")
        if path is not None:
            self.custom_file_var.set(str(path))

    def _browse_exe(self) -> None:
        kwargs = {
            "parent": self.root,
            "title": "Select Urban Assault executable",
            "filetypes": (("Executable files", "*.exe"), ("All files", "*.*")),
        }
        current = self.exe_var.get().strip()
        if current:
            current_path = Path(current)
            if current_path.parent.exists():
                kwargs["initialdir"] = str(current_path.parent)
        selected = filedialog.askopenfilename(**kwargs)
        if selected:
            self.exe_var.set(selected)

    def _browse_campaign_dir(self) -> None:
        path = self._ask_directory("Select campaign output folder", self.campaign_dir_var.get())
        if path is not None:
            self.campaign_dir_var.set(str(path))

    def _browse_generator2_single_file(self) -> None:
        level_id = self._generator2_level_id(show_error=False) or 1
        path = self._ask_save_file(
            "Select Generator2 single level output file",
            self.generator2_single_file_var.get(),
            level_filename(level_id),
        )
        if path is not None:
            self.generator2_single_file_var.set(str(path))

    def _browse_generator2_campaign_dir(self) -> None:
        path = self._ask_directory("Select Generator2 campaign output folder", self.generator2_campaign_dir_var.get())
        if path is not None:
            self.generator2_campaign_dir_var.set(str(path))

    def _ensure_file_path(self, variable: tk.StringVar, title: str, default_name: str = "level_01.ldf") -> Path | None:
        value = variable.get().strip()
        if value:
            return Path(value)
        path = self._ask_save_file(title, "", default_name)
        if path is None:
            return None
        variable.set(str(path))
        return path

    def _ensure_directory_path(self, variable: tk.StringVar, title: str) -> Path | None:
        value = variable.get().strip()
        if value:
            return Path(value)
        path = self._ask_directory(title, "")
        if path is None:
            return None
        variable.set(str(path))
        return path

    def _ask_save_file(self, title: str, current: str, default_name: str) -> Path | None:
        kwargs = {
            "parent": self.root,
            "title": title,
            "defaultextension": ".ldf",
            "filetypes": (("LDF files", "*.ldf"), ("All files", "*.*")),
            "initialfile": default_name,
        }
        if current:
            current_path = Path(current)
            kwargs["initialfile"] = current_path.name
            if current_path.parent.exists():
                kwargs["initialdir"] = str(current_path.parent)
        selected = filedialog.asksaveasfilename(**kwargs)
        return Path(selected) if selected else None

    def _ask_directory(self, title: str, current: str) -> Path | None:
        kwargs = {"parent": self.root, "title": title}
        if current and Path(current).exists():
            kwargs["initialdir"] = current
        selected = filedialog.askdirectory(**kwargs)
        return Path(selected) if selected else None

    def _ask_optional_seed(self, title: str, prompt: str) -> int | None:
        while True:
            value = simpledialog.askstring(title, prompt, parent=self.root)
            if value is None:
                return None
            value = value.strip()
            if not value:
                return 0
            try:
                return int(value)
            except ValueError:
                messagebox.showerror("Invalid Seed", "Seed must be a whole number.", parent=self.root)

    def _parse_optional_seed_entry(self, variable: tk.StringVar, title: str) -> int | None:
        value = variable.get().strip()
        if not value:
            return 0
        try:
            return int(value)
        except ValueError:
            messagebox.showerror(title, "Seed must be a whole number.", parent=self.root)
            return None

    def _generator2_level_id(self, show_error: bool = True) -> int | None:
        try:
            level_id = int(self.generator2_level_id_var.get())
        except ValueError:
            level_id = -1
        if level_id in GENERATOR2_LEVELS:
            return level_id
        if show_error:
            messagebox.showerror("Generator2 Level", "Select a valid Generator2 level ID.", parent=self.root)
        return None

    def _save_settings(self) -> None:
        try:
            path = save_settings(self._collect_settings(), self.settings_path)
        except OSError as exc:
            self._set_status("Could not save settings.")
            messagebox.showerror("Save Settings", str(exc), parent=self.root)
            return
        self._set_status(f"Settings saved to {path}")
        messagebox.showinfo("Save Settings", f"Settings saved to {path}", parent=self.root)

    def _save_settings_quiet(self) -> None:
        try:
            save_settings(self._collect_settings(), self.settings_path)
        except OSError as exc:
            self._set_status(f"Could not save settings: {exc}")

    def _collect_settings(self) -> GuiSettings:
        return GuiSettings(
            random_level_file=self.random_file_var.get().strip(),
            custom_level_file=self.custom_file_var.get().strip(),
            campaign_directory=self.campaign_dir_var.get().strip(),
            exe_location=self.exe_var.get().strip(),
            use_building_scripts=self.building_scripts_var.get(),
            generator2_single_level_file=self.generator2_single_file_var.get().strip(),
            generator2_campaign_directory=self.generator2_campaign_dir_var.get().strip(),
        )

    def _show_credits(self) -> None:
        if LEGACY_CREDITS_DIALOG in self.legacy_dialogs:
            LegacyModal(self.root, self.legacy_dialogs[LEGACY_CREDITS_DIALOG]).run()
            return
        messagebox.showinfo(
            "Credits",
            "Urban Assault Level Generator\n"
            "Python reimplementation of selected legacy generators.\n\n"
            "Original Random UA.exe: Daniel L. Orlando.\n"
            "Python project: Urban Assault Level Generator Contributors.",
            parent=self.root,
        )

    def _show_license(self) -> None:
        if LEGACY_LICENSE_DIALOG in self.legacy_dialogs:
            LegacyModal(
                self.root,
                self.legacy_dialogs[LEGACY_LICENSE_DIALOG],
                entry_defaults={1165: self.legacy_license_text},
            ).run()
            return
        messagebox.showinfo(
            "License Agreement",
            "This Python project is licensed under GPL-3.0-or-later.\n\n"
            "Generated level files are intended for use with Urban Assault. "
            "You are responsible for using them with a legally obtained copy of the game.",
            parent=self.root,
        )

    def _exit(self) -> None:
        self._save_settings_quiet()
        self.root.destroy()

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)
        self.root.update_idletasks()


def _int_value(value: object, label: str) -> int:
    if isinstance(value, str):
        raw_value = value.strip()
        if not raw_value:
            raise ValueError(f"Please enter {label}.")
        value = raw_value
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a whole number.") from exc


def _bool_slots(values: Sequence[object], *, count: int = 3) -> list[bool]:
    result = [bool(value) for value in list(values)[:count]]
    return (result + [False] * count)[:count]


def _int_slots(values: Sequence[object], default: int, *, count: int = 3) -> list[int]:
    raw_values = list(values)[:count]
    result = []
    for value in raw_values:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            result.append(default)
    return (result + [default] * count)[:count]


def _legacy_energy_value(value: object, label: str) -> int:
    energy = _int_value(value, label)
    if not 1 <= energy <= 10_000_000:
        raise ValueError(f"{label} must be between 1 and 10000000.")
    return energy * 400


def _faction_label(faction: int) -> str:
    labels = {
        FACTION_PLAYER: "Resistance",
        FACTION_GHORKOVS: "Ghorkovs",
        FACTION_TAERKASTEN: "Taerkasten",
        FACTION_MYKONIANS: "Mykonians",
        FACTION_SULGOGARS: "Sulgogars",
        FACTION_BLACK_SECT: "Black Sect",
        FACTION_TUTOR: "Tutorial",
    }
    return labels.get(faction, f"Faction {faction}")


def _vehicle_options_for_faction(faction: int) -> tuple[int, ...]:
    return tuple(dict.fromkeys(VEHICLES_BY_FACTION.get(faction, [])))


def _building_options_for_faction(faction: int, *, allow_new_buildings: bool = True) -> tuple[int, ...]:
    buildings = list(BUILDINGS_BY_FACTION.get(faction, []))
    if allow_new_buildings and faction == FACTION_PLAYER:
        buildings.extend(RESISTANCE_NEW_BUILDING_IDS)
    elif allow_new_buildings and faction == FACTION_BLACK_SECT:
        buildings.extend(BLACK_SECT_NEW_BUILDING_IDS)
    return tuple(dict.fromkeys(buildings))


def _option_label(kind: str, value: int) -> str:
    labels = VEHICLE_LABELS if kind == "vehicle" else BUILDING_LABELS
    return f"{labels.get(value, kind.title())} ({value})"


def _ordered_selected(selected: set[int], allowed: Sequence[int]) -> list[int]:
    return [value for value in allowed if value in selected]


def _active_custom_build_factions(state: CustomWizardState) -> list[int]:
    active = [FACTION_PLAYER]
    for faction in CUSTOM_WIZARD_FACTIONS:
        if any(_bool_slots(state.host_present.get(faction, []))):
            active.append(faction)
    return active


def _collect_build_options_from_state(
    state: CustomWizardState,
    options: Generator1CustomOptions,
    *,
    allow_new_buildings: bool,
) -> None:
    if state.random_build_options:
        return

    for faction in _active_custom_build_factions(state):
        if state.faction_random_build_options.get(faction, True):
            continue
        vehicle_options = _vehicle_options_for_faction(faction)
        building_options = _building_options_for_faction(faction, allow_new_buildings=allow_new_buildings)
        vehicles = _ordered_selected(state.enabled_vehicles.get(faction, set()), vehicle_options)
        buildings = _ordered_selected(state.enabled_buildings.get(faction, set()), building_options)
        options.enabled_vehicles[faction] = vehicles
        options.enabled_buildings[faction] = buildings


UNIT_RANDOM_CONTROL_BY_FACTION = {
    FACTION_PLAYER: 1089,
    FACTION_GHORKOVS: 1090,
    FACTION_TAERKASTEN: 1091,
    FACTION_MYKONIANS: 1092,
    FACTION_SULGOGARS: 1093,
    FACTION_BLACK_SECT: 1045,
    FACTION_TUTOR: 1047,
}

ENABLE_ALL_CONTROL_IDS = {1151, 1152, 1153}


def _control_map(control_ids: list[int], values: list[int]) -> dict[int, int]:
    return {control_id: value for control_id, value in zip(control_ids, values, strict=False)}


RESISTANCE_VEHICLE_CONTROLS = [
    1074, 1075, 1076, 1077, 1078, 1079, 1080, 1081,
    1082, 1083, 1084, 1045, 1046, 1047, 1048, 1049,
]

RESISTANCE_NEW_BUILDING_MAP = _control_map(
    [1095, 1067, 1068, 1069, 1070, 1071, 1072, 1073, 1059, 1060, 1061, 1066, 1062, 1063, 1064, 1065],
    [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 90, 91, 92, 93],
)

BLACK_SECT_NEW_BUILDING_MAP = _control_map(
    [1095, 1067, 1068, 1069, 1070, 1071, 1072, 1073, 1096, 1097, 1098, 1059, 1060, 1061, 1066, 1062, 1063, 1064, 1065],
    [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 90, 91, 92, 93, 94, 95, 96],
)

BLACK_SECT_VEHICLE_MAP = {
    **_control_map(
        [1128, 1129, 1130, 1131, 1132, 1133, 1134, 1135, 1139, 1149, 1150],
        VEHICLES_BY_FACTION[FACTION_GHORKOVS],
    ),
    **_control_map([1087, 1088, 1089, 1090, 1091, 1092, 1093, 1096, 1097], VEHICLES_BY_FACTION[FACTION_TAERKASTEN]),
    **_control_map([1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105], VEHICLES_BY_FACTION[FACTION_MYKONIANS]),
    **_control_map(RESISTANCE_VEHICLE_CONTROLS, VEHICLES_BY_FACTION[FACTION_PLAYER]),
    **_control_map([1050, 1051, 1054, 1055], VEHICLES_BY_FACTION[FACTION_SULGOGARS]),
}

BLACK_SECT_BUILDING_MAP = {
    1085: 63, 1053: 11, 1057: 28, 1140: 3,
    1086: 52, 1121: 12, 1136: 30, 1141: 71,
    1052: 53, 1122: 17, 1137: 31, 1142: 73,
    1123: 10, 1138: 13, 1143: 72,
    1144: 18,
}

UNIT_ENABLE_MAP: dict[int, tuple[int, dict[int, int], dict[int, int]]] = {
    143: (
        FACTION_PLAYER,
        _control_map(RESISTANCE_VEHICLE_CONTROLS, VEHICLES_BY_FACTION[FACTION_PLAYER]),
        {
            **_control_map([1085, 1086, 1052, 1053, 1087, 1055, 1088, 1057], BUILDINGS_BY_FACTION[FACTION_PLAYER]),
            **RESISTANCE_NEW_BUILDING_MAP,
        },
    ),
    144: (
        FACTION_GHORKOVS,
        _control_map(list(range(1074, 1085)), VEHICLES_BY_FACTION[FACTION_GHORKOVS]),
        _control_map([1085, 1086, 1052, 1053], BUILDINGS_BY_FACTION[FACTION_GHORKOVS]),
    ),
    145: (
        FACTION_TAERKASTEN,
        _control_map(list(range(1074, 1083)), VEHICLES_BY_FACTION[FACTION_TAERKASTEN]),
        _control_map([1085, 1086, 1052, 1053], BUILDINGS_BY_FACTION[FACTION_TAERKASTEN]),
    ),
    146: (
        FACTION_MYKONIANS,
        _control_map(list(range(1074, 1082)), VEHICLES_BY_FACTION[FACTION_MYKONIANS]),
        _control_map([1085, 1086, 1052], BUILDINGS_BY_FACTION[FACTION_MYKONIANS]),
    ),
    147: (
        FACTION_BLACK_SECT,
        BLACK_SECT_VEHICLE_MAP,
        BLACK_SECT_BUILDING_MAP,
    ),
    148: (
        FACTION_SULGOGARS,
        _control_map(list(range(1074, 1078)), VEHICLES_BY_FACTION[FACTION_SULGOGARS]),
        {},
    ),
    149: (
        FACTION_BLACK_SECT,
        {},
        BLACK_SECT_NEW_BUILDING_MAP,
    ),
    150: (
        FACTION_TUTOR,
        {1074: 142},
        {},
    ),
}


def _unit_enable_values(dialog_id: int, check_vars: dict[int, tk.BooleanVar]) -> tuple[list[int], list[int], int]:
    faction, vehicle_map, building_map = UNIT_ENABLE_MAP.get(dialog_id, (FACTION_PLAYER, {}, {}))
    enable_all = any(_checked(check_vars, control_id) for control_id in ENABLE_ALL_CONTROL_IDS)
    vehicles = [vehicle for control_id, vehicle in vehicle_map.items() if enable_all or _checked(check_vars, control_id)]
    buildings = [building for control_id, building in building_map.items() if enable_all or _checked(check_vars, control_id)]
    return vehicles, buildings, faction


def _checked(check_vars: dict[int, tk.BooleanVar], control_id: int) -> bool:
    variable = check_vars.get(control_id)
    return bool(variable.get()) if variable is not None else False


def _int_from_var(variable: tk.StringVar | None, label: str) -> int:
    if variable is None:
        raise ValueError(f"Missing {label}.")
    value = variable.get().strip()
    if not value:
        raise ValueError(f"Please enter {label}.")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a whole number.") from exc


def _legacy_energy(variable: tk.StringVar | None) -> int:
    if variable is None or not variable.get().strip():
        return 0
    value = int(variable.get())
    return max(1, value * 400)


def _leading_int(value: str) -> int:
    digits = []
    for char in value.strip():
        if char.isdigit():
            digits.append(char)
        elif digits:
            break
    return int("".join(digits)) if digits else 0


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


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.name}_{index}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not create a unique backup path for {path}")


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        raise SystemExit("ualg-gui does not accept command-line arguments")
    root = tk.Tk()
    Generator1GUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
