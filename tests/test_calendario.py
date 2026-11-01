from datetime import date

import pytest

from curva_pre.calendario import dias_uteis, eh_dia_util, feriados, pascoa, proximo_dia_util


@pytest.mark.parametrize("ano, esperado", [
    (2024, date(2024, 3, 31)),
    (2025, date(2025, 4, 20)),
    (2026, date(2026, 4, 5)),
])
def test_pascoa(ano, esperado):
    assert pascoa(ano) == esperado


def test_feriados_moveis_2026():
    f = feriados(2026)
    assert date(2026, 2, 16) in f  # Carnaval segunda
    assert date(2026, 2, 17) in f  # Carnaval terça
    assert date(2026, 4, 3) in f   # Sexta-feira Santa
    assert date(2026, 6, 4) in f   # Corpus Christi


def test_consciencia_negra_so_a_partir_de_2024():
    assert date(2023, 11, 20) not in feriados(2023)
    assert date(2024, 11, 20) in feriados(2024)


def test_calendario_vigente_na_data_base():
    # Em 2022 o 20/11/2024 ainda não era feriado; a contagem feita em 2022 o inclui.
    assert date(2024, 11, 20) not in feriados(2024, vigente_em=date(2022, 12, 29))
    assert date(2024, 11, 20) in feriados(2024, vigente_em=date(2023, 12, 26))
    # 29/12/2022 até 01/01/2029: 1508 du como o Tesouro contava na época; com o
    # calendário atual seriam 1504 (quatro 20/11 em dia de semana entre 2024 e 2028)
    assert dias_uteis(date(2022, 12, 29), date(2029, 1, 1)) == 1508


def test_fim_de_semana_nao_e_util():
    assert not eh_dia_util(date(2026, 10, 31))  # sábado
    assert eh_dia_util(date(2026, 10, 30))      # sexta


def test_dias_uteis_sexta_para_segunda():
    assert dias_uteis(date(2026, 10, 30), date(2026, 11, 3)) == 1  # segunda 2/11 é Finados


def test_dias_uteis_atravessando_carnaval():
    # sexta 13/02 rende; segunda e terça de Carnaval não; quarta 18/02 é o fim (exclusivo)
    assert dias_uteis(date(2026, 2, 13), date(2026, 2, 18)) == 1


def test_proximo_dia_util():
    assert proximo_dia_util(date(2027, 1, 1)) == date(2027, 1, 4)
