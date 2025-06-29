import shutil, os, pathlib, re
root = pathlib.Path('..') / 'prompts'
for p in root.glob('hop_Q*.lean.txt'):
    if '.confidence.lean' in p.name:
        dest_dir = root / 'confidence_lean'
    else:
        dest_dir = root / 'lean'
    dest_dir.mkdir(exist_ok=True)
    shutil.move(str(p), dest_dir / p.name)
for p in root.glob('hop_Q*.confidence.txt'):
    dest_dir = root / 'confidence'
    dest_dir.mkdir(exist_ok=True)
    shutil.move(str(p), dest_dir / p.name)
print('done') 