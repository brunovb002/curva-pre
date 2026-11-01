"""Preços e taxas do Tesouro Direto (Tesouro Transparente, dados abertos sob licença ODbL)."""

import csv
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

URL_CSV = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3"
    "/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
)

# "Tesouro Prefixado" é a LTN: paga R$ 1.000 no vencimento, sem cupom.
TIPO_LTN = "Tesouro Prefixado"


@dataclass(frozen=True)
class LTN:
    vencimento: date
    pu: float
    taxa_publicada: float  # arredondada em 2 casas pelo Tesouro; usamos o PU para calcular


def baixar_csv(destino: Path) -> Path:
    """Baixa o histórico completo (~15 MB) para `destino`."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(URL_CSV, destino)
    return destino


def _data(texto: str) -> date:
    return datetime.strptime(texto, "%d/%m/%Y").date()


def _numero(texto: str) -> float:
    return float(texto.replace(".", "").replace(",", "."))


def _linhas(caminho: Path):
    with open(caminho, encoding="latin-1", newline="") as f:
        yield from csv.DictReader(f, delimiter=";")


def ultima_data_base(caminho: Path) -> date:
    return max(_data(linha["Data Base"]) for linha in _linhas(caminho))


def ltns_por_data(caminho: Path, desde: date | None = None) -> dict[date, list[LTN]]:
    """LTNs de cada data-base (a partir de `desde`), com o PU de recompra do Tesouro (PU Base).

    Usamos o PU Base com a "Taxa Venda": até ~2021 a coluna "PU Venda" tinha outro significado.
    """
    por_data: dict[date, list[LTN]] = {}
    for linha in _linhas(caminho):
        if linha["Tipo Titulo"] != TIPO_LTN:
            continue
        data_base = _data(linha["Data Base"])
        if desde and data_base < desde:
            continue
        pu = _numero(linha["PU Base Manha"])
        if pu <= 0:
            continue
        por_data.setdefault(data_base, []).append(LTN(
            vencimento=_data(linha["Data Vencimento"]),
            pu=pu,
            taxa_publicada=_numero(linha["Taxa Venda Manha"]) / 100,
        ))
    return {d: sorted(ltns, key=lambda t: t.vencimento) for d, ltns in sorted(por_data.items())}


def ler_ltns(caminho: Path, data_base: date) -> list[LTN]:
    """LTNs de uma data-base, ordenadas por vencimento."""
    return ltns_por_data(caminho, desde=data_base).get(data_base, [])
