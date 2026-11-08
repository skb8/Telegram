"""Verify release identity, version, architectures and signing certificate."""
import os
from pathlib import Path
import re
import subprocess
import zipfile

apks = list(Path('TMessagesProj_AppStandalone/build/outputs/apk/afat/standalone').glob('*.apk'))
if len(apks) != 1:
    raise SystemExit('Expected exactly one standalone release APK.')
apk = apks[0]
tools = Path(os.environ['ANDROID_HOME']) / 'build-tools/36.0.0'
badging = subprocess.check_output([str(tools / 'aapt'), 'dump', 'badging', str(apk)], text=True)
properties = dict(line.split('=', 1) for line in Path('gradle.properties').read_text().splitlines()
                  if '=' in line and not line.startswith('#'))
expected = {'name': properties['APP_PACKAGE'], 'versionName': os.environ['RELEASE_TAG'],
            'versionCode': str(int(properties['APP_VERSION_CODE']) * 10 + 9)}
package = re.search(r'^package: (.+)$', badging, re.MULTILINE)
actual = dict(re.findall(r"(\w+)='([^']*)'", package.group(1))) if package else {}
if any(actual.get(key) != value for key, value in expected.items()):
    raise SystemExit('APK package/version does not match the release configuration.')
if re.search(r'^application-debuggable', badging, re.MULTILINE):
    raise SystemExit('Refusing to publish a debuggable APK.')
with zipfile.ZipFile(apk) as archive:
    abis = {name.split('/')[1] for name in archive.namelist() if name.startswith('lib/')}
if abis != {'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'}:
    raise SystemExit('Universal APK does not contain all four architectures.')
signature = subprocess.check_output(
    [str(tools / 'apksigner'), 'verify', '--verbose', '--print-certs', str(apk)], text=True)
digests = re.findall(r'^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)$', signature, re.MULTILINE)
expected_digest = os.environ['RELEASE_CERT_SHA256'].replace(':', '').lower()
if [digest.lower() for digest in digests] != [expected_digest]:
    raise SystemExit('APK signing certificate does not match RELEASE_CERT_SHA256.')
print('Verified non-debuggable universal APK, application ID, version and release signature.')
