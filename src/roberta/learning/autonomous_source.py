from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Mapping, Sequence

from .curriculum_io import TrustedSourceBinding


AUTONOMOUS_SOURCE_CONTRACT = "roberta-autonomous-source/v1"
AUTONOMOUS_SOURCE_VERSION = "1.0.0"
_CHAPTER_RE = re.compile(r"(?im)^\s*chapter\s+(\d+)\b(?:\s*[:.\-–—]?\s*([^\n]{0,160}))?")


class AutonomousSourceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SourcePage:
    page: int
    text: str


@dataclass(frozen=True, slots=True)
class AutonomousSource:
    source_key: str
    title: str
    version: str
    origin: str
    authority_class: str
    original_media_type: str
    original_page_count: int
    original_sha256: str
    transcript_sha256: str
    pages_sha256: str
    chapter_map_sha256: str
    original_path: str
    transcript_path: str
    pages_path: str
    chapter_map_path: str
    imported_at: str

    def trusted_binding(self) -> TrustedSourceBinding:
        return TrustedSourceBinding(
            source_artifact_sha256=self.original_sha256,
            source_transcript_sha256=self.transcript_sha256,
            source_title=self.title,
            source_version=self.version,
            source_origin=self.origin,
            source_authority_class=self.authority_class,
            original_media_type=self.original_media_type,
            original_page_count=self.original_page_count,
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "contract": AUTONOMOUS_SOURCE_CONTRACT,
            "version": AUTONOMOUS_SOURCE_VERSION,
            "source_key": self.source_key,
            "title": self.title,
            "source_version": self.version,
            "origin": self.origin,
            "authority_class": self.authority_class,
            "original_media_type": self.original_media_type,
            "original_page_count": self.original_page_count,
            "original_sha256": self.original_sha256,
            "transcript_sha256": self.transcript_sha256,
            "pages_sha256": self.pages_sha256,
            "chapter_map_sha256": self.chapter_map_sha256,
            "original_path": self.original_path,
            "transcript_path": self.transcript_path,
            "pages_path": self.pages_path,
            "chapter_map_path": self.chapter_map_path,
            "imported_at": self.imported_at,
        }


def source_root() -> Path:
    configured = os.getenv("ROBERTA_AUTONOMOUS_SOURCE_ROOT")
    return Path(configured).expanduser() if configured else Path.home() / ".roberta" / "autonomous_sources"


def _registry_path() -> Path:
    return source_root() / "registry.json"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _load_registry() -> dict[str, object]:
    path = _registry_path()
    if not path.exists():
        return {"contract": AUTONOMOUS_SOURCE_CONTRACT, "version": AUTONOMOUS_SOURCE_VERSION, "sources": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutonomousSourceError(f"cannot read autonomous source registry: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("contract") != AUTONOMOUS_SOURCE_CONTRACT or raw.get("version") != AUTONOMOUS_SOURCE_VERSION:
        raise AutonomousSourceError("autonomous source registry contract/version is invalid")
    if not isinstance(raw.get("sources"), dict):
        raise AutonomousSourceError("autonomous source registry sources must be an object")
    return raw


def _source_from_mapping(raw: Mapping[str, object]) -> AutonomousSource:
    try:
        source = AutonomousSource(
            source_key=str(raw["source_key"]),
            title=str(raw["title"]),
            version=str(raw["source_version"]),
            origin=str(raw["origin"]),
            authority_class=str(raw["authority_class"]),
            original_media_type=str(raw["original_media_type"]),
            original_page_count=int(raw["original_page_count"]),
            original_sha256=str(raw["original_sha256"]),
            transcript_sha256=str(raw["transcript_sha256"]),
            pages_sha256=str(raw["pages_sha256"]),
            chapter_map_sha256=str(raw["chapter_map_sha256"]),
            original_path=str(raw["original_path"]),
            transcript_path=str(raw["transcript_path"]),
            pages_path=str(raw["pages_path"]),
            chapter_map_path=str(raw["chapter_map_path"]),
            imported_at=str(raw["imported_at"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AutonomousSourceError(f"malformed autonomous source record: {exc}") from exc
    if source.authority_class not in {"primary", "secondary", "internal", "unknown"}:
        raise AutonomousSourceError("autonomous source authority_class is invalid")
    if source.original_page_count <= 0:
        raise AutonomousSourceError("autonomous source page count must be positive")
    if any(
        re.fullmatch(r"[0-9a-f]{64}", digest) is None
        for digest in (
            source.original_sha256,
            source.transcript_sha256,
            source.pages_sha256,
            source.chapter_map_sha256,
        )
    ):
        raise AutonomousSourceError("autonomous source digest is invalid")
    return source


def get_autonomous_source(source_key: str) -> AutonomousSource:
    registry = _load_registry()
    sources = registry["sources"]
    assert isinstance(sources, dict)
    raw = sources.get(source_key)
    if not isinstance(raw, Mapping):
        raise AutonomousSourceError(f"unknown autonomous source_key {source_key}")
    source = _source_from_mapping(raw)
    verify_autonomous_source(source)
    return source


def resolve_local_trusted_source(source_key: str) -> TrustedSourceBinding | None:
    registry = _load_registry()
    sources = registry["sources"]
    assert isinstance(sources, dict)
    raw = sources.get(source_key)
    if not isinstance(raw, Mapping):
        return None
    source = _source_from_mapping(raw)
    verify_autonomous_source(source)
    return source.trusted_binding()


def verify_autonomous_source(source: AutonomousSource) -> None:
    original = Path(source.original_path)
    transcript = Path(source.transcript_path)
    pages_path = Path(source.pages_path)
    chapter_map_path = Path(source.chapter_map_path)
    if not all(path.is_file() for path in (original, transcript, pages_path, chapter_map_path)):
        raise AutonomousSourceError(f"autonomous source {source.source_key} is missing durable artifacts")
    if _sha256_file(original) != source.original_sha256:
        raise AutonomousSourceError(f"autonomous source {source.source_key} original artifact hash changed")
    if _sha256_file(transcript) != source.transcript_sha256:
        raise AutonomousSourceError(f"autonomous source {source.source_key} transcript hash changed")
    if _sha256_file(pages_path) != source.pages_sha256:
        raise AutonomousSourceError(f"autonomous source {source.source_key} extracted pages hash changed")
    if _sha256_file(chapter_map_path) != source.chapter_map_sha256:
        raise AutonomousSourceError(f"autonomous source {source.source_key} chapter map hash changed")
    pages = load_source_pages(source, verify_hashes=False)
    if len(pages) != source.original_page_count:
        raise AutonomousSourceError(f"autonomous source {source.source_key} page count changed")


def _extract_pages(path: Path) -> tuple[SourcePage, ...]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise AutonomousSourceError("PDF autonomous training requires pypdf; install the project dependencies") from exc
        try:
            reader = PdfReader(str(path))
        except Exception as exc:
            raise AutonomousSourceError(f"cannot read PDF source: {exc}") from exc
        pages: list[SourcePage] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                raise AutonomousSourceError(f"cannot extract PDF page {index}: {exc}") from exc
            pages.append(SourcePage(index, text))
        if not pages or not any(page.text.strip() for page in pages):
            raise AutonomousSourceError("PDF source contains no extractable text; OCR-only sources are not accepted for unattended training")
        return tuple(pages)
    if suffix not in {".md", ".markdown", ".txt"}:
        raise AutonomousSourceError("autonomous source must be PDF, Markdown, or UTF-8 text")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AutonomousSourceError(f"cannot read UTF-8 source: {exc}") from exc
    if not text.strip():
        raise AutonomousSourceError("source is empty")
    # Text sources use form-feed as a real page boundary when present; otherwise
    # they are one logical page. The manifest records this as a non-PDF source.
    logical = text.split("\f")
    return tuple(SourcePage(index, value) for index, value in enumerate(logical, start=1))


def _chapter_map(pages: Sequence[SourcePage]) -> dict[str, object]:
    starts: dict[int, tuple[int, str]] = {}
    for page in pages:
        head = "\n".join(page.text.splitlines()[:35])
        matches = list(_CHAPTER_RE.finditer(head))
        # Table-of-contents pages often contain many chapter labels; do not use them
        # as chapter starts. A real chapter opening normally has one dominant label.
        if len(matches) != 1:
            continue
        match = matches[0]
        chapter = int(match.group(1))
        title = (match.group(2) or "").strip(" :-–—\t")
        starts.setdefault(chapter, (page.page, title))
    if not starts:
        return {
            "chapters": {
                "1": {"chapter": 1, "title": "Source", "start_page": 1, "end_page": len(pages)}
            },
            "detection": "single-logical-source",
        }
    ordered = sorted((page, chapter, title) for chapter, (page, title) in starts.items())
    chapters: dict[str, object] = {}
    for index, (start, chapter, title) in enumerate(ordered):
        end = ordered[index + 1][0] - 1 if index + 1 < len(ordered) else len(pages)
        chapters[str(chapter)] = {
            "chapter": chapter,
            "title": title or f"Chapter {chapter}",
            "start_page": start,
            "end_page": max(start, end),
        }
    return {"chapters": chapters, "detection": "chapter-heading-v1"}


def import_source(
    path: str | Path,
    *,
    title: str | None = None,
    version: str | None = None,
    authority_class: str = "secondary",
) -> AutonomousSource:
    original = Path(path).expanduser().resolve()
    if not original.is_file():
        raise AutonomousSourceError(f"source file does not exist: {original}")
    if authority_class not in {"primary", "secondary", "internal", "unknown"}:
        raise AutonomousSourceError("authority_class must be primary, secondary, internal, or unknown")
    original_bytes = original.read_bytes()
    original_sha = _sha256_bytes(original_bytes)
    source_key = f"local_{original_sha[:24]}"
    pages = _extract_pages(original)
    normalized_title = (title or original.stem).strip()
    if not normalized_title:
        raise AutonomousSourceError("source title is required")
    normalized_version = (version or f"sha256:{original_sha[:12]}").strip()
    if not normalized_version:
        raise AutonomousSourceError("source version is required")
    media_type = "application/pdf" if original.suffix.lower() == ".pdf" else "text/markdown" if original.suffix.lower() in {".md", ".markdown"} else "text/plain"

    destination = source_root() / source_key
    destination.mkdir(parents=True, exist_ok=True)
    original_copy = destination / ("original" + original.suffix.lower())
    transcript = destination / "transcript.md"
    pages_path = destination / "pages.jsonl"
    chapter_path = destination / "chapter_map.json"

    registry = _load_registry()
    sources = registry["sources"]
    assert isinstance(sources, dict)
    existing = sources.get(source_key)
    if isinstance(existing, Mapping):
        prior = _source_from_mapping(existing)
        if prior.original_sha256 != original_sha:
            raise AutonomousSourceError("autonomous source identity collision")
        # Re-selection is strictly read-only. Verify every immutable artifact
        # before returning and never repair or replace trusted derivations in place.
        verify_autonomous_source(prior)
        return prior

    if original_copy.exists() and _sha256_file(original_copy) != original_sha:
        raise AutonomousSourceError("existing autonomous source copy conflicts with selected source")
    if not original_copy.exists():
        shutil.copy2(original, original_copy)

    transcript_text = "".join(f"# Source Page {page.page}\n\n{page.text.rstrip()}\n\n" for page in pages)
    transcript.write_text(transcript_text, encoding="utf-8")
    pages_path.write_text(
        "".join(json.dumps({"page": page.page, "text": page.text}, ensure_ascii=False, sort_keys=True) + "\n" for page in pages),
        encoding="utf-8",
    )
    _atomic_json(chapter_path, _chapter_map(pages))
    transcript_sha = _sha256_file(transcript)
    pages_sha = _sha256_file(pages_path)
    chapter_map_sha = _sha256_file(chapter_path)
    imported_at = datetime.now(timezone.utc).isoformat()
    source = AutonomousSource(
        source_key=source_key,
        title=normalized_title,
        version=normalized_version,
        origin=original.as_uri(),
        authority_class=authority_class,
        original_media_type=media_type,
        original_page_count=len(pages),
        original_sha256=original_sha,
        transcript_sha256=transcript_sha,
        pages_sha256=pages_sha,
        chapter_map_sha256=chapter_map_sha,
        original_path=str(original_copy),
        transcript_path=str(transcript),
        pages_path=str(pages_path),
        chapter_map_path=str(chapter_path),
        imported_at=imported_at,
    )
    verify_autonomous_source(source)

    sources[source_key] = source.to_mapping()
    _atomic_json(_registry_path(), registry)
    return source


def load_source_pages(source: AutonomousSource | str, *, verify_hashes: bool = True) -> tuple[SourcePage, ...]:
    record = get_autonomous_source(source) if isinstance(source, str) else source
    if verify_hashes:
        original = Path(record.original_path)
        transcript = Path(record.transcript_path)
        if _sha256_file(original) != record.original_sha256 or _sha256_file(transcript) != record.transcript_sha256:
            raise AutonomousSourceError("autonomous source integrity check failed")
        if _sha256_file(Path(record.pages_path)) != record.pages_sha256:
            raise AutonomousSourceError("autonomous source extracted pages integrity check failed")
    try:
        lines = Path(record.pages_path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise AutonomousSourceError(f"cannot read source pages: {exc}") from exc
    pages: list[SourcePage] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            page = int(raw["page"])
            text = str(raw["text"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise AutonomousSourceError(f"invalid source page record: {exc}") from exc
        pages.append(SourcePage(page, text))
    if tuple(item.page for item in pages) != tuple(range(1, len(pages) + 1)):
        raise AutonomousSourceError("source page records are not contiguous")
    return tuple(pages)


def load_chapter_map(source: AutonomousSource | str) -> dict[int, tuple[int, int, str]]:
    record = get_autonomous_source(source) if isinstance(source, str) else source
    if _sha256_file(Path(record.chapter_map_path)) != record.chapter_map_sha256:
        raise AutonomousSourceError("autonomous source chapter map integrity check failed")
    try:
        raw = json.loads(Path(record.chapter_map_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutonomousSourceError(f"cannot read chapter map: {exc}") from exc
    chapters = raw.get("chapters") if isinstance(raw, Mapping) else None
    if not isinstance(chapters, Mapping):
        raise AutonomousSourceError("chapter map is malformed")
    result: dict[int, tuple[int, int, str]] = {}
    for key, value in chapters.items():
        if not isinstance(value, Mapping):
            raise AutonomousSourceError("chapter map entry is malformed")
        try:
            chapter = int(key)
            start = int(value["start_page"])
            end = int(value["end_page"])
            title = str(value.get("title") or f"Chapter {chapter}")
        except (KeyError, TypeError, ValueError) as exc:
            raise AutonomousSourceError(f"chapter map entry is malformed: {exc}") from exc
        if chapter <= 0 or start <= 0 or end < start or end > record.original_page_count:
            raise AutonomousSourceError("chapter map range is invalid")
        result[chapter] = (start, end, title)
    return result
