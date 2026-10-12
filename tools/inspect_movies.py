from pathlib import Path
import struct, json

def atoms(f, end):
    while f.tell()+8<=end:
        start=f.tell(); size,kind=struct.unpack('>I4s',f.read(8))
        if size==1: size=struct.unpack('>Q',f.read(8))[0]
        if size==0: size=end-start
        if size<8: break
        body=f.tell()
        yield kind,body,start+size
        f.seek(start+size)

def inspect(p):
    result={'file':str(p),'tracks':[]}
    with p.open('rb') as f:
        for kind,body,end in atoms(f,p.stat().st_size):
            if kind!=b'moov': continue
            for k,b,e in atoms(f,end):
                if k==b'mvhd':
                    raw=f.read(32); pos=20 if raw[0]==1 else 12
                    timescale=struct.unpack_from('>I',raw,pos)[0]
                    duration=struct.unpack_from('>Q' if raw[0]==1 else '>I',raw,pos+4)[0]
                    result['duration_seconds']=duration/timescale
                if k==b'trak':
                    track={}
                    for k2,b2,e2 in atoms(f,e):
                        if k2==b'mdia':
                            for k3,b3,e3 in atoms(f,e2):
                                if k3==b'hdlr': track['type']=f.read(12)[8:12].decode('ascii')
                    result['tracks'].append(track)
    return result

root=Path(__file__).parent
if __name__=='__main__':
    print(json.dumps([inspect(p) for region in ['jp','eur'] for p in (root/f'{region}-romfs/mov').rglob('*.mp4')],indent=2))
