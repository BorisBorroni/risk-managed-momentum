"""Grafici del README e del notebook. Stesso colore per la stessa strategia in tutti i grafici,
etichette dirette al posto delle legende, un solo asse verticale."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

COLORI = {"wml": "#eb6834", "wml_gestita": "#2a78d6", "mercato": "#6b6b6b", "vincenti": "#1baf7a"}
NOMI = {"wml": "WML semplice", "wml_gestita": "WML gestito", "mercato": "Mercato", "vincenti": "Vincenti solo lunghi"}
INCHIOSTRO, GRIGIO = "#222222", "#8a8a8a"


def _stile(ax):
    for lato in ("top", "right"):
        ax.spines[lato].set_visible(False)
    for lato in ("left", "bottom"):
        ax.spines[lato].set_color(GRIGIO)
    ax.tick_params(colors="#444444", labelsize=9)
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)


def _etichetta_finale(ax, serie, nome, colore, dy=0):
    ax.annotate(f"{NOMI[nome]}", xy=(serie.index[-1], serie.iloc[-1]), xytext=(6, dy), textcoords="offset points",
                va="center", fontsize=9, color=INCHIOSTRO)
    ax.plot(serie.index[-1], serie.iloc[-1], "o", color=colore, markersize=5)


def capitale(x, percorso, titolo):
    """Crescita di 1 euro con i rendimenti mensili in eccesso, scala logaritmica."""
    fig, ax = plt.subplots(figsize=(9, 4.6))
    _stile(ax)
    spostamenti = {"wml": -8, "wml_gestita": 0, "mercato": 0}
    for nome in ("mercato", "wml", "wml_gestita"):
        c = (1 + x[nome]).cumprod()
        c = pd.concat([pd.Series([1.0], index=[x.index[0] - pd.offsets.MonthEnd(1)]), c])
        ax.plot(c.index, c, color=COLORI[nome], linewidth=2)
        _etichetta_finale(ax, c, nome, COLORI[nome], spostamenti[nome])
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator([0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8]))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_ylabel("valore di 1 € con i rendimenti in eccesso (scala log.)", fontsize=9, color="#444444")
    ax.set_title(titolo, fontsize=11, loc="left", color=INCHIOSTRO)
    anni = range(x.index[0].year, x.index[-1].year + 1, 2)
    ax.set_xticks([pd.Timestamp(f"{a}-01-01") for a in anni], [str(a) for a in anni])
    ax.set_xlim(right=x.index[-1] + pd.DateOffset(years=2))
    fig.tight_layout()
    fig.savefig(percorso, dpi=130)
    plt.close(fig)


def drawdown(x, percorso, titolo):
    """Perdita dal massimo precedente del capitale composto."""
    fig, ax = plt.subplots(figsize=(9, 4.2))
    _stile(ax)
    for nome in ("wml", "wml_gestita"):
        c = np.concatenate([[1.0], (1 + x[nome]).cumprod().to_numpy()])
        dd = pd.Series((c / np.maximum.accumulate(c) - 1)[1:], index=x.index) * 100
        ax.plot(dd.index, dd, color=COLORI[nome], linewidth=2)
        minimo = dd.idxmin()
        ax.annotate(f"{NOMI[nome]}: {dd.min():.1f}%".replace(".", ",").replace("-", "−"), xy=(minimo, dd.min()),
                    xytext=(8, -2), textcoords="offset points", fontsize=9, color=INCHIOSTRO, va="top")
        ax.plot(minimo, dd.min(), "o", color=COLORI[nome], markersize=5)
    ax.axhline(0, color=GRIGIO, linewidth=0.8)
    ax.set_ylabel("drawdown (%)", fontsize=9, color="#444444")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}".replace("-", "−")))
    ax.set_ylim(top=3, bottom=ax.get_ylim()[0] * 1.12)
    ax.set_title(titolo, fontsize=11, loc="left", color=INCHIOSTRO)
    fig.tight_layout()
    fig.savefig(percorso, dpi=130)
    plt.close(fig)


def peso(pesi, inizio_test, percorso):
    """Peso del WML gestito nel tempo, con il periodo di test evidenziato."""
    fig, ax = plt.subplots(figsize=(9, 3.8))
    _stile(ax)
    ax.axvspan(pd.Timestamp(inizio_test), pesi.index[-1], color="#f0f0ee", zorder=0)
    ax.plot(pesi.index, pesi, color=COLORI["wml_gestita"], linewidth=1.2)
    ax.axhline(1, color=GRIGIO, linewidth=0.8, linestyle="--")
    ax.text(pesi.index[0], 1.10, "peso 1 = WML semplice", fontsize=8, color="#555555", va="bottom")
    ax.text(pd.Timestamp(inizio_test) + pd.DateOffset(months=6), pesi.max() * 0.97, "test", fontsize=9, color="#555555", va="top")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ",")))
    ax.set_ylabel("peso (12% / volatilità prevista)", fontsize=9, color="#444444")
    ax.set_ylim(0, pesi.max() * 1.05)
    ax.set_title("Peso del WML gestito, mese per mese", fontsize=11, loc="left", color=INCHIOSTRO)
    fig.tight_layout()
    fig.savefig(percorso, dpi=130)
    plt.close(fig)


def sharpe_periodi(valori, percorso):
    """Barre dello Sharpe per periodo: valori = {periodo: {nome: sharpe}}."""
    fig, ax = plt.subplots(figsize=(8, 4))
    _stile(ax)
    nomi = ["wml", "wml_gestita"]
    larghezza = 0.36
    for j, periodo in enumerate(valori):
        for i, nome in enumerate(nomi):
            v = valori[periodo][nome]
            xpos = j + (i - 0.5) * (larghezza + 0.03)
            ax.bar(xpos, v, width=larghezza, color=COLORI[nome])
            ax.text(xpos, v + 0.02, f"{v:.2f}".replace(".", ","), ha="center", va="bottom", fontsize=9, color=INCHIOSTRO)
    ax.set_xticks(range(len(valori)))
    ax.set_xticklabels(list(valori), fontsize=9)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    ax.set_ylabel("Sharpe annuo", fontsize=9, color="#444444")
    ax.set_ylim(0, max(max(v.values()) for v in valori.values()) * 1.18)
    ax.legend(handles=[matplotlib.patches.Patch(color=COLORI[n], label=NOMI[n]) for n in nomi],
              frameon=False, fontsize=9, loc="upper right")
    ax.set_title("Sharpe del momentum semplice e gestito", fontsize=11, loc="left", color=INCHIOSTRO)
    fig.tight_layout()
    fig.savefig(percorso, dpi=130)
    plt.close(fig)
