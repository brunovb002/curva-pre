"""Calendário de dias úteis no padrão ANBIMA (feriados nacionais)."""

from datetime import date, timedelta
from functools import lru_cache


def pascoa(ano: int) -> date:
    """Domingo de Páscoa pelo algoritmo de Meeus/Jones/Butcher (calendário gregoriano)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


# Lei 14.759, de 21/12/2023, tornou o 20 de novembro feriado nacional a partir de 2024.
# Antes disso o mercado contava os 20/11 futuros como dias úteis. Os preços do Tesouro
# passam a refletir o feriado no pregão de 26/12/2023 (ainda não em 21 e 22/12).
LEI_CONSCIENCIA_NEGRA = date(2023, 12, 26)


@lru_cache(maxsize=None)
def feriados(ano: int, vigente_em: date | None = None) -> frozenset[date]:
    """Feriados nacionais do calendário ANBIMA.

    `vigente_em` é a data em que o calendário é consultado: feriados criados
    depois dela ficam de fora, como o mercado fazia na época. None = calendário atual.
    """
    p = pascoa(ano)
    fixos = [
        date(ano, 1, 1),    # Confraternização Universal
        date(ano, 4, 21),   # Tiradentes
        date(ano, 5, 1),    # Dia do Trabalho
        date(ano, 9, 7),    # Independência
        date(ano, 10, 12),  # Nossa Senhora Aparecida
        date(ano, 11, 2),   # Finados
        date(ano, 11, 15),  # Proclamação da República
        date(ano, 12, 25),  # Natal
    ]
    if ano >= 2024 and (vigente_em is None or vigente_em >= LEI_CONSCIENCIA_NEGRA):
        fixos.append(date(ano, 11, 20))  # Consciência Negra
    moveis = [
        p - timedelta(days=48),  # Carnaval (segunda)
        p - timedelta(days=47),  # Carnaval (terça)
        p - timedelta(days=2),   # Sexta-feira Santa
        p + timedelta(days=60),  # Corpus Christi
    ]
    return frozenset(fixos + moveis)


def eh_dia_util(d: date, vigente_em: date | None = None) -> bool:
    return d.weekday() < 5 and d not in feriados(d.year, vigente_em)


def proximo_dia_util(d: date) -> date:
    """O próprio dia, se for útil; senão o próximo dia útil."""
    while not eh_dia_util(d):
        d += timedelta(days=1)
    return d


def dias_uteis(inicio: date, fim: date) -> int:
    """Dias úteis em [inicio, fim): cada dia útil que "rende" juros entre as duas datas.

    Usa o calendário vigente em `inicio` (a data-base), como o mercado contava naquele dia.
    """
    if fim < inicio:
        return -dias_uteis(fim, inicio)
    total = 0
    d = inicio
    while d < fim:
        if eh_dia_util(d, vigente_em=inicio):
            total += 1
        d += timedelta(days=1)
    return total
