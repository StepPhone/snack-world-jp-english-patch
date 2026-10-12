"""Add the supplied credit art as a separate native startup scene.

XQ32 layout reference: https://github.com/onepiecefreak3/XtractQuery
Uses the unused legacy 400x240 logo slot as storage, retaining all active logos.
No game resolution hook: the native 1920x1080 startup canvas scales to output.
"""
from level5 import *
import sys
sys.path.insert(0,str(Path(__file__).parent/'tools/python-libs'))
from PIL import Image

ROOT=Path(__file__).resolve().parent
ASSET='data/menu/img/criware400x240sw.xi'
SCRIPT='seq/menu/logo_menu.xq'

def compress_native(raw,method):
    if method==1:
        # Literal-only LZ10: preserve the native decoder without third-party codecs.
        body=b''.join(b'\0'+raw[i:i+8] for i in range(0,len(raw),8))
    elif method==4:
        body=bytearray();i=0
        while i<len(raw):
            run=1
            while i+run<len(raw) and raw[i+run]==raw[i] and run<130:run+=1
            if run>=3:
                body.extend((128|(run-3),raw[i]));i+=run
            else:
                start=i;i+=run
                while i<len(raw) and i-start<128:
                    if i+2<len(raw) and raw[i]==raw[i+1]==raw[i+2]:break
                    i+=1
                i=min(i,start+128)
                body.append(i-start-1);body.extend(raw[start:i])
        body=bytes(body)
    else: raise ValueError(method)
    encoded=struct.pack('<I',(len(raw)<<3)|method)+body
    assert decompress(encoded)==raw
    return encoded

def encode_image(template,png):
    im=Image.open(png).convert('RGBA');assert im.size==(1920,1080)
    assert template[:4]==b'IMGN' and template[10]==0
    w,h=im.size; pixels=im.tobytes();unique={};tiles=bytearray();ids=[]
    for y in range(0,h,8):
        for x in range(0,w,8):
            tile=b''.join(pixels[((y+dy)*w+x)*4:((y+dy)*w+x+8)*4] for dy in range(8))
            if tile not in unique:unique[tile]=len(unique);tiles.extend(tile)
            ids.append(unique[tile])
    original_size=struct.unpack_from('<I',template,52)[0]
    prefix=decompress(template[72:72+original_size])[:8]
    table=prefix+struct.pack('<'+'i'*len(ids),*ids)
    ct=compress_native(table,4);cd=compress_native(bytes(tiles),1);pad=-len(ct)%4
    header=bytearray(template[:72]);struct.pack_into('<III',header,52,len(ct),len(ct)+pad,len(cd))
    result=bytes(header)+ct+bytes(pad)+cd
    # Independently reconstruct every pixel from encoded tables.
    decoded=decode_image(result)
    assert decoded.tobytes()==pixels
    return result,decoded

def decode_image(d):
    w,h=struct.unpack_from('<HH',d,16);size,pad=struct.unpack_from('<II',d,52)
    table=decompress(d[72:72+size]);tiles=decompress(d[72+pad:]);ids=struct.unpack('<'+'i'*((len(table)-8)//4),table[8:])
    pixels=bytearray(w*h*4)
    for i,t in enumerate(ids):
        y=(i//(w//8))*8;x=(i%(w//8))*8
        for dy in range(8):pixels[((y+dy)*w+x)*4:((y+dy)*w+x+8)*4]=tiles[t*256+dy*32:t*256+(dy+1)*32]
    return Image.frombytes('RGBA',(w,h),bytes(pixels))

def patch_script(d):
    assert d[:4]==b'XQ32'
    offsets=[struct.unpack_from('<H',d,o)[0]*4 for o in (6,8,12,16,22)]
    ft,jt,it,at,st=[decompress(d[o:]) for o in offsets]
    assert len(ft)==72 and len(it)==97*12 and len(at)==149*8
    functions=[list(struct.unpack_from('<II6HI',ft,o)) for o in range(0,len(ft),24)]
    jumps=[list(struct.unpack_from('<III',jt,o)) for o in range(0,len(jt),12)]
    ins=[list(struct.unpack_from('<4HI',it,o)) for o in range(0,len(it),12)]
    args=[list(struct.unpack_from('<II',at,o)) for o in range(0,len(at),8)]
    strings=bytearray(st)
    def string(s):
        off=len(strings);strings.extend(s.encode()+b'\0');return [24,off]
    name=string('bg_step_credit');path=string(ASSET[:-3])
    def clone(index,newargs=None):
        r=ins[index].copy();a=[v.copy() for v in args[r[0]:r[0]+r[1]]] if newargs is None else newargs
        r[0]=len(args);r[1]=len(a);args.extend(a);return r
    preload=clone(1,[name,path])
    # Same fade-in / fixed wait / fade-out sequence as the native CESA notice.
    scene=[clone(7),clone(10,[name,[1,0],[1,200],[1,0]]),clone(11,[name,name]),
           clone(12),clone(13),clone(14,[[2,0xd0fd3a01],[1,300]]),clone(15),clone(16)]
    def relocate(index):return index+(1 if index>=4 else 0)+(8 if index>=69 else 0)
    for f in functions:f[2]=relocate(f[2]);f[3]=relocate(f[3])
    for j in jumps:j[2]=relocate(j[2])
    updated=ins[:4]+[preload]+ins[4:69]+scene+ins[69:]
    sections=[b''.join(struct.pack('<II6HI',*f) for f in functions),
              b''.join(struct.pack('<III',*j) for j in jumps),
              b''.join(struct.pack('<4HI',*i) for i in updated),
              b''.join(struct.pack('<II',*a) for a in args),bytes(strings)]
    out=bytearray(d[:32])
    for field,raw in zip((6,8,12,16,22),sections):
        struct.pack_into('<H',out,field,len(out)//4)
        out.extend(compress_native(raw,1));out.extend(bytes(-len(out)%4))
    struct.pack_into('<H',out,14,len(updated));struct.pack_into('<H',out,18,len(args))
    for original_index,original in enumerate(ins):
        # The inserted scene precedes old instruction 69, with all original instructions intact.
        assert updated[relocate(original_index)]==original
    for j in jumps:assert j[2]<len(updated)
    for f in functions:assert 0<=f[2]<f[3]<=len(updated)
    return bytes(out)

def replacements(original):
    png=ROOT/'credit-assets/StepHackerZ_title_switch_1920x1080.png'
    texture,preview=encode_image(original.read('data/menu/img/LEVEL5.xi'),png)
    preview.save(ROOT/'credit-assets/encoded-credit-preview.png')
    return {ASSET:texture,SCRIPT:patch_script(original.read(SCRIPT))}
