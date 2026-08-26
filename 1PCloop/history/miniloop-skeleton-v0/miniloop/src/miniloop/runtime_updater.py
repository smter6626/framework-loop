"""Restricted Markdown Runtime mutations with mechanical invariants only."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


class RuntimeInvariantError(ValueError):
    pass


_HEADING = re.compile(r"^## ([^\n]+)$", re.MULTILINE)
_COMMIT = re.compile(r"^[0-9a-f]{7,64}$")
_TRAILING_SEPARATOR = re.compile(r"(\n+---[ \t]*\n*)\Z")


@dataclass
class _Section:
    name: str
    body: str


class _RuntimeDocument:
    def __init__(self, *, preamble: str, sections: List[_Section]) -> None:
        self.preamble = preamble
        self.sections = sections
        names = [section.name for section in sections]
        if len(names) != len(set(names)):
            raise RuntimeInvariantError("duplicate H2 sections are not supported")

    @classmethod
    def parse(cls, text: str) -> "_RuntimeDocument":
        matches = list(_HEADING.finditer(text))
        if not matches:
            raise RuntimeInvariantError("Runtime has no H2 sections")
        sections = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append(_Section(match.group(1), text[match.end() : end]))
        return cls(preamble=text[: matches[0].start()], sections=sections)

    def section(self, name: str) -> _Section:
        for section in self.sections:
            if section.name == name:
                return section
        raise RuntimeInvariantError(f"required Runtime section is missing: {name}")

    def render(self) -> str:
        return self.preamble + "".join(
            "## " + section.name + section.body for section in self.sections
        )


def runtime_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_separator(body: str) -> Tuple[str, str]:
    match = _TRAILING_SEPARATOR.search(body)
    if match:
        return body[: match.start()], match.group(1)
    return body, ""


def _append_entry(body: str, entry: str) -> str:
    content, separator = _split_separator(body)
    # Preserve every existing byte in the historical content, then append.
    updated = content + "\n\n" + entry.strip("\n") + "\n"
    if separator:
        updated += "\n---\n\n"
    else:
        updated += "\n"
    return updated


def _replace_body_preserving_separator(old_body: str, new_body: str) -> str:
    _, separator = _split_separator(old_body)
    result = "\n\n" + new_body.strip("\n") + "\n"
    if separator:
        result += "\n---\n\n"
    else:
        result += "\n"
    return result


def _without_separator(body: str) -> str:
    return _split_separator(body)[0]


def _validate_fragment(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeInvariantError(f"{field} must not be empty")
    if _HEADING.search(value):
        raise RuntimeInvariantError(f"{field} must not inject an H2 section")
    return value


def _validate_provenance(step: str, commit: str) -> None:
    if not step or "\n" in step or "\r" in step:
        raise RuntimeInvariantError("Step provenance must be a non-empty single line")
    if not _COMMIT.fullmatch(commit):
        raise RuntimeInvariantError("commit provenance must be a 7-64 digit lowercase hex id")


def _replace_exact_once(body: str, expected: str, replacement: str) -> str:
    occurrences = body.count(expected)
    if occurrences != 1:
        raise RuntimeInvariantError(
            f"pending target must occur exactly once; observed {occurrences} occurrences"
        )
    return body.replace(expected, replacement, 1)


class RuntimeUpdater:
    """No semantic judgement: each method performs one explicit mechanical operation."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()

    def digest(self) -> str:
        return runtime_sha256(self.path.read_text(encoding="utf-8"))

    def append_done(
        self,
        *,
        step: str,
        commit: str,
        body: str,
        expected_sha256: Optional[str] = None,
    ) -> str:
        _validate_provenance(step, commit)
        _validate_fragment(body, "Done body")
        entry = (
            f"### {step}\n\n{body.strip()}\n\n"
            "Commit Notes:\n\n"
            f"- Step: `{step}`\n"
            f"- Commit: `{commit}`"
        )
        return self._mutate(
            lambda document: self._append(document, "Done", entry), expected_sha256
        )

    def append_other_note(
        self,
        *,
        step: str,
        commit: str,
        body: str,
        expected_sha256: Optional[str] = None,
    ) -> str:
        _validate_provenance(step, commit)
        _validate_fragment(body, "Other Note body")
        entry = (
            f"### Note — {step}\n\n{body.strip()}\n\n"
            "Provenance:\n\n"
            f"- Step: `{step}`\n"
            f"- Commit: `{commit}`"
        )
        return self._mutate(
            lambda document: self._append(document, "Other Notes", entry),
            expected_sha256,
        )

    def replace_active_step(
        self, *, body: str, expected_sha256: Optional[str] = None
    ) -> str:
        _validate_fragment(body, "Active Step body")
        return self._mutate(
            lambda document: self._replace_section(document, "Active Step", body),
            expected_sha256,
        )

    def append_pending_task(
        self, *, body: str, expected_sha256: Optional[str] = None
    ) -> str:
        _validate_fragment(body, "Pending Task body")
        return self._mutate(
            lambda document: self._append(document, "Pending Tasks", body),
            expected_sha256,
        )

    def progress_pending_task(
        self,
        *,
        expected: str,
        replacement: str,
        expected_sha256: Optional[str] = None,
    ) -> str:
        _validate_fragment(expected, "pending expected text")
        _validate_fragment(replacement, "pending replacement text")

        def mutation(document: _RuntimeDocument) -> None:
            section = document.section("Pending Tasks")
            section.body = _replace_exact_once(section.body, expected, replacement)

        return self._mutate(mutation, expected_sha256)

    def close_pending_task(
        self,
        *,
        expected: str,
        closure: str,
        expected_sha256: Optional[str] = None,
    ) -> str:
        _validate_fragment(expected, "pending expected text")
        _validate_fragment(closure, "pending closure record")
        replacement = (
            expected.rstrip()
            + "\n\nStatus: `CLOSED`\n\nClosure record:\n\n"
            + closure.strip()
        )

        def mutation(document: _RuntimeDocument) -> None:
            section = document.section("Pending Tasks")
            section.body = _replace_exact_once(section.body, expected, replacement)

        return self._mutate(mutation, expected_sha256)

    def replace_next_steps(
        self, *, body: str, expected_sha256: Optional[str] = None
    ) -> str:
        _validate_fragment(body, "Next Steps body")
        return self._mutate(
            lambda document: self._replace_section(document, "Next Steps", body),
            expected_sha256,
        )

    @staticmethod
    def _append(document: _RuntimeDocument, section_name: str, entry: str) -> None:
        section = document.section(section_name)
        section.body = _append_entry(section.body, entry)

    @staticmethod
    def _replace_section(
        document: _RuntimeDocument, section_name: str, body: str
    ) -> None:
        section = document.section(section_name)
        section.body = _replace_body_preserving_separator(section.body, body)

    def _mutate(
        self, mutation: Callable[[_RuntimeDocument], None], expected_sha256: Optional[str]
    ) -> str:
        with self._lock:
            old_text = self.path.read_text(encoding="utf-8")
            old_digest = runtime_sha256(old_text)
            if expected_sha256 is not None and expected_sha256 != old_digest:
                raise RuntimeInvariantError("Runtime digest changed before mutation")

            document = _RuntimeDocument.parse(old_text)
            old_done = document.section("Done").body
            old_other = document.section("Other Notes").body
            old_names = [section.name for section in document.sections]
            old_unknown: Dict[str, str] = {
                section.name: section.body
                for section in document.sections
                if section.name
                not in {"Done", "Other Notes", "Active Step", "Pending Tasks", "Next Steps"}
            }

            # All public callers pass a local closure; no content semantics are inspected.
            mutation(document)

            if not _without_separator(document.section("Done").body).startswith(
                _without_separator(old_done)
            ):
                raise RuntimeInvariantError("Done history would be rewritten")
            if not _without_separator(document.section("Other Notes").body).startswith(
                _without_separator(old_other)
            ):
                raise RuntimeInvariantError("Other Notes history would be rewritten")
            if [section.name for section in document.sections] != old_names:
                raise RuntimeInvariantError("Runtime section structure would change")
            for name, body in old_unknown.items():
                if document.section(name).body != body:
                    raise RuntimeInvariantError(f"non-updatable section would change: {name}")

            new_text = document.render()
            self._atomic_write(new_text)
            return runtime_sha256(new_text)

    def _atomic_write(self, text: str) -> None:
        mode = self.path.stat().st_mode & 0o777
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".runtime-", dir=str(self.path.parent)
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_name, mode)
            os.replace(temporary_name, self.path)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
