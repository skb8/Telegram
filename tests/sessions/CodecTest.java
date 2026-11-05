import org.telegram.messenger.sessions.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

public class CodecTest {
    static int checks;
    static void check(boolean ok) { checks++; if (!ok) throw new AssertionError("Check " + checks); }
    static void rejects(Runnable r) { try { r.run(); } catch (Exception expected) { checks++; return; } throw new AssertionError("Accepted invalid data"); }
    static String read(Path dir, String name) throws Exception { return Files.readString(dir.resolve(name)).trim(); }
    public static void main(String[] args) throws Exception {
        Path dir = Path.of(args[0]);
        byte[] key = new byte[256]; for (int i = 0; i < 256; i++) key[i] = (byte) i;
        SessionData original = new SessionData(2, key, 1234567890123L, 2040);
        for (String name : List.of("telethon4", "telethon6")) {
            SessionData s = StringSessionCodec.telethon(read(dir, name)); check(s.dcId == 2 && Arrays.equals(s.authKey, key));
        }
        for (String name : List.of("pyrogram32", "pyrogram64", "pyrogram2")) {
            SessionData s = StringSessionCodec.pyrogram(read(dir, name));
            check(s.dcId == 2 && Arrays.equals(s.authKey, key)); check(s.userId == (name.equals("pyrogram32") ? 1234567890L : original.userId));
        }
        check(StringSessionCodec.telethon(original).equals(read(dir, "telethon4")));
        check(StringSessionCodec.pyrogram(original).equals(read(dir, "pyrogram2")));
        check(Arrays.equals(StringSessionCodec.manual(StringSessionCodec.manual(original).split("Auth Key: ")[1], "2").authKey, key));
        rejects(() -> new SessionData(0, key, 1, 1)); rejects(() -> new SessionData(6, key, 1, 1));
        rejects(() -> new SessionData(2, new byte[256], 1, 1)); rejects(() -> new SessionData(2, new byte[255], 1, 1));
        rejects(() -> StringSessionCodec.telethon("2abcd")); rejects(() -> StringSessionCodec.telethon("1abcd"));
        rejects(() -> StringSessionCodec.pyrogram("!not base64")); rejects(() -> StringSessionCodec.manual("ff", "2"));
        for (int offset : new int[]{5, 270}) {
            byte[] invalid = Base64.getUrlDecoder().decode(read(dir, "pyrogram2")); invalid[offset] = 1;
            rejects(() -> StringSessionCodec.pyrogram(Base64.getUrlEncoder().encodeToString(invalid)));
        }
        Map<String, byte[]> incoming = new HashMap<>();
        try (var stream = Files.list(dir.resolve("input-tdata"))) {
            for (Path p : stream.toList()) incoming.put(p.getFileName().toString(), Files.readAllBytes(p));
        }
        List<SessionData> imported = TdataCodec.read(incoming, "local-passcode");
        check(imported.size() == 2); check(imported.get(0).userId == original.userId);
        check(imported.get(1).dcId == 4); check(imported.get(1).userId == 42);
        check(Arrays.equals(imported.get(0).authKey, key));
        try { TdataCodec.read(incoming, "wrong"); throw new AssertionError("Wrong password accepted"); } catch (IllegalArgumentException expected) { checks++; }
        Map<String, byte[]> exported = TdataCodec.write(original);
        List<SessionData> roundtrip = TdataCodec.read(exported, "");
        check(roundtrip.size() == 1 && roundtrip.get(0).userId == original.userId && Arrays.equals(roundtrip.get(0).authKey, key));
        for (var e : exported.entrySet()) { Path p = dir.resolve("output").resolve(e.getKey()); Files.createDirectories(p.getParent()); Files.write(p, e.getValue()); }
        byte[] corrupted = exported.get("tdata/key_datas").clone(); corrupted[20] ^= 1; exported.put("tdata/key_datas", corrupted);
        try { TdataCodec.read(exported, ""); throw new AssertionError("Corrupt checksum accepted"); } catch (IllegalArgumentException expected) { checks++; }
        original.clear(); check(Arrays.equals(original.authKey, new byte[256]));
        System.out.println("Codec checks passed: " + checks);
    }
}
