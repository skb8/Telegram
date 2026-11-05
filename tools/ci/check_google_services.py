"""Fail before native compilation if Firebase clients do not match module IDs."""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
library_gradle = (root / 'TMessagesProj/build.gradle').read_text()
namespace = re.search(r'''namespace\s+['"]([^'"]+)['"]''', library_gradle)
app_package = re.search(r'^APP_PACKAGE=(.+)$', (root / 'gradle.properties').read_text(), re.MULTILINE)
if not namespace or not app_package:
    raise SystemExit('Cannot determine library namespace or application ID.')
for module, expected in [('TMessagesProj', namespace.group(1)),
                         ('TMessagesProj_AppStandalone', app_package.group(1).strip())]:
    config = json.loads((root / module / 'google-services.json').read_text())
    packages = {client.get('client_info', {}).get('android_client_info', {}).get('package_name')
                for client in config.get('client', [])}
    if expected not in packages:
        raise SystemExit(module + '/google-services.json: missing client for ' + expected)
    print(module + ': Firebase client matches ' + expected)
