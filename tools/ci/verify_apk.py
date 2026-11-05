"""Verify the packaged application ID, including variant suffixes."""
import os
from pathlib import Path
import re
import subprocess

apks = list(Path('TMessagesProj_AppStandalone/build/outputs/apk').rglob('*.apk'))
if not apks:
    raise SystemExit('No APK found to verify.')
aapt = Path(os.environ['ANDROID_HOME']) / 'build-tools/36.0.0/aapt'
for apk in apks:
    badging = subprocess.check_output([str(aapt), 'dump', 'badging', str(apk)], text=True)
    package = re.search(r"^package: name='([^']+)'", badging, re.MULTILINE)
    if not package or package.group(1) != 'org.skb8.telegram':
        raise SystemExit('Unexpected APK application ID: ' + (package.group(1) if package else 'missing'))
    print('Verified APK application ID: ' + package.group(1))
