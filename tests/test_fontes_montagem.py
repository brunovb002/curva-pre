import json
from datetime import date
from pathlib import Path

import pytest

from curva_pre.fontes.bcb import SerieCDI, serie_de_json
from curva_pre.fontes.tesouro import LTN, ler_ltns, ltns_por_data, ultima_data_base
from curva_pre.historico import gerar, salvar
from curva_pre.juros import pu
from curva_pre.montagem import montar_curva, montar_vertices, tabela

FIXTURES = Path(__file__).parent / "fixtures"
CSV = FIXTURES / "tesouro_amostra.csv"
DATA = date(2026, 10, 30)
CDI = SerieCDI(serie_de_json((FIXTURES / "bcb_cdi.json").read_text()))


def test_le_so_ltn_da_data():
    ltns = ler_ltns(CSV, DATA)
    assert [t.vencimento.year for t in ltns] == [2027, 2028, 2029, 2031, 2032]
    assert ltns[0].pu == pytest.approx(978.97)


def test_ltns_por_data():
    por_data = ltns_por_data(CSV)
    assert list(por_data) == [date(2026, 10, 29), DATA]
    assert all(len(ltns) == 5 for ltns in por_data.values())


def test_ultima_data_base():
    assert ultima_data_base(CSV) == DATA


def test_cdi_mais_recente_ate_a_data():
    dia, taxa = CDI.em(DATA)
    assert dia == date(2026, 10, 29)
    assert taxa == pytest.approx(0.1365, abs=1e-4)  # 0,050788% a.d. em base 252


def test_cdi_sem_dados():
    with pytest.raises(ValueError):
        CDI.em(date(2026, 1, 1))


def test_taxa_do_pu_bate_com_a_publicada_pelo_tesouro():
    # Valida calendário + conversão: nossa taxa, calculada do PU, tem que bater
    # com a taxa (arredondada em 2 casas) que o Tesouro publica.
    ltns = ler_ltns(CSV, DATA)
    vertices, descartadas = montar_vertices(DATA, ltns, cdi_anual=0.1365)
    assert descartadas == []
    for ltn, v in zip(ltns, vertices[1:]):
        assert v.taxa == pytest.approx(ltn.taxa_publicada, abs=0.00006)


def test_descarta_ltn_com_pu_inconsistente():
    venc = date(2028, 1, 1)
    boa = LTN(venc, pu(0.14, 293, 1000), 0.14)
    errada = LTN(venc, pu(0.14, 293, 1000), 0.18)  # taxa publicada não bate com o PU
    vertices, descartadas = montar_vertices(DATA, [boa, errada], cdi_anual=0.1365)
    assert len(vertices) == 2 and descartadas == [errada]


def test_ignora_ltn_vencendo():
    vencendo = LTN(date(2026, 11, 3), 999.0, 0.13)
    vertices, _ = montar_vertices(DATA, [vencendo], cdi_anual=0.1365)
    assert [v.nome for v in vertices] == ["CDI"]


def test_curva_do_dia():
    vertices, _ = montar_vertices(DATA, ler_ltns(CSV, DATA), cdi_anual=0.1365)
    assert vertices[0].nome == "CDI" and vertices[0].du == 1
    assert vertices[1].du == 42  # 30/10/2026 até 01/01/2027
    curva = montar_curva(vertices)
    linhas = tabela(curva, passo=21)
    assert linhas[0]["du"] == 21
    assert linhas[-1]["du"] <= curva.prazo_maximo
    for v in vertices:
        assert curva.taxa(v.du) == pytest.approx(v.taxa)


def test_historico_compacto(tmp_path):
    anos, avisos = gerar(ltns_por_data(CSV), CDI)
    assert avisos == []
    curvas = anos[2026]["curvas"]
    assert list(curvas) == ["2026-10-29", "2026-10-30"]
    assert curvas["2026-10-30"]["cdi"] == "2026-10-29"
    du, taxa, venc = curvas["2026-10-30"]["v"][0]
    assert (du, venc) == (1, None) and taxa == pytest.approx(13.65, abs=1e-4)
    assert curvas["2026-10-30"]["v"][1][0] == 42 and curvas["2026-10-30"]["v"][1][2] == "2027-01-01"

    indice = salvar(anos, tmp_path)
    assert indice["anos"] == [2026]
    assert (indice["primeira"], indice["ultima"]) == ("2026-10-29", "2026-10-30")
    assert json.loads((tmp_path / "2026.json").read_text())["curvas"] == curvas
