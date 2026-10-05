"""Congela la configurazione del test in config_congelata.json, dopo la replica e prima del test.

Il file contiene i parametri della regola, il periodo di test, il bootstrap, gli scenari di costo
e l'impronta SHA-256 di docs/criteri_del_verdetto.md. Non sovrascrive un file gia' esistente.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from risk_managed_momentum import configurazione as cfg  # noqa: E402


def main():
    if cfg.CONFIG.exists():
        sys.exit("config_congelata.json esiste gia': non si sovrascrive.")
    if "replica superata" not in cfg.REPLICA.read_text(encoding="utf-8"):
        sys.exit("La replica non risulta superata: prima scripts/02_replica_paper.py.")
    cfg.CONFIG.write_text(json.dumps(cfg.attesa(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(cfg.CONFIG.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
