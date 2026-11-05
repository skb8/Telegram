#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
python3 tests/sessions/interop.py generate "$work/fixtures"
source_dir=TMessagesProj/src/main/java/org/telegram/messenger/sessions
# java's compiler entry point works on JDK distributions without a javac launcher too.
java com.sun.tools.javac.Main -d "$work/classes" "$source_dir/SessionData.java" "$source_dir/StringSessionCodec.java" "$source_dir/TdataCodec.java" tests/sessions/CodecTest.java
java -cp "$work/classes" CodecTest "$work/fixtures"
python3 tests/sessions/interop.py verify "$work/fixtures"
