"""Lettura dei file della biblioteca di Kenneth R. French (zip con un CSV dentro).

Ogni file contiene piu' blocchi uno sotto l'altro (pesati per capitalizzazione, pesati in modo
uguale, annuali, numero di imprese). Leggo solo il primo blocco, che nei file usati e' sempre
quello mensile o giornaliero pesato per capitalizzazione. I valori sono in percento: li
restituisco come rendimenti decimali (1,5% -> 0.015).

Indici: date di fine mese per i file mensili (192701 -> 1927-01-31), date di borsa per i
giornalieri (19261103 -> 1926-11-03).
"""
import hashlib
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

RADICE = Path(__file__).resolve().parents[2]
CARTELLA_DATI = RADICE / "data" / "raw"

FILE = {
    "fattori_m": "F-F_Research_Data_Factors_CSV.zip",
    "fattori_g": "F-F_Research_Data_Factors_daily_CSV.zip",
    "mom_m": "F-F_Momentum_Factor_CSV.zip",
    "mom_g": "F-F_Momentum_Factor_daily_CSV.zip",
    "sei_m": "6_Portfolios_ME_Prior_12_2_CSV.zip",
    "sei_g": "6_Portfolios_ME_Prior_12_2_Daily_CSV.zip",
    "decili_m": "10_Portfolios_Prior_12_2_CSV.zip",
    "decili_g": "10_Portfolios_Prior_12_2_Daily_CSV.zip",
}
# impronte SHA-256 degli zip usati per i numeri del repository (versione CRSP 202608): French
# pubblica solo l'ultima versione, quindi con file scaricati piu' tardi i numeri possono cambiare
IMPRONTE = {
    "F-F_Research_Data_Factors_CSV.zip": "593f4fbef03181bc0b22ff6292f217689dd1fb79355049ca905d95b262040a66",
    "F-F_Research_Data_Factors_daily_CSV.zip": "2f29e22546069914890a712680a6f81f3680ebc3543b52864484d209ca13a7db",
    "F-F_Momentum_Factor_CSV.zip": "c06d1c2e9a5e4f6985879722f23c6bb585f46b34eaf3fcb681d4de887e353f3e",
    "F-F_Momentum_Factor_daily_CSV.zip": "ecf82b116e6ec56d2b79a2f27bd1d1598c217b5c6c25caa55b945bdd8a2c0b78",
    "6_Portfolios_ME_Prior_12_2_CSV.zip": "68d90a218235b2c14e67eb1b7b1acd2d9fcc6b626bc4c64e854e2788bcf44bf3",
    "6_Portfolios_ME_Prior_12_2_Daily_CSV.zip": "7b7bbfdfa4833adf64ed9b473b77e15ebccbb4943f880206e888685e1261ce87",
    "10_Portfolios_Prior_12_2_CSV.zip": "dce836c412a4ce0a9c4bdb2d4f3a613672b6ffd10e434132e2a21bf9bb18f001",
    "10_Portfolios_Prior_12_2_Daily_CSV.zip": "3de44baadc727518a3e78f772d103055197d606175e3091b39fff8be97302214",
}
MANCANTI = (-99.99, -999.0)
VINCENTI, PERDENTI = "Hi PRIOR", "Lo PRIOR"


def leggi_testo(testo):
    """Primo blocco di dati di un file di French come DataFrame di rendimenti decimali.

    Il blocco comincia con la riga di intestazione (che inizia con una virgola) e finisce alla
    prima riga che non comincia con una data di 6 cifre (mensile) o 8 cifre (giornaliera).
    """
    righe = testo.splitlines()
    inizio = next(i for i, r in enumerate(righe) if r.startswith(","))
    colonne = [c.strip() for c in righe[inizio].split(",")[1:]]
    date, valori = [], []
    for riga in righe[inizio + 1:]:
        campi = [c.strip() for c in riga.split(",")]
        if not campi[0].isdigit() or len(campi[0]) not in (6, 8):
            break
        if date and len(campi[0]) != len(date[0]):
            raise ValueError(f"date di lunghezza diversa nello stesso blocco: {campi[0]}")
        if len(campi) != len(colonne) + 1:
            raise ValueError(f"numero di colonne inatteso nella riga {riga!r}")
        date.append(campi[0])
        valori.append([float(c) for c in campi[1:]])
    if not date:
        raise ValueError("nessuna riga di dati dopo l'intestazione")
    x = np.array(valori)
    if np.isin(x, MANCANTI).any():
        raise ValueError("il blocco contiene valori mancanti (-99.99 o -999)")
    if len(date[0]) == 6:
        indice = pd.to_datetime(date, format="%Y%m") + pd.offsets.MonthEnd(0)
    else:
        indice = pd.to_datetime(date, format="%Y%m%d")
    tabella = pd.DataFrame(x / 100.0, index=pd.DatetimeIndex(indice, name="data"), columns=colonne)
    if not tabella.index.is_monotonic_increasing or tabella.index.has_duplicates:
        raise ValueError("date non crescenti o duplicate")
    return tabella


def leggi_zip(percorso):
    """Legge il primo blocco del CSV contenuto in uno zip di French."""
    with zipfile.ZipFile(percorso) as z:
        nomi = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(nomi) != 1:
            raise ValueError(f"atteso un solo CSV in {percorso}, trovati {nomi}")
        testo = io.TextIOWrapper(z.open(nomi[0]), encoding="latin-1").read()
    return leggi_testo(testo)


@dataclass
class Dati:
    fattori_m: pd.DataFrame
    fattori_g: pd.DataFrame
    mom_m: pd.Series
    mom_g: pd.Series
    sei_m: pd.DataFrame
    sei_g: pd.DataFrame
    decili_m: pd.DataFrame
    decili_g: pd.DataFrame


def stessa_versione(cartella=CARTELLA_DATI):
    """Per ogni zip: True se coincide con il file usato nel repository (stessa impronta SHA-256)."""
    return {f: hashlib.sha256((Path(cartella) / f).read_bytes()).hexdigest() == h for f, h in IMPRONTE.items()}


def dati_presenti(cartella=CARTELLA_DATI):
    return all((Path(cartella) / f).exists() for f in FILE.values())


def carica(cartella=CARTELLA_DATI):
    """Carica gli otto file di French. Errore chiaro se ne manca qualcuno."""
    cartella = Path(cartella)
    mancanti = [f for f in FILE.values() if not (cartella / f).exists()]
    if mancanti:
        raise FileNotFoundError(f"mancano in {cartella}: {mancanti} (vedi scripts/00_scarica_dati.py)")
    t = {k: leggi_zip(cartella / f) for k, f in FILE.items()}
    return Dati(t["fattori_m"], t["fattori_g"], t["mom_m"]["Mom"], t["mom_g"]["Mom"],
                t["sei_m"], t["sei_g"], t["decili_m"], t["decili_g"])


def wml(decili):
    """Winners minus losers: decile vincente meno decile perdente (autofinanziato)."""
    return (decili[VINCENTI] - decili[PERDENTI]).rename("WML")


def mom_dai_sei(sei):
    """Fattore Mom ricostruito dai 6 portafogli taglia x momentum, con la definizione di French."""
    vincenti = 0.5 * (sei["SMALL HiPRIOR"] + sei["BIG HiPRIOR"])
    perdenti = 0.5 * (sei["SMALL LoPRIOR"] + sei["BIG LoPRIOR"])
    return (vincenti - perdenti).rename("Mom")
