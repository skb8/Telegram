"""Optionally supply the fork's Telegram API credentials from Actions secrets.
The values are compiled into the APK, as required by Telegram's API. Never log them.
"""
from pathlib import Path
import os
import re

api_id = os.environ.get('TELEGRAM_API_ID', '')
api_hash = os.environ.get('TELEGRAM_API_HASH', '')
if bool(api_id) != bool(api_hash):
    raise SystemExit('Set both TELEGRAM_API_ID and TELEGRAM_API_HASH, or leave both unset.')
if api_id:
    if not api_id.isascii() or not api_id.isdigit() or not 0 < int(api_id) < 2**31 or not re.fullmatch(r'[0-9a-fA-F]{32}', api_hash):
        raise SystemExit('Invalid Telegram API credential format.')
    path = Path('TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java')
    source, id_count = re.subn(r'public static int APP_ID = \d+;', 'public static int APP_ID = ' + str(int(api_id)) + ';', path.read_text())
    source, hash_count = re.subn(r'public static String APP_HASH = "[^"]*";', 'public static String APP_HASH = "' + api_hash + '";', source)
    if id_count != 1 or hash_count != 1:
        raise SystemExit('Cannot locate API fields in BuildVars.java.')
    path.write_text(source)
    print('Configured Telegram API credentials from repository secrets.')
else:
    print('No custom API credentials supplied; building with upstream placeholders. Configure your own API keys before using the client.')
