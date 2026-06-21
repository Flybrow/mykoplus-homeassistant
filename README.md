<p align="center">
  <img src="custom_components/mykoplus/brand/logo.png" alt="Myko+" width="160">
</p>

# Myko+ pour Home Assistant

Intégration personnalisée (custom integration) pour les appareils connectés de la
marque **Myko+** (Kingfisher — vendus chez B&Q, Castorama et Screwfix, parfois
co-marqués *GoodHome* ou *Jacobsen*).

Elle se connecte au cloud Myko+ avec vos identifiants de l'application mobile et
expose vos appareils dans Home Assistant. Aucune modification du matériel n'est
nécessaire.

[![hacs](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![version](https://img.shields.io/badge/version-1.0.0-blue.svg)

## Fonctionnalités

- Connexion par e-mail / mot de passe du compte Myko+.
- Découverte automatique des appareils de vos maisons.
- **Mises à jour en temps réel** (push) de l'état des appareils.
- Reconnexion automatique en cas d'expiration de session.

## Appareils pris en charge

| Type | Entité Home Assistant | État |
|------|-----------------------|------|
| Prise connectée | `switch` (marche/arrêt) + `switch` « Voyant LED » | ✅ pris en charge |
| Lumière variable | `light` | 🧪 expérimental |
| Radiateur / thermostat | `climate` | 🧪 expérimental |
| Capteurs (température, batterie, humidité) | `sensor` | 🧪 expérimental |

Les types marqués 🧪 sont implémentés mais n'ont pas encore été validés sur du
matériel réel — les retours sont les bienvenus via les
[issues](https://github.com/Flybrow/mykoplus-homeassistant/issues). Les entités ne
sont créées que si l'appareil expose les informations correspondantes.

## Installation

### Via HACS (recommandé)

1. HACS → menu (⋮) → **Dépôts personnalisés**.
2. Ajouter `https://github.com/Flybrow/mykoplus-homeassistant`, catégorie
   **Integration**.
3. Installer **Myko+**, puis redémarrer Home Assistant.

### Manuelle

Copier le dossier `custom_components/mykoplus` dans le dossier `config/custom_components`
de votre installation Home Assistant, puis redémarrer.

## Configuration

1. **Paramètres → Appareils et services → Ajouter une intégration**.
2. Rechercher **Myko+**.
3. Saisir l'**e-mail** et le **mot de passe** de votre compte Myko+.

Vos appareils apparaissent ensuite automatiquement.

## Dépannage

- **Identifiants invalides** : vérifiez que vous pouvez vous connecter dans
  l'application mobile Myko+ avec les mêmes identifiants.
- **Appareil indisponible** : vérifiez que l'appareil est en ligne dans
  l'application Myko+ ; l'intégration reflète l'état du cloud.

## Aider à intégrer votre appareil

Votre appareil Myko+ n'est pas (bien) géré ? Un petit outil exporte la
description **anonymisée** de vos appareils pour m'aider à les ajouter — aucune
capture réseau compliquée nécessaire.

1. Téléchargez **MykoDiagnostics.exe** depuis la
   [dernière release](https://github.com/Flybrow/mykoplus-homeassistant/releases)
   (ou, si vous avez Python : `python tools/myko_diagnostics.py`).
2. Lancez-le, saisissez vos identifiants Myko+ (ils ne sont **ni enregistrés ni
   transmis** — ils servent uniquement à interroger le cloud Myko+).
3. Suivez les invites (option « diff » pour capturer un réglage précis).
4. Envoyez le fichier `myko_report.json` généré via une
   [issue](https://github.com/Flybrow/mykoplus-homeassistant/issues).

Le rapport ne contient ni mot de passe, ni jeton, ni données personnelles
(adresse, GPS, numéros de série et identifiants sont masqués).

## Avertissement

Projet communautaire **non affilié** à Kingfisher, Myko+ ou leurs partenaires.
Utilise une API non officielle, susceptible d'évoluer sans préavis. Fourni « en
l'état », sans garantie.

## Licence

[MIT](LICENSE)
