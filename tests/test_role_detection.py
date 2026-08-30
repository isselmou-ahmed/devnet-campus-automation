"""
test_role_detection.py
Vérifie que detect_role() déduit correctement le rôle logique d'un
équipement à partir de son hostname réel (obligation du cahier des charges :
au moins un test pytest).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import detect_role


def test_detect_role_routeur():
    assert detect_role("R1-DKR") == "routeur"
    assert detect_role("R2-ABJ") == "routeur"
    assert detect_role("R3-SL") == "routeur"


def test_detect_role_switch_coeur():
    assert detect_role("SW1-CORE") == "switch_coeur"
    assert detect_role("SW2-CORE") == "switch_coeur"


def test_detect_role_switch_acces():
    assert detect_role("SW3-ACC") == "switch_acces"
    assert detect_role("SW4-ACC") == "switch_acces"


def test_detect_role_inconnu():
    assert detect_role("SRV-DNS") == "inconnu"


def test_detect_role_insensible_a_la_casse():
    assert detect_role("r1-dkr") == "routeur"
    assert detect_role("sw1-core") == "switch_coeur"
