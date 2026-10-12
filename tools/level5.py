"""Local ARC0/XPCK inspection helpers. Format references: Kuriimu2 Level5 plugin."""
import struct, zlib, json
from pathlib import Path

def decompress(data):
    h, = struct.unpack_from('<I', data)
    size, method = h >> 3, h & 7
    if method == 0: out = data[4:4+size]
    elif method == 5: out = zlib.decompress(data[4:])
    elif method == 1:
        out=bytearray(); p=4
        while len(out)<size:
            flags=data[p]; p+=1
            for bit in range(7,-1,-1):
                if len(out)>=size: break
                if flags & (1<<bit):
                    a,b=data[p:p+2]; p+=2
                    length=(a>>4)+3; distance=((a&15)<<8)+b+1
                    for _ in range(length): out.append(out[-distance])
                else: out.append(data[p]); p+=1
    elif method in (2,3):
        tree_size=data[4]; root=data[5]; tree=data[6:6+tree_size*2]
        p=6+tree_size*2; out=bytearray(); node=root; nxt=0
        target=size*(2 if method==2 else 1)
        while len(out)<target:
            code,=struct.unpack_from('<I',data,p); p+=4
            for bit in range(31,-1,-1):
                nxt+=((node&63)<<1)+2
                direction=1 if code&(1<<bit) else 2
                leaf=(node>>(5+direction))&1
                node=tree[nxt-direction]
                if leaf:
                    out.append(node); node=root; nxt=0
                    if len(out)==target: break
        if method==2: out=bytes(out[i]|out[i+1]<<4 for i in range(0,len(out),2))
    elif method == 4:
        out=bytearray(); p=4
        while len(out)<size:
            flag=data[p]; p+=1
            if flag&128:
                out.extend(bytes([data[p]])*((flag&127)+3)); p+=1
            else:
                n=flag+1; out.extend(data[p:p+n]); p+=n
    else: raise ValueError(f'Unknown compression {method}')
    assert len(out)==size, (method,len(out),size)
    return bytes(out)

def cstring(data, p):
    return data[p:data.index(0,p)].decode('cp932')

class T2B:
    def __init__(self,data):
        assert data[-15:-12]==b't2b',data[-16:]
        self.data=data
        count,self.string_offset,self.string_size,self.string_count=struct.unpack_from('<4I',data)
        self.encoding='utf-8' if data[-10]==1 else 'cp932'
        self.records=[]; p=16
        for _ in range(count):
            start=p
            tag,argc=struct.unpack_from('<IB',data,p); p+=5
            masklen=3+4*((argc-13)//16+1) if argc>12 else 3
            mask=data[p:p+masklen]; p+=masklen
            types=[(b>>bit)&3 for b in mask for bit in range(0,8,2)][:argc]
            assert len(types)==argc and 3 not in types
            args=[]
            for t in types:
                value,=struct.unpack_from('<I',data,p)
                text=None
                if t==0 and value!=0xffffffff:
                    assert value<self.string_size,(value,self.string_size)
                    s=self.string_offset+value
                    text=data[s:data.index(0,s)].decode(self.encoding)
                args.append({'type':t,'value':value,'pos':p,'text':text}); p+=4
            self.records.append({'tag':tag,'args':args,'start':start,'end':p})
        assert p<=self.string_offset
    def strings(self):
        for i,r in enumerate(self.records):
            ids=tuple(a['value'] for a in r['args'] if a['type']!=0)
            for k,a in enumerate(r['args']):
                if a['text'] is not None:
                    yield (r['tag'],ids,k),a['text'],(i,k)
    def rebuild(self,replacements):
        prefix=bytearray(self.data[:self.string_offset]); strings=bytearray(); offsets={}
        for i,r in enumerate(self.records):
            for k,a in enumerate(r['args']):
                if a['text'] is None: continue
                text=replacements.get((i,k),a['text'])
                raw=text.encode(self.encoding)+b'\0'
                if raw not in offsets:
                    offsets[raw]=len(strings); strings.extend(raw)
                struct.pack_into('<I',prefix,a['pos'],offsets[raw])
        struct.pack_into('<I',prefix,8,len(strings))
        struct.pack_into('<I',prefix,12,len(offsets))
        tail=self.data[(self.string_offset+self.string_size+15)&~15:]
        return bytes(prefix)+strings+b'\xff'*((-len(strings))%16)+tail

class Arc:
    def __init__(self,path):
        self.path=Path(path)
        with self.path.open('rb') as f:
            self.header=f.read(72)
            assert self.header[:4]==b'ARC0'
            offsets=struct.unpack_from('<5I',self.header,4)
            self.data_offset=offsets[-1]
            nd,nh,nf=struct.unpack_from('<HHI',self.header,24)
            self.tables=[]
            for a,b in zip(offsets,offsets[1:]):
                f.seek(a); self.tables.append(decompress(f.read(b-a)))
        dirs,hashes,files,names=self.tables
        assert len(dirs)==nd*20,(len(dirs),nd)
        assert len(files)==nf*16,(len(files),nf)
        self.entries={}
        for i in range(nd):
            crc,firstd,numd,firstf,numf,fn,dn=struct.unpack_from('<IHHHHII',dirs,i*20)
            directory=cstring(names,dn)
            for j in range(firstf,firstf+numf):
                crc,no,off,size=struct.unpack_from('<4I',files,j*16)
                name=directory+cstring(names,fn+no)
                assert name not in self.entries,name
                assert self.data_offset+off+size<=self.path.stat().st_size,name
                self.entries[name]={'index':j,'offset':off,'size':size,'crc':crc}
        assert len(self.entries)==nf,(len(self.entries),nf)
    def read(self,name):
        e=self.entries[name]
        with self.path.open('rb') as f:
            f.seek(self.data_offset+e['offset']); return f.read(e['size'])

class Xpck:
    def __init__(self,data):
        assert data[:4]==b'XPCK'
        self.data=data; self.header=data[:20]
        fc,io,no,do,isz,nsz,dsz=struct.unpack_from('<6HI',data,4)
        count=fc&4095; self.info_offset=io*4; self.name_offset=no*4; self.data_offset=do*4
        names=decompress(data[no*4:(no+nsz)*4]); self.entries={}
        for i in range(count):
            crc,name,off,size,oh,sh=struct.unpack_from('<IHHHBB',data,io*4+i*12)
            name=cstring(names,name); off=((oh<<16)|off)*4; size|=sh<<16
            assert self.data_offset+off+size<=len(data)
            self.entries[name]={'index':i,'offset':off,'size':size,'crc':crc}
    def read(self,name):
        e=self.entries[name]; return self.data[self.data_offset+e['offset']:self.data_offset+e['offset']+e['size']]
    def rebuild(self,replacements):
        out=bytearray(self.data[:self.data_offset])
        for n,e in sorted(self.entries.items(),key=lambda pair:pair[1]['offset']):
            raw=replacements.get(n,self.read(n)); off=(len(out)-self.data_offset)//4; size=len(raw)
            assert off<1<<24 and size<1<<24
            struct.pack_into('<HHBB',out,self.info_offset+e['index']*12+6,off&65535,size&65535,off>>16,size>>16)
            out.extend(raw); out.extend(b'\0'*(-len(out)%4))
        struct.pack_into('<I',out,16,(len(out)-self.data_offset)//4)
        return bytes(out)

if __name__=='__main__':
    import sys, collections
    for region in sys.argv[1:] or ['jp','eur']:
        arc=Arc(Path(__file__).parent/f'{region}-romfs/archive_a.fa')
        (Path(__file__).parent/f'{region}-inventory.json').write_text(json.dumps(arc.entries,indent=2),encoding='utf-8')
        print(region,len(arc.entries),'files')
        print(collections.Counter(Path(n).suffix for n in arc.entries).most_common(20))
        print('Text candidates:',*[n for n in arc.entries if any(s in n.lower() for s in ['text/','message','font','language'])][:50],sep='\n')
