"""
inventory.py
Construit dynamiquement, à partir de inventory.yaml, la liste complète des
équipements à traiter (routeurs + switches, pour N sites). Aucune IP ni
aucun rôle n'est codé en dur dans le code : tout vient de l'inventaire.
device_type est volontairement absent ici : il est déterminé par SSHDetect
au moment de la connexion (voir push_config.py).
"""

from src.utils import get_credentials


def _base_params(username, password, secret, config):
    return {
        "username": username,
        "password": password,
        "secret": secret,
        "port": config["settings"].get("ssh_port", 22),
        "timeout": config["settings"].get("device_timeout", 20),
    }


def build_device_list(config):
    """
    Transforme la section `sites` de l'inventaire en une liste de
    dictionnaires prêts pour Netmiko : un routeur de passerelle par site,
    plus l'ensemble de ses switches (cœur/accès). Fonctionne pour N sites
    sans modification : ajouter un site dans inventory.yaml suffit.
    """
    username, password, secret = get_credentials()
    base = _base_params(username, password, secret, config)

    devices = []
    for site in config["sites"]:
        devices.append(
            {
                "kind": "routeur",
                "site": site["name"],
                "expected_hostname": site["router"],
                "host": site["host"],
                "vlan": site["vlan"],
                "network": site["network"],
                "gateway": site["gateway"],
                **base,
            }
        )
        for sw in site.get("switches", []):
            devices.append(
                {
                    "kind": "switch",
                    "site": site["name"],
                    "expected_hostname": sw["name"],
                    "host": sw["host"],
                    "role": sw["role"],
                    "vlan": site["vlan"],
                    "access_ports": sw.get("access_ports", []),
                    **base,
                }
            )
    return devices
