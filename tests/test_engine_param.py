"""US-001: as skills keyless-image:generate e keyless-image:edit declaram
o parametro `engine` de generate_image com os dois valores reais da tool
(`codex`, `grok`), o mesmo default (`codex`), e sem tratar `prompt` como
valor do enum.
"""
from pathlib import Path
import re

import pytest


EXCLUDED_DIRECTORY_NAMES: frozenset[str] = frozenset(
    {".git", ".ralph", ".depth-loop", "node_modules", "__pycache__"}
)
EXCLUDED_FILE_NAMES: frozenset[str] = frozenset(
    {
        "CHANGELOG.md",  # Historico legitimo em qualquer nivel do repositorio.
    }
)
EXCLUDED_RELATIVE_PATHS: frozenset[str] = frozenset({"AGENTS.md"})

REQUIRED_SKILLS: tuple[str, ...] = ("generate", "edit")
ENGINE_VALUES: tuple[str, ...] = ("codex", "grok")
DEFAULT_ENGINE: str = "codex"
ENGINE_ROUTING_REFERENCE: str = "engine-routing.md"

ENGINE_PARAM: re.Pattern[str] = re.compile(r"`engine`|\*\*engine\*\*")
ENGINE_ASSIGNED_PROMPT: re.Pattern[str] = re.compile(
    r"engine\s*[:=]\s*['\"`]?prompt['\"`]?\b",
    re.IGNORECASE,
)
QUOTED_ENGINE_TOKEN: re.Pattern[str] = re.compile(
    r"[`'\"](codex|grok|prompt)[`'\"]",
    re.IGNORECASE,
)
DEFAULT_VALUE: re.Pattern[str] = re.compile(
    r"`(codex|grok)`\s*\(\s*default(?:\s*,[^)]*)?\)"
    r"|\bdefault\b[^\n]{0,50}`(codex|grok)`",
    re.IGNORECASE,
)
ENUM_WITH_PROMPT: re.Pattern[str] = re.compile(
    r"z\.enum\([^)]*\bprompt\b",
    re.IGNORECASE,
)
ENGINE_HEAD: re.Pattern[str] = re.compile(r"^(\s*)-\s+\*\*`engine`\*\*")
VALUE_HEAD: re.Pattern[str] = re.compile(r"^\*\*`([^`]+)`\*\*")
BULLET: re.Pattern[str] = re.compile(r"^(\s*)-\s+(.*)$")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_excluded(path: Path, root: Path, test_path: Path) -> bool:
    relative_path = path.relative_to(root)
    if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts):
        return True
    if path == test_path:
        return True
    if relative_path.as_posix() in EXCLUDED_RELATIVE_PATHS:
        return True
    return relative_path.name in EXCLUDED_FILE_NAMES


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_keyless_image_skills(root: Path, test_path: Path) -> list[Path]:
    skills_root = root / "plugins" / "keyless-image" / "skills"
    if not skills_root.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(skills_root.glob("*/SKILL.md")):
        if path.is_file() and not _is_excluded(path, root, test_path):
            found.append(path)
    return found


def _load_required_skills() -> dict[str, tuple[str, str]]:
    """nome da skill -> (rel_path, texto). Falha se generate ou edit faltar."""
    root = _repo_root()
    test_path = Path(__file__).resolve()
    by_name: dict[str, tuple[str, str]] = {}
    for path in _iter_keyless_image_skills(root, test_path):
        name = path.parent.name
        if name in REQUIRED_SKILLS:
            by_name[name] = (_rel(path, root), path.read_text(encoding="utf-8"))
    missing = [name for name in REQUIRED_SKILLS if name not in by_name]
    if missing:
        pytest.fail(
            "SKILL.md ausente em plugins/keyless-image/skills/: "
            + ", ".join(missing)
        )
    return by_name


def _sibling_indices(
    lines: list[str], start: int, parent_indent: int
) -> tuple[list[int], int]:
    found: list[int] = []
    child_indent: int | None = None
    idx = start
    while idx < len(lines):
        line = lines[idx]
        if line.strip():
            indent = len(line) - len(line.lstrip())
            if indent <= parent_indent:
                break
            if BULLET.match(line):
                if child_indent is None:
                    child_indent = indent
                if indent == child_indent:
                    found.append(idx)
        idx += 1
    return found, idx


def _iter_engine_blocks(lines: list[str]) -> list[tuple[int, list[int]]]:
    """Cada bloco: (idx da linha `engine`, idxs dos sub-bullets irmãos)."""
    blocks: list[tuple[int, list[int]]] = []
    idx = 0
    while idx < len(lines):
        match = ENGINE_HEAD.match(lines[idx])
        if match is None:
            idx += 1
            continue
        engine_idx = idx
        siblings, idx = _sibling_indices(lines, idx + 1, len(match.group(1)))
        blocks.append((engine_idx, siblings))
    return blocks


def _sibling_token(line: str) -> str | None:
    bullet = BULLET.match(line)
    if bullet is None:
        return None
    match = VALUE_HEAD.match(bullet.group(2))
    if match is None:
        return None
    return match.group(1)


def _declares_engine_value(text: str, value: str) -> bool:
    lines = text.splitlines()
    quoted = re.compile(rf"`{re.escape(value)}`", re.IGNORECASE)
    for engine_idx, sibling_idxs in _iter_engine_blocks(lines):
        span = (engine_idx, *sibling_idxs)
        if any(quoted.search(lines[idx]) for idx in span):
            return True
    return False


def _declared_defaults(text: str) -> set[str]:
    found: set[str] = set()
    for match in DEFAULT_VALUE.finditer(text):
        value = match.group(1) or match.group(2)
        found.add(value.lower())
    return found


def _invalid_engine_value_hits(rel_path: str, text: str) -> list[str]:
    # Recaída provável imita o layout existente: um sub-bullet irmão
    # (`  - **`prompt`**: ...`) sem `codex`/`grok` na mesma linha. Olhar
    # só mesma-linha deixa essa forma passar; a guarda varre os irmãos
    # da sub-lista ancorada no bullet `engine`.
    hits: list[str] = []
    lines = text.splitlines()
    allowed = {value.lower() for value in ENGINE_VALUES}
    for _engine_idx, sibling_idxs in _iter_engine_blocks(lines):
        for idx in sibling_idxs:
            token = _sibling_token(lines[idx])
            if token is None or token.lower() in allowed:
                continue
            hits.append(
                f"{rel_path}:{idx + 1}: valor de engine inválido `{token}` "
                f"(só `codex` e `grok`); {lines[idx].strip()}"
            )
    return hits


def _prompt_as_engine_hits(rel_path: str, text: str) -> list[str]:
    hits: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if ENGINE_ASSIGNED_PROMPT.search(line):
            hits.append(
                f"{rel_path}:{line_number}: engine atribuido a prompt "
                f"({line.strip()})"
            )
            continue
        quoted = {token.lower() for token in QUOTED_ENGINE_TOKEN.findall(line)}
        if "prompt" in quoted and quoted & {"codex", "grok"}:
            hits.append(
                f"{rel_path}:{line_number}: `prompt` listado junto dos "
                f"valores de engine ({line.strip()})"
            )
    if ENUM_WITH_PROMPT.search(text):
        hits.append(f"{rel_path}: z.enum inclui prompt")
    hits.extend(_invalid_engine_value_hits(rel_path, text))
    return hits


def test_both_skills_declare_engine_parameter() -> None:
    missing: list[str] = []
    for _name, (rel_path, text) in _load_required_skills().items():
        if not ENGINE_PARAM.search(text):
            missing.append(
                f"{rel_path}: falta o parametro `engine` de generate_image"
            )
    if missing:
        pytest.fail("\n".join(missing))


def test_both_skills_declare_codex_and_grok_engine_values() -> None:
    missing: list[str] = []
    for _name, (rel_path, text) in _load_required_skills().items():
        for value in ENGINE_VALUES:
            if not _declares_engine_value(text, value):
                missing.append(
                    f"{rel_path}: nao menciona o valor de engine `{value}`"
                )
        if ENGINE_ROUTING_REFERENCE not in text:
            missing.append(
                f"{rel_path}: falta o ponteiro para {ENGINE_ROUTING_REFERENCE}"
            )
    if missing:
        pytest.fail("\n".join(missing))


def test_neither_skill_lists_prompt_as_engine_value() -> None:
    hits: list[str] = []
    for _name, (rel_path, text) in _load_required_skills().items():
        hits.extend(_prompt_as_engine_hits(rel_path, text))
    if hits:
        pytest.fail(
            "`prompt` nao e valor de engine (so `codex` e `grok`); "
            "modo prompt e da skill, nao do enum:\n" + "\n".join(hits)
        )


def test_both_skills_declare_the_same_codex_default() -> None:
    defaults_by_file: dict[str, set[str]] = {}
    problems: list[str] = []
    for _name, (rel_path, text) in _load_required_skills().items():
        defaults = _declared_defaults(text)
        defaults_by_file[rel_path] = defaults
        if not defaults:
            problems.append(f"{rel_path}: nao declara default de `engine`")
        elif defaults != {DEFAULT_ENGINE}:
            problems.append(
                f"{rel_path}: default de engine e {sorted(defaults)}, "
                f"esperado ['{DEFAULT_ENGINE}']"
            )
    unique = {frozenset(values) for values in defaults_by_file.values()}
    if len(unique) > 1:
        rendered = ", ".join(
            f"{path}={sorted(values)}"
            for path, values in sorted(defaults_by_file.items())
        )
        problems.append(f"defaults de engine divergem entre as skills: {rendered}")
    if problems:
        pytest.fail("\n".join(problems))
