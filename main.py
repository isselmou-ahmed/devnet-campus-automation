#!/usr/bin/env python3
"""
main.py
Point d'entrée : orchestre le pipeline complet d'automatisation du réseau
campus multi-sites — inventaire -> déploiement -> vérification -> rapport.

Usage:
    python main.py
"""

from src.utils import load_inventory, setup_logging
from src.inventory import build_device_list
from src.push_config import deploy
from src.verify import verify_device, ROUTER_CHECKS


def main():
    logger = setup_logging()
    logger.info("=== Démarrage du pipeline d'automatisation réseau campus ===")

    config = load_inventory("inventory.yaml")
    devices = build_device_list(config)
    logger.info(f"{len(devices)} équipement(s) chargé(s) depuis inventory.yaml "
                f"({len(config['sites'])} site(s)).")

    # 1. Déploiement (backup -> push -> save_config), résilient équipement par équipement
    resultats = deploy(devices, config["settings"], logger)

    # 2. Vérification post-déploiement (couche 2/3, routage, sécurité)
    for device in devices:
        if device["kind"] == "routeur":
            verify_device(device, ROUTER_CHECKS, logger)

    # 3. Rapport de synthèse final
    logger.info("=== Rapport de synthèse ===")
    for hostname, statut in resultats.items():
        logger.info(f"  {hostname:15s} -> {statut}")

    echecs = [h for h, s in resultats.items() if s == "ÉCHEC"]
    if echecs:
        logger.warning(f"Équipements en échec: {', '.join(echecs)}")
    else:
        logger.info("Tous les équipements ont été déployés et vérifiés avec succès.")


if __name__ == "__main__":
    main()
