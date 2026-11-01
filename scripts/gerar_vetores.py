"""Gera vetores de teste da flat-forward para outras implementações (ex.: o TypeScript do site).

    python scripts/gerar_vetores.py historico vetores/flat_forward.json

Pega algumas curvas reais do histórico e calcula, com o motor Python, a taxa spot
e a forward em vários prazos. A outra implementação tem que chegar nos mesmos números.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from curva_pre.curva import CurvaPre  # noqa: E402

DATAS = ["2008-10-01", "2015-12-30", "2020-08-05", "2026-10-30"]


def main(pasta: Path, saida: Path) -> None:
    casos = []
    for data in DATAS:
        curvas = json.loads((pasta / f"{data[:4]}.json").read_text(encoding="utf-8"))["curvas"]
        vertices = [[du, taxa] for du, taxa, _ in curvas[data]["v"]]
        curva = CurvaPre([(du, taxa / 100) for du, taxa in vertices])
        prazos = sorted({1, 5, 21, 63, 126, 252, 300, 504, curva.prazo_maximo} & set(range(1, curva.prazo_maximo + 1)))
        casos.append({
            "data": data,
            "vertices": vertices,
            "taxa": [[du, curva.taxa(du) * 100] for du in prazos],
            "forward": [[a, b, curva.forward(a, b) * 100] for a, b in zip(prazos, prazos[1:])],
        })
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps({"unidade": "% a.a. base 252", "casos": casos}, indent=1), encoding="utf-8")
    print(f"{len(casos)} casos salvos em {saida}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
