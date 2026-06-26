"""Main Tkinter application shell for the Urban Assault generators."""

from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..constants import (
    GENERATOR1_CAMPAIGN_PROFILES,
    GENERATOR2_CAMPAIGN_PROFILES,
    GENERATOR2_LEVELS,
    level_filename,
)
from ..generator1 import Generator1, Generator1CustomOptions
from ..generator2 import Generator2
from ..legacy_resources import LegacyDialog
from .backups import backup_campaign_ldfs, backup_existing_file
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


APP_TITLE = "Urban Assault Level Generator"


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
        self.generator2_single_file_var = tk.StringVar(value=settings.generator2_single_level_file)
        self.generator2_campaign_dir_var = tk.StringVar(value=settings.generator2_campaign_directory)
        self.generator2_level_id_var = tk.StringVar(value="1")
        self.generator2_seed_var = tk.StringVar(value="")
        self.generator2_campaign_seed_var = tk.StringVar(value="")
        self.generator2_campaign_profile_var = tk.StringVar(value="original")
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
        tk.Button(menu, text="Create a WHOLE CAMPAIGN", command=self._make_campaign).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=2
        )
        tk.Button(menu, text="Credits", command=self._show_credits).grid(row=5, column=0, sticky="ew", padx=(0, 2), pady=2)
        tk.Button(menu, text="Read The License Agreement", command=self._show_license).grid(
            row=5, column=1, sticky="ew", padx=(2, 0), pady=2
        )
        tk.Button(menu, text="Create Backup", command=self._create_backup).grid(
            row=6, column=0, sticky="ew", padx=(0, 2), pady=2
        )
        tk.Button(menu, text="Exit", command=self._exit).grid(row=6, column=1, sticky="ew", padx=(2, 0), pady=2)

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
        campaign_profile = self.generator1_campaign_profile_var.get().strip() or "original"
        self._generate_campaign(directory, seed=seed, campaign_profile=campaign_profile)

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
        campaign_profile = self.generator2_campaign_profile_var.get().strip() or "original"
        self._generate_generator2_campaign(directory, seed=seed, campaign_profile=campaign_profile)

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

    def _generate_campaign(self, directory: Path, seed: int, campaign_profile: str) -> None:
        try:
            self._set_status("Generating campaign...")
            backup_dir, moved = backup_campaign_ldfs(directory)
            campaign = Generator1().generate_campaign(
                seed=seed,
                difficulty=5,
                improved=True,
                campaign_profile=campaign_profile,
            )
            written = campaign.write(directory)
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status("Campaign generation failed.")
            messagebox.showerror("Campaign Generation Failed", str(exc), parent=self.root)
            return

        lines = [
            f"Wrote {len(written)} Generator1 levels to {directory}",
            f"Seed: {campaign.seed}",
            f"Profile: {campaign_profile}",
        ]
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

    def _generate_generator2_campaign(self, directory: Path, seed: int, campaign_profile: str) -> None:
        try:
            self._set_status("Generating Generator2 campaign...")
            backup_dir, moved = backup_campaign_ldfs(directory)
            campaign = Generator2().generate_campaign(seed=seed, campaign_profile=campaign_profile)
            written = campaign.write(directory)
            self._save_settings_quiet()
        except Exception as exc:
            self._set_status("Generator2 campaign generation failed.")
            messagebox.showerror("Campaign Generation Failed", str(exc), parent=self.root)
            return

        lines = [
            f"Wrote {len(written)} Generator2 levels to {directory}",
            f"Seed: {campaign.seed}",
            f"Profile: {campaign_profile}",
        ]
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
