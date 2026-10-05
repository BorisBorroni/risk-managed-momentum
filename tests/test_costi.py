import pandas as pd
import pytest

from risk_managed_momentum import costi


def test_costi_fatti_a_mano_lungo_corto():
    w = pd.Series([1.0, 1.5, 0.5])
    c = costi.costo_mensile(w, "alto")
    # mese 2: prestito 1%/12 x 1,5 + negoziazione 4%/12 x 3 + 20 punti base x 2 x 0,5
    assert c.iloc[1] == pytest.approx(0.01 / 12 * 1.5 + 0.04 / 12 * 3.0 + 0.002 * 2 * 0.5)
    # il primo mese non paga la variazione del peso
    assert c.iloc[0] == pytest.approx(0.01 / 12 + 0.04 / 12 * 2)


def test_costi_solo_lungo_senza_prestito():
    w = pd.Series([1.0, 2.0])
    c = costi.costo_mensile(w, "medio", lungo_corto=False)
    assert c.iloc[1] == pytest.approx(0.02 / 12 * 2.0 + 0.001 * 1.0)


def test_lordo_non_cambia_nulla_e_peso_costante():
    r = pd.Series([0.01, -0.02, 0.03])
    assert costi.netto(r, 1.0, "lordo").tolist() == pytest.approx(r.tolist())
    netti = costi.netto(r, 1.0, "medio")
    assert (r - netti).tolist() == pytest.approx([0.005 / 12 + 0.02 / 12 * 2] * 3)
