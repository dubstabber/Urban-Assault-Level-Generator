"""Main Tkinter application shell for the Urban Assault generators."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..constants import (
    GENERATOR1_CAMPAIGN_PROFILES,
    GENERATOR2_CAMPAIGN_PROFILES,
    GENERATOR2_LEVELS,
    GENERATOR3_CAMPAIGN_PROFILES,
    GENERATOR4_CAMPAIGN_PROFILES,
    level_filename,
)
from ..generator1 import Generator1CustomOptions
from ..legacy_resources import LegacyDialog
from .custom_wizard import CustomWizardDialog
from .legacy_dialogs import (
    LEGACY_CAMPAIGN_DIALOG,
    LEGACY_CREDITS_DIALOG,
    LEGACY_LICENSE_DIALOG,
    LEGACY_MAIN_DIALOG,
    LEGACY_SEED_DIALOG,
    LEGACY_SKILL_DIALOG,
    LegacyDialogRenderer,
    LegacyModal,
    _int_from_var,
)
from .settings import GuiSettings, default_settings_path, load_settings, save_settings
from .workflows import (
    CampaignGenerationResult,
    LevelGenerationResult,
    create_configured_backups,
    generate_generator1_campaign,
    generate_generator1_custom,
    generate_generator1_single,
    generate_generator2_campaign,
    generate_generator2_single,
    generate_generator3_campaign,
    generate_generator3_single,
    generate_generator4_campaign,
    generate_generator4_single,
)


APP_TITLE = "Urban Assault Level Generator"
GENERATOR3_MODES = ("remix", "synthesis")
GENERATOR3_MODE_TOOLTIP = (
    "Remix reuses a real hand-made level's terrain and balance, swapping factions and rosters. "
    "Synthesis generates brand-new Wave Function Collapse terrain learned from the original levels."
)
ENEMY_RADAR_BUDGET_TOOLTIP = (
    "Prevents enemy AI from spending budget on radar stations. This keeps host stations from roaming away from "
    "their bases, where nearby squads could destroy them."
)
WorkflowResult = TypeVar("WorkflowResult")


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event: object | None = None) -> None:
        self._cancel()
        self._after_id = self.widget.after(450, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        self._after_id = None
        if self._window is not None:
            return
        x = self.widget.winfo_rootx() + 22
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        window = tk.Toplevel(self.widget)
        window.wm_overrideredirect(True)
        window.wm_geometry(f"+{x}+{y}")
        tk.Label(
            window,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4,
            wraplength=320,
        ).pack()
        self._window = window

    def _hide(self, _event: object | None = None) -> None:
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None


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
        self.generator1_campaign_profile_var = tk.StringVar(value="original")
        self.generator1_zero_enemy_radar_budgets_var = tk.BooleanVar(
            value=settings.generator1_zero_enemy_radar_budgets
        )
        self.generator2_single_file_var = tk.StringVar(value=settings.generator2_single_level_file)
        self.generator2_campaign_dir_var = tk.StringVar(value=settings.generator2_campaign_directory)
        self.generator2_level_id_var = tk.StringVar(value="1")
        self.generator2_seed_var = tk.StringVar(value="")
        self.generator2_campaign_seed_var = tk.StringVar(value="")
        self.generator2_campaign_profile_var = tk.StringVar(value="original")
        self.generator2_zero_enemy_station_delays_var = tk.BooleanVar(
            value=settings.generator2_zero_enemy_station_delays
        )
        self.generator2_zero_enemy_radar_budgets_var = tk.BooleanVar(
            value=settings.generator2_zero_enemy_radar_budgets
        )
        self.generator3_single_file_var = tk.StringVar(value=settings.generator3_single_level_file)
        self.generator3_campaign_dir_var = tk.StringVar(value=settings.generator3_campaign_directory)
        self.generator3_seed_var = tk.StringVar(value="")
        self.generator3_campaign_seed_var = tk.StringVar(value="")
        self.generator3_single_profile_var = tk.StringVar(value="original")
        self.generator3_campaign_profile_var = tk.StringVar(value="original")
        self.generator3_single_mode_var = tk.StringVar(value="remix")
        self.generator3_campaign_mode_var = tk.StringVar(value="remix")
        self.generator3_skeleton_var = tk.StringVar(value="")
        self.generator3_zero_enemy_station_delays_var = tk.BooleanVar(
            value=settings.generator3_zero_enemy_station_delays
        )
        self.generator3_zero_enemy_radar_budgets_var = tk.BooleanVar(
            value=settings.generator3_zero_enemy_radar_budgets
        )
        self.generator4_single_file_var = tk.StringVar(value=settings.generator4_single_level_file)
        self.generator4_campaign_dir_var = tk.StringVar(value=settings.generator4_campaign_directory)
        self.generator4_seed_var = tk.StringVar(value="")
        self.generator4_campaign_seed_var = tk.StringVar(value="")
        self.generator4_single_profile_var = tk.StringVar(value="original")
        self.generator4_campaign_profile_var = tk.StringVar(value="original")
        self.generator4_level_id_var = tk.StringVar(value="")
        self.generator4_zero_enemy_station_delays_var = tk.BooleanVar(
            value=settings.generator4_zero_enemy_station_delays
        )
        self.generator4_zero_enemy_radar_budgets_var = tk.BooleanVar(
            value=settings.generator4_zero_enemy_radar_budgets
        )
        self.building_scripts_var = tk.BooleanVar(value=settings.use_building_scripts)
        self.status_var = tk.StringVar(value="Ready.")
        self.tooltips: list[ToolTip] = []

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
        generator3_tab = tk.Frame(notebook, padx=8, pady=8)
        generator4_tab = tk.Frame(notebook, padx=8, pady=8)
        notebook.add(generator1_tab, text="Generator1")
        notebook.add(generator2_tab, text="Generator2")
        notebook.add(generator3_tab, text="Generator3")
        notebook.add(generator4_tab, text="Generator4")
        self._build_generator1_tab(generator1_tab)
        self._build_generator2_tab(generator2_tab)
        self._build_generator3_tab(generator3_tab)
        self._build_generator4_tab(generator4_tab)

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
        profile_row = tk.Frame(menu)
        profile_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)
        profile_row.columnconfigure(1, weight=1)
        tk.Label(profile_row, text="Generator1 campaign profile:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Combobox(
            profile_row,
            textvariable=self.generator1_campaign_profile_var,
            values=list(GENERATOR1_CAMPAIGN_PROFILES),
            state="readonly",
            width=16,
        ).grid(row=0, column=1, sticky="ew")
        radar_check = tk.Checkbutton(
            menu,
            text="Disable enemy radar budgets",
            variable=self.generator1_zero_enemy_radar_budgets_var,
            anchor="w",
        )
        radar_check.grid(row=4, column=0, columnspan=2, sticky="ew", pady=2)
        self._add_tooltip(radar_check, ENEMY_RADAR_BUDGET_TOOLTIP)
        tk.Button(menu, text="Create a WHOLE CAMPAIGN", command=self._make_campaign).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=2
        )
        tk.Button(menu, text="Credits", command=self._show_credits).grid(row=6, column=0, sticky="ew", padx=(0, 2), pady=2)
        tk.Button(menu, text="Read The License Agreement", command=self._show_license).grid(
            row=6, column=1, sticky="ew", padx=(2, 0), pady=2
        )
        tk.Button(menu, text="Create Backup", command=self._create_backup).grid(
            row=7, column=0, sticky="ew", padx=(0, 2), pady=2
        )
        tk.Button(menu, text="Exit", command=self._exit).grid(row=7, column=1, sticky="ew", padx=(2, 0), pady=2)

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

        options = tk.LabelFrame(outer, text="Options", padx=8, pady=8)
        options.grid(row=0, column=0, sticky="ew")
        tk.Checkbutton(
            options,
            text="Set enemy host station delays to 0",
            variable=self.generator2_zero_enemy_station_delays_var,
        ).grid(row=0, column=0, sticky="w")
        radar_check = tk.Checkbutton(
            options,
            text="Disable enemy radar budgets",
            variable=self.generator2_zero_enemy_radar_budgets_var,
        )
        radar_check.grid(row=1, column=0, sticky="w")
        self._add_tooltip(radar_check, ENEMY_RADAR_BUDGET_TOOLTIP)

        single = tk.LabelFrame(outer, text="Single Level", padx=8, pady=8)
        single.grid(row=1, column=0, sticky="ew", pady=(8, 0))
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
        campaign.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        campaign.columnconfigure(1, weight=1)

        tk.Label(campaign, text="Seed (blank for random):", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(campaign, textvariable=self.generator2_campaign_seed_var, width=18).grid(
            row=0, column=1, sticky="w", pady=2
        )
        tk.Label(campaign, text="Campaign profile:", anchor="w").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=2
        )
        ttk.Combobox(
            campaign,
            textvariable=self.generator2_campaign_profile_var,
            values=list(GENERATOR2_CAMPAIGN_PROFILES),
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="w", pady=2)
        self._path_row(
            campaign,
            2,
            "Campaign output folder:",
            self.generator2_campaign_dir_var,
            self._browse_generator2_campaign_dir,
        )
        tk.Button(campaign, text="Generate Campaign", command=self._make_generator2_campaign).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_generator3_tab(self, outer: tk.Frame) -> None:
        outer.columnconfigure(0, weight=1)

        intro = tk.Label(
            outer,
            text="Generator3 builds authored-style levels from the original game levels.",
            justify="left",
            anchor="w",
        )
        intro.grid(row=0, column=0, sticky="ew")

        options = tk.LabelFrame(outer, text="Options", padx=8, pady=8)
        options.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        tk.Checkbutton(
            options,
            text="Set enemy host station delays to 0",
            variable=self.generator3_zero_enemy_station_delays_var,
        ).grid(row=0, column=0, sticky="w")
        radar_check = tk.Checkbutton(
            options,
            text="Disable enemy radar budgets",
            variable=self.generator3_zero_enemy_radar_budgets_var,
        )
        radar_check.grid(row=1, column=0, sticky="w")
        self._add_tooltip(radar_check, ENEMY_RADAR_BUDGET_TOOLTIP)

        single = tk.LabelFrame(outer, text="Single Level", padx=8, pady=8)
        single.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        single.columnconfigure(1, weight=1)

        tk.Label(single, text="Mode:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        single_mode = ttk.Combobox(
            single,
            textvariable=self.generator3_single_mode_var,
            values=list(GENERATOR3_MODES),
            state="readonly",
            width=12,
        )
        single_mode.grid(row=0, column=1, sticky="w", pady=2)
        self._add_tooltip(single_mode, GENERATOR3_MODE_TOOLTIP)

        tk.Label(single, text="Campaign profile (rosters):", anchor="w").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=2
        )
        ttk.Combobox(
            single,
            textvariable=self.generator3_single_profile_var,
            values=list(GENERATOR3_CAMPAIGN_PROFILES),
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(single, text="Skeleton (remix, optional e.g. L1515):", anchor="w").grid(
            row=2, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(single, textvariable=self.generator3_skeleton_var, width=18).grid(row=2, column=1, sticky="w", pady=2)

        tk.Label(single, text="Seed (blank for random):", anchor="w").grid(
            row=3, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(single, textvariable=self.generator3_seed_var, width=18).grid(row=3, column=1, sticky="w", pady=2)

        self._path_row(
            single,
            2,
            "Single level output file:",
            self.generator3_single_file_var,
            self._browse_generator3_single_file,
        )
        tk.Button(single, text="Generate Single Level", command=self._make_generator3_single).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        campaign = tk.LabelFrame(outer, text="Campaign", padx=8, pady=8)
        campaign.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        campaign.columnconfigure(1, weight=1)

        tk.Label(campaign, text="Mode:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        campaign_mode = ttk.Combobox(
            campaign,
            textvariable=self.generator3_campaign_mode_var,
            values=list(GENERATOR3_MODES),
            state="readonly",
            width=12,
        )
        campaign_mode.grid(row=0, column=1, sticky="w", pady=2)
        self._add_tooltip(campaign_mode, GENERATOR3_MODE_TOOLTIP)

        tk.Label(campaign, text="Campaign profile:", anchor="w").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=2
        )
        ttk.Combobox(
            campaign,
            textvariable=self.generator3_campaign_profile_var,
            values=list(GENERATOR3_CAMPAIGN_PROFILES),
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(campaign, text="Seed (blank for random):", anchor="w").grid(
            row=2, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(campaign, textvariable=self.generator3_campaign_seed_var, width=18).grid(
            row=2, column=1, sticky="w", pady=2
        )
        self._path_row(
            campaign,
            2,
            "Campaign output folder:",
            self.generator3_campaign_dir_var,
            self._browse_generator3_campaign_dir,
        )
        tk.Button(campaign, text="Generate Campaign", command=self._make_generator3_campaign).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_generator4_tab(self, outer: tk.Frame) -> None:
        outer.columnconfigure(0, weight=1)

        intro = tk.Label(
            outer,
            text="Generator4 synthesizes new maps constrained by authored campaign progression.",
            justify="left",
            anchor="w",
        )
        intro.grid(row=0, column=0, sticky="ew")

        options = tk.LabelFrame(outer, text="Options", padx=8, pady=8)
        options.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        tk.Checkbutton(
            options,
            text="Set enemy host station delays to 0",
            variable=self.generator4_zero_enemy_station_delays_var,
        ).grid(row=0, column=0, sticky="w")
        radar_check = tk.Checkbutton(
            options,
            text="Disable enemy radar budgets",
            variable=self.generator4_zero_enemy_radar_budgets_var,
        )
        radar_check.grid(row=1, column=0, sticky="w")
        self._add_tooltip(radar_check, ENEMY_RADAR_BUDGET_TOOLTIP)

        single = tk.LabelFrame(outer, text="Single Level", padx=8, pady=8)
        single.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        single.columnconfigure(1, weight=1)

        tk.Label(single, text="Campaign profile:", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=2
        )
        ttk.Combobox(
            single,
            textvariable=self.generator4_single_profile_var,
            values=list(GENERATOR4_CAMPAIGN_PROFILES),
            state="readonly",
            width=16,
        ).grid(row=0, column=1, sticky="w", pady=2)

        tk.Label(single, text="Level ID (blank for seeded):", anchor="w").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(single, textvariable=self.generator4_level_id_var, width=18).grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(single, text="Seed (blank for random):", anchor="w").grid(
            row=2, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(single, textvariable=self.generator4_seed_var, width=18).grid(row=2, column=1, sticky="w", pady=2)

        self._path_row(
            single,
            3,
            "Single level output file:",
            self.generator4_single_file_var,
            self._browse_generator4_single_file,
        )
        tk.Button(single, text="Generate Single Level", command=self._make_generator4_single).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        campaign = tk.LabelFrame(outer, text="Campaign", padx=8, pady=8)
        campaign.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        campaign.columnconfigure(1, weight=1)

        tk.Label(campaign, text="Campaign profile:", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=2
        )
        ttk.Combobox(
            campaign,
            textvariable=self.generator4_campaign_profile_var,
            values=list(GENERATOR4_CAMPAIGN_PROFILES),
            state="readonly",
            width=16,
        ).grid(row=0, column=1, sticky="w", pady=2)

        tk.Label(campaign, text="Seed (blank for random):", anchor="w").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=2
        )
        tk.Entry(campaign, textvariable=self.generator4_campaign_seed_var, width=18).grid(
            row=1, column=1, sticky="w", pady=2
        )
        self._path_row(
            campaign,
            2,
            "Campaign output folder:",
            self.generator4_campaign_dir_var,
            self._browse_generator4_campaign_dir,
        )
        tk.Button(campaign, text="Generate Campaign", command=self._make_generator4_campaign).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0)
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

    def _add_tooltip(self, widget: tk.Widget, text: str) -> None:
        self.tooltips.append(ToolTip(widget, text))

    def _make_random_single(self) -> None:
        target = self._ensure_file_path(self.random_file_var, "Select single level output file")
        if target is None:
            return
        self._generate_single(
            target,
            seed=0,
            difficulty=5,
            skill=0,
            improved=True,
            zero_enemy_radar_budgets=self.generator1_zero_enemy_radar_budgets_var.get(),
        )

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
        self._generate_single(
            target,
            seed=0,
            difficulty=5,
            skill=skill,
            improved=True,
            zero_enemy_radar_budgets=self.generator1_zero_enemy_radar_budgets_var.get(),
        )

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
        self._generate_single(
            target,
            seed=seed,
            difficulty=5,
            skill=0,
            improved=True,
            zero_enemy_radar_budgets=self.generator1_zero_enemy_radar_budgets_var.get(),
        )

    def _make_custom_single(self) -> None:
        options = CustomWizardDialog(
            self.root,
            allow_new_buildings=self.building_scripts_var.get(),
        ).run()
        if options is None:
            return
        options.zero_enemy_radar_budgets = self.generator1_zero_enemy_radar_budgets_var.get()
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
        campaign_profile = self.generator1_campaign_profile_var.get().strip() or "original"
        self._generate_campaign(
            directory,
            seed=seed,
            campaign_profile=campaign_profile,
            zero_enemy_radar_budgets=self.generator1_zero_enemy_radar_budgets_var.get(),
        )

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
        self._generate_generator2_single(
            target,
            seed=seed,
            level_id=level_id,
            zero_enemy_station_delays=self.generator2_zero_enemy_station_delays_var.get(),
            zero_enemy_radar_budgets=self.generator2_zero_enemy_radar_budgets_var.get(),
        )

    def _make_generator2_campaign(self) -> None:
        seed = self._parse_optional_seed_entry(self.generator2_campaign_seed_var, "Generator2 Campaign")
        if seed is None:
            return
        directory = self._ensure_directory_path(self.generator2_campaign_dir_var, "Select Generator2 campaign output folder")
        if directory is None:
            return
        campaign_profile = self.generator2_campaign_profile_var.get().strip() or "original"
        self._generate_generator2_campaign(
            directory,
            seed=seed,
            campaign_profile=campaign_profile,
            zero_enemy_station_delays=self.generator2_zero_enemy_station_delays_var.get(),
            zero_enemy_radar_budgets=self.generator2_zero_enemy_radar_budgets_var.get(),
        )

    def _generate_single(
        self,
        target: Path,
        seed: int,
        difficulty: int,
        skill: int,
        improved: bool,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating level...",
            failure_status="Generation failed.",
            error_title="Generation Failed",
            success_title="Level Created",
            action=lambda: generate_generator1_single(
                target,
                seed=seed,
                difficulty=difficulty,
                skill=skill,
                improved=improved,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
            ),
            success_status=lambda result: f"Wrote {result.written}",
            success_lines=self._level_created_lines,
        )

    def _generate_custom(self, target: Path, options: Generator1CustomOptions) -> None:
        self._run_generation_workflow(
            start_status="Generating custom level...",
            failure_status="Custom generation failed.",
            error_title="Generation Failed",
            success_title="Level Created",
            action=lambda: generate_generator1_custom(target, options),
            success_status=lambda result: f"Wrote {result.written}",
            success_lines=self._level_created_lines,
        )

    def _generate_campaign(
        self,
        directory: Path,
        seed: int,
        campaign_profile: str,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating campaign...",
            failure_status="Campaign generation failed.",
            error_title="Campaign Generation Failed",
            success_title="Campaign Created",
            action=lambda: generate_generator1_campaign(
                directory,
                seed=seed,
                campaign_profile=campaign_profile,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
            ),
            success_status=lambda result: f"Wrote {len(result.written)} campaign levels.",
            success_lines=lambda result: self._campaign_created_lines(result, "Generator1"),
        )

    def _generate_generator2_single(
        self,
        target: Path,
        seed: int,
        level_id: int,
        zero_enemy_station_delays: bool,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating Generator2 level...",
            failure_status="Generator2 generation failed.",
            error_title="Generation Failed",
            success_title="Generator2 Level Created",
            action=lambda: generate_generator2_single(
                target,
                seed=seed,
                level_id=level_id,
                zero_enemy_station_delays=zero_enemy_station_delays,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
            ),
            success_status=lambda result: f"Wrote {result.written}",
            success_lines=self._generator2_level_created_lines,
        )

    def _generate_generator2_campaign(
        self,
        directory: Path,
        seed: int,
        campaign_profile: str,
        zero_enemy_station_delays: bool,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating Generator2 campaign...",
            failure_status="Generator2 campaign generation failed.",
            error_title="Campaign Generation Failed",
            success_title="Generator2 Campaign Created",
            action=lambda: generate_generator2_campaign(
                directory,
                seed=seed,
                campaign_profile=campaign_profile,
                zero_enemy_station_delays=zero_enemy_station_delays,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
            ),
            success_status=lambda result: f"Wrote {len(result.written)} Generator2 campaign levels.",
            success_lines=lambda result: self._campaign_created_lines(result, "Generator2"),
        )

    def _make_generator3_single(self) -> None:
        seed = self._parse_optional_seed_entry(self.generator3_seed_var, "Generator3 Single Level")
        if seed is None:
            return
        target = self._ensure_file_path(
            self.generator3_single_file_var,
            "Select Generator3 single level output file",
        )
        if target is None:
            return
        self._generate_generator3_single(
            target,
            seed=seed,
            campaign_profile=self.generator3_single_profile_var.get().strip() or "original",
            mode=self.generator3_single_mode_var.get().strip() or "remix",
            skeleton=self.generator3_skeleton_var.get().strip() or None,
            zero_enemy_station_delays=self.generator3_zero_enemy_station_delays_var.get(),
            zero_enemy_radar_budgets=self.generator3_zero_enemy_radar_budgets_var.get(),
        )

    def _make_generator3_campaign(self) -> None:
        seed = self._parse_optional_seed_entry(self.generator3_campaign_seed_var, "Generator3 Campaign")
        if seed is None:
            return
        directory = self._ensure_directory_path(
            self.generator3_campaign_dir_var, "Select Generator3 campaign output folder"
        )
        if directory is None:
            return
        self._generate_generator3_campaign(
            directory,
            seed=seed,
            campaign_profile=self.generator3_campaign_profile_var.get().strip() or "original",
            mode=self.generator3_campaign_mode_var.get().strip() or "remix",
            zero_enemy_station_delays=self.generator3_zero_enemy_station_delays_var.get(),
            zero_enemy_radar_budgets=self.generator3_zero_enemy_radar_budgets_var.get(),
        )

    def _generate_generator3_single(
        self,
        target: Path,
        *,
        seed: int,
        campaign_profile: str,
        mode: str,
        skeleton: str | None,
        zero_enemy_station_delays: bool,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating Generator3 level...",
            failure_status="Generator3 generation failed.",
            error_title="Generation Failed",
            success_title="Generator3 Level Created",
            action=lambda: generate_generator3_single(
                target,
                seed=seed,
                campaign_profile=campaign_profile,
                mode=mode,
                skeleton=skeleton,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
                zero_enemy_station_delays=zero_enemy_station_delays,
            ),
            success_status=lambda result: f"Wrote {result.written}",
            success_lines=self._generator3_level_created_lines,
        )

    def _generate_generator3_campaign(
        self,
        directory: Path,
        *,
        seed: int,
        campaign_profile: str,
        mode: str,
        zero_enemy_station_delays: bool,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating Generator3 campaign...",
            failure_status="Generator3 campaign generation failed.",
            error_title="Campaign Generation Failed",
            success_title="Generator3 Campaign Created",
            action=lambda: generate_generator3_campaign(
                directory,
                seed=seed,
                campaign_profile=campaign_profile,
                mode=mode,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
                zero_enemy_station_delays=zero_enemy_station_delays,
            ),
            success_status=lambda result: f"Wrote {len(result.written)} Generator3 campaign levels.",
            success_lines=lambda result: self._campaign_created_lines(result, "Generator3"),
        )

    def _make_generator4_single(self) -> None:
        seed = self._parse_optional_seed_entry(self.generator4_seed_var, "Generator4 Single Level")
        if seed is None:
            return
        level_id = self._parse_optional_level_id_entry(self.generator4_level_id_var, "Generator4 Single Level")
        if level_id is None and self.generator4_level_id_var.get().strip():
            return
        target = self._ensure_file_path(
            self.generator4_single_file_var,
            "Select Generator4 single level output file",
        )
        if target is None:
            return
        self._generate_generator4_single(
            target,
            seed=seed,
            campaign_profile=self.generator4_single_profile_var.get().strip() or "original",
            level_id=level_id,
            zero_enemy_station_delays=self.generator4_zero_enemy_station_delays_var.get(),
            zero_enemy_radar_budgets=self.generator4_zero_enemy_radar_budgets_var.get(),
        )

    def _make_generator4_campaign(self) -> None:
        seed = self._parse_optional_seed_entry(self.generator4_campaign_seed_var, "Generator4 Campaign")
        if seed is None:
            return
        directory = self._ensure_directory_path(
            self.generator4_campaign_dir_var, "Select Generator4 campaign output folder"
        )
        if directory is None:
            return
        self._generate_generator4_campaign(
            directory,
            seed=seed,
            campaign_profile=self.generator4_campaign_profile_var.get().strip() or "original",
            zero_enemy_station_delays=self.generator4_zero_enemy_station_delays_var.get(),
            zero_enemy_radar_budgets=self.generator4_zero_enemy_radar_budgets_var.get(),
        )

    def _generate_generator4_single(
        self,
        target: Path,
        *,
        seed: int,
        campaign_profile: str,
        level_id: int | None,
        zero_enemy_station_delays: bool,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating Generator4 level...",
            failure_status="Generator4 generation failed.",
            error_title="Generation Failed",
            success_title="Generator4 Level Created",
            action=lambda: generate_generator4_single(
                target,
                seed=seed,
                campaign_profile=campaign_profile,
                level_id=level_id,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
                zero_enemy_station_delays=zero_enemy_station_delays,
            ),
            success_status=lambda result: f"Wrote {result.written}",
            success_lines=self._generator4_level_created_lines,
        )

    def _generate_generator4_campaign(
        self,
        directory: Path,
        *,
        seed: int,
        campaign_profile: str,
        zero_enemy_station_delays: bool,
        zero_enemy_radar_budgets: bool,
    ) -> None:
        self._run_generation_workflow(
            start_status="Generating Generator4 campaign...",
            failure_status="Generator4 campaign generation failed.",
            error_title="Campaign Generation Failed",
            success_title="Generator4 Campaign Created",
            action=lambda: generate_generator4_campaign(
                directory,
                seed=seed,
                campaign_profile=campaign_profile,
                zero_enemy_radar_budgets=zero_enemy_radar_budgets,
                zero_enemy_station_delays=zero_enemy_station_delays,
            ),
            success_status=lambda result: f"Wrote {len(result.written)} Generator4 campaign levels.",
            success_lines=lambda result: self._campaign_created_lines(result, "Generator4"),
        )

    def _generator3_level_created_lines(self, result: LevelGenerationResult) -> list[str]:
        level = result.level
        metadata = level.metadata
        origin = metadata.get("skeleton") or f"synthesized ({metadata.get('synth_method')})"
        lines = [
            f"Wrote {result.written}",
            f"Mode: {metadata.get('mode')}",
            f"Source: {origin}",
            f"Seed: {level.seed}",
            f"Map: {level.width}x{level.height}",
            f"Tileset: {level.tileset}",
        ]
        if result.backup_path is not None:
            lines.append(f"Backup: {result.backup_path}")
        return lines

    def _generator4_level_created_lines(self, result: LevelGenerationResult) -> list[str]:
        level = result.level
        metadata = level.metadata
        lines = [
            f"Wrote {result.written}",
            f"Archetype: {metadata.get('level_archetype')} ({metadata.get('source')})",
            f"Synthesis: {metadata.get('synth_method')}",
            f"Seed: {level.seed}",
            f"Map: {level.width}x{level.height}",
            f"Tileset: {level.tileset}",
            f"Warnings: {len(metadata.get('warnings', []))}",
        ]
        if result.backup_path is not None:
            lines.append(f"Backup: {result.backup_path}")
        return lines

    def _browse_generator3_single_file(self) -> None:
        path = self._ask_save_file(
            "Select Generator3 single level output file",
            self.generator3_single_file_var.get(),
            "level_01.ldf",
        )
        if path is not None:
            self.generator3_single_file_var.set(str(path))

    def _browse_generator3_campaign_dir(self) -> None:
        path = self._ask_directory("Select Generator3 campaign output folder", self.generator3_campaign_dir_var.get())
        if path is not None:
            self.generator3_campaign_dir_var.set(str(path))

    def _browse_generator4_single_file(self) -> None:
        path = self._ask_save_file(
            "Select Generator4 single level output file",
            self.generator4_single_file_var.get(),
            "level_01.ldf",
        )
        if path is not None:
            self.generator4_single_file_var.set(str(path))

    def _browse_generator4_campaign_dir(self) -> None:
        path = self._ask_directory("Select Generator4 campaign output folder", self.generator4_campaign_dir_var.get())
        if path is not None:
            self.generator4_campaign_dir_var.set(str(path))

    def _create_backup(self) -> None:
        result = create_configured_backups(
            (
                self.random_file_var.get(),
                self.custom_file_var.get(),
                self.generator2_single_file_var.get(),
                self.generator3_single_file_var.get(),
                self.generator4_single_file_var.get(),
            ),
            (
                self.campaign_dir_var.get(),
                self.generator2_campaign_dir_var.get(),
                self.generator3_campaign_dir_var.get(),
                self.generator4_campaign_dir_var.get(),
            ),
        )
        if not result.created:
            self._set_status("No existing generated files found to back up.")
            messagebox.showinfo("Create Backup", "No existing generated files found to back up.", parent=self.root)
            return
        self._set_status(f"Created backup for {len(result.created)} item(s).")
        messagebox.showinfo("Create Backup", "Backup created.", parent=self.root)

    def _run_generation_workflow(
        self,
        *,
        start_status: str,
        failure_status: str,
        error_title: str,
        success_title: str,
        action: Callable[[], WorkflowResult],
        success_status: Callable[[WorkflowResult], str],
        success_lines: Callable[[WorkflowResult], list[str]],
    ) -> None:
        try:
            self._set_status(start_status)
            result = action()
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status(failure_status)
            messagebox.showerror(error_title, str(exc), parent=self.root)
            return

        self._set_status(success_status(result))
        messagebox.showinfo(success_title, "\n".join(success_lines(result)), parent=self.root)

    def _level_created_lines(self, result: LevelGenerationResult) -> list[str]:
        level = result.level
        lines = [
            f"Wrote {result.written}",
            f"Seed: {level.seed}",
            f"Map: {level.width}x{level.height}",
            f"Tileset: {level.tileset}",
        ]
        if result.backup_path is not None:
            lines.append(f"Backup: {result.backup_path}")
        return lines

    def _generator2_level_created_lines(self, result: LevelGenerationResult) -> list[str]:
        level = result.level
        lines = [
            f"Wrote {result.written}",
            f"Level ID: {level.level_id}",
            f"Seed: {level.seed}",
            f"Map: {level.width}x{level.height}",
            f"Tileset: {level.tileset}",
        ]
        if result.backup_path is not None:
            lines.append(f"Backup: {result.backup_path}")
        return lines

    def _campaign_created_lines(self, result: CampaignGenerationResult, generator_name: str) -> list[str]:
        lines = [
            f"Wrote {len(result.written)} {generator_name} levels to {result.directory}",
            f"Seed: {result.campaign.seed}",
            f"Profile: {result.campaign_profile}",
        ]
        if result.backup_dir is not None:
            lines.append(f"Backed up {len(result.moved)} existing LDF files to {result.backup_dir}")
        return lines

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

    def _parse_optional_level_id_entry(self, variable: tk.StringVar, title: str) -> int | None:
        value = variable.get().strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            messagebox.showerror(title, "Level ID must be a whole number.", parent=self.root)
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
            generator1_zero_enemy_radar_budgets=self.generator1_zero_enemy_radar_budgets_var.get(),
            generator2_single_level_file=self.generator2_single_file_var.get().strip(),
            generator2_campaign_directory=self.generator2_campaign_dir_var.get().strip(),
            generator2_zero_enemy_station_delays=self.generator2_zero_enemy_station_delays_var.get(),
            generator2_zero_enemy_radar_budgets=self.generator2_zero_enemy_radar_budgets_var.get(),
            generator3_single_level_file=self.generator3_single_file_var.get().strip(),
            generator3_campaign_directory=self.generator3_campaign_dir_var.get().strip(),
            generator3_zero_enemy_station_delays=self.generator3_zero_enemy_station_delays_var.get(),
            generator3_zero_enemy_radar_budgets=self.generator3_zero_enemy_radar_budgets_var.get(),
            generator4_single_level_file=self.generator4_single_file_var.get().strip(),
            generator4_campaign_directory=self.generator4_campaign_dir_var.get().strip(),
            generator4_zero_enemy_station_delays=self.generator4_zero_enemy_station_delays_var.get(),
            generator4_zero_enemy_radar_budgets=self.generator4_zero_enemy_radar_budgets_var.get(),
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
            "Generator2 legacy/PHP generator: GitHub user dportalesr.\n"
            "Python reimplementation: Ydro.",
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
