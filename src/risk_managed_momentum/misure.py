"""Misure di rendimento e di rischio su rendimenti mensili in eccesso, e bootstrap stazionario.

Convenzioni (le stesse per tutte le strategie):
- Sharpe annuo = media mensile / deviazione standard mensile (ddof=1) x radice di 12;
- media annua = 12 x media mensile; volatilita' annua = deviazione standard x radice di 12;
- asimmetria e curtosi in eccesso dai momenti centrali della popolazione (m3/m2^1.5, m4/m2^2 - 3);
- drawdown massimo sul capitale composto 1 x prod(1 + r), con il capitale iniziale come primo massimo.
"""
import math

import numpy as np
import pandas as pd


def _array(r):
    x = np.asarray(r, dtype=float)
    if np.isnan(x).any():
        raise ValueError("rendimenti con valori mancanti")
    return x


def sharpe(r):
    x = _array(r)
    return x.mean() / x.std(ddof=1) * np.sqrt(12)


def media_annua(r):
    return 12 * _array(r).mean()


def volatilita_annua(r):
    return _array(r).std(ddof=1) * np.sqrt(12)


def asimmetria(r):
    x = _array(r)
    s = x - x.mean()
    return (s ** 3).mean() / (s ** 2).mean() ** 1.5


def curtosi_eccesso(r):
    x = _array(r)
    s = x - x.mean()
    return (s ** 4).mean() / (s ** 2).mean() ** 2 - 3


def drawdown_massimo(r):
    """Perdita massima dal picco precedente del capitale composto (numero negativo, es. -0.35)."""
    capitale = np.concatenate([[1.0], np.cumprod(1 + _array(r))])
    return (capitale / np.maximum.accumulate(capitale) - 1).min()


def riepilogo(r):
    """Le misure usate nelle tabelle, in un dizionario."""
    return {
        "mesi": len(_array(r)),
        "media": media_annua(r),
        "volatilita": volatilita_annua(r),
        "sharpe": sharpe(r),
        "asimmetria": asimmetria(r),
        "curtosi": curtosi_eccesso(r),
        "mese_peggiore": float(np.min(r)),
        "mese_migliore": float(np.max(r)),
        "drawdown": drawdown_massimo(r),
    }


def tabella(serie):
    """Riepilogo di piu' serie (dizionario nome -> rendimenti) come DataFrame."""
    return pd.DataFrame({nome: riepilogo(r) for nome, r in serie.items()}).T


def indici_bootstrap(n, ricampionamenti, blocco_medio, seed=0):
    """Indici del bootstrap stazionario di Politis e Romano (1994).

    Ogni ricampionamento e' una sequenza di blocchi di mesi consecutivi (circolari) con lunghezza
    geometrica di media blocco_medio: a ogni passo si ricomincia da un mese a caso con
    probabilita' 1/blocco_medio, altrimenti si prende il mese successivo.
    """
    rng = np.random.default_rng(seed)
    p = 1.0 / blocco_medio
    indici = np.empty((ricampionamenti, n), dtype=np.int64)
    indici[:, 0] = rng.integers(0, n, ricampionamenti)
    nuovo = rng.random((ricampionamenti, n)) < p
    casuali = rng.integers(0, n, (ricampionamenti, n))
    for t in range(1, n):
        indici[:, t] = np.where(nuovo[:, t], casuali[:, t], (indici[:, t - 1] + 1) % n)
    return indici


def sharpe_righe(x):
    return x.mean(axis=1) / x.std(axis=1, ddof=1) * np.sqrt(12)


def differenza_sharpe(a, b, ricampionamenti=10_000, blocco_medio=6, seed=0, livello=0.95):
    """Sharpe(a) - Sharpe(b) con intervallo percentile del bootstrap stazionario.

    Le due serie sono ricampionate con gli stessi indici, cosi' la correlazione tra le due resta.
    """
    a, b = _array(a), _array(b)
    if len(a) != len(b):
        raise ValueError("serie di lunghezza diversa")
    idx = indici_bootstrap(len(a), ricampionamenti, blocco_medio, seed)
    diff = sharpe_righe(a[idx]) - sharpe_righe(b[idx])
    coda = (1 - livello) / 2
    basso, alto = np.quantile(diff, [coda, 1 - coda])
    return {"stima": sharpe(a) - sharpe(b), "basso": basso, "alto": alto,
            "quota_positiva": float((diff > 0).mean())}


def alfa(y, x, ritardi=6):
    """Regressione y = alfa + beta x con errori di Newey e West; alfa annuo (x12) e t di alfa."""
    y, x = _array(y), _array(x)
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    u = y - X @ coef
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for k in range(1, ritardi + 1):
        g = Xu[k:].T @ Xu[:-k]
        S += (1 - k / (ritardi + 1)) * (g + g.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    cov = XtX_inv @ S @ XtX_inv
    return {"alfa": 12 * coef[0], "t_alfa": coef[0] / np.sqrt(cov[0, 0]), "beta": coef[1]}


def memmel(a, b):
    """Test di Jobson e Korkie con la correzione di Memmel (2003) sulla differenza di Sharpe.

    Ipotesi: rendimenti indipendenti e normali. Serve solo come controllo incrociato del bootstrap.
    Restituisce la differenza degli Sharpe mensili, la statistica z e il p-value a due code.
    """
    a, b = _array(a), _array(b)
    n = len(a)
    sa, sb = a.mean() / a.std(ddof=1), b.mean() / b.std(ddof=1)
    rho = np.corrcoef(a, b)[0, 1]
    varianza = (2 - 2 * rho + 0.5 * (sa ** 2 + sb ** 2 - 2 * sa * sb * rho ** 2)) / n
    z = (sa - sb) / np.sqrt(varianza)
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"differenza_mensile": sa - sb, "z": z, "p": p, "correlazione": rho}


def errore_standard_sharpe(r):
    """Errore standard approssimato dello Sharpe annuo con rendimenti indipendenti (Lo 2002)."""
    x = _array(r)
    s = x.mean() / x.std(ddof=1)
    return np.sqrt((1 + 0.5 * s ** 2) / len(x)) * np.sqrt(12)
