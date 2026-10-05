import numpy as np
import pytest

from risk_managed_momentum import misure


def test_sharpe_media_volatilita_a_mano():
    r = np.array([0.02, -0.01, 0.03, 0.00])
    media = 0.01
    dev = np.sqrt(((r - media) ** 2).sum() / 3)
    assert misure.sharpe(r) == pytest.approx(media / dev * np.sqrt(12))
    assert misure.media_annua(r) == pytest.approx(0.12)
    assert misure.volatilita_annua(r) == pytest.approx(dev * np.sqrt(12))


def test_drawdown_a_mano():
    # capitale: 1 -> 1,1 -> 0,55 -> 0,605 -> 0,3025: picco 1,1, minimo 0,3025
    r = [0.10, -0.50, 0.10, -0.50]
    assert misure.drawdown_massimo(r) == pytest.approx(0.3025 / 1.1 - 1)
    # una perdita nel primo mese conta, il capitale iniziale e' il primo massimo
    assert misure.drawdown_massimo([-0.2, 0.1]) == pytest.approx(-0.2)


def test_curtosi_e_asimmetria_a_mano():
    r = np.array([-3.0, 0.0, 0.0, 0.0, 3.0])
    # m2 = 18/5, m4 = 162/5 -> m4/m2^2 = 2,5
    assert misure.curtosi_eccesso(r) == pytest.approx(2.5 - 3)
    assert misure.asimmetria(r) == pytest.approx(0.0)
    assert misure.asimmetria([0.0, 0.0, 0.0, 1.0]) > 0


def test_rifiuta_valori_mancanti():
    with pytest.raises(ValueError):
        misure.sharpe([0.01, np.nan])


def test_indici_bootstrap():
    idx = misure.indici_bootstrap(200, 500, blocco_medio=6, seed=3)
    assert idx.shape == (500, 200)
    assert idx.min() >= 0 and idx.max() < 200
    # lunghezza media dei blocchi vicina a 6: un blocco nuovo quando l'indice non e' il successivo
    nuovi = (idx[:, 1:] != (idx[:, :-1] + 1) % 200).mean()
    assert 1 / nuovi == pytest.approx(6, rel=0.1)
    assert np.array_equal(idx, misure.indici_bootstrap(200, 500, blocco_medio=6, seed=3))


def test_differenza_sharpe():
    rng = np.random.default_rng(0)
    a = rng.normal(0.01, 0.04, 240)
    d = misure.differenza_sharpe(a, a, ricampionamenti=200)
    assert d["stima"] == 0 and d["basso"] == 0 and d["alto"] == 0
    d = misure.differenza_sharpe(a + 0.01, a, ricampionamenti=500)
    assert d["stima"] > 0 and d["basso"] > 0 and d["basso"] < d["stima"] < d["alto"]


def test_alfa_ritrova_i_coefficienti():
    rng = np.random.default_rng(1)
    x = rng.normal(0, 0.05, 600)
    y = 0.002 + 0.5 * x + rng.normal(0, 0.001, 600)
    a = misure.alfa(y, x)
    assert a["alfa"] == pytest.approx(12 * 0.002, rel=0.05)
    assert a["beta"] == pytest.approx(0.5, rel=0.01)
    assert a["t_alfa"] > 10


def test_memmel_e_errore_standard_a_mano():
    rng = np.random.default_rng(2)
    a = rng.normal(0.01, 0.05, 300)
    b = 0.8 * a + rng.normal(0.0, 0.02, 300)
    t = misure.memmel(a, b)
    sa, sb = a.mean() / a.std(ddof=1), b.mean() / b.std(ddof=1)
    rho = np.corrcoef(a, b)[0, 1]
    v = (2 - 2 * rho + 0.5 * (sa ** 2 + sb ** 2 - 2 * sa * sb * rho ** 2)) / 300
    assert t["z"] == pytest.approx((sa - sb) / np.sqrt(v))
    assert 0 <= t["p"] <= 1
    # stessi rendimenti in ordine inverso: stesso Sharpe, quindi z = 0 e p = 1
    inverso = misure.memmel(a, a[::-1])
    assert inverso["z"] == pytest.approx(0, abs=1e-12) and inverso["p"] == pytest.approx(1)
    assert misure.errore_standard_sharpe(a) == pytest.approx(np.sqrt((1 + sa ** 2 / 2) / 300) * np.sqrt(12))


def serie_con_statistiche(media, dev, n, rng, base=None, rho=0.0):
    """Serie con media, deviazione standard (ddof=1) e correlazione con base esattamente fissate."""
    z = rng.normal(size=n)
    z = z - z.mean()
    if base is not None:
        b = (base - base.mean()) / base.std(ddof=1)
        z = z - (z @ b) / (b @ b) * b  # ortogonale alla base
        z = z / z.std(ddof=1)
        z = rho * b + np.sqrt(1 - rho ** 2) * z
    return media + dev * z / z.std(ddof=1)


def test_memmel_e_errore_standard_con_valori_calcolati_a_parte():
    rng = np.random.default_rng(7)
    a = serie_con_statistiche(0.01, 0.05, 100, rng)            # Sharpe mensile 0,2
    b = serie_con_statistiche(0.005, 0.05, 100, rng, a, 0.9)   # Sharpe mensile 0,1, correlazione 0,9
    # varianza = (2 - 1,8 + 0,5 (0,04 + 0,01 - 2 x 0,2 x 0,1 x 0,81)) / 100 = 0,002088; z = 0,1 / 0,04570
    t = misure.memmel(a, b)
    assert t["correlazione"] == pytest.approx(0.9)
    assert t["z"] == pytest.approx(2.18843, rel=1e-4)
    assert t["p"] == pytest.approx(0.02864, abs=1e-4)
    # errore standard dello Sharpe annuo: radice((1 + 0,2^2 / 2) / 100) x radice(12) = 0,34986
    assert misure.errore_standard_sharpe(a) == pytest.approx(0.34986, rel=1e-4)
