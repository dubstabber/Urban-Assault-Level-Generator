# Urban Assault Level Generator

Python reimplementation of the selected legacy Urban Assault generators.

Implemented targets:

- `generator1`: Random UA-derived terrain and campaign generator, defaulting to the improved recovered behavior.
- `generator2`: PHP-derived.

Compatibility policy:

- `generator1` defaults to improved playable output. Use `--strict-parity` to disable the improved tileset filtering path where supported.
- `generator2` follows the PHP legacy `SET_LIST` terrain allowlists instead of the broader shared tileset compatibility table.

## Credits

- Python reimplementation: Ydro.
- Generator2 legacy/PHP generator: GitHub user `dportalesr`.
- Original Random UA.exe: Daniel L. Orlando.

## License

This project is licensed under GPL-3.0-or-later. See [LICENSE](LICENSE).

## Requirements

- Python 3.11 or newer.
- No third-party Python packages are required for normal CLI or GUI use.
- The GUI uses Python's standard `tkinter` module. Windows and python.org macOS installers usually include it. On Linux, install your distribution's Tk package if needed, for example `python3-tk` on Debian/Ubuntu.

## Usage

```powershell
$env:PYTHONPATH = "src"
python -m ualg.cli gen1 single --seed 12345 --output out/L0101.ldf
python -m ualg.cli gen1 campaign --seed 12345 --output-dir out/gen1
python -m ualg.cli gen2 single --seed 12345 --level-id 1 --output out/L0101.ldf
python -m ualg.cli gen2 campaign --seed 12345 --output-dir out/gen2
```

When installed as a package, the CLI command is `ualg`.

Full references:

- [CLI options](docs/cli.md)
- [Backend API](docs/api.md)
- [Backend architecture](docs/architecture.md)

For Generator2, add `--zero-enemy-station-delays` to set all enemy host station `*_delay` values to `0`.

Launch the GUI:

```powershell
$env:PYTHONPATH = "src"
python -m ualg.gui
```

When installed as a package, the GUI command is `ualg-gui`. The GUI includes tabs for Generator1 and Generator2 generation workflows.

Double-click launchers:

- Windows: `launch-gui.cmd`
- Linux: `launch-gui.sh`

On Linux, make the launcher executable once:

```sh
chmod +x launch-gui.sh
```

Run tests:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s tests
```
