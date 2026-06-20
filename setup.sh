#!/bin/bash
cd ~/FSINT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 << 'EOF'
import gdown, rarfile, os
os.makedirs('data', exist_ok=True)
gdown.download('https://drive.google.com/uc?id=1MDSf7r-vekMUTxx1q0osUswpERso5xyv', 'data/data.rar', quiet=False)
with rarfile.RarFile('data/data.rar') as rf:
    rf.extractall('data/extracted/')
print('✅ تم')
EOF
