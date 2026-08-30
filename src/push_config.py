"""
push_config.py
Cœur de l'automatisation : pour chaque équipement de l'inventaire,
- détecte le device_type via SSHDetect (aucune saisie manuelle),
- lit le hostname réel via find_prompt() et en déduit le rôle,
- sauvegarde le running-config avant toute modification,
- pousse la configuration adaptée au rôle (routeur -> EIGRP ; switch -> VLAN
  + ports d'accès + PortFast/BPDU Guard ; jamais PortFast sur un uplink/trunk),
- sauvegarde la configuration (save_config) et journalise le résultat.
Une panne sur un équipement (SSH, auth, timeout) est capturée et journalisée
sans interrompre le traitement des autres équipements.
"""

from netmiko import (
    ConnectHandler,
    SSHDetect,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

from src.utils import backup_running_config, detect_role


def _connect_with_autodetect(device):
    """SSHDetect : identifie le device_type sans saisie manuelle, puis se connecte."""
    guesser = SSHDetect(**{k: v for k, v in device.items() if k not in (
        "kind", "site", "expected_hostname", "vlan", "network", "gateway",
        "role", "access_ports",
    )})
    best_match = guesser.autodetect()
    conn_params = {
        k: v for k, v in device.items()
        if k not in ("kind", "site", "expected_hostname", "vlan", "network",
                      "gateway", "role", "access_ports")
    }
    conn_params["device_type"] = best_match or "cisco_ios"
    return ConnectHandler(**conn_params)


def _push_router_eigrp(net_connect, device, eigrp_as, logger):
    """Retire OSPF (si présent) et pousse la config EIGRP finale du routeur."""
    commands = [
        "no router ospf 1",
        f"router eigrp {eigrp_as}",
        f"network {device['network'].split('/')[0]} 0.0.0.255",
        "network 192.168.10.0 0.0.0.255",
        "no auto-summary",
    ]
    output = net_connect.send_config_set(commands)
    logger.debug(output)


def _push_switch_config(net_connect, device, logger):
    """Crée le VLAN du site, l'assigne aux ports d'accès (PortFast + BPDU Guard)."""
    vlan_id = device["vlan"]
    commands = [f"vlan {vlan_id}", f"name SITE_{device['site'].upper()}", "exit"]

    for port in device.get("access_ports", []):
        commands += [
            f"interface {port}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}",
            "spanning-tree portfast",
            "spanning-tree bpduguard enable",
            "exit",
        ]
    output = net_connect.send_config_set(commands)
    logger.debug(output)


def deploy(devices, settings, logger):
    """
    Boucle principale : traite chaque équipement indépendamment.
    Retourne un résumé {hostname: statut} pour le rapport de synthèse final.
    """
    resultats = {}

    for device in devices:
        label = f"{device['site']} / {device['expected_hostname']}"
        try:
            net_connect = _connect_with_autodetect(device)
            real_hostname = net_connect.find_prompt().strip("#>")
            role = detect_role(real_hostname)

            backup_path = backup_running_config(
                net_connect, real_hostname, settings.get("backup_dir", "backups/")
            )
            logger.info(f"[{label}] Sauvegarde effectuée -> {backup_path}")

            if role == "routeur":
                _push_router_eigrp(net_connect, device, settings["eigrp_as"], logger)
            elif role in ("switch_coeur", "switch_acces"):
                _push_switch_config(net_connect, device, logger)
            else:
                logger.warning(f"[{label}] Rôle non reconnu ({real_hostname}), aucune action.")

            net_connect.save_config()
            net_connect.disconnect()

            resultats[real_hostname] = "OK"
            logger.info(f"[{label}] Déploiement réussi (rôle détecté: {role}).")

        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            resultats[device["expected_hostname"]] = "ÉCHEC"
            logger.error(f"[{label}] Échec de connexion: {e}")
        except Exception as e:  # sécurité additionnelle : ne jamais bloquer les autres sites
            resultats[device["expected_hostname"]] = "ÉCHEC"
            logger.error(f"[{label}] Erreur inattendue: {e}")

    return resultats
