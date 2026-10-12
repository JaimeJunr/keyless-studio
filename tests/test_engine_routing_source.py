"""US-002: a recomendação de motor por asset vive em uma fonte única.

A varredura de preferência abaixo é heurística: ela procura, na mesma linha,
um motor, um tipo de asset e uma palavra de recomendação. Isso cobre as formas
de regressão conhecidas, mas não tenta interpretar afirmações espalhadas por
várias linhas nem equivalentes sem os termos catalogados.
"""
from pathlib import Path
import re
from typing import Iterator

import pytest


ROUTING_SOURCE: str = "plugins/keyless-image/references/engine-routing.md"
INSTALLED_ROUTING_SOURCE: str = "references/engine-routing.md"
EXPECTED_ASSET_TYPES: tuple[str, ...] = (
    "sprite de personagem / pixel art",
    "retrato",
    "ilustração detalhada",
    "cena",
    "slide de deck",
    "criativo social",
    "infográfico",
)
ALLOWED_ENGINES: frozenset[str] = frozenset({"codex", "grok"})
FILES_THAT_DECLARE_ROUTING: tuple[str, ...] = (
    "CLAUDE.md",
    "plugins/keyless-sprite/references/sprites.md",
    "plugins/keyless-sprite/skills/sprite/SKILL.md",
    "plugins/keyless-image/skills/generate/SKILL.md",
    "plugins/keyless-image/skills/edit/SKILL.md",
)
RUNTIME_FILES_THAT_REFERENCE_ROUTING: tuple[str, ...] = (
    *[path for path in FILES_THAT_DECLARE_ROUTING if path.startswith("plugins/")],
    "plugins/keyless-sprite/skills/handoff/SKILL.md",
)
EXCLUDED_DIRECTORY_NAMES: frozenset[str] = frozenset(
    {".git", ".ralph", ".depth-loop", "node_modules", "__pycache__"}
)
EXCLUDED_FILE_NAMES: frozenset[str] = frozenset({"CHANGELOG.md"})
EXCLUDED_RELATIVE_PATHS: frozenset[str] = frozenset(
    {"AGENTS.md", ROUTING_SOURCE, "tests/test_engine_routing_source.py"}
)

ENGINE_PATTERN: re.Pattern[str] = re.compile(r"\b(?:grok|codex)\b", re.IGNORECASE)
ASSET_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:sprite|pixel[ -]?art|retrato|ilustra|cena)", re.IGNORECASE
)
PREFERENCE_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:melhor|preferid|ganha|sobretudo|sai\s+n[ií]tido|recomend)",
    re.IGNORECASE,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _parse_table_rows(text: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0].lower() == "tipo de asset":
            continue
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append((cells[0], cells[1].strip("` ").lower(), cells[2]))
    return rows


def _iter_markdown_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.md"):
        relative_path = path.relative_to(root)
        if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts):
            continue
        if relative_path.name in EXCLUDED_FILE_NAMES:
            continue
        if relative_path.as_posix() in EXCLUDED_RELATIVE_PATHS:
            continue
        if path.is_file():
            yield path


def _find_preference_claims(root: Path) -> list[tuple[str, int, str]]:
    """Retorna linhas que parecem reafirmar preferência de motor por asset."""
    claims: list[tuple[str, int, str]] = []
    for path in _iter_markdown_files(root):
        relative_path = path.relative_to(root).as_posix()
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if (
                ENGINE_PATTERN.search(line)
                and ASSET_PATTERN.search(line)
                and PREFERENCE_PATTERN.search(line)
            ):
                claims.append((relative_path, line_number, line.strip()))
    return sorted(claims)


def _find_runtime_routing_pointer_problems(root: Path) -> list[str]:
    """Verifica ponteiros em skills/references nas raízes de plugins instalados."""
    problems: list[str] = []
    for directory in ("skills", "references"):
        for base in root.glob(f"plugins/*/{directory}"):
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                relative_path = path.relative_to(root).as_posix()
                text = path.read_text(encoding="utf-8")
                if ROUTING_SOURCE in text:
                    problems.append(f"{relative_path}: ponteiro com prefixo do repo")
                if (
                    relative_path in RUNTIME_FILES_THAT_REFERENCE_ROUTING
                    or "engine-routing.md" in text
                ) and INSTALLED_ROUTING_SOURCE not in text:
                    problems.append(f"{relative_path}: ponteiro relativo ausente")
    for relative_path in RUNTIME_FILES_THAT_REFERENCE_ROUTING:
        if not (root / relative_path).is_file():
            problems.append(f"{relative_path}: arquivo ausente")
    return sorted(problems)


def _format_claims(claims: list[tuple[str, int, str]]) -> str:
    return "\n".join(
        f"{path}:{line_number}: {line}"
        for path, line_number, line in claims
    )


def test_routing_source_table_covers_assets_with_engine_and_reason() -> None:
    source_path = _repo_root() / ROUTING_SOURCE
    assert source_path.is_file(), f"fonte única ausente: {ROUTING_SOURCE}"

    rows = _parse_table_rows(source_path.read_text(encoding="utf-8"))
    by_asset = {asset.lower(): (engine, reason) for asset, engine, reason in rows}
    assert set(by_asset) == set(EXPECTED_ASSET_TYPES)

    problems: list[str] = []
    for asset, (engine, reason) in by_asset.items():
        if engine not in ALLOWED_ENGINES:
            problems.append(f"{asset}: motor inválido {engine!r}")
        if re.search(r"[^\W_]", reason, re.UNICODE) is None:
            problems.append(f"{asset}: motivo vazio ou só pontuação")
    assert not problems, "\n".join(problems)


def test_routing_source_documents_default_no_fallback_and_user_override() -> None:
    source_path = _repo_root() / ROUTING_SOURCE
    assert source_path.is_file(), f"fonte única ausente: {ROUTING_SOURCE}"
    text = source_path.read_text(encoding="utf-8").lower()

    assert "default `codex`" in text
    assert "não faz fallback entre motores" in text
    assert "pedido explícito do usuário vence" in text
    assert "sem pergunta" in text


def test_previous_routing_declarations_reference_single_source() -> None:
    root = _repo_root()
    missing: list[str] = []
    for relative_path in FILES_THAT_DECLARE_ROUTING:
        text = (root / relative_path).read_text(encoding="utf-8")
        if "engine-routing.md" not in text:
            missing.append(relative_path)
    assert not missing, "arquivos sem ponteiro para engine-routing.md:\n" + "\n".join(
        missing
    )


def test_runtime_routing_pointers_resolve_in_installed_plugins() -> None:
    problems = _find_runtime_routing_pointer_problems(_repo_root())
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("directory", ("skills", "references"))
def test_runtime_routing_pointer_guard_catches_mutations(
    tmp_path: Path, directory: str,
) -> None:
    for relative_path in RUNTIME_FILES_THAT_REFERENCE_ROUTING:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(INSTALLED_ROUTING_SOURCE, encoding="utf-8")
    candidate = tmp_path / "plugins" / "other" / directory / "routing.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(INSTALLED_ROUTING_SOURCE, encoding="utf-8")
    assert _find_runtime_routing_pointer_problems(tmp_path) == []

    candidate.write_text(ROUTING_SOURCE, encoding="utf-8")
    assert _find_runtime_routing_pointer_problems(tmp_path) == [
        f"plugins/other/{directory}/routing.md: ponteiro com prefixo do repo"
    ]

    candidate.write_text("engine-routing.md", encoding="utf-8")
    assert _find_runtime_routing_pointer_problems(tmp_path) == [
        f"plugins/other/{directory}/routing.md: ponteiro relativo ausente"
    ]

    candidate.write_text(INSTALLED_ROUTING_SOURCE, encoding="utf-8")
    required = tmp_path / RUNTIME_FILES_THAT_REFERENCE_ROUTING[0]
    required.write_text("Sem ponteiro.", encoding="utf-8")
    assert _find_runtime_routing_pointer_problems(tmp_path) == [
        f"{RUNTIME_FILES_THAT_REFERENCE_ROUTING[0]}: ponteiro relativo ausente"
    ]


def test_no_markdown_outside_source_claims_engine_preference_by_asset() -> None:
    claims = _find_preference_claims(_repo_root())
    if claims:
        pytest.fail(
            "preferência de motor por asset fora da fonte única:\n"
            + _format_claims(claims)
        )


def test_preference_guard_catches_regression_and_allows_engine_example(
    tmp_path: Path,
) -> None:
    regressed = tmp_path / "regressed.md"
    regressed.write_text(
        "`grok` sai melhor pra sprite/pixel art\n", encoding="utf-8"
    )
    claims = _find_preference_claims(tmp_path)
    assert len(claims) == 1
    assert claims[0][0] == "regressed.md"

    regressed.write_text("Exemplo: `engine: grok`.\n", encoding="utf-8")
    assert _find_preference_claims(tmp_path) == []
