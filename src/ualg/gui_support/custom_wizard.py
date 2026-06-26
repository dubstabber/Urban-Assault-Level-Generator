"""Tkinter custom-level wizard dialogs."""

from __future__ import annotations

from typing import Sequence

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from ..constants import (
    FACTION_GHORKOVS,
    FACTION_PLAYER,
    GENERATOR1_CAMPAIGN_FILENAMES,
    level_id_from_filename,
)
from ..generator1 import Generator1CustomOptions
from .custom_options import (
    CUSTOM_BUILD_FACTIONS,
    CUSTOM_WIZARD_FACTIONS,
    CUSTOM_WIZARD_PAGE_TITLES,
    GHORKOV_HOST_VEHICLES,
    CustomGenerationOptions,
    CustomWizardState,
    _building_options_for_faction,
    _faction_label,
    _int_value,
    _leading_int,
    _option_label,
    _vehicle_options_for_faction,
    custom_wizard_options_from_state,
)


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

        self.outer = tk.Frame(self.window, padx=10, pady=8)
        self.outer.grid(row=0, column=0, sticky="nsew")
        self.outer.columnconfigure(0, weight=1)

        self.title_var = tk.StringVar()
        tk.Label(self.outer, textvariable=self.title_var, anchor="w", font=("TkDefaultFont", 10, "bold")).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        self.page_frame = tk.Frame(self.outer)
        self.page_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 8))

        nav = tk.Frame(self.outer)
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
        self.ghorkov_type_vars = [tk.StringVar(value="Turantul I") for _ in range(3)]

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
        self._schedule_fit_to_content()

    def _schedule_fit_to_content(self) -> None:
        self._fit_to_content()
        self.window.after_idle(self._fit_to_content)

    def _fit_to_content(self) -> None:
        try:
            if not self.window.winfo_exists():
                return
            self.window.update_idletasks()
            width = self.window.winfo_reqwidth()
            height = self.window.winfo_reqheight()
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = max(0, min(self.window.winfo_x(), max(0, screen_width - width)))
            y = max(0, min(self.window.winfo_y(), max(0, screen_height - height)))
            self.window.geometry(f"{width}x{height}+{x}+{y}")
        except tk.TclError:
            return

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
