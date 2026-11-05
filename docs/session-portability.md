# Account session import and export

This change adds only session portability to the existing Telegram client. It does
not add Cherrygram's QR login, cameras, message menus, filters, folders or other
features, and has no Cherrygram package, resources or private-source dependencies.

On the phone-number screen, **Log in with a session** opens these choices:

- Telethon or Pyrogram SQLite `.session`, selected using Android's document picker.
- ZIP containing `tdata/` or its contents, optionally protected by a Desktop local
  passcode. Multi-account archives show an account selector.
- Telethon String Session, Pyrogram String Session, or Auth Key + DC ID entered
  manually. Auth Key is exactly 512 hexadecimal characters; DC ID is 1–5.

Under **Settings → Devices → This device**, **Export account session** offers the
same formats. String/manual formats are saved as `.txt`, SQLite as `.session`,
and Desktop as `.zip`, using Android's document creation dialog.

The imported key is installed on the account's native network thread and verified
with `users.getUsers(inputUserSelf)` before the existing login completion path
saves user data. Existing accounts are never overwritten. Rejected, mismatched or
timed-out imports clear the imported local authorization without `auth.logOut`.

## Format limits

- Production user sessions only; bots and test sessions are rejected.
- Telethon StringSession v1 (IPv4/IPv6) and SQLite named-column import; SQLite v7
  export, migrated by newer Telethon 1.x releases.
- Pyrogram old 32-bit/64-bit and current string layouts; SQLite v3 export.
- Modern `key_data` / TDF$ Desktop format, including local passcodes. Export is a
  minimal single-account tdata with an empty local map and no local passcode.
  Desktop recreates caches. Legacy Desktop formats/custom data-file names are not
  supported.
- ZIP only, one tdata root, maximum 4,096 entries and 64 MiB unpacked. Remove
  Desktop caches first. Authorization files are parsed in memory, without archive
  extraction. SQLite documents are limited to 16 MiB and must have been cleanly
  closed by the originating client; WAL sidecars are not recovered.

Exports contain the existing device's authorization and grant full account access.
They do not create an independent device/session. Do not run clients sharing that
key concurrently (`AUTH_KEY_DUPLICATED` can revoke it). Revoke this device if an
export is exposed; exported copies then stop working too. Credential values are
not logged or automatically copied to the clipboard/uploaded. Temporary SQLite
files use private app cache and are removed after the operation.

## GitHub Actions

`Session portability` runs on pushes to master, PRs and manual dispatch. It runs
format interoperability checks and builds a standalone debug APK. Push builds
produce arm64-v8a; manual dispatch also offers armeabi-v7a, x86_64 and universal.
Download `Telegram-session-debug-<architecture>` from the workflow's artifacts.
The debug build uses the upstream dummy signing key and Firebase configuration.
Release signing and branding retain the upstream configuration.

Compilation does not require your Telegram API credentials. To use your own API
application, add **both** repository Actions secrets:

| Secret | Value |
| --- | --- |
| `TELEGRAM_API_ID` | Numeric Telegram application API ID |
| `TELEGRAM_API_HASH` | 32-character hexadecimal API hash |

`tools/ci/configure_api.py` injects them into BuildVars only inside the runner and
does not print them. Without them the source's existing placeholders are retained;
that is a build artifact, not a client configured for real login. You can add the
keys later and rerun the workflow. For local builds configure BuildVars.java as
in the upstream README. API credentials are compiled into the app and should not
be confused with an account's Auth Key or String Session.

## Verification

`bash tests/sessions/run.sh` requires JDK 17, Python 3 and
`cryptography==50.0.2`. It checks synthetic fixed Python struct/base64 vectors and
independent PBKDF2/AES-IGE/tdata interoperability, including passcoded multi-account
input, corrupt data, wrong passwords and output's encrypted local map. No live
Telegram account is used.

Android SQLite/stream instrumentation tests are in
`TMessagesProj_AppTests/src/androidTest/java/org/telegram/messenger/sessions/SessionFilesTest.java`.
On a device also check first/additional-account login, canceled pickers, revoked
keys, all export formats opened in their source clients, back/rotation during
verification, light/dark themes and Russian/English. An APK build alone does not
establish a successful login with a real account.

Format references: AndroidTelePorter, Telethon's sessions, Pyrogram's storage,
and opentele's Desktop storage implementations:

- https://github.com/batreller/AndroidTelePorter/blob/main/AndroidTelePorter/androidsession.py
- https://github.com/LonamiWebs/Telethon/tree/v1/telethon/sessions
- https://github.com/pyrogram/pyrogram/tree/master/pyrogram/storage
- https://github.com/thedemons/opentele/tree/main/src/td
