"""Curva pré a partir das LTNs do Tesouro e do CDI do Banco Central.

    python -m curva_pre dia                         # curva da última data, na tela
    python -m curva_pre dia --data 2026-10-30 --saida curva.json
    python -m curva_pre historico --desde 2005      # um JSON por ano em historico/
    python -m curva_pre historico                   # só o ano atual (uso diário)
"""

import argparse
import json
from datetime import date
from pathlib import Path

from . import historico
from .fontes import bcb, tesouro
from .montagem import montar_curva, montar_vertices, tabela

CSV_PADRAO = Path("dados/precotaxatesourodireto.csv")


def preparar_csv(args) -> Path:
    if args.atualizar or not args.csv.exists():
        print(f"Baixando dados do Tesouro para {args.csv}...")
        tesouro.baixar_csv(args.csv)
    return args.csv


def cmd_dia(args) -> None:
    caminho = preparar_csv(args)
    data_base = args.data or tesouro.ultima_data_base(caminho)
    ltns = tesouro.ler_ltns(caminho, data_base)
    if not ltns:
        raise SystemExit(f"Nenhuma LTN no Tesouro para {data_base}")
    data_cdi, cdi = bcb.buscar_serie(data_base, data_base).em(data_base)

    vertices, descartadas = montar_vertices(data_base, ltns, cdi)
    for t in descartadas:
        print(f"Aviso: LTN {t.vencimento} descartada (PU não bate com a taxa publicada)")
    curva = montar_curva(vertices)

    resultado = {
        "data_base": data_base.isoformat(),
        "fontes": {
            "ltn": "Tesouro Direto (Tesouro Transparente, ODbL), PU de recompra",
            "cdi": f"BCB SGS série 12, observação de {data_cdi.isoformat()}",
        },
        "vertices": [
            {
                "nome": v.nome,
                "vencimento": v.vencimento.isoformat() if v.vencimento else None,
                "du": v.du,
                "taxa": v.taxa,
                "pu": v.pu,
            }
            for v in vertices
        ],
        "curva": tabela(curva, args.passo),
    }

    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(texto, encoding="utf-8")
        print(f"Curva de {data_base} salva em {args.saida}")
    else:
        print(texto)


def cmd_historico(args) -> None:
    caminho = preparar_csv(args)
    desde = date(args.desde, 1, 1)
    por_data = tesouro.ltns_por_data(caminho, desde=desde)
    if not por_data:
        raise SystemExit(f"Nenhuma LTN no Tesouro desde {desde}")
    print(f"{len(por_data)} datas de {min(por_data)} a {max(por_data)}. Baixando o CDI...")
    cdi = bcb.buscar_serie(min(por_data), max(por_data))

    anos, avisos = historico.gerar(por_data, cdi)
    for aviso in avisos:
        print("Aviso:", aviso)
    indice = historico.salvar(anos, args.saida)
    print(f"Anos {min(anos)}-{max(anos)} salvos em {args.saida} (histórico de {indice['primeira']} a {indice['ultima']})")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="curva_pre", description=__doc__.splitlines()[0])
    p.add_argument("--csv", type=Path, default=CSV_PADRAO, help="CSV do Tesouro Direto")
    p.add_argument("--atualizar", action="store_true", help="baixa o CSV de novo")
    sub = p.add_subparsers(required=True)

    dia = sub.add_parser("dia", help="curva de uma data, com grade spot/forward")
    dia.add_argument("--data", type=date.fromisoformat, help="data-base (AAAA-MM-DD)")
    dia.add_argument("--passo", type=int, default=21, help="passo da grade em dias úteis")
    dia.add_argument("--saida", type=Path, help="arquivo JSON (padrão: imprime na tela)")
    dia.set_defaults(func=cmd_dia)

    hist = sub.add_parser("historico", help="vértices de todas as datas, um JSON por ano")
    hist.add_argument("--desde", type=int, default=date.today().year, help="primeiro ano (padrão: o atual)")
    hist.add_argument("--saida", type=Path, default=Path("historico"), help="pasta de saída")
    hist.set_defaults(func=cmd_historico)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
