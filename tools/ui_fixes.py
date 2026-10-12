"""Adapt EUR presentation settings to the original JP record schema."""
from level5 import *
import re

DESCRIPTION_TABLES = {
    'data/txt/ja/gamedata/skill/skill_desc_text_ja.cfg.bin',
    'data/txt/ja/gamedata/item/item_text_ja.cfg.bin',
    'data/txt/ja/gamedata/battle/hackslash_special_technic_desc_text_ja.cfg.bin',
    'data/txt/ja/gamedata/battle/hackslash_technic_desc_text_ja.cfg.bin',
}

def wrap_description(path, text):
    # JP widgets do not inherit EUR automatic wrapping. Keep all words/tags.
    # Jara panels are narrower than the inventory description widget.
    if path not in DESCRIPTION_TABLES: return text
    width = 24 if '/skill/' in path else 28 if '/battle/' in path else 44
    return reflow(text, width)

def wrap_display_text(path, text):
    if path in DESCRIPTION_TABLES: return wrap_description(path, text)
    if any(part in path for part in ('/gamedata/ev/', '/gamedata/map/')):
        lines=text.split('\\n')
        # Preserve intentional short lines, choices and pauses when they fit.
        visible=lambda s: re.sub(r'<[^>]*>',lambda m: 'XXXXXXXX' if m[0]=='<PNAME>' else '',s)
        if len(lines)>4 or any(len(visible(line))>40 for line in lines):
            return reflow(text,40)
    return text

def reflow(text,width=36):
    """Wrap words without splitting commands; reserve room for player names."""
    def length(word):
        def tag(m):
            return 'XXXXXXXX' if m[0] in ('<PNAME>','<PLAYER_NAME>','<NAME>') else ''
        return len(re.sub(r'<[^>]*>',tag,word))
    words=text.replace('\\n',' ').split();lines=[];line=[];used=0
    for word in words:
        size=length(word)
        if line and used+1+size>width:
            lines.append(' '.join(line));line=[];used=0
        used+=(1 if line else 0)+size;line.append(word)
    if line:lines.append(' '.join(line))
    return '\\n'.join(lines)

def font_styles(j,e):
    name='data/gamedata/sys/font_style_0.00.00.cfg.bin'
    raw=j.read(name); target=T2B(raw); donor=T2B(e.read(name))
    lookup={r['args'][0]['value']:r for r in donor.records if len(r['args'])==16}
    result=bytearray(raw); changes=[]
    for r in target.records:
        if len(r['args'])!=11: continue
        d=lookup[r['args'][0]['value']]
        assert r['tag']==d['tag']
        # EUR added a name argument after ID. Its font IDs 3/4 and extra
        # auto-fit fields do not exist in JP. Preserve JP font and schema.
        # EUR resources assume EUR horizontal/vertical alignment. In particular,
        # its Jara description anchors expect vertically centered text, whereas
        # JP top alignment makes wrapped lines run below those same anchors.
        for index in (4,5,6,7):
            a,b=r['args'][index],d['args'][index+1]
            assert a['type']==b['type']==1
            if a['value']!=b['value']:
                struct.pack_into('<I',result,a['pos'],b['value'])
                changes.append({'style':d['args'][1]['text'],'argument':index,
                                'before':a['value'],'after':b['value']})
    # Imported EUR menu resources reference these styles, absent in the JP
    # table. Translate only their common fields into native 11-argument rows;
    # never copy EUR's unsupported wrapping/scaling fields or font IDs.
    required={'fn_na_c_w_ss','fn_prof_lc_b','fn_tprof_c_b','fn_qt_lc_b_s',
              'fn_online_c_b','fn_qt_lc_w_s','fn_sk_lc_w','fn_22_c_b_ba',
              'fn_sk_c_w','fn_online_lc_b','fn_qt_c_b','fn_6_rc_w','fn_online_c_w'}
    existing={r['args'][0]['value'] for r in target.records if len(r['args'])==11}
    added=[]
    template=target.records[1]
    for d in donor.records:
        if len(d['args'])!=16 or d['args'][1]['text'] not in required:continue
        if d['args'][0]['value'] in existing:continue
        values=[d['args'][0]['value']]+[a['value'] for a in d['args'][2:12]]
        values[1]=0  # JP's normal text font, already used for English body text.
        row=bytearray(raw[template['start']:template['end']])
        for a,v in zip(template['args'],values):
            struct.pack_into('<I',row,a['pos']-template['start'],v)
        added.append(bytes(row))
        changes.append({'style':d['args'][1]['text'],'added_native_definition':True})
    if added:
        assert target.string_size==0
        end=target.records[-1]['start']
        body=result[16:end]+b''.join(added)+result[end:target.records[-1]['end']]
        header=bytearray(result[:16]);offset=(16+len(body)+15)&~15
        struct.pack_into('<II',header,0,len(target.records)+len(added),offset)
        result=header+body+b'\xff'*(offset-16-len(body))+raw[target.string_offset:]
        struct.pack_into('<I',result,target.records[0]['args'][0]['pos'],len(existing)+len(added))
    check=T2B(bytes(result));assert len(check.records)==len(target.records)+len(added)
    return name,bytes(result),changes
