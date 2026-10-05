"""Controlli di qualita' sui dati grezzi, prima di calcolare qualsiasi rendimento di strategia.

Per ogni file: periodo, numero di righe, buchi nel calendario. Poi tre controlli incrociati:
1. il fattore Mom si ricostruisce dai 6 portafogli taglia x momentum (mensile e giornaliero);
2. i quattro file giornalieri hanno gli stessi giorni di borsa;
3. il mercato mensile coincide con il composto dei rendimenti giornalieri dello stesso mese.
Stampa un riepilogo e si ferma con errore se un controllo non passa.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from risk_managed_momentum import dati  # noqa: E402

TOLLERANZA_MOM = 0.0002      # 0,02 punti percentuali: i file sono arrotondati a 0,01
TOLLERANZA_COMPOSTO = 0.002  # 0,2 punti: arrotondamento dei giornalieri accumulato in un mese


def mesi_mancanti(indice):
    attesi = pd.date_range(indice[0], indice[-1], freq="ME")
    return len(attesi.difference(indice))


def main():
    d = dati.carica()
    problemi = []

    print("File letti (solo il primo blocco, pesato per capitalizzazione):")
    for nome in dati.FILE:
        x = getattr(d, nome)
        buchi = mesi_mancanti(x.index) if nome.endswith("_m") else "-"
        print(f"  {nome:10s} {x.index[0].date()} -> {x.index[-1].date()}  righe {len(x):6d}  "
              f"NaN {int(x.isna().to_numpy().sum())}  mesi mancanti {buchi}")
        if x.isna().to_numpy().any():
            problemi.append(f"valori mancanti in {nome}")
        if nome.endswith("_m") and buchi:
            problemi.append(f"mesi mancanti in {nome}")

    for nome in ("mom_m", "sei_m", "decili_m"):
        if not getattr(d, nome).index.equals(d.decili_m.index):
            problemi.append(f"{nome}: mesi diversi dai decili")

    giorni = d.decili_g.index
    for nome in ("fattori_g", "mom_g", "sei_g"):
        x = getattr(d, nome)
        comuni = x.index.intersection(giorni)
        print(f"  giorni di {nome} in comune con i decili giornalieri: {len(comuni)} su {len(giorni)}")
        if len(comuni) != len(giorni):
            problemi.append(f"{nome}: giorni diversi dai decili")

    print("\nRicostruzione del fattore Mom dai 6 portafogli (differenza in punti percentuali):")
    for frequenza, sei, mom in (("mensile", d.sei_m, d.mom_m), ("giornaliero", d.sei_g, d.mom_g)):
        diff = (dati.mom_dai_sei(sei) - mom).abs()
        print(f"  {frequenza:12s} massima {100 * diff.max():.4f}  media {100 * diff.mean():.5f}")
        if diff.max() > TOLLERANZA_MOM:
            problemi.append(f"Mom {frequenza} non ricostruito")

    print("\nMercato mensile contro composto dei giornalieri (Mkt-RF + RF):")
    mkt_g = d.fattori_g["Mkt-RF"] + d.fattori_g["RF"]
    composto = (1 + mkt_g).groupby(mkt_g.index.to_period("M")).prod() - 1
    composto.index = composto.index.to_timestamp(how="end").normalize()
    mkt_m = (d.fattori_m["Mkt-RF"] + d.fattori_m["RF"]).loc[composto.index[1]:]
    diff = (composto.reindex(mkt_m.index) - mkt_m).abs()
    print(f"  mesi confrontati {diff.notna().sum()}  differenza massima {100 * diff.max():.3f} punti "
          f"({diff.idxmax():%Y-%m})  mesi oltre 0,2 punti {int((diff > TOLLERANZA_COMPOSTO).sum())}")
    if (diff > TOLLERANZA_COMPOSTO).mean() > 0.01:
        problemi.append("mercato mensile e giornaliero non coerenti")

    print("\nCalendario dei giorni di borsa:")
    salti = pd.Series(giorni[1:] - giorni[:-1], index=giorni[1:])
    for giorno, salto in salti[salti > pd.Timedelta(days=5)].items():
        print(f"  {salto.days} giorni tra due sedute, fino al {giorno.date()}")
    per_mese = pd.Series(1, index=giorni).groupby(giorni.to_period("M")).sum().iloc[1:]
    sabati = int((giorni.dayofweek == 5).sum())
    print(f"  sabati di borsa: {sabati} (l'ultimo il {giorni[giorni.dayofweek == 5][-1].date()})")
    print(f"  giorni di borsa per mese in media: {per_mese.loc[:'1952-05'].mean():.1f} fino a maggio 1952, "
          f"{per_mese.loc['1952-06':].mean():.1f} da giugno 1952")

    versione = dati.stessa_versione()
    print(f"\nZip identici a quelli usati nel repository (versione CRSP 202608): {sum(versione.values())} su {len(versione)}")
    if not all(versione.values()):
        print("  Con dati di una versione diversa i numeri possono cambiare e lo script 04 puo' rifiutarsi di partire.")

    if problemi:
        sys.exit("PROBLEMI: " + "; ".join(problemi))
    print("\nTutti i controlli sono passati.")


if __name__ == "__main__":
    main()
