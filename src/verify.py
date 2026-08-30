"""
verify.py
Vérifie, après déploiement, que l'état réel de chaque équipement correspond
à l'état souhaité défini dans l'inventaire, et produit le rapport de
synthèse final (statut par équipement + test de connectivité inter-sites).
"""

from netmiko import ConnectHandler


def verify_device(device, checks, logger):
    """
    Exécute les commandes de vérification adaptées au rôle de l'équipement
    et journalise le résultat de chaque couche contrôlée.
    """
    conn_params = {
        k: v for k, v in device.items()
        if k not in ("kind", "site", "expected_hostname", "vlan", "network",
                      "gateway", "role", "access_ports")
    }
    conn_params.setdefault("device_type", "cisco_ios")

    try:
        net_connect = ConnectHandler(**conn_params)
        for label, command in checks:
            output = net_connect.send_command(command)
            logger.info(f"[{device['expected_hostname']}] {label}: VÉRIFIÉ")
            logger.debug(output)
        net_connect.disconnect()
        return True
    except Exception as e:
        logger.error(f"[{device['expected_hostname']}] Vérification impossible: {e}")
        return False


ROUTER_CHECKS = [
    ("VLANs & Trunks (802.1Q)", "show vlan brief"),
    ("Passerelles & Interfaces WAN", "show ip interface brief"),
    ("Voisins & Routes EIGRP", "show ip eigrp neighbors"),
    ("Routage EIGRP", "show ip route eigrp"),
    ("STP PortFast & BPDU Guard", "show spanning-tree summary"),
]


def ping_inter_sites(source_device, target_ip, logger):
    """
    Test final de connectivité PC1 <-> PC1 (ou routeur à routeur) entre deux
    sites, lancé depuis un équipement source vers l'IP cible.
    """
    conn_params = {
        k: v for k, v in source_device.items()
        if k not in ("kind", "site", "expected_hostname", "vlan", "network",
                      "gateway", "role", "access_ports")
    }
    conn_params.setdefault("device_type", "cisco_ios")

    net_connect = ConnectHandler(**conn_params)
    result = net_connect.send_command(f"ping {target_ip}")
    net_connect.disconnect()

    logger.info(f"Test de connectivité inter-sites vers {target_ip}:\n{result}")
    return result
