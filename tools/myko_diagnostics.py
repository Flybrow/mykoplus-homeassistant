#!/usr/bin/env python3
"""Myko+ diagnostics — aide a integrer vos appareils a Home Assistant.

Aucune dependance : Python 3.8+ uniquement.  Lancement :  python myko_diagnostics.py

Vous choisissez un appareil, puis vous enregistrez les actions que vous voulez
piloter depuis Home Assistant (l'outil detecte tout seul le reglage modifie).
Le fichier genere (myko_report.json) est ANONYMISE : pas de mot de passe, pas de
jeton, et les donnees personnelles (adresse, GPS, numeros de serie, identifiants)
sont masquees.

Envoyez le rapport via une issue :
https://github.com/Flybrow/mykoplus-homeassistant/issues
"""

from __future__ import annotations

import getpass
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

API_BASE = "https://mobileapi1.mykoapp.kingfisher.com"
HEADERS = {
    "application": "myko",
    "application-version": "2.5.0",
    "os": "android",
    "source-type": "myko",
    "source-id": "ha-diagnostics",
    "accept": "application/json",
    "content-type": "application/json",
    "cache-control": "no-cache",
    "user-agent": "okhttp/4.12.0",
}

REDACT_KEYS = {
    "street", "zipcode", "city", "country", "longitude", "latitude",
    "userHash", "deviceSN", "serial_number", "commissioningId", "ip", "mac",
    "token", "refresh_token", "password", "email", "log", "name", "nickname",
}
ID_KEYS = {"_id", "id", "owner", "home", "homeId", "userId", "manager", "profile"}
NOISE_KEYS = {"rssi", "log", "nbRestart", "logLevel", "bleAdvertising", "last_connection"}

_id_map: dict[str, str] = {}


def _anon_id(val):
    if val in ("", None):
        return val
    if val not in _id_map:
        _id_map[val] = "id_" + hashlib.sha1(str(val).encode()).hexdigest()[:8]
    return _id_map[val]


def redact(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in REDACT_KEYS:
                out[k] = "***" if v not in (None, "", [], {}) else v
            elif k in ID_KEYS and isinstance(v, str):
                out[k] = _anon_id(v)
            elif k in ("devices", "groups", "associatedDevices", "children") and isinstance(v, list):
                out[k] = [_anon_id(x) if isinstance(x, str) else redact(x) for x in v]
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


class MykoError(Exception):
    pass


class Session:
    """Session Myko+ avec re-login automatique sur 401.

    Myko n'autorise qu'UNE session active : si l'app Myko reprend la main pendant
    l'utilisation de l'outil, notre jeton est invalide. On se reconnecte alors
    automatiquement pour reprendre la main.
    """

    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password
        self.token = None
        self.user_id = None
        self._login()

    def _login(self):
        data = self._raw("POST", "/v1/auth/login",
                         body={"email": self._email, "password": self._password}, auth=False)
        if not isinstance(data, dict) or "token" not in data:
            raise MykoError("Login refuse (verifiez email / mot de passe).")
        self.token = data["token"]
        self.user_id = data["id"]

    def _raw(self, method, path, body=None, auth=True):
        headers = dict(HEADERS)
        if auth and self.token:
            headers["authorization"] = f"Bearer {self.token}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(API_BASE + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            raise MykoError(f"HTTP {e.code}") from e
        except urllib.error.URLError as e:
            raise MykoError(f"Reseau injoignable : {e}")
        return json.loads(raw) if raw else None

    def request(self, method, path, body=None):
        try:
            return self._raw(method, path, body)
        except MykoError as e:
            if "401" in str(e):
                self._login()
                return self._raw(method, path, body)
            raise

    def homes(self):
        data = self.request("GET", f"/v1/users/{self.user_id}/homes") or {}
        return data.get("homes", data if isinstance(data, list) else [])

    def devices(self):
        out = []
        for h in self.homes():
            hid = h.get("_id") or h.get("id")
            devs = self.request("GET", f"/v1/homes/{hid}/devices") or []
            if isinstance(devs, dict):
                devs = devs.get("devices", [])
            out.extend(devs)
        return out


def device_label(d):
    name = d.get("name") or d.get("profile_name") or "Appareil"
    model = d.get("reference") or d.get("model") or d.get("profile_name") or "?"
    online = "en ligne" if d.get("connected") else "hors ligne"
    return f"{name}  [{model}]  ({online})"


def diff_state(before: dict, after: dict):
    changes = []
    for k, v in after.items():
        if k in NOISE_KEYS or k in REDACT_KEYS:
            continue
        if before.get(k) != v:
            changes.append({"key": k, "before": before.get(k), "after": v})
    return changes


def capture_action(session: Session, device_id: str):
    print("\n  Nom court de l'action (ex: \"Allumer\", \"Luminosite 50%\",")
    label = input("  \"Consigne 20 degres\"), ou Entree pour revenir : ").strip()
    if not label:
        return None

    def state_of(did):
        for d in session.devices():
            if d.get("_id") == did:
                return dict(d.get("state", {}))
        return {}

    baseline = state_of(device_id)
    print(f"\n  >>> Faites « {label} » dans l'app Myko maintenant.")
    print("      Quand c'est fait, revenez ici et appuyez sur Entree.")
    input("      (Entree pour lancer la detection) ")

    print("      Detection en cours...", end="", flush=True)
    deadline = time.time() + 25
    changes = []
    while time.time() < deadline:
        try:
            cur = state_of(device_id)
        except MykoError:
            time.sleep(1.5)
            continue
        changes = diff_state(baseline, cur)
        if changes:
            break
        print(".", end="", flush=True)
        time.sleep(1.5)
    print()

    if changes:
        print("  >> Action enregistree :")
        for c in changes:
            print(f"       {c['key']} : {c['before']} -> {c['after']}")
    else:
        print("  >> Aucun changement detecte. L'action n'a peut-etre pas eu lieu,")
        print("     ou ce reglage n'est pas remonte par le cloud Myko. Reessayez.")
    return {"label": label, "changes": changes}


def device_menu(session: Session, device_id: str, name: str, actions: list):
    while True:
        print(f"\n=== {name} ===")
        if actions:
            print(f"  ({len(actions)} action(s) deja enregistree(s))")
        print("  [a] Enregistrer une action")
        print("  [r] Revenir a la liste des appareils")
        choice = input("  Votre choix : ").strip().lower()
        if choice == "a":
            res = capture_action(session, device_id)
            if res:
                actions.append(res)
        elif choice in ("r", ""):
            return


def main() -> int:
    print("=== Myko+ diagnostics ===")
    print("Vos identifiants servent UNIQUEMENT a interroger le cloud Myko+.")
    print("Ils ne sont ni enregistres ni transmis.\n")
    print("ASTUCE : pendant la detection d'une action, l'outil peut reprendre la")
    print("session a l'app Myko (Myko n'autorise qu'une connexion a la fois). Si")
    print("l'app vous deconnecte, c'est normal ; reconnectez-vous-y au besoin.\n")

    email = input("Email Myko+ : ").strip()
    password = getpass.getpass("Mot de passe Myko+ : ")
    try:
        session = Session(email, password)
    except MykoError as e:
        print("\nErreur :", e)
        return 1
    print("Connexion OK.")

    actions_by_device: dict[str, list] = {}
    while True:
        try:
            devices = session.devices()
        except MykoError as e:
            print("\nErreur de lecture :", e)
            return 1
        print("\n==================== VOS APPAREILS ====================")
        for i, d in enumerate(devices, 1):
            mark = " *" if actions_by_device.get(d.get("_id")) else ""
            print(f"  {i}) {device_label(d)}{mark}")
        print("  q) Terminer et generer le rapport")
        choice = input("Choisissez un appareil (numero) : ").strip().lower()
        if choice in ("q", "quit", "fin", ""):
            break
        if not choice.isdigit() or not (1 <= int(choice) <= len(devices)):
            print("  Choix invalide.")
            continue
        d = devices[int(choice) - 1]
        did = d.get("_id")
        name = d.get("name") or d.get("profile_name") or "Appareil"
        actions = actions_by_device.setdefault(did, [])
        device_menu(session, did, name, actions)

    # Rapport (anonymise)
    try:
        homes = session.homes()
        devices = session.devices()
    except MykoError:
        homes, devices = [], []
    report = {"homes": [redact(h) for h in homes], "devices": []}
    for d in devices:
        rd = redact(d)
        acts = actions_by_device.get(d.get("_id"))
        if acts:
            rd["actions"] = acts
        report["devices"].append(rd)
    report["_note"] = "Donnees anonymisees. Aucune info personnelle/identifiant reel."

    out = "myko_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in actions_by_device.values())
    print(f"\nTermine : {len(devices)} appareil(s), {total} action(s) dans '{out}'.")
    print("Envoyez ce fichier via une issue :")
    print("  https://github.com/Flybrow/mykoplus-homeassistant/issues")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        code = 1
    except Exception as e:
        print("\nErreur inattendue :", e)
        code = 1
    try:
        input("\nAppuyez sur Entree pour quitter...")
    except EOFError:
        pass
    sys.exit(code)
