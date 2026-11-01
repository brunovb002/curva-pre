"""Capa do projeto: a curva pré do último pregão de cada ano, de 2005 até hoje, sobrepostas.

    python scripts/gerar_capa.py historico capa.png

Precisa do Pillow (pip install pillow). Gera 900x1200 (3:4), o formato dos cards do site.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from curva_pre.curva import CurvaPre  # noqa: E402

S = 2  # desenha em 2x e reduz no fim, para as linhas ficarem suaves
W, H = 900 * S, 1200 * S
ESQ, DIR, TOPO, BASE_Y = 90 * S, 90 * S, 170 * S, 330 * S
INDIGO = (59, 74, 140)
PRAZO_MAX = 252 * 6
FONTE = "C:/Windows/Fonts/consola.ttf"


def mistura(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def curvas_por_ano(pasta: Path):
    for arquivo in sorted(pasta.glob("[0-9][0-9][0-9][0-9].json")):
        curvas = json.loads(arquivo.read_text(encoding="utf-8"))["curvas"]
        ultima = max(curvas)
        curva = CurvaPre([(du, taxa / 100) for du, taxa, _ in curvas[ultima]["v"]])
        ate = min(curva.prazo_maximo, PRAZO_MAX)
        yield int(arquivo.stem), [(du, curva.taxa(du) * 100) for du in range(1, ate + 1, 3)]


def main(pasta: Path, saida: Path) -> None:
    anos = list(curvas_por_ano(pasta))
    taxas = [t for _, pts in anos for _, t in pts]
    lo, hi = min(taxas) - 0.5, max(taxas) + 0.5
    x = lambda du: ESQ + du / PRAZO_MAX * (W - ESQ - DIR)
    y = lambda t: TOPO + (hi - t) / (hi - lo) * (H - TOPO - BASE_Y)

    # Fundo: o mesmo degradê índigo dos cards sem capa.
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    claro, escuro = mistura(INDIGO, (255, 255, 255), 0.25), mistura(INDIGO, (0, 0, 0), 0.35)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=mistura(claro, INDIGO, t / 0.55) if t < 0.55 else mistura(INDIGO, escuro, (t - 0.55) / 0.45))

    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c = ImageDraw.Draw(camada)
    fonte = ImageFont.truetype(FONTE, 28 * S)
    for k, (ano, pts) in enumerate(anos[:-1]):
        alfa = round(70 + 100 * k / max(1, len(anos) - 2))  # as mais recentes um pouco mais visíveis
        c.line([(x(du), y(t)) for du, t in pts], fill=(255, 255, 255, alfa), width=3 * S, joint="curve")
    ano, pts = anos[-1]
    c.line([(x(du), y(t)) for du, t in pts], fill=(255, 255, 255, 255), width=8 * S, joint="curve")

    # Ano no fim das curvas mais alta, mais baixa e da atual.
    nivel = lambda item: item[1][-1][1]
    for alvo, alfa in ((max(anos[:-1], key=nivel), 150), (min(anos[:-1], key=nivel), 150), (anos[-1], 255)):
        a, p = alvo
        du, t = p[-1]
        c.text((x(du) + 12 * S, y(t)), str(a), font=fonte, fill=(255, 255, 255, alfa), anchor="lm")

    titulo = ImageFont.truetype(FONTE, 66 * S)
    c.text((ESQ, H - 205 * S), "curva pré", font=titulo, fill=(255, 255, 255, 255))
    c.text((ESQ, H - 130 * S), f"{anos[0][0]}–{anos[-1][0]} · % a.a. · até 6 anos", font=fonte, fill=(255, 255, 255, 170))

    img = Image.alpha_composite(img.convert("RGBA"), camada).convert("RGB")
    img.resize((W // S, H // S), Image.LANCZOS).save(saida, optimize=True)
    print(f"Capa salva em {saida} ({len(anos)} curvas, de {lo + 0.5:.1f}% a {hi - 0.5:.1f}%)")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
