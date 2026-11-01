"""Contratos de DI futuro (DI1) da B3."""

from datetime import date

from .calendario import dias_uteis, proximo_dia_util
from .juros import taxa_de_pu

# Letra do mês no código do contrato: F = janeiro ... Z = dezembro
LETRAS_MES = "FGHJKMNQUVXZ"


def vencimento(codigo: str) -> date:
    """Data de vencimento a partir do código, ex.: "DI1F27" ou "F27" -> 1º dia útil de jan/2027."""
    codigo = codigo.upper().removeprefix("DI1")
    if len(codigo) != 3 or codigo[0] not in LETRAS_MES or not codigo[1:].isdigit():
        raise ValueError(f"código de DI1 inválido: {codigo!r}")
    mes = LETRAS_MES.index(codigo[0]) + 1
    ano = 2000 + int(codigo[1:])
    return proximo_dia_util(date(ano, mes, 1))


def taxa_implicita(codigo: str, preco: float, data_base: date) -> tuple[int, float]:
    """(du até o vencimento, taxa anual) implícitos no PU de ajuste do contrato."""
    du = dias_uteis(data_base, vencimento(codigo))
    if du <= 0:
        raise ValueError(f"{codigo} já venceu em {data_base}")
    return du, taxa_de_pu(preco, du)
