from level5 import *
import re,collections
ROOT=Path(__file__).parent
JP=re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')
def normalize(s): return re.sub(r'\[([^\[\]/]+)/[^\[\]]+\]',r'\1',s).replace('　',' ').strip()
def key(k): return k[0],k[1][:(1 if k[0]==0x2240ea93 else 2)],k[2]
def english(n): return n.replace('/ja/','/en/').replace('_ja.','_en.')
j=Arc(ROOT/'jp-romfs/archive_a.fa'); e=Arc(ROOT/'eur-romfs/archive_a.fa')
global_en=collections.defaultdict(set); en_files={}; errors=[]
for n in e.entries:
    if not (n.startswith('data/txt/en/') or n.endswith('_en.cfg.bin')): continue
    try: t=T2B(e.read(n))
    except Exception as ex: errors.append([n,str(ex)]); continue
    en_files[n]={key(k):s for k,s,pos in t.strings()}
    for k,s in en_files[n].items(): global_en[k].add(s)
names=[n for n in j.entries if n.startswith('data/txt/ja/') or n.endswith('_ja.cfg.bin')]
tables={n:T2B(j.read(n)) for n in names}
lookup=collections.defaultdict(set); plans={}; misses=[]; stats=collections.Counter()
for n,t in tables.items():
    local=en_files.get(english(n),{})
    plans[n]=[]
    for k,s,pos in t.strings():
        ek=key(k); donor=local.get(ek); origin='EUR matching file and ID'
        if donor is None and len(global_en[ek])==1:
            donor=next(iter(global_en[ek])); origin='EUR unique global ID'
        if donor is not None and not JP.search(donor) and donor.strip():
            lookup[normalize(s)].add(donor)
        plans[n].append({'pos':pos,'key':ek,'jp':s,'en':donor,'origin':origin})
for n,rows in plans.items():
    for row in rows:
        donor=row['en']; s=row['jp']
        if donor is None or JP.search(donor):
            candidates=lookup[normalize(s)]
            if len(candidates)==1:
                donor=next(iter(candidates)); row['origin']='EUR identical Japanese text'
            elif not JP.search(s): donor=s; row['origin']='Original non-Japanese text'
            else: donor=None; row['origin']='Needs translation'
        row['en']=donor
        stats[row['origin']]+=1
        if donor is None: misses.append({'file':n,**row})
unique=list(dict.fromkeys(normalize(row['jp']) for row in misses))
(ROOT/'translation-plan.json').write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'remaining.json').write_text(json.dumps([{'id':i,'jp':s,'en':''} for i,s in enumerate(unique)],ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'remaining-context.json').write_text(json.dumps(misses,ensure_ascii=False,indent=2),encoding='utf-8')
print(dict(stats)); print('Remaining unique:',len(unique)); print('Parse errors:',errors)
