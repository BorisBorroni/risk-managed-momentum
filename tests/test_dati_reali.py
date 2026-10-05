"""Test sui dati reali di French: saltati se i dati non sono in data/raw (per esempio nella CI)."""
import numpy as np
import pandas as pd
import pytest

from risk_managed_momentum import configurazione as cfg
from risk_managed_momentum import dati, esame, misure, serie, strategia

pytestmark = [pytest.mark.slow,
              pytest.mark.skipif(not dati.dati_presenti(), reason="dati di French non presenti in data/raw")]


# i numeri versionati valgono per gli zip usati nel repository (versione CRSP 202608)
stessa_versione = pytest.mark.skipif(not dati.dati_presenti() or not all(dati.stessa_versione().values()),
                                     reason="dati assenti o di una versione diversa da quella usata nel repository")


@pytest.fixture(scope="module")
def caricati():
    d = dati.carica()
    tabella, pesi = serie.costruisci(d)
    return d, tabella, pesi


def test_pesi_reali_non_usano_dati_futuri(caricati):
    d, _, pesi = caricati
    g = dati.wml(d.decili_g)
    for taglio in ("1932-06-30", "2008-12-31", "2011-12-30"):
        parziali = strategia.pesi(g.loc[:taglio])
        assert np.allclose(parziali.to_numpy(), pesi["wml"].loc[parziali.index].to_numpy())
    # il peso di gennaio 2012 (primo mese del test) e' gia' noto con i dati fino a dicembre 2011
    assert parziali.index[-1] == pd.Timestamp("2012-01-31")


@stessa_versione
def test_replica_entro_la_tolleranza(caricati):
    _, tabella, _ = caricati
    x = serie.finestra(tabella, None, "2011-12-31", ["wml", "wml_gestita"])
    assert x.index[0] == pd.Timestamp("1927-05-31") and len(x) == 1016
    assert abs(misure.sharpe(x["wml"]) - 0.53) <= 0.10
    assert abs(misure.sharpe(x["wml_gestita"]) - 0.97) <= 0.10
    testo = (cfg.RADICE / "docs" / "esito_replica.txt").read_text(encoding="utf-8")
    assert f"Sharpe {misure.sharpe(x['wml_gestita']):.2f} (paper 0.97" in testo


@stessa_versione
def test_esito_versionato_coincide_con_il_calcolo(caricati):
    _, tabella, pesi = caricati
    righe, risultati = esame.analisi(tabella, pesi, cfg.TEST_INIZIO, cfg.TEST_FINE, cfg.SOTTOPERIODI,
                                     cfg.BOOTSTRAP, cfg.RITARDI_NEWEY_WEST)
    assert len(risultati["x"]) == 176
    testo = (cfg.RADICE / "docs" / "esito_test.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert "\n".join(righe) in testo


def test_dati_reali_completi_e_coerenti(caricati):
    d = caricati[0]
    assert d.decili_m.index[0] == pd.Timestamp("1927-01-31")
    assert d.decili_g.index[0] == pd.Timestamp("1926-11-03")
    for x in (d.mom_m, d.sei_m, d.decili_m):
        assert x.index.equals(d.decili_m.index)
    for x in (d.mom_g, d.sei_g):
        assert x.index.equals(d.decili_g.index)
    assert d.decili_g.index.isin(d.fattori_g.index).all()
    assert np.abs(dati.mom_dai_sei(d.sei_m) - d.mom_m).max() <= 0.0002
    assert np.abs(dati.mom_dai_sei(d.sei_g) - d.mom_g).max() <= 0.0002
