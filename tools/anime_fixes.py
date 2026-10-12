"""Replace only the two unused EUR anime-label atlas rectangles.

All original BC3 blocks outside the label rectangles and all menu logic remain
byte-identical. The Japanese anime menu exists and is intentionally retained.
"""
from level5 import *
from pathlib import Path
import io
from PIL import Image

def anime_submenu(package):
    x = Xpck(package)
    d = x.read('006.xi')
    assert d[:4] == b'IMGN' and d[10] == 31 and d[12] == 1
    w, h = struct.unpack_from('<HH', d, 16)
    assert (w, h) == (1024, 1024)
    offset = struct.unpack_from('<I', d, 28)[0]
    size, padded = struct.unpack_from('<II', d, 52)
    table = decompress(d[offset:offset+size])
    tiles = decompress(d[offset+padded:])
    ids = struct.unpack('<'+'i'*((len(table)-8)//4), table[8:])
    raw = b''.join(tiles[i*64:(i+1)*64] if i >= 0 else bytes(64) for i in ids)
    result = bytearray(raw)
    changed = set()
    for i,(dx,dy,rw,rh) in enumerate([(4,4,540,64),(4,76,484,64),(4,148,428,64),(4,220,344,64),(4,292,500,88)]):
        name=f'anime-submenu-{i}'
        im = Image.open(Path(__file__).parent/'credit-assets'/f'{name}.png').convert('RGBA')
        assert im.size == (rw,rh)
        stream = io.BytesIO()
        im.save(stream, format='DDS', pixel_format='DXT5')
        dds = stream.getvalue()
        assert dds[84:88] == b'DXT5' and len(dds) == 128+rw*rh
        blocks = dds[128:]
        for y in range(rh//4):
            dest = ((dy//4+y)*(w//4)+dx//4)*16
            src = y*(rw//4)*16
            result[dest:dest+rw*4] = blocks[src:src+rw*4]
            changed.update(range(dest,dest+rw*4))
    assert all(a==b for i,(a,b) in enumerate(zip(raw,result)) if i not in changed)
    unique={};newtiles=bytearray();newids=[]
    for i in range(0,len(result),64):
        tile=bytes(result[i:i+64])
        if tile not in unique: unique[tile]=len(unique);newtiles.extend(tile)
        newids.append(unique[tile])
    # Native UI texture loading uses LZ10, matching both original streams.
    from startup_credit import compress_native
    compress=lambda b:compress_native(bytes(b),1)
    nt=compress(table[:8]+struct.pack('<'+'i'*len(newids),*newids));nd=compress(newtiles)
    header=bytearray(d[:offset]);pad=-len(nt)%4
    struct.pack_into('<III',header,52,len(nt),len(nt)+pad,len(nd))
    replacement=bytes(header)+nt+bytes(pad)+nd
    output=x.rebuild({'006.xi':replacement});check=Xpck(output)
    assert set(check.entries)==set(x.entries)
    for n in x.entries:
        if n!='006.xi':assert check.read(n)==x.read(n)
    return output
