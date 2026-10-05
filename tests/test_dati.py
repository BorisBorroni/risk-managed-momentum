import numpy as np
import pandas as pd
import pytest

from risk_managed_momentum import dati

MENSILE = (
    "Intestazione del file\r\n"
    "Missing data are indicated by -99.99 or -999.\r\n"
    "\r\n"
    "  Average Value Weighted Returns -- Monthly\r\n"
    ",Lo PRIOR,Hi PRIOR\r\n"
    "192701,  -3.32,  -0.24\r\n"
    "192702,   7.39,   7.04\r\n"
    "\r\n"
    "  Average Equal Weighted Returns -- Monthly\r\n"
    ",Lo PRIOR,Hi PRIOR\r\n"
    "192701,  10.00,  20.00\r\n"
)

GIORNALIERO = (
    "Testo\n"
    ",Mom\n"
    "19261103,   0.55\n"
    "19261104,  -0.51\n"
    "\n"
    "Copyright\n"
)


def test_legge_solo_il_primo_blocco_mensile():
    t = dati.leggi_testo(MENSILE)
    assert list(t.columns) == ["Lo PRIOR", "Hi PRIOR"]
    assert list(t.index) == [pd.Timestamp("1927-01-31"), pd.Timestamp("1927-02-28")]
    assert t.loc["1927-01-31", "Lo PRIOR"] == pytest.approx(-0.0332)
    assert t.loc["1927-02-28", "Hi PRIOR"] == pytest.approx(0.0704)


def test_legge_date_giornaliere_e_si_ferma_al_copyright():
    t = dati.leggi_testo(GIORNALIERO)
    assert list(t.index) == [pd.Timestamp("1926-11-03"), pd.Timestamp("1926-11-04")]
    assert t["Mom"].tolist() == pytest.approx([0.0055, -0.0051])


def test_rifiuta_valori_mancanti():
    with pytest.raises(ValueError, match="mancanti"):
        dati.leggi_testo(GIORNALIERO.replace("-0.51", "-99.99"))


def test_rifiuta_righe_con_colonne_sbagliate():
    with pytest.raises(ValueError, match="colonne"):
        dati.leggi_testo(GIORNALIERO.replace("19261104,  -0.51", "19261104,  -0.51, 3.00"))


def test_rifiuta_date_non_crescenti():
    with pytest.raises(ValueError, match="crescenti"):
        dati.leggi_testo(GIORNALIERO.replace("19261104", "19261102"))


def test_wml_e_mom_dai_sei():
    decili = pd.DataFrame({"Lo PRIOR": [0.01, -0.02], "Hi PRIOR": [0.03, 0.01]})
    assert dati.wml(decili).tolist() == pytest.approx([0.02, 0.03])
    sei = pd.DataFrame({"SMALL LoPRIOR": [0.01], "BIG LoPRIOR": [0.03],
                        "SMALL HiPRIOR": [0.05], "BIG HiPRIOR": [0.02]})
    assert dati.mom_dai_sei(sei).iloc[0] == pytest.approx(0.5 * (0.05 + 0.02) - 0.5 * (0.01 + 0.03))


def test_carica_segnala_file_mancanti(tmp_path):
    with pytest.raises(FileNotFoundError, match="00_scarica_dati"):
        dati.carica(tmp_path)


@pytest.mark.slow
@pytest.mark.skipif(not dati.dati_presenti(), reason="dati di French non presenti in data/raw")
def test_dati_reali_completi_e_coerenti():
    d = dati.carica()
    assert d.decili_m.index[0] == pd.Timestamp("1927-01-31")
    assert d.decili_g.index[0] == pd.Timestamp("1926-11-03")
    for x in (d.mom_m, d.sei_m, d.decili_m):
        assert x.index.equals(d.decili_m.index)
    for x in (d.mom_g, d.sei_g):
        assert x.index.equals(d.decili_g.index)
    assert d.decili_g.index.isin(d.fattori_g.index).all()
    assert np.abs(dati.mom_dai_sei(d.sei_m) - d.mom_m).max() <= 0.0002
    assert np.abs(dati.mom_dai_sei(d.sei_g) - d.mom_g).max() <= 0.0002
