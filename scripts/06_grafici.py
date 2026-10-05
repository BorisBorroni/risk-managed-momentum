"""Grafici del README (cartella img/), calcolati dai dati come tutti gli altri numeri."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from risk_managed_momentum import configurazione as cfg  # noqa: E402
from risk_managed_momentum import dati, grafici, misure, serie  # noqa: E402

IMG = cfg.RADICE / "img"


def main():
    IMG.mkdir(exist_ok=True)
    tabella, pesi = serie.costruisci(dati.carica())
    test = tabella.loc[cfg.TEST_INIZIO:cfg.TEST_FINE]
    (a1, b1), (a2, b2) = cfg.SOTTOPERIODI
    replica = serie.finestra(tabella, None, "2011-12-31", ["wml", "wml_gestita"])
    grafici.capitale(test, IMG / "capitale_test.png", "Crescita di 1 $ nel test, rendimenti in eccesso (gennaio 2012 - agosto 2026)")
    grafici.drawdown(test, IMG / "drawdown_test.png", "Drawdown nel test: semplice contro gestito")
    grafici.peso(pesi["wml"].dropna(), cfg.TEST_INIZIO, IMG / "peso_nel_tempo.png")
    # il test completo e i suoi due sottoperiodi (che insieme lo compongono)
    valori = {
        "Replica\n1927-2011": {n: misure.sharpe(replica[n]) for n in ("wml", "wml_gestita")},
        f"Test completo\n{a1[:4]}-{b2[:4]}": {n: misure.sharpe(test[n]) for n in ("wml", "wml_gestita")},
        f"Sottoperiodo del test\n{a1[:4]}-{b1[:4]}": {n: misure.sharpe(test.loc[a1:b1, n]) for n in ("wml", "wml_gestita")},
        f"Sottoperiodo del test\n{a2[:4]}-{b2[:4]}": {n: misure.sharpe(test.loc[a2:b2, n]) for n in ("wml", "wml_gestita")},
    }
    grafici.sharpe_periodi(valori, IMG / "sharpe_per_periodo.png")
    for nome in sorted(p.name for p in IMG.glob("*.png")):
        print("salvato img/" + nome)


if __name__ == "__main__":
    main()
