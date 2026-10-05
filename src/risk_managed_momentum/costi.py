"""Costi come ipotesi esplicite (i file di French non contengono il turnover dei portafogli).

Per ogni mese, con peso w (1 per le strategie non gestite):
- prestito titoli: tasso annuo / 12 x nozionale corto (w per la strategia lungo-corta, 0 per il solo lungo);
- negoziazione: tasso annuo / 12 x esposizione lorda (2w per la strategia lungo-corta, w per il solo lungo);
- variazione del peso: costo per lato x esposizione lorda scambiata (2|dw| o |dw|).
Il primo mese non paga la variazione del peso (la posizione iniziale non e' un ribilanciamento).
"""
import pandas as pd

SCENARI = {
    "lordo": {"prestito": 0.0, "negoziazione": 0.0, "variazione": 0.0},
    "medio": {"prestito": 0.005, "negoziazione": 0.02, "variazione": 0.0010},
    "alto": {"prestito": 0.01, "negoziazione": 0.04, "variazione": 0.0020},
}


def costo_mensile(peso, scenario, lungo_corto=True):
    """Costo di ogni mese (frazione del capitale) per una serie di pesi."""
    c = SCENARI[scenario]
    gambe = 2 if lungo_corto else 1
    corto = peso if lungo_corto else 0 * peso
    variazione = peso.diff().abs().fillna(0.0)
    return c["prestito"] / 12 * corto + c["negoziazione"] / 12 * gambe * peso + c["variazione"] * gambe * variazione


def netto(rendimenti, peso, scenario, lungo_corto=True):
    """Rendimenti mensili al netto dei costi dello scenario."""
    peso = pd.Series(peso, index=rendimenti.index) if not isinstance(peso, pd.Series) else peso.loc[rendimenti.index]
    return rendimenti - costo_mensile(peso, scenario, lungo_corto)
