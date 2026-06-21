from __future__ import annotations
from datetime import timedelta
DOMAIN = 'mykoplus'
CONF_EMAIL = 'email'
CONF_PASSWORD = 'password'
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
PLATFORMS = ['switch', 'light', 'climate', 'sensor']
