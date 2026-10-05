import numpy as np
import pandas as pd
import pytest

from risk_managed_momentum import strategia


def giorni_finti(seed=1, inizio="2000-01-03", fine="2001-12-31"):
    giorni = pd.bdate_range(inizio, fine)
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0, 0.01, len(giorni)), index=giorni)


def test_varianza_fatta_a_mano():
    g = pd.Series([0.01, -0.02, 0.03, 0.04, -0.01],
                  index=pd.to_datetime(["2000-01-27", "2000-01-28", "2000-01-31", "2000-02-01", "2000-02-29"]))
    v = strategia.varianza_prevista(g, finestra=3, giorni_mese=21)
    # febbraio usa gli ultimi 3 giorni di gennaio; marzo gli ultimi 3 giorni fino al 29 febbraio
    assert list(v.index) == [pd.Timestamp("2000-02-29"), pd.Timestamp("2000-03-31")]
    assert v.iloc[0] == pytest.approx(21 * (0.01 ** 2 + 0.02 ** 2 + 0.03 ** 2) / 3)
    assert v.iloc[1] == pytest.approx(21 * (0.03 ** 2 + 0.04 ** 2 + 0.01 ** 2) / 3)


def test_peso_fatto_a_mano():
    g = pd.Series([0.01, -0.01, 0.01], index=pd.to_datetime(["2000-01-27", "2000-01-28", "2000-01-31"]))
    w = strategia.pesi(g, obiettivo=0.12, finestra=3)
    # varianza mensile 21 x 0,0001; volatilita' annua radice(12 x 21 x 0,0001) = 0,1587
    assert w.iloc[0] == pytest.approx(0.12 / np.sqrt(12 * 21 * 0.0001))
    assert w.index[0] == pd.Timestamp("2000-02-29")


def test_rendimento_gestito_e_peso_per_rendimento():
    g = giorni_finti()
    mesi = pd.Series(0.01, index=pd.date_range("2000-01-31", "2001-12-31", freq="ME"))
    r, w = strategia.gestita(mesi, g, finestra=63)
    assert r.index.equals(w.index)
    assert np.allclose(r.to_numpy(), 0.01 * w.to_numpy())
    # 63 giorni di borsa finiscono a fine marzo 2000: il primo peso e' per aprile
    assert w.index[0] == pd.Timestamp("2000-04-30")


def test_il_peso_del_mese_non_usa_giorni_dello_stesso_mese():
    g = giorni_finti()
    base = strategia.pesi(g)
    modificati = g.copy()
    modificati.loc["2001-06-01":"2001-06-30"] = 0.5  # un mese di rendimenti enormi
    nuovi = strategia.pesi(modificati)
    assert np.allclose(base.loc[:"2001-06-30"], nuovi.loc[:"2001-06-30"])
    assert nuovi.loc["2001-07-31"] < base.loc["2001-07-31"] / 10


def test_troncare_i_dati_non_cambia_il_passato():
    g = giorni_finti()
    completo = strategia.pesi(g)
    # tagli all'ultimo giorno di borsa di un mese: e' l'informazione disponibile quando si fissa il peso
    for taglio in ("2000-11-30", "2001-03-30", "2001-08-31"):
        parziale = strategia.pesi(g.loc[:taglio])
        assert np.allclose(parziale.to_numpy(), completo.loc[parziale.index].to_numpy())
        # l'ultimo peso disponibile e' quello del mese dopo l'ultimo giorno usato
        mese_dopo = (pd.Timestamp(taglio).to_period("M") + 1).to_timestamp(how="end").normalize()
        assert parziale.index[-1] == mese_dopo
