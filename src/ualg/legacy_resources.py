"""Read legacy Random UA dialog resources from the original PE executable."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


RT_DIALOG = 5
RT_STRING = 6
PE_RESOURCE_DIRECTORY_INDEX = 2
IDC_STATIC = 65535
LICENSE_TEXT_MARKER = b"AOE_Danny's Random Urban Assault Level Generator BETA version 0.01 License Agreement."


@dataclass(frozen=True, slots=True)
class LegacyControl:
    control_id: int
    class_name: str | None
    text: str | None
    x: int
    y: int
    width: int
    height: int
    style: int
    ex_style: int

    @property
    def is_checkbox(self) -> bool:
        return self.class_name == "BUTTON" and self.style & 0xF == 3

    @property
    def is_groupbox(self) -> bool:
        return self.class_name == "BUTTON" and self.style & 0xF == 7

    @property
    def disabled(self) -> bool:
        return bool(self.style & 0x08000000)


@dataclass(frozen=True, slots=True)
class LegacyDialog:
    resource_id: int
    title: str
    x: int
    y: int
    width: int
    height: int
    controls: tuple[LegacyControl, ...] = field(default_factory=tuple)


class LegacyResourceError(RuntimeError):
    pass


class LegacyResourceReader:
    def __init__(self, exe_path: str | Path) -> None:
        self.exe_path = Path(exe_path)
        self.data = self.exe_path.read_bytes()
        self.sections = self._read_sections()
        self.resource_rva = self._resource_directory_rva()
        self.resource_offset = self._rva_to_offset(self.resource_rva)

    def dialogs(self) -> dict[int, LegacyDialog]:
        result: dict[int, LegacyDialog] = {}
        for resource_type, resource_id, _lang, offset, _size in self._resource_items():
            if resource_type == RT_DIALOG:
                dialog = self._parse_dialog(resource_id, offset)
                result[dialog.resource_id] = dialog
        return result

    def strings(self) -> dict[int, str]:
        result: dict[int, str] = {}
        for resource_type, resource_id, _lang, offset, _size in self._resource_items():
            if resource_type != RT_STRING:
                continue
            cursor = offset
            for index in range(16):
                length = self._u16(cursor)
                cursor += 2
                if length:
                    result[(resource_id - 1) * 16 + index] = self.data[cursor:cursor + length * 2].decode(
                        "utf-16le", "replace"
                    )
                cursor += length * 2
        return result

    def license_text(self) -> str:
        start = self.data.find(LICENSE_TEXT_MARKER)
        if start < 0:
            return ""
        end = self.data.find(b"\0", start)
        if end < 0:
            end = len(self.data)
        return self.data[start:end].decode("ascii", "replace").replace("\r\n", "\n")

    def _read_sections(self) -> list[tuple[int, int, int, int]]:
        pe_offset = self._u32(0x3C)
        if self.data[pe_offset:pe_offset + 4] != b"PE\0\0":
            raise LegacyResourceError(f"not a PE file: {self.exe_path}")
        section_count = self._u16(pe_offset + 6)
        optional_size = self._u16(pe_offset + 20)
        section_offset = pe_offset + 24 + optional_size
        sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            offset = section_offset + index * 40
            virtual_size = self._u32(offset + 8)
            virtual_address = self._u32(offset + 12)
            raw_size = self._u32(offset + 16)
            raw_pointer = self._u32(offset + 20)
            sections.append((virtual_address, virtual_size, raw_pointer, raw_size))
        return sections

    def _resource_directory_rva(self) -> int:
        pe_offset = self._u32(0x3C)
        optional_offset = pe_offset + 24
        magic = self._u16(optional_offset)
        if magic != 0x10B:
            raise LegacyResourceError("only PE32 resources are supported")
        return self._u32(optional_offset + 96 + PE_RESOURCE_DIRECTORY_INDEX * 8)

    def _resource_items(self) -> list[tuple[int, int, int, int, int]]:
        items: list[tuple[int, int, int, int, int]] = []
        for resource_type, is_type_dir, type_offset in self._parse_resource_dir(0):
            if not is_type_dir:
                continue
            for resource_id, is_name_dir, name_offset in self._parse_resource_dir(type_offset):
                if not is_name_dir:
                    continue
                for language, is_lang_dir, data_offset in self._parse_resource_dir(name_offset):
                    if is_lang_dir:
                        continue
                    entry_offset = self.resource_offset + data_offset
                    rva = self._u32(entry_offset)
                    size = self._u32(entry_offset + 4)
                    items.append((resource_type, resource_id, language, self._rva_to_offset(rva), size))
        return items

    def _parse_resource_dir(self, relative_offset: int) -> list[tuple[int, bool, int]]:
        offset = self.resource_offset + relative_offset
        count = self._u16(offset + 12) + self._u16(offset + 14)
        cursor = offset + 16
        result: list[tuple[int, bool, int]] = []
        for _ in range(count):
            raw_name = self._u32(cursor)
            raw_offset = self._u32(cursor + 4)
            cursor += 8
            if raw_name & 0x80000000:
                name = raw_name & 0x7FFFFFFF
            else:
                name = raw_name
            result.append((name, bool(raw_offset & 0x80000000), raw_offset & 0x7FFFFFFF))
        return result

    def _parse_dialog(self, resource_id: int, offset: int) -> LegacyDialog:
        first = self._u16(offset)
        second = self._u16(offset + 2)
        if first == 1 and second == 0xFFFF:
            return self._parse_dialog_ex(resource_id, offset)
        return self._parse_dialog_standard(resource_id, offset)

    def _parse_dialog_standard(self, resource_id: int, offset: int) -> LegacyDialog:
        style = self._u32(offset)
        control_count = self._u16(offset + 8)
        x, y, width, height = self._s16(offset + 10), self._s16(offset + 12), self._s16(offset + 14), self._s16(offset + 16)
        cursor = offset + 18
        _, cursor = self._read_resource_name(cursor)
        _, cursor = self._read_resource_name(cursor)
        title, cursor = self._read_utf16z(cursor)
        if style & 0x40:
            cursor += 2
            _, cursor = self._read_utf16z(cursor)
        controls: list[LegacyControl] = []
        for _ in range(control_count):
            cursor = _align4(cursor)
            control_style = self._u32(cursor)
            control_ex_style = self._u32(cursor + 4)
            cx = self._s16(cursor + 8)
            cy = self._s16(cursor + 10)
            cwidth = self._s16(cursor + 12)
            cheight = self._s16(cursor + 14)
            control_id = self._u16(cursor + 16)
            cursor += 18
            class_name, cursor = self._read_control_class(cursor)
            text, cursor = self._read_resource_name(cursor)
            extra_size = self._u16(cursor)
            cursor += 2 + extra_size
            controls.append(LegacyControl(control_id, class_name, text, cx, cy, cwidth, cheight, control_style, control_ex_style))
        return LegacyDialog(resource_id, title, x, y, width, height, tuple(controls))

    def _parse_dialog_ex(self, resource_id: int, offset: int) -> LegacyDialog:
        style = self._u32(offset + 12)
        control_count = self._u16(offset + 16)
        x, y, width, height = self._s16(offset + 18), self._s16(offset + 20), self._s16(offset + 22), self._s16(offset + 24)
        cursor = offset + 26
        _, cursor = self._read_resource_name(cursor)
        _, cursor = self._read_resource_name(cursor)
        title, cursor = self._read_utf16z(cursor)
        if style & 0x40 or style & 0x48:
            cursor += 6
            _, cursor = self._read_utf16z(cursor)
        controls: list[LegacyControl] = []
        for _ in range(control_count):
            cursor = _align4(cursor)
            control_ex_style = self._u32(cursor + 4)
            control_style = self._u32(cursor + 8)
            cx = self._s16(cursor + 12)
            cy = self._s16(cursor + 14)
            cwidth = self._s16(cursor + 16)
            cheight = self._s16(cursor + 18)
            control_id = self._u32(cursor + 20)
            cursor += 24
            class_name, cursor = self._read_control_class(cursor)
            text, cursor = self._read_resource_name(cursor)
            extra_size = self._u16(cursor)
            cursor += 2 + extra_size
            controls.append(LegacyControl(control_id, class_name, text, cx, cy, cwidth, cheight, control_style, control_ex_style))
        return LegacyDialog(resource_id, title, x, y, width, height, tuple(controls))

    def _read_control_class(self, offset: int) -> tuple[str | None, int]:
        value, next_offset = self._read_resource_name(offset)
        if value is None:
            return None, next_offset
        if value.startswith("#"):
            return {
                0x80: "BUTTON",
                0x81: "EDIT",
                0x82: "STATIC",
                0x83: "LISTBOX",
                0x84: "SCROLLBAR",
                0x85: "COMBOBOX",
            }.get(int(value[1:]), value), next_offset
        return value, next_offset

    def _read_resource_name(self, offset: int) -> tuple[str | None, int]:
        value = self._u16(offset)
        if value == 0:
            return None, offset + 2
        if value == 0xFFFF:
            return f"#{self._u16(offset + 2)}", offset + 4
        return self._read_utf16z(offset)

    def _read_utf16z(self, offset: int) -> tuple[str, int]:
        chars: list[int] = []
        while True:
            value = self._u16(offset)
            offset += 2
            if value == 0:
                return "".join(chr(char) for char in chars), offset
            chars.append(value)

    def _rva_to_offset(self, rva: int) -> int:
        for virtual_address, virtual_size, raw_pointer, raw_size in self.sections:
            if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
                return raw_pointer + rva - virtual_address
        raise LegacyResourceError(f"could not map RVA 0x{rva:x}")

    def _u16(self, offset: int) -> int:
        return struct.unpack_from("<H", self.data, offset)[0]

    def _s16(self, offset: int) -> int:
        return struct.unpack_from("<h", self.data, offset)[0]

    def _u32(self, offset: int) -> int:
        return struct.unpack_from("<I", self.data, offset)[0]


@lru_cache(maxsize=4)
def load_dialogs(exe_path: str) -> dict[int, LegacyDialog]:
    return LegacyResourceReader(exe_path).dialogs()


@lru_cache(maxsize=4)
def load_license_text(exe_path: str) -> str:
    return LegacyResourceReader(exe_path).license_text()


def _align4(offset: int) -> int:
    return (offset + 3) & ~3
