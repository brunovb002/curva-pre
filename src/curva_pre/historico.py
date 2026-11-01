"""Histórico compacto das curvas: um JSON por ano, só com os vértices.

A interpolação flat-forward é refeita por quem lê (o site faz isso no navegador),
então guardar a grade inteira seria desperdício.
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path

from .fontes.bcb import SerieCDI
from .fontes.tesouro import LTN
from .montagem import montar_vertices

FORMATO = "v: [du, taxa % a.a., vencimento ou null para o CDI]; cdi: data da observação do CDI"


def curva_compacta(data_base: date, ltns: list[LTN], cdi: SerieCDI) -> tuple[dict, list[LTN]]:
    data_cdi, taxa_cdi = cdi.em(data_base)
    vertices, descartadas = montar_vertices(data_base, ltns, taxa_cdi)
    compacta = {
        "cdi": data_cdi.isoformat(),
        "v": [
            [v.du, round(v.taxa * 100, 4), v.vencimento.isoformat() if v.vencimento else None]
            for v in vertices
        ],
    }
    return compacta, descartadas


def gerar(ltns_por_data: dict[date, list[LTN]], cdi: SerieCDI) -> tuple[dict[int, dict], list[str]]:
    """({ano: conteúdo do arquivo}, avisos sobre LTNs descartadas)."""
    anos: dict[int, dict] = {}
    avisos = []
    for data_base, ltns in ltns_por_data.items():
        compacta, descartadas = curva_compacta(data_base, ltns, cdi)
        if len(compacta["v"]) < 2:
            avisos.append(f"{data_base}: sem LTN válida, curva ignorada")
            continue
        arquivo = anos.setdefault(data_base.year, {"ano": data_base.year, "formato": FORMATO, "curvas": {}})
        arquivo["curvas"][data_base.isoformat()] = compacta
        avisos += [f"{data_base}: LTN {t.vencimento} descartada (PU não bate com a taxa publicada)"
                   for t in descartadas]
    return anos, avisos


def salvar(anos: dict[int, dict], pasta: Path) -> dict:
    """Grava os anos e reescreve o indice.json a partir de todos os anos da pasta."""
    pasta.mkdir(parents=True, exist_ok=True)
    for ano, conteudo in anos.items():
        (pasta / f"{ano}.json").write_text(json.dumps(conteudo, separators=(",", ":")), encoding="utf-8")

    existentes = sorted(int(p.stem) for p in pasta.glob("[0-9][0-9][0-9][0-9].json"))
    datas = lambda ano: list(json.loads((pasta / f"{ano}.json").read_text(encoding="utf-8"))["curvas"])
    indice = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "primeira": datas(existentes[0])[0],
        "ultima": datas(existentes[-1])[-1],
        "anos": existentes,
    }
    (pasta / "indice.json").write_text(json.dumps(indice, indent=2), encoding="utf-8")
    return indice
