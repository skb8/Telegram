"""Independent Python wire fixtures: struct/base64, hashlib PBKDF2 and OpenSSL AES.
Only synthetic keys; no Telegram connection or live authorization is used.
"""
import base64
import hashlib
import os
from pathlib import Path
import struct
import sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEY = bytes(range(256))
UID = 1234567890123

def qarray(b): return struct.pack('>I', len(b)) + b

def qread(b, pos=0):
    n, = struct.unpack_from('>I', b, pos)
    assert n <= len(b) - pos - 4
    return b[pos+4:pos+4+n], pos+4+n

def local_key(salt, password):
    return hashlib.pbkdf2_hmac('sha512', hashlib.sha512(salt+password+salt).digest(), salt, 100000 if password else 1, 256)

def ige(data, key, msg, encrypt):
    a = hashlib.sha1(msg+key[8:40]).digest()
    b = hashlib.sha1(key[40:56]+msg+key[56:72]).digest()
    c = hashlib.sha1(key[72:104]+msg).digest()
    d = hashlib.sha1(msg+key[104:136]).digest()
    aes = a[:8]+b[8:20]+c[4:16]
    iv = a[8:20]+b[:8]+c[16:20]+d[:8]
    ctx = Cipher(algorithms.AES(aes), modes.ECB())
    ctx = ctx.encryptor() if encrypt else ctx.decryptor()
    pc, pp = iv[:16], iv[16:]
    out = b''
    for i in range(0, len(data), 16):
        block = data[i:i+16]
        before, after = (pc, pp) if encrypt else (pp, pc)
        transformed = ctx.update(bytes(x^y for x,y in zip(block, before)))
        transformed = bytes(x^y for x,y in zip(transformed, after))
        pc, pp = (transformed, block) if encrypt else (block, transformed)
        out += transformed
    ctx.finalize()
    return out

def encrypt(b, key):
    size = len(b)+4
    plain = struct.pack('<I', size)+b+os.urandom((-size)%16)
    msg = hashlib.sha1(plain).digest()[:16]
    return msg+ige(plain,key,msg,True)

def decrypt(b, key):
    plain = ige(b[16:], key, b[:16], False)
    assert hashlib.sha1(plain).digest()[:16] == b[:16]
    size, = struct.unpack_from('<I', plain)
    assert len(plain)-16 < size <= len(plain)
    return plain[4:size]

def wrap(b):
    version = struct.pack('<I', 3004000)
    return b'TDF$'+version+b+hashlib.md5(b+struct.pack('<I',len(b))+version+b'TDF$').digest()

def unwrap(b):
    assert b[:4] == b'TDF$'
    body = b[8:-16]
    assert hashlib.md5(body+struct.pack('<I',len(body))+b[4:8]+b'TDF$').digest() == b[-16:]
    return body

def name(index):
    md5 = hashlib.md5(('data' if not index else f'data#{index+1}').encode()).digest()[:8]
    return ''.join(f'{x:02X}'[::-1] for x in md5)+'s'

def generate(path):
    path.mkdir(parents=True,exist_ok=True)
    vectors = {
        'telethon4': b'1'+base64.urlsafe_b64encode(struct.pack('>B4sH256s',2,bytes([149,154,167,51]),443,KEY)),
        'telethon6': b'1'+base64.urlsafe_b64encode(struct.pack('>B16sH256s',2,bytes(range(16)),443,KEY)),
        'pyrogram32': base64.urlsafe_b64encode(struct.pack('>B?256sI?',2,False,KEY,1234567890,False)).rstrip(b'='),
        'pyrogram64': base64.urlsafe_b64encode(struct.pack('>B?256sQ?',2,False,KEY,UID,False)).rstrip(b'='),
        'pyrogram2': base64.urlsafe_b64encode(struct.pack('>BI?256sQ?',2,2040,False,KEY,UID,False)).rstrip(b'='),
    }
    for k,v in vectors.items(): (path/k).write_bytes(v)
    root = path/'input-tdata'; root.mkdir(exist_ok=True)
    local, salt = os.urandom(256), os.urandom(32)
    info = struct.pack('>iiii',2,0,1,0)
    (root/'key_datas').write_bytes(wrap(qarray(salt)+qarray(encrypt(local,local_key(salt,b'local-passcode')))+qarray(encrypt(info,local))))
    for index, uid, dc in [(0,UID,2),(1,42,4)]:
        # Include a second DC key to exercise main-DC selection.
        auth = struct.pack('>qqii',-1,uid,dc,2)+struct.pack('>i',1)+KEY[::-1]+struct.pack('>i',dc)+KEY+struct.pack('>i',0)
        (root/name(index)).write_bytes(wrap(qarray(encrypt(struct.pack('>i',0x4b)+qarray(auth),local))))

def verify(path):
    root = path/'output/tdata'
    keyfile = unwrap((root/'key_datas').read_bytes())
    salt,p = qread(keyfile); enc,p=qread(keyfile,p); inf,p=qread(keyfile,p)
    local = decrypt(enc,local_key(salt,b'')); assert len(local)==256
    assert decrypt(inf,local)==struct.pack('>iii',1,0,0)
    mapfile=unwrap((root/name(0)[:-1]/'maps').read_bytes())
    salt_unused,p=qread(mapfile); key_unused,p=qread(mapfile,p); encrypted_map,p=qread(mapfile,p)
    assert not salt_unused and not key_unused and decrypt(encrypted_map,local)==b''
    outer,_=qread(unwrap((root/name(0)).read_bytes()))
    data = decrypt(outer,local); assert data[:4]==struct.pack('>i',0x4b)
    auth,_=qread(data,4)
    tag, uid, dc, count, keydc = struct.unpack_from('>qqiii', auth)
    assert (tag,uid,dc,count,keydc)==(-1,UID,2,1,2)
    assert auth[28:284]==KEY and auth[284:]==b'\0'*4
    print('Independent Python tdata verification passed')

if __name__=='__main__':
    (generate if sys.argv[1]=='generate' else verify)(Path(sys.argv[2]))
