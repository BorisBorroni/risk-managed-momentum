"""Analisi completa su una finestra di mesi: verdetto (ipotesi 1 e 2) e misure descrittive.

La usa scripts/04_test_fuori_campione.py sul periodo 2012-2026. La stessa funzione si puo' provare
su un periodo gia' visto (per esempio dentro il campione del paper) per controllare che il codice
giri, senza toccare il test.
"""
import numpy as np
import pandas as pd

from . import costi, misure

NOMI = {
    "wml": "WML semplice",
    "wml_gestita": "WML gestito",
    "mom": "Mom di French",
    "mom_gestita": "Mom gestito",
    "vincenti": "Vincenti solo lunghi",
    "vincenti_gestita": "Vincenti gestiti",
    "mercato": "Mercato",
    "mercato_piu_wml_gestita": "Mercato + WML gestito",
}


def formatta(t):
    """Tabella di misure in testo, con percentuali e due decimali."""
    t = t.copy()
    for c in ("media", "volatilita", "mese_peggiore", "mese_migliore", "drawdown"):
        t[c] = (100 * t[c]).map("{:.2f}%".format)
    for c in ("sharpe", "asimmetria", "curtosi"):
        t[c] = t[c].map("{:.2f}".format)
    t["mesi"] = t["mesi"].astype(int)
    return t.to_string()


def _mese(testo, fine=False):
    p = pd.Period(testo, freq="M")
    return p.to_timestamp(how="end").normalize() if fine else p.to_timestamp(how="start")


def verdetto(semplice, gestita, boot):
    """Ipotesi 1 (rischio) e ipotesi 2 (differenza di Sharpe) con le regole di criteri_del_verdetto.md."""
    s, g = misure.riepilogo(semplice), misure.riepilogo(gestita)
    rischio = {
        "drawdown": bool(g["drawdown"] > s["drawdown"]),          # meno negativo = piu' basso
        "mese_peggiore": bool(g["mese_peggiore"] > s["mese_peggiore"]),
        "curtosi": bool(g["curtosi"] < s["curtosi"]),
    }
    d = misure.differenza_sharpe(gestita, semplice, boot["ricampionamenti"], boot["blocco_medio"],
                                 boot["seed"], boot["livello"])
    if d["basso"] > 0:
        sharpe = "evidenza di miglioramento"
    elif d["stima"] > 0:
        sharpe = "indicazione debole"
    else:
        sharpe = "nessun miglioramento"
    return {"semplice": s, "gestita": g, "rischio": rischio, "ipotesi_1": all(rischio.values()),
            "differenza": d, "ipotesi_2": sharpe}


def analisi(tabella, pesi, inizio, fine, sottoperiodi, boot, ritardi):
    """Testo del rapporto (lista di righe) e risultati principali per una finestra di mesi."""
    x = tabella.loc[_mese(inizio):_mese(fine, True)]
    colonne = list(NOMI)
    if x[colonne].isna().any().any():
        raise ValueError("valori mancanti nella finestra")
    w = pesi.loc[x.index]
    r = []
    r.append(f"Finestra: {x.index[0]:%Y-%m} -> {x.index[-1]:%Y-%m}, {len(x)} mesi")
    r.append("")
    r.append("Misure lorde (rendimenti mensili in eccesso, valori annui):")
    r.append(formatta(misure.tabella({NOMI[c]: x[c] for c in colonne})))
    r.append("")
    r.append(f"Peso del WML gestito: minimo {w['wml'].min():.2f}, massimo {w['wml'].max():.2f}, "
             f"medio {w['wml'].mean():.2f}, mesi con peso sopra 1: {int((w['wml'] > 1).sum())}")

    v = verdetto(x["wml"], x["wml_gestita"], boot)
    s, g, d = v["semplice"], v["gestita"], v["differenza"]
    r.append("")
    r.append("IPOTESI 1 (rischio: tutte e tre devono migliorare)")
    r.append(f"  drawdown massimo   semplice {100 * s['drawdown']:.2f}%  gestito {100 * g['drawdown']:.2f}%  "
             f"{'migliora' if v['rischio']['drawdown'] else 'NON migliora'}")
    r.append(f"  mese peggiore      semplice {100 * s['mese_peggiore']:.2f}%  gestito {100 * g['mese_peggiore']:.2f}%  "
             f"{'migliora' if v['rischio']['mese_peggiore'] else 'NON migliora'}")
    r.append(f"  curtosi in eccesso semplice {s['curtosi']:.2f}  gestito {g['curtosi']:.2f}  "
             f"{'migliora' if v['rischio']['curtosi'] else 'NON migliora'}")
    r.append(f"  -> ipotesi 1 {'CONFERMATA' if v['ipotesi_1'] else 'NON confermata'}")
    r.append("")
    r.append(f"IPOTESI 2 (differenza di Sharpe gestito meno semplice, bootstrap stazionario, "
             f"blocco medio {boot['blocco_medio']}, {boot['ricampionamenti']} ricampionamenti)")
    r.append(f"  Sharpe semplice {s['sharpe']:.3f}  gestito {g['sharpe']:.3f}  differenza {d['stima']:+.3f}  "
             f"IC95 [{d['basso']:+.3f}; {d['alto']:+.3f}]  ricampionamenti con differenza positiva {100 * d['quota_positiva']:.1f}%")
    r.append(f"  -> ipotesi 2: {v['ipotesi_2'].upper()}")

    r.append("")
    r.append("DESCRITTIVO (non entra nel verdetto)")
    a = misure.alfa(x["wml_gestita"], x["wml"], ritardi)
    r.append(f"Alfa del WML gestito sul semplice: {100 * a['alfa']:.2f}% annuo, t (Newey-West, {ritardi} ritardi) "
             f"{a['t_alfa']:.2f}, beta {a['beta']:.2f}")
    a = misure.alfa(x["mom_gestita"], x["mom"], ritardi)
    r.append(f"Alfa del Mom gestito sul Mom semplice: {100 * a['alfa']:.2f}% annuo, t {a['t_alfa']:.2f}, beta {a['beta']:.2f}")
    for coppia in (("mom_gestita", "mom"), ("vincenti_gestita", "vincenti"), ("mercato_piu_wml_gestita", "mercato")):
        dd = misure.differenza_sharpe(x[coppia[0]], x[coppia[1]], boot["ricampionamenti"], boot["blocco_medio"],
                                      boot["seed"], boot["livello"])
        r.append(f"Differenza di Sharpe {NOMI[coppia[0]]} meno {NOMI[coppia[1]]}: {dd['stima']:+.3f} "
                 f"IC95 [{dd['basso']:+.3f}; {dd['alto']:+.3f}]")
    r.append(f"Correlazione mensile WML semplice - mercato: {np.corrcoef(x['wml'], x['mercato'])[0, 1]:+.2f}")

    r.append("")
    r.append("Sottoperiodi (WML):")
    sotto = {}
    for a_, b_ in sottoperiodi:
        y = x.loc[_mese(a_):_mese(b_, True)]
        ms, mg = misure.riepilogo(y["wml"]), misure.riepilogo(y["wml_gestita"])
        sotto[f"{a_}/{b_}"] = (ms, mg)
        r.append(f"  {a_} -> {b_} ({len(y)} mesi): Sharpe semplice {ms['sharpe']:.2f}  gestito {mg['sharpe']:.2f}  "
                 f"differenza {mg['sharpe'] - ms['sharpe']:+.2f} | drawdown {100 * ms['drawdown']:.1f}% / "
                 f"{100 * mg['drawdown']:.1f}% | mese peggiore {100 * ms['mese_peggiore']:.1f}% / {100 * mg['mese_peggiore']:.1f}%")

    r.append("")
    r.append("Costi (scenari di criteri_del_verdetto.md): Sharpe e media annua netti")
    netti = {}
    uno = pd.Series(1.0, index=x.index)
    for scen in costi.SCENARI:
        n = {
            "wml": costi.netto(x["wml"], uno, scen),
            "wml_gestita": costi.netto(x["wml_gestita"], w["wml"], scen),
            "vincenti": costi.netto(x["vincenti"], uno, scen, lungo_corto=False),
            "vincenti_gestita": costi.netto(x["vincenti_gestita"], w["vincenti"], scen, lungo_corto=False),
        }
        netti[scen] = n
        dd = misure.differenza_sharpe(n["wml_gestita"], n["wml"], boot["ricampionamenti"], boot["blocco_medio"],
                                      boot["seed"], boot["livello"])
        r.append(f"  {scen:6s} " + "  ".join(f"{NOMI[k]} {misure.sharpe(s_):.2f} ({100 * misure.media_annua(s_):.1f}%)"
                                         for k, s_ in n.items())
                 + f"  | differenza gestito-semplice {dd['stima']:+.3f} IC95 [{dd['basso']:+.3f}; {dd['alto']:+.3f}]")
    return r, {"x": x, "pesi": w, "verdetto": v, "sottoperiodi": sotto, "netti": netti}
