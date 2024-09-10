# -*- encoding:utf-8 -*-

# 如果有flac就删掉mp3
# v2

import os
import unicodedata, re

# 操作目录
os.chdir('网易云音乐')

a = os.listdir('.')
mp3 = {}
flac = {}
for i in a:
    if i.endswith('.flac') or i.endswith('.FLAC'):
        flac[unicodedata.normalize("NFC", re.sub(r'[()（）]|[　 ]', '', i[:-5]))] = i
    elif i.endswith('.mp3') or i.endswith('.MP3'):
        mp3[unicodedata.normalize("NFC", re.sub(r'[()（）]|[　 ]', '', i[:-4]))] = i

mp3Keys = mp3.keys()
for i in flac:
    if i in mp3Keys:
        print(flac[i] + '\n' + mp3[i] + '\n')
        os.remove(mp3[i])