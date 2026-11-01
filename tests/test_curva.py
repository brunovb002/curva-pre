import pytest

from curva_pre.curva import CurvaPre

# Exemplo da revisão de conceitos: 1 ano a 10%, 2 anos a 11%
CURVA = CurvaPre([(252, 0.10), (504, 0.11)])


def test_vertices_sao_respeitados():
    assert CURVA.taxa(252) == pytest.approx(0.10)
    assert CURVA.taxa(504) == pytest.approx(0.11)


def test_forward_entre_vertices():
    assert CURVA.forward(252, 504) == pytest.approx(0.12009, abs=1e-5)


def test_interpolacao_flat_forward():
    # 1,5 ano: 10,67%, e não os 10,5% da média simples
    assert CURVA.taxa(378) == pytest.approx(0.1067, abs=1e-4)


def test_forward_constante_dentro_do_intervalo():
    assert CURVA.forward(300, 400) == pytest.approx(CURVA.forward(252, 504))


def test_antes_do_primeiro_vertice_vale_a_taxa_dele():
    assert CURVA.taxa(10) == pytest.approx(0.10)


def test_fora_da_curva():
    with pytest.raises(ValueError):
        CURVA.taxa(505)


def test_vertices_invalidos():
    with pytest.raises(ValueError):
        CurvaPre([])
    with pytest.raises(ValueError):
        CurvaPre([(252, 0.10), (252, 0.11)])
