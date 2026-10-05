"""Momentum gestito per il rischio (Barroso e Santa-Clara 2015).

Regola, mese per mese:
1. varianza prevista del mese t = 21 x media dei quadrati degli ultimi 126 rendimenti giornalieri
   della strategia, fino all'ultimo giorno di borsa del mese t-1 (nessun dato del mese t);
2. volatilita' annua prevista = radice di (12 x varianza mensile);
3. peso del mese t = volatilita' obiettivo (12%) / volatilita' prevista, senza tetto;
4. rendimento gestito del mese t = peso x rendimento mensile della strategia.
La media dei quadrati non toglie la media dei rendimenti, come nel paper.
"""
import numpy as np
import pandas as pd

OBIETTIVO = 0.12
FINESTRA = 126
GIORNI_MESE = 21


def varianza_prevista(giornalieri, finestra=FINESTRA, giorni_mese=GIORNI_MESE):
    """Varianza mensile prevista per ogni mese, indicizzata con la fine del mese in cui si usa.

    Il valore con data 1927-06-30 e' calcolato con i giorni fino all'ultimo giorno di borsa di
    maggio 1927. I mesi senza 126 giorni precedenti restano esclusi. La serie giornaliera deve
    finire con un mese completo (i file di French finiscono sempre a fine mese).
    """
    media_quadrati = (giornalieri ** 2).rolling(finestra, min_periods=finestra).mean()
    mesi = giornalieri.index.to_period("M")
    ultimo_giorno = media_quadrati.groupby(mesi).tail(1)
    stima = pd.Series(giorni_mese * ultimo_giorno.to_numpy(), index=ultimo_giorno.index.to_period("M") + 1)
    stima.index = stima.index.to_timestamp(how="end").normalize()
    stima.index.name = "data"
    return stima.dropna().rename("varianza_prevista")


def volatilita_annua(varianza_mensile):
    return np.sqrt(12 * varianza_mensile)


def pesi(giornalieri, obiettivo=OBIETTIVO, finestra=FINESTRA):
    """Peso del mese t: obiettivo / volatilita' annua prevista con i dati fino a t-1."""
    return (obiettivo / volatilita_annua(varianza_prevista(giornalieri, finestra))).rename("peso")


def gestita(mensili, giornalieri, obiettivo=OBIETTIVO, finestra=FINESTRA):
    """Rendimenti mensili gestiti e pesi, solo nei mesi in cui il peso esiste."""
    w = pesi(giornalieri, obiettivo, finestra)
    comuni = mensili.index.intersection(w.index)
    w = w.loc[comuni]
    return (w * mensili.loc[comuni]).rename(f"{mensili.name}_gestita"), w
