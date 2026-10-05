"""Test fuori campione, gennaio 2012 - agosto 2026: da eseguire UNA sola volta.

Prima di partire lo script controlla che:
- config_congelata.json esista e coincida con i valori del codice (regola, periodo, bootstrap, costi);
- docs/criteri_del_verdetto.md abbia la stessa impronta SHA-256 registrata nella configurazione;
- l'esito non esista gia' (output/esito_test.txt con la riga finale): in quel caso si ferma.
Il rapporto va su schermo e in output/esito_test.txt; la copia versionata e' docs/esito_test.txt.
Le serie mensili della finestra vanno in output/test_mensile.csv (servono ai grafici).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from risk_managed_momentum import configurazione as cfg  # noqa: E402
from risk_managed_momentum import dati, esame, serie  # noqa: E402

OUT = cfg.RADICE / "output"
ESITO = OUT / "esito_test.txt"
FINE_ANALISI = "FINE ANALISI"


def controlli():
    if not cfg.CONFIG.exists():
        sys.exit("config_congelata.json non trovato: prima scripts/03_congela_configurazione.py.")
    if ESITO.exists() and FINE_ANALISI in ESITO.read_text(encoding="utf-8"):
        sys.exit("Il test e' gia' stato eseguito (output/esito_test.txt): non si ripete.")
    congelata = json.loads(cfg.CONFIG.read_text(encoding="utf-8"))
    attesa = json.loads(json.dumps(cfg.attesa()))
    if congelata["sha256_criteri"] != attesa["sha256_criteri"]:
        sys.exit("docs/criteri_del_verdetto.md e' cambiato dopo il congelamento: il test non parte.")
    if congelata != attesa:
        sys.exit("config_congelata.json non coincide con i valori del codice: il test non parte.")
    return congelata


def main():
    c = controlli()
    tabella, pesi = serie.costruisci(dati.carica())
    if f"{tabella.index[-1]:%Y-%m}" != c["test"]["fine"]:
        sys.exit(f"i dati finiscono a {tabella.index[-1]:%Y-%m}, la configurazione a {c['test']['fine']}")
    righe, risultati = esame.analisi(tabella, pesi, c["test"]["inizio"], c["test"]["fine"], c["sottoperiodi"],
                                     c["bootstrap"], c["ritardi_newey_west"])
    if len(risultati["x"]) != c["test"]["mesi"]:
        sys.exit(f"mesi nella finestra: {len(risultati['x'])}, attesi {c['test']['mesi']}")
    testa = ["Test fuori campione con la configurazione congelata (config_congelata.json)",
             f"Impronta dei criteri verificata: {c['sha256_criteri'][:16]}...", ""]
    testo = "\n".join(testa + righe + ["", FINE_ANALISI]) + "\n"
    OUT.mkdir(exist_ok=True)
    risultati["x"].assign(peso_wml=risultati["pesi"]["wml"], peso_vincenti=risultati["pesi"]["vincenti"],
                          peso_mom=risultati["pesi"]["mom"]).to_csv(OUT / "test_mensile.csv")
    ESITO.write_text(testo, encoding="utf-8")
    print(testo)


if __name__ == "__main__":
    main()
