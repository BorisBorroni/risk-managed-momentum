import numpy as np
import pandas as pd

from risk_managed_momentum import esame, grafici

BOOT = {"ricampionamenti": 300, "blocco_medio": 6, "seed": 0, "livello": 0.95}


def serie_finta(n=180, seed=0):
    rng = np.random.default_rng(seed)
    indice = pd.date_range("2000-01-31", periods=n, freq="ME")
    return pd.Series(rng.standard_t(4, n) * 0.04 + 0.005, index=indice)


def test_verdetto_rischio_richiede_tutte_e_tre_le_misure():
    s = serie_finta()
    # meta' esposizione: drawdown e mese peggiore migliorano, curtosi identica -> ipotesi 1 non confermata
    v = esame.verdetto(s, 0.5 * s, BOOT)
    assert v["rischio"]["drawdown"] and v["rischio"]["mese_peggiore"]
    assert not v["rischio"]["curtosi"]
    assert not v["ipotesi_1"]
    # scalare una serie non cambia lo Sharpe
    assert abs(v["differenza"]["stima"]) < 1e-12


def test_verdetto_sharpe_tre_esiti():
    s = serie_finta()
    assert esame.verdetto(s, s + 0.02, BOOT)["ipotesi_2"] == "evidenza di miglioramento"
    assert esame.verdetto(s, s - 0.01, BOOT)["ipotesi_2"] == "nessun miglioramento"
    rumore = serie_finta(seed=5) * 0.5
    v = esame.verdetto(s, s + 0.004 + rumore, BOOT)
    assert v["differenza"]["stima"] > 0 and v["differenza"]["basso"] < 0
    assert v["ipotesi_2"] == "indicazione debole"


def test_grafici_scrivono_i_file(tmp_path):
    s = serie_finta()
    x = pd.DataFrame({"wml": s, "wml_gestita": 0.5 * s, "mercato": serie_finta(seed=2) * 0.5})
    grafici.capitale(x, tmp_path / "c.png", "titolo")
    grafici.drawdown(x, tmp_path / "d.png", "titolo")
    grafici.peso(pd.Series(np.linspace(0.2, 1.5, len(s)), index=s.index), "2010-01-01", tmp_path / "p.png")
    grafici.sharpe_periodi({"A": {"wml": 0.5, "wml_gestita": 0.9}, "B": {"wml": 0.2, "wml_gestita": 0.4}},
                           tmp_path / "s.png")
    assert all((tmp_path / f).stat().st_size > 10_000 for f in ("c.png", "d.png", "p.png", "s.png"))
