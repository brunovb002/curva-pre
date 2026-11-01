"""CDI pela API pública do Banco Central (SGS)."""

import json
import urllib.request
from bisect import bisect_right
from datetime import date, datetime, timedelta

from ..juros import BASE

# Série 12: taxa DI diária, em % ao dia. A API devolve no máximo 10 anos por consulta.
URL_SERIE_CDI = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={ini}&dataFinal={fim}"


def _baixar(ini: date, fim: date) -> str:
    url = URL_SERIE_CDI.format(ini=ini.strftime("%d/%m/%Y"), fim=fim.strftime("%d/%m/%Y"))
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8")


def serie_de_json(texto: str) -> dict[date, float]:
    """{data: CDI anual base 252} a partir da resposta da API."""
    return {
        datetime.strptime(o["data"], "%d/%m/%Y").date(): (1 + float(o["valor"]) / 100) ** BASE - 1
        for o in json.loads(texto)
    }


class SerieCDI:
    def __init__(self, observacoes: dict[date, float]):
        self._datas = sorted(observacoes)
        self._valores = [observacoes[d] for d in self._datas]

    def em(self, data_base: date) -> tuple[date, float]:
        """(data da observação, CDI anual) mais recente até `data_base`.

        O BCB publica o CDI do dia só no dia útil seguinte; até lá vale o anterior.
        """
        i = bisect_right(self._datas, data_base)
        if i == 0:
            raise ValueError(f"sem CDI publicado até {data_base}")
        return self._datas[i - 1], self._valores[i - 1]


def buscar_serie(inicio: date, fim: date) -> SerieCDI:
    """Baixa o CDI entre as datas, um ano por consulta."""
    observacoes: dict[date, float] = {}
    ini = inicio - timedelta(days=10)  # garante o CDI anterior à primeira data-base
    while ini <= fim:
        fim_bloco = min(date(ini.year, 12, 31), fim)
        observacoes |= serie_de_json(_baixar(ini, fim_bloco))
        ini = fim_bloco + timedelta(days=1)
    return SerieCDI(observacoes)
