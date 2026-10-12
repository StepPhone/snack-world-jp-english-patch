"""Build the patch locally from extracted JP and EUR base-game RomFS folders."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jp-romfs', type=Path, required=True)
    parser.add_argument('--eur-romfs', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    work = root / 'work'
    source_hashes = {'jp': 'b57cb1c44b77fc80b8084dc029bbfc8630d027cfd01a7cfa097f67b0ac16ade5',
                     'eur': '08a1818603d2d98eddd1cea5c20e6c8a77636430d4d5d8af25c6bce3308e85d6'}
    for region, folder in [('jp', args.jp_romfs), ('eur', args.eur_romfs)]:
        source = folder.resolve() / 'archive_a.fa'
        with source.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != source_hashes[region]:
            parser.error(f'{region.upper()} archive does not match the supported base version: {digest}')
    if (root / 'output').exists():
        parser.error('output already exists; move it aside before building again')
    work.mkdir(exist_ok=True)
    shutil.copytree(root / 'tools', work / 'translation-work', dirs_exist_ok=True)
    tools = work / 'translation-work'
    for region, folder in [('jp', args.jp_romfs), ('eur', args.eur_romfs)]:
        target = tools / f'{region}-romfs'
        target.mkdir(exist_ok=True)
        shutil.copy2(folder / 'archive_a.fa', target / 'archive_a.fa')
    for script in ['prepare_patch.py', 'build_patch.py']:
        subprocess.run([sys.executable, str(tools / script)], check=True)
    output = work / 'Snack-World-JP-English-Patch'
    sys.path.insert(0, str(tools))
    from inspect_movies import inspect
    movies = output / 'romfs/mov'
    movies.mkdir(parents=True, exist_ok=True)
    for name in ['sw-t_eved_0001.mp4', 'sw-t_eved_0002.mp4', 'sw-t_evop_0001.mp4']:
        donor = args.eur_romfs / 'mov/[eu]' / name.replace('evop_0001.', 'evop_0001_en.')
        original = args.jp_romfs / 'mov' / name
        a, b = inspect(original), inspect(donor)
        if abs(a['duration_seconds'] - b['duration_seconds']) >= .04 or a['tracks'] != [{'type': 'vide'}] or b['tracks'] != [{'type': 'vide'}]:
            raise ValueError(f'Unexpected movie format or duration: {name}')
        shutil.copy2(donor, movies / name)
    shutil.move(str(output), str(root / 'output'))
    print('Done. Install output/romfs using README.md. Original games were not modified.')

if __name__ == '__main__':
    main()
