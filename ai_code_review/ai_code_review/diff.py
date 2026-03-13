from __future__ import annotations

import os

from dataclasses import dataclass, field

from unidiff import PatchSet


MAX_DIFF_LENGTH = int(os.environ.get('AI_REVIEW_MAX_DIFF_LENGTH', '60000'))


@dataclass
class DiffFile:
    added: set[int] = field(default_factory=set)
    lines: set[int] = field(default_factory=set)
    path: str = ''
    text: str = ''


@dataclass
class DiffSet:
    files: dict[str, DiffFile] = field(default_factory=dict)

    @property
    def added(self) -> dict[str, set[int]]:
        return {
            path: entry.added
            for path, entry in self.files.items()
        }

    @property
    def line_map(self) -> dict[str, set[int]]:
        return {
            path: entry.lines
            for path, entry in self.files.items()
        }

    @property
    def paths(self) -> list[str]:
        return list(self.files.keys())

    def filter_by_extension(
        self,
        extensions: tuple[str, ...],
        max_length: int = MAX_DIFF_LENGTH,
    ) -> str:
        sections = [
            entry.text
            for path, entry in sorted(self.files.items())
            if path.endswith(extensions)
        ]

        filtered = ''.join(sections)

        if len(filtered) > max_length:
            return (
                filtered[:max_length]
                + '\n\n... (diff truncated due to size)'
            )

        return filtered

    def has_extension(self, extensions: tuple[str, ...]) -> bool:
        return any(
            path.endswith(extensions)
            for path in self.files
        )

    @classmethod
    def from_patch(cls, text: str) -> DiffSet:
        files: dict[str, DiffFile] = {}
        patch = PatchSet(text)

        for patched in patch:
            entry = DiffFile(
                path=patched.path,
                text=str(patched),
            )

            for hunk in patched:
                for line in hunk:
                    if line.is_added:
                        entry.added.add(line.target_line_no)

                    if line.is_added or line.is_context:
                        entry.lines.add(line.target_line_no)

            files[patched.path] = entry

        return cls(files=files)
