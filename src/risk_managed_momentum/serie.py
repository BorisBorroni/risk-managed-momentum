"""Costruzione delle serie mensili usate da tutti gli script, cosi' replica, test e grafici
calcolano esattamente le stesse cose.

Tutte le serie sono rendimenti mensili in eccesso:
- wml, mom: lungo-corti autofinanziati, gia' in eccesso;
- vincenti: decile vincente solo lungo meno RF;
- mercato: Mkt-RF di French;
- versioni "_gestita": peso x serie, con il peso dalla varianza dei 126 giorni precedenti della
  serie giornaliera corrispondente (per i vincenti, decile vincente giornaliero meno RF giornaliero).
"""
import pandas as pd

from . import dati, strategia


def costruisci(d):
    """Serie mensili semplici, gestite e pesi, a partire dai dati di French caricati."""
    rf_g = d.fattori_g["RF"].reindex(d.decili_g.index)
    giornaliere = {
        "wml": dati.wml(d.decili_g),
        "mom": d.mom_g,
        "vincenti": d.decili_g[dati.VINCENTI] - rf_g,
    }
    rf_m = d.fattori_m["RF"].reindex(d.decili_m.index)
    mensili = {
        "wml": dati.wml(d.decili_m),
        "mom": d.mom_m,
        "vincenti": d.decili_m[dati.VINCENTI] - rf_m,
    }
    semplici, gestite, pesi = {}, {}, {}
    for nome, m in mensili.items():
        semplici[nome] = m.rename(nome)
        g, w = strategia.gestita(m.rename(nome), giornaliere[nome])
        gestite[nome] = g.rename(f"{nome}_gestita")
        pesi[nome] = w
    tabella = pd.concat([*semplici.values(), *gestite.values()], axis=1)
    tabella["mercato"] = d.fattori_m["Mkt-RF"].reindex(tabella.index)
    tabella["rf"] = rf_m
    tabella["mercato_piu_wml_gestita"] = tabella["mercato"] + tabella["wml_gestita"]
    pesi = pd.DataFrame(pesi)
    return tabella, pesi


def finestra(tabella, inizio, fine, colonne):
    """Righe tra inizio e fine (inclusi) in cui tutte le colonne richieste esistono."""
    x = tabella.loc[inizio:fine, colonne]
    return x.dropna()
