import json

import pytest

from risk_managed_momentum import configurazione as cfg


def test_impronta_uguale_con_fine_riga_windows(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_bytes(b"riga uno\nriga due\n")
    b.write_bytes(b"riga uno\r\nriga due\r\n")
    assert cfg.impronta(a) == cfg.impronta(b)


@pytest.mark.skipif(not cfg.CONFIG.exists(), reason="configurazione non ancora congelata")
def test_configurazione_congelata_coincide_con_codice_e_criteri():
    congelata = json.loads(cfg.CONFIG.read_text(encoding="utf-8"))
    assert congelata == json.loads(json.dumps(cfg.attesa()))
