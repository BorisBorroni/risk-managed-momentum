"""Configurazione del test: valori fissati prima di guardare il periodo 2012-2026.

scripts/03_congela_configurazione.py la scrive in config_congelata.json; scripts/04_test_fuori_campione.py
controlla che il file coincida con questi valori e con l'impronta dei criteri prima di partire.
"""
import hashlib
from pathlib import Path

from . import costi, strategia

RADICE = Path(__file__).resolve().parents[2]
CONFIG = RADICE / "config_congelata.json"
CRITERI = RADICE / "docs" / "criteri_del_verdetto.md"
REPLICA = RADICE / "docs" / "esito_replica.txt"

TEST_INIZIO, TEST_FINE = "2012-01", "2026-08"
SOTTOPERIODI = [["2012-01", "2015-12"], ["2016-01", "2026-08"]]
BOOTSTRAP = {"ricampionamenti": 10000, "blocco_medio": 6, "seed": 0, "livello": 0.95}
RITARDI_NEWEY_WEST = 6


def impronta(percorso):
    """SHA-256 del testo con fine riga uniformi (lo stesso valore su Windows e su Linux)."""
    testo = Path(percorso).read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(testo.encode("utf-8")).hexdigest()


def attesa():
    return {
        "regola": {"obiettivo_volatilita": strategia.OBIETTIVO, "finestra_giorni": strategia.FINESTRA,
                   "giorni_per_mese": strategia.GIORNI_MESE, "tetto_al_peso": None},
        "test": {"inizio": TEST_INIZIO, "fine": TEST_FINE, "mesi": 176},
        "sottoperiodi": SOTTOPERIODI,
        "bootstrap": BOOTSTRAP,
        "costi": costi.SCENARI,
        "ritardi_newey_west": RITARDI_NEWEY_WEST,
        "dati": "Kenneth R. French Data Library, database CRSP 202608",
        "sha256_criteri": impronta(CRITERI),
    }
