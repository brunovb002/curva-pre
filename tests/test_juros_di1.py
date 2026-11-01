from datetime import date

import pytest

from curva_pre.di1 import taxa_implicita, vencimento
from curva_pre.juros import fator, pu, taxa_de_pu


def test_fator_meio_ano():
    # 10% a.a. por 126 du = 1,10^0,5
    assert fator(0.10, 126) == pytest.approx(1.048809, abs=1e-6)


def test_pu_do_exemplo():
    assert pu(0.10, 126) == pytest.approx(95_346.26, abs=0.01)


def test_ida_e_volta_taxa_pu():
    assert taxa_de_pu(pu(0.1375, 417), 417) == pytest.approx(0.1375)


@pytest.mark.parametrize("codigo, esperado", [
    ("DI1F27", date(2027, 1, 4)),  # 01/01 é feriado, 02 e 03 fim de semana
    ("DI1N26", date(2026, 7, 1)),
    ("j28", date(2028, 4, 3)),     # 01/04/2028 é sábado
])
def test_vencimento(codigo, esperado):
    assert vencimento(codigo) == esperado


@pytest.mark.parametrize("codigo", ["DI1A27", "DI1F2", "XYZ"])
def test_vencimento_codigo_invalido(codigo):
    with pytest.raises(ValueError):
        vencimento(codigo)


def test_taxa_implicita():
    data_base = date(2026, 10, 30)
    du, taxa = taxa_implicita("DI1F27", pu(0.15, 42), data_base)
    assert du == 42
    assert taxa == pytest.approx(0.15)
