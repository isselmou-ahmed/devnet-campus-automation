"""
utils.py
Fonctions transverses : chargement de la configuration, logging,
sauvegarde horodatée des running-config, lecture des identifiants.
"""

import os
import logging
from datetime import datetime

import yaml
from dotenv import load_dotenv

load_dotenv()


def load_inventory(path="inventory.yaml"):
    """Charge l'inventaire YAML externalisé (settings, sites, backbone)."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_credentials():
    """
    Récupère les identifiants SSH depuis les variables d'environnement
    (fichier .env, jamais commité — voir .gitignore). Aucun secret en clair
    dans le code ou dans inventory.yaml.
    """
    username = os.getenv("NET_USERNAME")
    password = os.getenv("NET_PASSWORD")
    secret = os.getenv("NET_SECRET", password)

    if not username or not password:
        raise EnvironmentError(
            "NET_USERNAME et NET_PASSWORD doivent être définis (fichier .env)."
        )
    return username, password, secret


def setup_logging(log_dir="logs/"):
    """Configure un logging double : console (suivi en direct) + fichier horodaté (audit)."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"deploiement_{timestamp}.log")

    logger = logging.getLogger("devnet_campus")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def backup_running_config(net_connect, hostname, backup_dir="backups/"):
    """
    Sauvegarde horodatée du running-config AVANT toute modification.
    Retourne le chemin du fichier de sauvegarde créé.
    """
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{hostname}_{timestamp}.cfg")

    running_config = net_connect.send_command("show running-config")
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(running_config)

    return backup_path


def detect_role(hostname):
    """
    Déduit le rôle logique d'un équipement à partir de son hostname réel
    (obtenu via find_prompt(), jamais depuis l'IP codée en dur).
        R*      -> routeur (passerelle de site / backbone)
        *CORE*  -> switch cœur
        *ACC*   -> switch d'accès
    """
    h = hostname.upper()
    if h.startswith("R"):
        return "routeur"
    if "CORE" in h:
        return "switch_coeur"
    if "ACC" in h:
        return "switch_acces"
    return "inconnu"
