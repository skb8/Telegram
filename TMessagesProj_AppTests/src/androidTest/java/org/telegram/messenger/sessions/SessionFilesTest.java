package org.telegram.messenger.sessions;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.net.Uri;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.File;
import java.io.FileOutputStream;
import java.util.Arrays;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Device-only tests for Android SQLite and ContentResolver streams; synthetic keys. */
@RunWith(AndroidJUnit4.class)
public class SessionFilesTest {
    private final Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
    private SessionData sample() {
        byte[] key = new byte[256]; for (int i = 0; i < 256; i++) key[i] = (byte) i;
        return new SessionData(2, key, 1234567890123L, 2040);
    }
    private File temp(String suffix) throws Exception { return File.createTempFile("codec-test-", suffix, context.getCacheDir()); }

    @Test public void sqliteSchemasAndPortableKeys() throws Exception {
        for (int format : new int[]{SessionFiles.TELETHON_FILE, SessionFiles.PYROGRAM_FILE}) {
            File file = temp(".session"); SessionData source = sample();
            try {
                SessionFiles.write(context, Uri.fromFile(file), format, source);
                try (SQLiteDatabase db = SQLiteDatabase.openDatabase(file.getPath(), null, SQLiteDatabase.OPEN_READONLY)) {
                    String versionColumn = format == SessionFiles.TELETHON_FILE ? "version" : "number";
                    try (Cursor c = db.rawQuery("SELECT " + versionColumn + " FROM version", null)) {
                        assertTrue(c.moveToFirst()); assertEquals(format == SessionFiles.TELETHON_FILE ? 7 : 3, c.getInt(0));
                    }
                    try (Cursor c = db.rawQuery("SELECT dc_id, length(auth_key) FROM sessions", null)) {
                        assertEquals(1, c.getCount()); assertTrue(c.moveToFirst()); assertEquals(2, c.getInt(0)); assertEquals(256, c.getInt(1));
                    }
                }
                List<SessionData> loaded = SessionFiles.read(context, Uri.fromFile(file), false, "");
                assertArrayEquals(source.authKey, loaded.get(0).authKey);
                if (format == SessionFiles.PYROGRAM_FILE) assertEquals(source.userId, loaded.get(0).userId);
                loaded.get(0).clear();
            } finally { source.clear(); SQLiteDatabase.deleteDatabase(file); }
        }
    }

    @Test public void pyrogramTestAndBotSessionsAreRejected() throws Exception {
        for (String field : new String[]{"test_mode", "is_bot"}) {
            File file = temp(".session"); SessionData source = sample();
            try {
                SessionFiles.write(context, Uri.fromFile(file), SessionFiles.PYROGRAM_FILE, source);
                try (SQLiteDatabase db = SQLiteDatabase.openDatabase(file.getPath(), null, SQLiteDatabase.OPEN_READWRITE)) { db.execSQL("UPDATE sessions SET " + field + "=1"); }
                try { SessionFiles.read(context, Uri.fromFile(file), false, ""); fail("Accepted " + field); }
                catch (java.io.IOException expected) { }
            } finally { source.clear(); SQLiteDatabase.deleteDatabase(file); }
        }
    }

    @Test public void tdataZipCanBeImported() throws Exception {
        File file = temp(".zip"); SessionData source = sample();
        try {
            SessionFiles.write(context, Uri.fromFile(file), SessionFiles.TDATA, source);
            SessionData loaded = SessionFiles.read(context, Uri.fromFile(file), true, "").get(0);
            assertEquals(source.userId, loaded.userId); assertArrayEquals(source.authKey, loaded.authKey); loaded.clear();
        } finally { source.clear(); file.delete(); }
    }

    @Test public void traversalZipIsRejectedWithoutExtraction() throws Exception {
        File file = temp(".zip");
        try {
            try (ZipOutputStream out = new ZipOutputStream(new FileOutputStream(file))) {
                out.putNextEntry(new ZipEntry("../key_datas")); out.write(new byte[]{1}); out.closeEntry();
            }
            try { SessionFiles.read(context, Uri.fromFile(file), true, ""); fail("Accepted traversal"); }
            catch (java.io.IOException expected) { }
        } finally { file.delete(); }
    }
}
