"""Scarica gli otto file della biblioteca di Kenneth R. French in data/raw (gli zip, senza aprirli).

I dati non sono nel repository: ogni lettore li scarica da solo. Prima di ogni richiesta lo script
controlla il robots.txt del sito e si ferma se il percorso e' vietato; tra una richiesta e l'altra
aspetta qualche secondo. I file gia' presenti non vengono riscaricati.

Se la rete blocca il sito, si possono scaricare a mano dal browser, dalla pagina
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
(sezioni "Fama/French 3 Factors" e "Momentum Factor (Mom)", versione mensile e giornaliera;
"6 Portfolios Formed on Size and Momentum (2 x 3)" e "10 Portfolios Formed on Momentum",
mensili e giornalieri), mettendo gli zip in data/raw con il loro nome originale.
I numeri del repository sono calcolati con la versione costruita sul database CRSP 202608:
con una versione piu' recente i valori possono cambiare leggermente.
"""
import sys
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from risk_managed_momentum import dati  # noqa: E402

INTESTAZIONE = {"User-Agent": "risk-managed-momentum (progetto universitario, uso personale)"}
INDIRIZZO = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
ATTESA = 3


def permesso(url):
    """True se il robots.txt del sito consente di scaricare l'indirizzo."""
    parti = urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{parti.scheme}://{parti.netloc}/robots.txt")
    rp.read()
    return rp.can_fetch(INTESTAZIONE["User-Agent"], url)


def main():
    dati.CARTELLA_DATI.mkdir(parents=True, exist_ok=True)
    for archivio in dati.FILE.values():
        destinazione = dati.CARTELLA_DATI / archivio
        if destinazione.exists():
            print(archivio, "gia' presente")
            continue
        url = INDIRIZZO + archivio
        if not permesso(url):
            sys.exit(f"Vietato dal robots.txt: {url}. Scaricare a mano (vedi docstring).")
        risposta = requests.get(url, headers=INTESTAZIONE, timeout=120)
        risposta.raise_for_status()
        destinazione.write_bytes(risposta.content)
        print(archivio, "scaricato")
        time.sleep(ATTESA)


if __name__ == "__main__":
    main()
