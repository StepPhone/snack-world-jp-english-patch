"""Build a local RomFS overlay from the user's JP and EUR archives."""
from level5 import *
import re, collections, hashlib, mmap, textwrap
from ui_fixes import font_styles,reflow,wrap_display_text
from voice_fixes import quote_voice_parameters
ROOT=Path(__file__).parent
OUT=ROOT.parent/'Snack-World-JP-English-Patch'
JAPANESE=re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')
def normalize(s): return re.sub(r'\[([^\[\]/]+)/[^\[\]]+\]',r'\1',s).replace('　',' ').strip()
def sha(d): return hashlib.sha256(d).hexdigest()
def english_tags(s,jp):
    # The Japanese binary does not implement the EUR grammatical conditionals.
    hero={'he':'<PNAME>','He':'<PNAME>','his':"<PNAME>'s",'His':"<PNAME>'s",'him':'<PNAME>',
          'himself':'<PNAME>','sir':'friend','Mr.':'','boy':'friend','my boy':'my friend',
          'man':'person','lad':'friend','laddie':'friend','attaboy':'well done','guy':'friend',
          'hero':'hero','fellow':'person'}
    s=re.sub(r'<IF_HERO>(.*?)<ELSE_HEROINE>.*?<ENDIF_HERO>',lambda m:hero.get(m[1],m[1]),s)
    # Resolve innermost noun/number conditionals. Generic noun names work in JP.
    pattern=re.compile(r'<(IF_[^>]+)>((?:(?!<IF_).)*?)<ENDIF_[^>]+>')
    while '<IF_' in s:
        def branch(m):
            choices=re.split(r'<ELSE[^>]*>',m[2])
            if m[1].startswith('IF_SGL'): return choices[-1]
            if m[1].startswith('IF_MALE'): return choices[-1]
            return choices[0] if m[1].startswith('IF_PROPER') else choices[-1]
        new=pattern.sub(branch,s)
        if new==s: raise ValueError('Unresolved conditional: '+s)
        s=new
    s=re.sub(r'<(?:INDEF_ART_SGL_|DEF_ART_SGL_|SGL_|PLR_)([^>]+)>',r'<\1>',s)
    s=s.replace('<PNAME-CAP>','<PNAME>').replace('<NBSP>',' ').replace('<NB->','-')
    s=s.replace('<ITEM_EFFECT_GIRAN_VAL>','<ITEM_EFFECT_VAL>')
    s=s.replace('<PG>',' ')
    for tag in ['<EBI>','</E>','<Cap>','<TC>','<MK_1>','<MK_CW>','<MK_OW>','<->']:
        s=s.replace(tag,'')
    s=s.replace('<B->','-').replace('<NOT_NEEDED>','Unused').replace('<NOT USED?>','Unused')
    s=s.replace('<Latest fashion news>','Latest fashion news')
    # Keep JP voice cues, which name Japanese audio assets; retain choice codes.
    voices=re.findall(r'<P?V#[^>]+>',jp)
    s=re.sub(r'<P?V(?:#[^>]+|"[^">]+")>','',s)
    s=''.join(voices)+s
    choices=re.findall(r'<SEL\d[^>]*>',jp)
    s=re.sub(r'<SEL\d[^>]*>','',s)+''.join(choices)
    s=s.replace('<PNAME>self','<PNAME>')
    # Avoid unsupported typographic glyphs; the original fonts include these ASCII forms.
    for a,b in [('’',"'"),('‘',"'"),('“','"'),('”','"'),('…','...'),('–','-'),('—','-'),('\u00a0',' ')]: s=s.replace(a,b)
    return quote_voice_parameters(s)

def build():
    j=Arc(ROOT/'jp-romfs/archive_a.fa'); e=Arc(ROOT/'eur-romfs/archive_a.fa')
    plans=json.loads((ROOT/'translation-plan.json').read_text(encoding='utf8'))
    manual=json.loads((ROOT/'manual-translations.json').read_text(encoding='utf8'))
    layout=json.loads((ROOT/'layout-overrides.json').read_text(encoding='utf8'))
    applied_layout=[]
    manual.update({
        '自販機は待ってくれるけど\\nママは あんまり待てないわよぅ～':"The vending machine can wait, but Mama can't wait much longer!",
        '魔王ワザの力は <CR>『ジャラタッチ』</C>で\\n生み出されたジャラほど宿しやすいという。':'They say Jara created through <CR>Jara Touch</C> are more likely to hold the power of a Demon King move.',
        'あのオババ… いったい何者なのだ…。':'That old woman... Who on earth is she?'
    })
    replacements={}; manifest=[]; counts=collections.Counter(); remaining=[]
    for n,rows in plans.items():
        original=j.read(n); t=T2B(original); changes={}
        for row in rows:
            s=row['en']
            if s is None:
                s=manual[normalize(row['jp'])]; counts['manually_translated_entries']+=1
            else: counts['EUR_or_existing_entries']+=1
            position=':'.join(map(str,row['pos']))
            if position in layout.get(n,{}):
                s=layout[n][position]
                applied_layout.append((n,position))
                counts['layout_corrected_entries']+=1
            s=english_tags(s,row['jp'])
            if '/gamedata/ev/' in n and '<PG>' in (row['en'] or '') and position not in layout.get(n,{}):
                s=reflow(s)
                counts['EUR_page_messages_reflowed']+=1
            wrapped=wrap_display_text(n,s)
            if wrapped!=s: counts['display_entries_wrapped']+=1
            s=wrapped
            if JAPANESE.search(s): remaining.append([n,row['pos'],s])
            changes[tuple(row['pos'])]=s
        result=t.rebuild(changes); check=T2B(result)
        assert len(t.records)==len(check.records)
        for a,b in zip(t.records,check.records):
            assert a['tag']==b['tag'] and len(a['args'])==len(b['args'])
            for x,y in zip(a['args'],b['args']):
                assert x['type']==y['type']
                if x['text'] is None: assert x['value']==y['value']
        actual={pos:s for key,s,pos in check.strings()}
        assert actual==changes,(n,'string roundtrip failed')
        if result!=original:
            replacements[n]=result; counts['text_files']+=1
            manifest.append({'path':n,'kind':'text','sha256':sha(result),'original_sha256':sha(original),'strings':len(changes)})
    assert not remaining,remaining[:3]
    assert len(applied_layout)==sum(len(rows) for rows in layout.values()),'Unused layout override'
    graphics={}; skipped=[]
    for n in e.entries:
        candidates=[]
        if n.startswith('data/menu/en/'): candidates.append(n.replace('/menu/en/','/menu/'))
        if re.search(r'_en\.',n) and not n.startswith('data/txt/') and not n.endswith('.bin'):
            candidates += [n.replace('_en.','_ja.'),n.replace('_en.','.')]
        for dest in candidates:
            if dest in j.entries: graphics[dest]=n; break
    for dest,source in graphics.items():
        # The edited keyboard package caused an invisible input dialog in Eden.
        # Restoring the original package restored the keyboard (user screenshot).
        if dest == 'data/menu/keyboard_d00.xa':
            skipped.append({'path':dest,'source':source,
                            'reason':'retain original keyboard; edited package broke dialog rendering'})
            continue
        orig=j.read(dest); donor=e.read(source)
        if orig==donor: continue
        kind='localized graphic'
        if orig.startswith(b'XPCK'):
            a=Xpck(orig); b=Xpck(donor)
            if set(a.entries)!=set(b.entries):
                compatible=False
                if dest.startswith('data/menu/') and 'RES.bin' in a.entries and 'RES.bin' in b.entries:
                    def resource_names(x):
                        raw=decompress(x.read('RES.bin'))
                        # Frame/sub-part numbers may change with translated art; keep named animations.
                        return {s for s in re.findall(rb'[A-Za-z_][A-Za-z_0-9#.-]{3,}\x00',raw) if not s.startswith(b'font_')}
                    compatible=resource_names(a)<=resource_names(b) and not dest.endswith('keyboard_d00.xa')
                if not compatible:
                    skipped.append({'path':dest,'source':source,'reason':'different XPCK layout/resource names',
                                    'jp_count':len(a.entries),'eur_count':len(b.entries)})
                    continue
                kind='localized graphics package; Japanese named resources retained'
            else: kind='localized graphics package; matching member list'
        elif orig[:4]!=donor[:4]:
            skipped.append({'path':dest,'source':source,'reason':'different format signature'}); continue
        replacements[dest]=donor; counts['graphic_files']+=1
        manifest.append({'path':dest,'source':source,'kind':kind,'sha256':sha(donor),'original_sha256':sha(orig)})
    style_path,style_data,style_changes=font_styles(j,e)
    replacements[style_path]=style_data
    counts['font_style_fields_corrected']=len(style_changes)
    manifest.append({'path':style_path,'kind':'JP-compatible English font spacing',
                     'sha256':sha(style_data),'original_sha256':sha(j.read(style_path)),
                     'changes':style_changes})
    assert 'data/menu/keyboard_d00.xa' not in replacements
    counts['keyboard_labels_localized']=0
    from startup_credit import replacements as startup_replacements
    for path,data in startup_replacements(j).items():
        replacements[path]=data
        manifest.append({'path':path,'kind':'StepHackerZ additional startup credit',
                         'sha256':sha(data),'original_sha256':sha(j.read(path))})
    counts['startup_credit_members']=2
    # Preserve every ARC0 directory, hash and filename, replacing file data only.
    file_table=bytearray(j.tables[2]); offset=0
    order=sorted(j.entries.items(),key=lambda pair:pair[1]['offset'])
    for n,entry in order:
        size=len(replacements[n]) if n in replacements else entry['size']
        struct.pack_into('<II',file_table,entry['index']*16+8,offset,size)
        offset=(offset+size+3)&~3
    tables=[j.tables[0],j.tables[1],bytes(file_table),j.tables[3]]
    header=bytearray(j.header); metadata=bytearray(header); offsets=[]
    for table in tables:
        offsets.append(len(metadata)); metadata.extend(struct.pack('<I',len(table)<<3)+table)
        metadata.extend(b'\0'*(-len(metadata)%4))
    offsets.append(len(metadata)); struct.pack_into('<5I',metadata,4,*offsets)
    output=OUT/'romfs/archive_a.fa'; output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_suffix('.fa.building')
    with j.path.open('rb') as original, mmap.mmap(original.fileno(),0,access=mmap.ACCESS_READ) as mm, temp.open('wb') as out:
        out.write(metadata)
        for n,entry in order:
            raw=replacements.get(n)
            if raw is None: raw=mm[j.data_offset+entry['offset']:j.data_offset+entry['offset']+entry['size']]
            out.write(raw); out.write(b'\0'*(-len(raw)%4))
    temp.replace(output)
    # Independent reopen, compare every member, not just selected samples.
    patched=Arc(output); assert set(patched.entries)==set(j.entries)
    print('Archive rebuilt. Verifying every member...',flush=True)
    with j.path.open('rb') as jf, output.open('rb') as pf:
        for n,entry in order:
            pe=patched.entries[n]; pf.seek(patched.data_offset+pe['offset']); got=pf.read(pe['size'])
            if n in replacements: expected=replacements[n]
            else: jf.seek(j.data_offset+entry['offset']); expected=jf.read(entry['size'])
            assert got==expected,n
    counts['archive_members_verified']=len(j.entries)
    counts['unchanged_members']=len(j.entries)-len(replacements)
    counts['skipped_graphics']=len(skipped)
    report={'target_title_id':'010072B007418000','target_version':'1.0.0 (base/v0)',
            'counts':dict(counts),'remaining_Japanese_in_target_text_entries':remaining,
            'skipped_graphics':skipped,'runtime_tested':False,'archive_size':output.stat().st_size,
            'archive_sha256':hashlib.file_digest(output.open('rb'),'sha256').hexdigest(),
            'source_jp_sha256':hashlib.file_digest(j.path.open('rb'),'sha256').hexdigest(),
            'source_eur_sha256':hashlib.file_digest(e.path.open('rb'),'sha256').hexdigest()}
    (OUT/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__': build()
