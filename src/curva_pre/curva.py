"""Curva pré com interpolação flat-forward."""

from bisect import bisect_left

from .juros import BASE, fator, taxa_de_fator


class CurvaPre:
    """Curva de juros pré a partir de vértices (du, taxa anual base 252).

    Entre dois vértices a taxa a termo é constante (flat-forward). Antes do
    primeiro vértice vale a taxa dele; depois do último a curva não é definida.
    """

    def __init__(self, vertices: list[tuple[int, float]]):
        if not vertices:
            raise ValueError("a curva precisa de pelo menos um vértice")
        vertices = sorted(vertices)
        prazos = [du for du, _ in vertices]
        if prazos[0] <= 0:
            raise ValueError("prazos dos vértices devem ser positivos")
        if len(set(prazos)) != len(prazos):
            raise ValueError("prazos dos vértices repetidos")

        self.vertices = vertices
        # Nó (0, 1.0): hoje, R$ 1 vale R$ 1. Interpolamos sempre nos fatores.
        self._prazos = [0] + prazos
        self._fatores = [1.0] + [fator(taxa, du) for du, taxa in vertices]

    @property
    def prazo_maximo(self) -> int:
        return self._prazos[-1]

    def fator(self, du: int) -> float:
        if du < 0 or du > self.prazo_maximo:
            raise ValueError(f"prazo {du} fora da curva [0, {self.prazo_maximo}]")
        i = bisect_left(self._prazos, du)
        if self._prazos[i] == du:
            return self._fatores[i]
        t1, t2 = self._prazos[i - 1], self._prazos[i]
        f1, f2 = self._fatores[i - 1], self._fatores[i]
        return f1 * (f2 / f1) ** ((du - t1) / (t2 - t1))

    def taxa(self, du: int) -> float:
        """Taxa spot anual de hoje até `du`."""
        if du <= 0:
            raise ValueError("prazo deve ser positivo")
        return taxa_de_fator(self.fator(du), du)

    def forward(self, du1: int, du2: int) -> float:
        """Taxa a termo anual entre `du1` e `du2`."""
        if du2 <= du1:
            raise ValueError("du2 deve ser maior que du1")
        return (self.fator(du2) / self.fator(du1)) ** (BASE / (du2 - du1)) - 1
