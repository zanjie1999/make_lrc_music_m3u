# -*- encoding:utf-8 -*-

# 如果有flac就删掉mp3

import os

# 操作目录
os.chdir('音乐')

a = os.listdir(.)
mp3 = []
flac = []
for i in a:
    if i.endswith('.flac') or i.endswith('.FLAC'):
        flac.append(i[:-5])
    elif i.endswith('.mp3') or i.endswith('.MP3'):
        mp3.append(i[:-4])
    
for i in flac:
    if i in mp3:
        os.remove(i + '.mp3')