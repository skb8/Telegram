# Releases

Push a tag matching `APP_VERSION_NAME` in `gradle.properties`, for example
`git tag 13.1.1 && git push origin 13.1.1`. The Release workflow builds a signed,
non-debuggable APK for each of the four supported ABIs plus a universal APK, and publishes them only
after session interoperability and APK identity/signature checks pass.
To retry a failed release, rerun the workflow or dispatch it against the tag.
Published releases are never overwritten by a rerun.

The standalone application ID is `org.skb8.telegram`. The release APK uses the
fork's own signing certificate; the upstream dummy keystore remains available
for local development and debug builds.

Required GitHub Actions repository secrets:

| Secret | Value |
| --- | --- |
| `TELEGRAM_API_ID` | Fork's Telegram API ID |
| `TELEGRAM_API_HASH` | Fork's Telegram API hash |
| `RELEASE_KEYSTORE_BASE64` | Base64 encoded private release keystore |
| `RELEASE_STORE_PASSWORD` | Keystore password |
| `RELEASE_KEY_ALIAS` | Release key alias |
| `RELEASE_KEY_PASSWORD` | Private key password |
| `RELEASE_CERT_SHA256` | SHA-256 fingerprint of the public signing certificate |

Public signing certificate SHA-256:

```
08d095d1b0be544b15f99eccb87b3a0199116db2966bf96a602b206ae475604e
```

The five APKs, `SHA256SUMS`, and `release-certificate.pem` are attached to each release.
Verify the downloaded files with `sha256sum --check SHA256SUMS`; verify the APK
signature using Android SDK `apksigner verify --verbose --print-certs <apk>`
and compare the certificate fingerprint above.

Keep an independent secure backup of the release keystore and its passwords.
GitHub does not let you read back secret values. Future APK updates must use the
same signing key. Do not commit private keys or passwords to the repository.
