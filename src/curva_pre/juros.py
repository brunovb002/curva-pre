"""Conversões entre taxa, fator e PU na convenção exponencial base 252."""

BASE = 252
NOCIONAL_DI1 = 100_000.0
NOCIONAL_LTN = 1_000.0


def fator(taxa: float, du: int) -> float:
    """Quanto R$ 1 vira em `du` dias úteis a uma taxa anual `taxa`."""
    return (1 + taxa) ** (du / BASE)


def taxa_de_fator(f: float, du: int) -> float:
    """Taxa anual equivalente a um fator acumulado em `du` dias úteis."""
    return f ** (BASE / du) - 1


def pu(taxa: float, du: int, nocional: float = NOCIONAL_DI1) -> float:
    """Valor presente do nocional descontado pela taxa."""
    return nocional / fator(taxa, du)


def taxa_de_pu(preco: float, du: int, nocional: float = NOCIONAL_DI1) -> float:
    """Taxa implícita em um PU."""
    return taxa_de_fator(nocional / preco, du)
