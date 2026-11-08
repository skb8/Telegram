"""Validate release inputs and restore signing material without logging secrets."""
import base64
import os
from pathlib import Path
import re

properties = dict(
    line.split('=', 1) for line in Path('gradle.properties').read_text().splitlines()
    if '=' in line and not line.startswith('#')
)
tag = os.environ['RELEASE_TAG']
if not re.fullmatch(r'\d+\.\d+\.\d+', tag) or tag != properties['APP_VERSION_NAME']:
    raise SystemExit('Release tag must exactly match APP_VERSION_NAME (for example, 13.1.1).')
required = ('RELEASE_KEYSTORE_BASE64', 'RELEASE_STORE_PASSWORD', 'RELEASE_KEY_ALIAS',
            'RELEASE_KEY_PASSWORD', 'RELEASE_CERT_SHA256', 'TELEGRAM_API_ID', 'TELEGRAM_API_HASH')
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise SystemExit('Missing repository secrets: ' + ', '.join(missing))
fingerprint = os.environ['RELEASE_CERT_SHA256'].replace(':', '').lower()
if not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
    raise SystemExit('Invalid signing certificate SHA-256 fingerprint.')
keystore = Path(os.environ['RELEASE_KEYSTORE_PATH'])
keystore.write_bytes(base64.b64decode(os.environ['RELEASE_KEYSTORE_BASE64'], validate=True))
keystore.chmod(0o600)
print('Release version and required secrets validated; restored signing keystore.')
