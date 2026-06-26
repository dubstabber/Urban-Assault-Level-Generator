"""Legacy resource-dialog rendering and mapping helpers."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from ..constants import (
    FACTION_BLACK_SECT,
    FACTION_GHORKOVS,
    FACTION_MYKONIANS,
    FACTION_PLAYER,
    FACTION_SULGOGARS,
    FACTION_TAERKASTEN,
    FACTION_TUTOR,
    GENERATOR1_CAMPAIGN_FILENAMES,
    BUILDINGS_BY_FACTION,
    VEHICLES_BY_FACTION,
    level_id_from_filename,
)
from ..generator1 import Generator1CustomOptions
from ..legacy_resources import LegacyControl, LegacyDialog
from .custom_options import (
    GHORKOV_HOST_VEHICLES,
    NEW_BUILDING_IDS,
    _ghorkov_host_vehicle_id,
    _leading_int,
)


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
            values = list(GHORKOV_HOST_VEHICLES)
            return {1003: values, 1004: values, 1005: values}
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
                vehicles: list[int] = []
                for index, combo_id in enumerate(combos):
                    combo_value = page.entry_vars.get(combo_id)
                    vehicles.append(
                        _ghorkov_host_vehicle_id(combo_value.get() if combo_value else "") if present[index] else 0
                    )
                if any(vehicles):
                    options.ai_slot_host_vehicle_id[FACTION_GHORKOVS] = vehicles
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
