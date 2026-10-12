"""US-003: pedido por chamada, modo prompt e relato de motor/origem."""
from pathlib import Path
import re

import pytest


ROUTING_SOURCE: str = "plugins/keyless-image/references/engine-routing.md"
INSTALLED_ROUTING_SOURCE: str = "references/engine-routing.md"
SKILLS: tuple[str, ...] = ("generate", "edit")
ORIGINS: tuple[str, ...] = ("pedido explícito", "tabela", "padrão")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^{re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else ""


def _find_source_problems(root: Path) -> list[str]:
    text = (root / ROUTING_SOURCE).read_text(encoding="utf-8")
    override = _section(text, "## Pedido explícito do usuário")
    problems: list[str] = []
    requirements: tuple[tuple[str, str], ...] = (
        (r"(?m)^- Motor `codex`:", "pedido codex ausente"),
        (r"(?m)^- Motor `grok`:", "pedido grok ausente"),
        (r"modo prompt", "pedido modo prompt ausente"),
        (r"só o prompt.*modo prompt.*prompt only", "formas de pedido ausentes"),
        (r"qualquer pedido claro de motor ou de modo prompt conta",
         "pedidos claros além dos exemplos ausentes"),
        (r"pedidos em português ou inglês.*por exemplo:",
         "formas de pedido como exemplos ausentes"),
        (r"pedido explícito do usuário vence.*tabela.*sem pergunta",
         "precedência sem pergunta ausente"),
        (r"O parâmetro `engine` aceita exatamente `codex` e `grok`\.",
         "valores exatos de engine ausentes"),
        (r"se o tipo estiver fora da tabela, use o default `codex` da tool\.",
         "tipo fora da tabela sem default codex"),
        (r"não chama `generate_image`", "curto-circuito ausente"),
        (r"não gera arquivo", "modo prompt sem arquivo ausente"),
        (r"mesmo com os dois motores (?:disponíveis|instalados)",
         "modo prompt com dois motores ausente"),
        (r"escolha, não falha", "modo prompt como escolha ausente"),
        (r"não é (?:um terceiro )?valor de `engine`", "enum preservado ausente"),
        (r"edição.*prompt de edição.*imagem.*anexar", "edição externa ausente"),
        (r"nenhum motor foi usado.*`pedido explícito`", "relato modo prompt ausente"),
        (r"não há preferência persistente.*chamada.*nada é gravado em disco/config",
         "não-persistência ausente"),
        (r"detecção e a confirmação antes de trocar de motor pertencem à US-004",
         "limite US-004 ausente"),
        (r"vocabulário mínimo", "vocabulário mínimo ausente"),
        (r"quando a troca do Pré-requisito da skill ocorrer, relate a origem como "
         r"`pré-requisito: Codex ausente`",
         "origem por Codex ausente até US-004 ausente"),
    )
    for pattern, problem in requirements:
        if re.search(pattern, override, re.IGNORECASE | re.DOTALL) is None:
            problems.append(problem)
    origin_section = _section(override, "### Origem da decisão e relato")
    for origin in ORIGINS:
        if re.search(rf"^- `{re.escape(origin)}`:", origin_section, re.MULTILINE) is None:
            problems.append(f"origem ausente: {origin}")
    if re.search(r"motor efetivamente usado.*origem", origin_section, re.DOTALL) is None:
        problems.append("relato motor e origem ausente")
    return problems


def _find_skill_problems(root: Path) -> list[str]:
    problems: list[str] = []
    for skill in SKILLS:
        path = root / f"plugins/keyless-image/skills/{skill}/SKILL.md"
        text = path.read_text(encoding="utf-8")
        report = _section(text, "### 5. Reportar")
        for term in ("motor", "origem", INSTALLED_ROUTING_SOURCE):
            if term not in report:
                problems.append(f"{skill}: Reportar sem {term}")
        if "não faz fallback entre motores" not in text:
            problems.append(f"{skill}: aviso de não-fallback ausente")
        if re.search(r"Modo prompt.*curto-circuita.*antes.*generate_image", text,
                     re.DOTALL) is None:
            problems.append(f"{skill}: modo prompt sem curto-circuito")
        engine = re.search(r"- \*\*`engine`\*\*:.*?(?=\n\n)", text, re.DOTALL)
        pointer = f"  - Siga `{INSTALLED_ROUTING_SOURCE}` (§ Pedido explícito do usuário)."
        if engine is None or pointer not in engine.group().splitlines():
            problems.append(f"{skill}: escolha sem ponteiro para seção de pedido explícito")
        main_line = (
            '- **`engine`**: `codex` (default) ou `grok`. Ambos keyless. '
            'Só esses dois valores — o enum da tool é `z.enum(["codex","grok"])`.'
        )
        if engine is None or engine.group().splitlines() != [main_line, pointer]:
            problems.append(
                f"{skill}: bullet engine deve conter só a linha principal e o ponteiro"
            )
        if engine is not None and "tem precedência" in engine.group().casefold():
            problems.append(f"{skill}: resumo de precedência duplicado no bullet engine")
    return problems


def test_override_source_contract() -> None:
    assert _find_source_problems(_repo_root()) == []


def test_override_skill_contract() -> None:
    assert _find_skill_problems(_repo_root()) == []


def _copy_contract_files(root: Path) -> None:
    paths: tuple[str, ...] = (
        ROUTING_SOURCE,
        *[f"plugins/keyless-image/skills/{skill}/SKILL.md" for skill in SKILLS],
    )
    for relative_path in paths:
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            (_repo_root() / relative_path).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


@pytest.mark.parametrize(
    "mutation", ("origin", "persistence", "edit_report", "codex_trigger", "grok_trigger")
)
def test_override_guard_catches_mutations(tmp_path: Path, mutation: str) -> None:
    _copy_contract_files(tmp_path)
    assert _find_source_problems(tmp_path) + _find_skill_problems(tmp_path) == []
    relative_path = (
        "plugins/keyless-image/skills/edit/SKILL.md"
        if mutation == "edit_report" else ROUTING_SOURCE
    )
    path = tmp_path / relative_path
    text = path.read_text(encoding="utf-8")
    expected: list[str]
    if mutation == "origin":
        text, count = re.subn(r"^- `padrão`:.*\n", "", text, flags=re.MULTILINE)
        expected = ["origem ausente: padrão"]
    elif mutation == "persistence":
        text, count = re.subn(r"^Não há preferência persistente.*\n", "", text,
                             flags=re.MULTILINE)
        expected = ["não-persistência ausente"]
    elif mutation in ("codex_trigger", "grok_trigger"):
        engine = mutation.removesuffix("_trigger")
        text, count = re.subn(rf"^- Motor `{engine}`:.*\n", "", text,
                             flags=re.MULTILINE)
        expected = [f"pedido {engine} ausente"]
    else:
        report = _section(text, "### 5. Reportar")
        assert report.count("origem") == 1
        text = text.replace(report, report.replace("origem", "decisão"))
        count = 1
        expected = ["edit: Reportar sem origem"]
    assert count == 1
    path.write_text(text, encoding="utf-8")
    assert _find_source_problems(tmp_path) + _find_skill_problems(tmp_path) == expected


@pytest.mark.parametrize(
    ("skill", "inline"),
    (("generate", False), ("edit", False), ("generate", True)),
)
def test_engine_bullet_guard_catches_duplicate_summary(
    tmp_path: Path, skill: str, inline: bool,
) -> None:
    _copy_contract_files(tmp_path)
    assert _find_skill_problems(tmp_path) == []
    path = tmp_path / f"plugins/keyless-image/skills/{skill}/SKILL.md"
    text = path.read_text(encoding="utf-8")
    summary = "O pedido explícito do usuário tem precedência sobre a tabela."
    pattern = r"(^- \*\*`engine`\*\*:.*)(\n  - Siga .*\n)"
    replacement = (
        rf"\1 {summary}\2" if inline else rf"\1\2  - {summary}\n"
    )
    text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    assert count == 1
    path.write_text(text, encoding="utf-8")
    assert _find_skill_problems(tmp_path) == [
        f"{skill}: bullet engine deve conter só a linha principal e o ponteiro",
        f"{skill}: resumo de precedência duplicado no bullet engine",
    ]


@pytest.mark.parametrize(
    ("phrase", "problem"),
    (
        ("O parâmetro `engine` aceita exatamente `codex` e `grok`.",
         "valores exatos de engine ausentes"),
        ("se o tipo estiver fora da tabela, use o default `codex` da tool.",
         "tipo fora da tabela sem default codex"),
    ),
)
def test_source_guard_catches_engine_rule_deletions(
    tmp_path: Path, phrase: str, problem: str,
) -> None:
    _copy_contract_files(tmp_path)
    assert _find_source_problems(tmp_path) == []
    path = tmp_path / ROUTING_SOURCE
    text = path.read_text(encoding="utf-8")
    assert text.count(phrase) == 1
    path.write_text(text.replace(phrase, ""), encoding="utf-8")
    assert _find_source_problems(tmp_path) == [problem]


@pytest.mark.parametrize(
    ("phrase", "problem"),
    (
        ("US-004", "limite US-004 ausente"),
        ("`pré-requisito: Codex ausente`",
         "origem por Codex ausente até US-004 ausente"),
    ),
)
def test_source_guard_preserves_availability_boundary(
    tmp_path: Path, phrase: str, problem: str,
) -> None:
    _copy_contract_files(tmp_path)
    assert _find_source_problems(tmp_path) == []
    path = tmp_path / ROUTING_SOURCE
    text = path.read_text(encoding="utf-8")
    assert text.count(phrase) == 1
    path.write_text(text.replace(phrase, ""), encoding="utf-8")
    assert _find_source_problems(tmp_path) == [problem]
