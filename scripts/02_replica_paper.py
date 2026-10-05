"""Replica di Barroso e Santa-Clara (2015) sul loro periodo, fino a dicembre 2011.

E' una verifica del codice, non un risultato: con le stesse regole gli Sharpe devono tornare
entro +-0,10 dai valori del paper (0,53 momentum semplice, 0,97 gestito). Le due serie sono
confrontate sugli stessi mesi: dal primo mese con 126 giorni precedenti a dicembre 2011.
Il riepilogo va su schermo e in docs/esito_replica.txt.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from risk_managed_momentum import dati, misure, serie  # noqa: E402

RADICE = Path(__file__).resolve().parents[1]
ESITO = RADICE / "docs" / "esito_replica.txt"
FINE = "2011-12-31"
PAPER = {  # tabella 1 di Barroso e Santa-Clara (2015), periodo 1927-2011
    "wml": {"sharpe": 0.53, "curtosi": 18.24, "mese_peggiore": -0.7896},
    "wml_gestita": {"sharpe": 0.97, "curtosi": 2.68, "mese_peggiore": -0.2840},
}
TOLLERANZA_SHARPE = 0.10


def formatta(t):
    t = t.copy()
    for c in ("media", "volatilita", "mese_peggiore", "mese_migliore", "drawdown"):
        t[c] = (100 * t[c]).map("{:.2f}%".format)
    for c in ("sharpe", "asimmetria", "curtosi"):
        t[c] = t[c].map("{:.2f}".format)
    t["mesi"] = t["mesi"].astype(int)
    return t.to_string()


def main():
    tabella, pesi = serie.costruisci(dati.carica())
    x = serie.finestra(tabella, None, FINE, ["wml", "wml_gestita", "mom", "mom_gestita"])
    w = pesi["wml"].loc[x.index]
    righe = []
    righe.append(f"Replica: {x.index[0]:%Y-%m} -> {x.index[-1]:%Y-%m}, {len(x)} mesi")
    righe.append("")
    righe.append(formatta(misure.tabella({c: x[c] for c in x.columns})))
    righe.append("")
    righe.append(f"Peso del momentum gestito: minimo {w.min():.2f}, massimo {w.max():.2f}, medio {w.mean():.2f} "
                 "(paper: 0,13 - 2,00)")
    righe.append("")
    righe.append("Confronto con il paper (tabella 1):")
    esito = True
    for nome, attesi in PAPER.items():
        m = misure.riepilogo(x[nome])
        diff = m["sharpe"] - attesi["sharpe"]
        ok = abs(diff) <= TOLLERANZA_SHARPE
        esito &= ok
        righe.append(f"  {nome:12s} Sharpe {m['sharpe']:.2f} (paper {attesi['sharpe']:.2f}, differenza {diff:+.2f}, "
                     f"{'entro' if ok else 'FUORI'} +-{TOLLERANZA_SHARPE:.2f})   curtosi {m['curtosi']:.2f} "
                     f"(paper {attesi['curtosi']:.2f})   mese peggiore {100 * m['mese_peggiore']:.2f}% "
                     f"(paper {100 * attesi['mese_peggiore']:.2f}%)")
    corrette = {n: x[n].kurt() for n in PAPER}  # stimatore corretto per il campione (pandas)
    righe.append("  curtosi corretta per il campione (solo confronto): "
                 + ", ".join(f"{n} {k:.2f}" for n, k in corrette.items()))
    pieno = tabella["wml"].loc[:FINE]
    righe.append(f"  WML semplice su tutti i mesi {pieno.index[0]:%Y-%m} -> {FINE[:7]}: "
                 f"Sharpe {misure.sharpe(pieno):.2f}")
    righe.append("")
    righe.append("ESITO: replica " + ("superata" if esito else "NON superata"))
    testo = "\n".join(righe) + "\n"
    print(testo)
    ESITO.parent.mkdir(exist_ok=True)
    ESITO.write_text(testo, encoding="utf-8")
    pd.DataFrame(x).assign(peso=w).to_csv(RADICE / "output" / "replica_mensile.csv")
    if not esito:
        sys.exit(1)


if __name__ == "__main__":
    main()
