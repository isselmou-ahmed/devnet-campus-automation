# Automatisation d'un réseau campus multi-sites — Projet Cisco DevNet

Automatisation complète (déploiement + vérification) d'un réseau campus
réparti sur 3 sites (Dakar, Abidjan, Saint-Louis) interconnectés par un
backbone WAN commun, piloté entièrement par un inventaire YAML.

## Fonctionnalités

- Inventaire externalisé (`inventory.yaml`) : ajouter un site ne demande
  aucune modification de code.
- Détection automatique du `device_type` via `SSHDetect` (Netmiko).
- Lecture du hostname réel via `find_prompt()` et déduction du rôle
  (routeur / switch cœur / switch accès) — jamais depuis l'IP.
- Migration OSPF → EIGRP (AS 100) sur les routeurs de site.
- Création automatique des VLAN et affectation des ports d'accès, avec
  PortFast + BPDU Guard (jamais activés sur un lien trunk/uplink).
- Sauvegarde horodatée du running-config avant toute modification.
- Logging double (console + fichier persistant `.log`).
- `save_config()` systématique après validation.
- Gestion d'exceptions par équipement : une panne SSH sur un site ne
  bloque pas le déploiement des autres.
- Vérification post-déploiement (VLAN/trunks, interfaces WAN, voisins et
  routes EIGRP, STP) et test de connectivité inter-sites.
- Au moins un test `pytest` (détection de rôle).

## Installation

```bash
git clone <url-du-depot>
cd devnet-campus-automation
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis renseigner NET_USERNAME / NET_PASSWORD / NET_SECRET
```

## Exécution

```bash
python main.py
```

Le pipeline : charge `inventory.yaml` → sauvegarde chaque équipement →
pousse la configuration adaptée à son rôle → `save_config()` → vérifie
l'état réel → affiche un rapport de synthèse final.

## Tests

```bash
pytest tests/
```

## Structure du dépôt

```
.
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── inventory.yaml
├── main.py
├── src/
│   ├── inventory.py      # construction de la liste d'équipements (N sites)
│   ├── push_config.py     # SSHDetect, backup, push EIGRP/VLAN, save_config
│   ├── verify.py          # vérification post-déploiement
│   └── utils.py            # config, logging, backup, credentials, detect_role
├── configs/                # configs de référence (état initial OSPF / final EIGRP)
├── tests/
│   └── test_role_detection.py
├── backups/                 # sauvegardes horodatées générées à l'exécution
└── logs/                    # journaux horodatés générés à l'exécution
```

## Limites connues

- Les noms d'interfaces d'accès sont spécifiques au lab et doivent être
  adaptés pour un déploiement hors GNS3.
- L'adressage de management de Saint-Louis reste à finaliser pour un
  déploiement hors backbone WAN.
- Le pare-feu / DMZ (192.168.200.0/24) n'est pas automatisé par l'outil ;
  seule son adressage est documenté dans l'architecture cible.
