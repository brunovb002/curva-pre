"""Montagem da curva pré do dia: CDI na ponta curta + LTNs do Tesouro."""

from dataclasses import dataclass
from datetime import date

from .calendario import dias_uteis
from .curva import CurvaPre
from .fontes.tesouro import LTN
from .juros import BASE, NOCIONAL_LTN, taxa_de_pu

# LTN muito perto do vencimento: o PU arredondado em centavos distorce a taxa,
# e o CDI já cobre a ponta curta.
DU_MINIMO_LTN = 21


@dataclass(frozen=True)
class Vertice:
    nome: str
    vencimento: date | None
    du: int
    taxa: float
    pu: float | None = None


def taxa_confere(taxa_calculada: float, ltn: LTN, du: int) -> bool:
    """A taxa calculada do PU bate com a publicada, dentro do erro de arredondamento?

    O Tesouro publica a taxa com 2 casas (meio centésimo de erro) e o PU em centavos,
    que pesa mais quanto menor o prazo.
    """
    tolerancia = 0.00006 + (BASE / du) * 0.006 / ltn.pu
    return abs(taxa_calculada - ltn.taxa_publicada) <= tolerancia


def montar_vertices(data_base: date, ltns: list[LTN], cdi_anual: float) -> tuple[list[Vertice], list[LTN]]:
    """(vértices, LTNs descartadas por erro nos dados do Tesouro)."""
    # O CDI de hoje rende até o próximo dia útil: é o vértice de 1 du.
    vertices = [Vertice("CDI", None, 1, cdi_anual)]
    descartadas = []
    for ltn in ltns:
        du = dias_uteis(data_base, ltn.vencimento)
        if du < DU_MINIMO_LTN:
            continue
        taxa = taxa_de_pu(ltn.pu, du, NOCIONAL_LTN)
        if not taxa_confere(taxa, ltn, du):
            descartadas.append(ltn)
            continue
        vertices.append(Vertice(f"LTN {ltn.vencimento:%m/%Y}", ltn.vencimento, du, taxa, ltn.pu))
    return vertices, descartadas


def montar_curva(vertices: list[Vertice]) -> CurvaPre:
    return CurvaPre([(v.du, v.taxa) for v in vertices])


def tabela(curva: CurvaPre, passo: int = 21) -> list[dict]:
    """Taxa spot e forward do período anterior em uma grade de `passo` dias úteis."""
    linhas = []
    anterior = 0
    for du in range(passo, curva.prazo_maximo + 1, passo):
        linhas.append({
            "du": du,
            "taxa": curva.taxa(du),
            "forward": curva.forward(anterior, du),
        })
        anterior = du
    return linhas
