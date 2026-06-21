# Changelog

Toutes les modifications notables de ce projet sont documentées ici.
Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
projet adhère au [versionnage sémantique](https://semver.org/lang/fr/).

## [1.0.0] - 2026-06-21

Première version stable.

### Ajouté
- Connexion au cloud Myko+ (Kingfisher) par e-mail / mot de passe.
- Découverte automatique des appareils de toutes les maisons.
- Prise connectée : entité `switch` (marche/arrêt) et `switch` « Voyant LED ».
- Mises à jour d'état en **temps réel** (socket.io) avec polling de secours.
- Reconnexion automatique en cas d'expiration de session.
- Plateformes **expérimentales** `light`, `climate` et `sensor` (créées selon les
  informations exposées par l'appareil).
- Outil de diagnostic (`tools/myko_diagnostics.py` / `MykoDiagnostics.exe`) pour
  exporter une description anonymisée des appareils et aider à leur intégration.

[1.0.0]: https://github.com/Flybrow/mykoplus-homeassistant/releases/tag/v1.0.0
