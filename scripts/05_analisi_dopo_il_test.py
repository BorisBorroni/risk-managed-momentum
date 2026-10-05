"""Analisi descrittive fatte DOPO il test: non cambiano il verdetto, aiutano a leggerlo.

1. Meccanismo: la volatilita' prevista anticipa la volatilita' realizzata del mese dopo, ma non
   il suo rendimento (se fosse cosi', il peso toglierebbe rischio senza togliere rendimento atteso).
2. Timing contro semplice riduzione dell'esposizione: WML semplice scalato con una costante fino
   ad avere la stessa volatilita' del gestito nel test (la costante usa dati del test: e' solo un confronto).
3. Crolli: peso del WML gestito, decile vincente e perdente nei 5 mesi peggiori del WML semplice nel test.
4. Solidita' della differenza di Sharpe: altri semi e altre lunghezze di blocco del bootstrap,
   test di Jobson e Korkie con la correzione di Memmel, errore standard dello Sharpe.
Il riepilogo va su schermo e in docs/analisi_dopo_il_test.txt.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from risk_managed_momentum import configurazione as cfg  # noqa: E402
from risk_managed_momentum import dati, misure, serie, strategia  # noqa: E402

USCITA = cfg.RADICE / "docs" / "analisi_dopo_il_test.txt"


def volatilita_realizzata(giornalieri):
    """Volatilita' annua realizzata in ogni mese dai rendimenti giornalieri dello stesso mese."""
    v = (giornalieri ** 2).groupby(giornalieri.index.to_period("M")).mean()
    v.index = v.index.to_timestamp(how="end").normalize()
    return np.sqrt(252 * v)


def main():
    d = dati.carica()
    tabella, pesi = serie.costruisci(d)
    test = tabella.loc[cfg.TEST_INIZIO:cfg.TEST_FINE]
    w = pesi["wml"].loc[test.index]
    b = cfg.BOOTSTRAP
    righe = ["Analisi descrittive fatte dopo il test (non cambiano il verdetto)", ""]

    righe.append("1. Meccanismo: correlazione della volatilita' prevista (dati fino a t-1) con il mese t")
    wml_g = dati.wml(d.decili_g)
    prevista = strategia.volatilita_annua(strategia.varianza_prevista(wml_g))
    realizzata = volatilita_realizzata(wml_g)
    for nome, inizio, fine in (("1927-2011", None, "2011-12"), ("test", cfg.TEST_INIZIO, cfg.TEST_FINE)):
        y = tabella["wml"].loc[inizio:fine].loc[prevista.index[0]:]
        p, r = prevista.loc[y.index], realizzata.loc[y.index]
        c_vol, c_rend = np.corrcoef(p, r)[0, 1], np.corrcoef(p, y)[0, 1]
        t_rend = c_rend * np.sqrt((len(y) - 2) / (1 - c_rend ** 2))
        righe.append(f"  {nome:10s} con la volatilita' realizzata {c_vol:+.2f}   con il rendimento del WML "
                     f"{c_rend:+.2f} (t {t_rend:+.1f})   {len(y)} mesi")
    terzi = np.quantile(w, [1 / 3, 2 / 3])
    gruppi = np.digitize(w, terzi)
    righe.append("  WML semplice nel test per terzi del peso (peso basso = volatilita' prevista alta):")
    for k, nome in enumerate(("peso basso", "peso medio", "peso alto")):
        y = test["wml"][gruppi == k]
        es = y.std(ddof=1) / np.sqrt(len(y)) * 12
        righe.append(f"    {nome:10s} {len(y):3d} mesi  media annua {100 * misure.media_annua(y):6.2f}% "
                     f"(errore standard {100 * es:.1f}%)  volatilita' annua {100 * misure.volatilita_annua(y):6.2f}%")
    for nome in ("wml", "wml_gestita"):
        y = test[nome]
        righe.append(f"  t della media nel test, {nome}: {y.mean() / y.std(ddof=1) * np.sqrt(len(y)):.2f}")

    righe.append("")
    righe.append("2. Timing o solo meno esposizione? WML semplice scalato alla volatilita' del gestito nel test")
    k = test["wml_gestita"].std(ddof=1) / test["wml"].std(ddof=1)
    for nome, y in (("WML semplice", test["wml"]), (f"WML semplice x {k:.3f}", k * test["wml"]),
                    ("WML gestito", test["wml_gestita"])):
        m = misure.riepilogo(y)
        righe.append(f"  {nome:20s} volatilita' {100 * m['volatilita']:5.2f}%  drawdown {100 * m['drawdown']:7.2f}%  "
                     f"mese peggiore {100 * m['mese_peggiore']:7.2f}%  curtosi {m['curtosi']:.2f}  Sharpe {m['sharpe']:.3f}")

    righe.append("")
    righe.append("3. I 5 mesi peggiori del WML semplice nel test (rendimenti dei decili non in eccesso)")
    decili = d.decili_m.loc[test.index]
    totale = tabella["mercato"] + tabella["rf"]
    mercato_24 = (1 + totale).rolling(24).apply(np.prod, raw=True).shift(1) - 1  # 24 mesi fino a t-1
    for data in test["wml"].nsmallest(5).index:
        righe.append(f"  {data:%Y-%m}  semplice {100 * test.loc[data, 'wml']:7.2f}%  peso {w.loc[data]:.2f}  "
                     f"gestito {100 * test.loc[data, 'wml_gestita']:7.2f}%  mercato {100 * test.loc[data, 'mercato']:6.2f}%  "
                     f"vincenti {100 * decili.loc[data, dati.VINCENTI]:6.2f}%  perdenti {100 * decili.loc[data, dati.PERDENTI]:6.2f}%  "
                     f"mercato nei 24 mesi prima {100 * mercato_24.loc[data]:6.1f}%")

    righe.append("")
    righe.append("4. Differenza di Sharpe (gestito meno semplice) nel test: solidita'")
    bassi = [misure.differenza_sharpe(test["wml_gestita"], test["wml"], b["ricampionamenti"], b["blocco_medio"],
                                      seed)["basso"] for seed in range(20)]
    righe.append(f"  blocco 6, semi 0-19: limite inferiore tra {min(bassi):+.4f} e {max(bassi):+.4f}, "
                 f"sotto zero in {sum(x <= 0 for x in bassi)} casi su 20")
    for blocco in (1, 3, 6, 12, 24):
        dd = misure.differenza_sharpe(test["wml_gestita"], test["wml"], b["ricampionamenti"], blocco, b["seed"])
        righe.append(f"  blocco medio {blocco:2d}: IC95 [{dd['basso']:+.3f}; {dd['alto']:+.3f}]")
    jk = misure.memmel(test["wml_gestita"], test["wml"])
    righe.append(f"  Jobson-Korkie con correzione di Memmel (rendimenti indipendenti e normali): z {jk['z']:.2f}, "
                 f"p {jk['p']:.3f}, correlazione tra le due serie {jk['correlazione']:.2f}")
    storico = serie.finestra(tabella, None, "2011-12-31", ["wml", "wml_gestita"])["wml"]
    es_test, es_storico = misure.errore_standard_sharpe(test["wml"]), misure.errore_standard_sharpe(storico)
    righe.append(f"  Sharpe del WML semplice: 1927-2011 {misure.sharpe(storico):.2f} (errore standard {es_storico:.2f}), "
                 f"test {misure.sharpe(test['wml']):.2f} (errore standard {es_test:.2f}); errore standard della "
                 f"differenza {np.hypot(es_test, es_storico):.2f}, t {(misure.sharpe(storico) - misure.sharpe(test['wml'])) / np.hypot(es_test, es_storico):.2f}")
    testo = "\n".join(righe) + "\n"
    print(testo)
    USCITA.write_text(testo, encoding="utf-8")


if __name__ == "__main__":
    main()
