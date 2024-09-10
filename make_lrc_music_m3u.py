# -*- encoding:utf-8 -*-

# 网抑云 lrc歌曲m3u生成器
# 版本: 13.1
import platform
import sys
import codecs
import hashlib
import json
import os
import urllib.request, urllib.parse, urllib.error
from http import cookiejar
import gzip
import signal
from sys import argv
from io import StringIO
import unicodedata, re


if len(argv) < 2:
    print("请传入歌单id")
    sys.exit()

# 歌单id设置 设置为 argv[1] 将使用 " python make_lrc_music_m3u.py 歌单id " 这种方式传入
playlistId = argv[1]

# 播放列表存放位置
m3udir = "./播放列表/"

# 相对于播放列表存放位置的 音乐存放位置
mp3dir_in_m3udir = "../网易云音乐/"

# 是否按m3u分类
if len(argv) > 2:
    sortBym3u = True
else:
    sortBym3u = False

# 是否下载歌词
downLrc = False

# 是否下载音乐
down128Music = False

# 账号cookie 
# 由于不登录只会返回前10首歌 更多的需要登录 (歌单创建者 失效了可以打开一次输出的url再复制) 别人得到了这段cookie相当于能登录你的账号 请务必不要泄露
# Chrome打开网抑云 -> 登录 -> 按F12打开 开发者工具 -> 切换到 Console -> 输入 document.cookie 按回车 -> 复制输出内容替换下面的双引号
cookie = ""

translationTable = str.maketrans("àèéùâêîôûçë", "aeuaeeiouce")

# Ctrl + C 退出
def signal_handler(signal, frame):
   print('Ctrl + C, exit now...')
   sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

# 加载头部 防ban
cookieJar = cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookieJar))
opener.addheaders = [
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'),
    ('Accept-Encoding', 'gzip, deflate'),
    ('Accept-Language', 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6'),
    ('Connection', 'keep-alive'),
    ('Cookie', cookie),
    ('DNT', '1'),
    ('Host', 'music.163.com'),
    ('Upgrade-Insecure-Requests', '1'),
    ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')
]
urllib.request.install_opener(opener)


# 判断文件是否存在
def hasFile(fileName):
    # 文件名不区分大小写
    for i in listdir:
        # 适配网易云的迷惑unicode行为 比如 '結束バンド' != '結束バンド' 文件名开始结束或歌手的全角空格
        fn1 = unicodedata.normalize("NFC", re.sub(r'[()（）]|[　 ]', '', fileName))
        fn2 = unicodedata.normalize("NFC", re.sub(r'[()（）]|[　 ]', '', i))
        if fn1 == fn2:
            return i

    return ''


# 寻找存在的音频文件
fType = ''
def findHasMusicFileFullFileName(name):
    global fType
    fType = ''
    fileTyps = ['.flac', '.ape', '.wav', '.mp3']
    for t in fileTyps:
        fullFileName = hasFile(name + t)
        if fullFileName != '':
            fType = t
            return fullFileName

    return ''


# 半角转全角
def half2full(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:
            inside_code += 65248

        rstring += chr(inside_code)
    return rstring


# 发送请求
def urlGetJsonLoad(url):
    gzdata = ''
    try:
        gzdata = urllib.request.urlopen(url, timeout=10)
    except Exception as e:
        print('connect error: ', url)
        return {'code': ''}
    try:
        if gzdata.info().get('Content-Encoding') == 'gzip':
            gziper = gzip.GzipFile(fileobj=gzdata)
            return json.loads(gziper.read().decode('utf-8'))
        else:
            return json.loads(gzdata.read().decode('utf-8'))
    except Exception as e:
        print('decode error: ', url)
        return {'code': ''}


# 替换文件名不允许字符
def replaceName(name):
    name = name.replace('?', half2full('?'))
    name = name.replace('*', half2full('*'))
    name = name.replace('/', half2full('/'))
    name = name.replace('\\', half2full('\\'))
    name = name.replace('<', half2full('<'))
    name = name.replace('>', half2full('>'))
    name = name.replace(':', half2full(':'))
    name = name.replace('\"', half2full('\"'))
    name = name.replace('|', half2full('|'))
    name = name.replace('[', half2full('['))
    name = name.replace(']', half2full(']'))
    name = name.strip()
    return name


# 获取歌词
def getLrc(tracksId):
    url = 'http://music.163.com/api/song/lyric?lv=-1&tv=-1&id=' + tracksId
    dataS = urlGetJsonLoad(url)
    if dataS['code'] != 200:
        ecode = str(dataS['code'])
        print('errorCode: ' + ecode)
        return ''
    else:
        if 'lrc' not in dataS or 'lyric' not in dataS['lrc'] or dataS['lrc']['lyric'] == None:
            return ''

        if 'tlyric' not in dataS or 'lyric' not in dataS['tlyric'] or dataS['tlyric']['lyric'] == None:
            return dataS['lrc']['lyric']

        # 按换行分割
        lrcL = dataS['lrc']['lyric'].splitlines()
        tlyricL = dataS['tlyric']['lyric'].splitlines()
        tlyricD = {}
        lrcStr = ''

        # 分割翻译
        for tlyric in tlyricL:
            tl = tlyric.split(']', 1)
            # 防止有时间但翻译为空
            if len(tl) > 1:
                tlyricD[tl[0]] = tl[1]

        # 合并歌词
        for lrc in lrcL:
            l = lrc.split(']', 1)
            if l[0] in tlyricD:
                lrcStr += l[0] + ']' + l[1] + '\t' + tlyricD[l[0]] + '\n'
            else:
                lrcStr += lrc + '\n'

        return lrcStr


# 下载歌曲
def downMusic(tracksId, fileName):
    url = 'http://music.163.com/song/media/outer/url?id=' + tracksId + '.mp3'
    try:
        print('Download music: ' + fileName.replace(m3udir, '').replace(mp3dir, ''))
    except:
        print('Download music: ' + tracksId)
    try:
        urllib.request.urlretrieve(url, fileName)
        if os.path.getsize(fileName) < 20000:
            # 小于10k这音频肯定有问题 给它扬了
            print('Need VIP')
            os.remove(fileName)
            return False
    except:
        print('error')
        return False
    return True


# 写出文件
def writeToFile(name, text):
    try:
        print('Write to file: ' + name.replace(m3udir, '').replace(mp3dir, ''))
    except:
        print('Write to file: ')
    try:
        file = codecs.open(name, "w", "utf-8")
        file.write(text)
        file.close()
    except:
        print('error')


# 生成播放列表
m3uText = "#EXTM3U"
def addPlaylist(mp3Title, mp3Name):
    global m3uText
    m3uText += "\n#EXTINF:" + mp3Title + "\n" + mp3dir.replace("/", "\\") + mp3Name


# 确保需要的文件夹
if not os.path.isdir(m3udir):
    os.mkdir(m3udir)

if not os.path.isdir(m3udir + mp3dir_in_m3udir):
    os.mkdir(m3udir + mp3dir_in_m3udir)

# 弄个文件来存对应关系
db = {}
if os.path.isfile(m3udir + 'db.json'):
    with codecs.open(m3udir + 'db.json', "r", "utf-8") as dbf:
        try:
            db = json.load(dbf)
        except:
            print('Error DB')
else:
    print('NO DB')

# 获取歌单
url = 'http://music.163.com/api/v6/playlist/detail?n=2147483647&id=' + playlistId
print(url)
dataL = urlGetJsonLoad(url)
if dataL['code'] != 200:
    ecode = str(dataL['code'])
    print('errorCode: ' + ecode)
else:
    m3uName = replaceName(dataL['playlist']['name'])
    allNum = len(dataL['playlist']['tracks'])
    nowNum = 0

    # 如按歌单分文件夹,不存在文件夹就创建
    if sortBym3u:
        mp3dir = mp3dir_in_m3udir + m3uName + "/"
        if not os.path.isdir(m3udir + mp3dir):
            os.mkdir(m3udir + mp3dir)

    else:
        mp3dir = mp3dir_in_m3udir

    # 查找所有文件
    listdir = os.listdir(m3udir + mp3dir)
    noFileTxt = ''

    # 循环歌单
    for tracks in dataL['playlist']['tracks']:
        nowNum += 1
        print("\r" + str(nowNum) + '/ ' + str(allNum), end=' ')
        fileName = ''
        fileNameAndroid = ''
        fileNameReverse = ''
        fileNameReverseAndroid = ''
        # 循环歌手
        i = len(tracks['ar']) - 1
        for artist in tracks['ar']:
            if i > 0:
                fileName += artist['name'] + ","
                fileNameAndroid += artist['name'] + " "
                fileNameReverse = "," + artist['name'] + fileNameReverse
                fileNameReverseAndroid = " " + artist['name'] + fileNameReverse
                i -= 1
            elif artist['name']:
                fileName += artist['name']
                fileNameAndroid += artist['name']
                fileNameReverse = artist['name'] + fileNameReverse
                fileNameReverseAndroid = artist['name'] + fileNameReverse

        # PC的命名规则 转全角
        fileName += " - " + tracks['name'].strip()
        fileName = replaceName(fileName)
        # 按照空格分隔歌手,例如Android端
        fileNameAndroid += " - " + tracks['name'].strip()
        fileNameAndroid = replaceName(fileNameAndroid.replace('/', ' ').replace('*', ' ').replace('+', half2full('+')).replace('\"', '”'))
        fileNameAndroidOld = fileNameAndroid.translate(translationTable)
        # 歌手翻转的
        fileNameReverse += " - " + tracks['name'].strip()
        fileNameReverseAndroid += " - " + tracks['name'].strip()
        fileNameReverse = replaceName(fileNameReverse)
        fileNameReverseAndroid = replaceName(fileNameReverseAndroid)
        fileNameReverseAndroidOld = fileNameReverseAndroid.translate(translationTable)

        tid = str(tracks['id'])
        # 检查存在的文件
        fullFileNameAndroid = findHasMusicFileFullFileName(fileNameAndroid)

        if fullFileNameAndroid == '':
            fullFileName = ""
            lastFindName = ""
            # 从db找，找到了就重命名
            if tid in db:
                lastFindName = db[tid]
                fullFileName = findHasMusicFileFullFileName(lastFindName)
            # PC 命名方式重命名为Android命名方式
            if fileNameAndroid != fileName:
                lastFindName = fileName
                fullFileName = findHasMusicFileFullFileName(lastFindName)
            # 最近网易整理了一下歌手,处理一下已有文件翻转的情况
            if fullFileName == '' and fileNameAndroid != fileNameReverse:
                lastFindName = fileNameReverse
                fullFileName = findHasMusicFileFullFileName(lastFindName)
            if fullFileName == '' and fileNameAndroid != fileNameReverseAndroid:
                lastFindName = fileNameReverseAndroid
                fullFileName = findHasMusicFileFullFileName(lastFindName)
            # 最近整理发型客户端突然支持法语子字符了 大量文件改名
            if fullFileName == '' and fileNameAndroid != fileNameAndroidOld:
                lastFindName = fileNameAndroidOld
                fullFileName = findHasMusicFileFullFileName(lastFindName)
            if fullFileName == '' and fileNameAndroid != fileNameReverseAndroidOld:
                lastFindName = fileNameReverseAndroidOld
                fullFileName = findHasMusicFileFullFileName(lastFindName)

            if fullFileName != '':
                try:
                    print('Rename file: ' + fullFileName)
                except:
                    print('Rename file: ')
                try:
                    os.rename(m3udir + mp3dir + fullFileName, m3udir + mp3dir + fileNameAndroid + fType)
                    fullFileNameAndroid = fileNameAndroid + fType
                    try:
                        os.remove(lastFindName + '.lrc')
                    except:
                        pass
                except:
                    print('Rename error!')
                fullFileNameAndroid = fileNameAndroid + fType

        if fullFileNameAndroid == '':
            fullFileNameAndroid = fileNameAndroid + '.mp3'
            if down128Music:
                # 这里将下载一个无封面的128kbps的版本 听个响
                if downMusic(tid, m3udir + mp3dir + fullFileNameAndroid):
                    db[tid] = fileNameAndroid
                else:
                    noFileTxt += fileNameAndroid + '\r\n'
            else:
                print('NO File: ' + fileNameAndroid)
                noFileTxt += fileNameAndroid + '\r\n'
        else:
            db[tid] = fileNameAndroid

        # 如果需要下载歌词,不存在歌词就下载
        if downLrc:
            if not hasFile(fileNameAndroid + ".lrc"):
                lrcS = getLrc(tid)
                if len(lrcS) > 0:
                    writeToFile(m3udir + mp3dir + fileNameAndroid + ".lrc", lrcS)

        # 添加到播放列表 理论上这里fullFileName是不会为空的
        if fullFileNameAndroid != '':
            addPlaylist(tracks['name'], fullFileNameAndroid)

    # 写db文件
    writeToFile(m3udir + 'db.json', json.dumps(db, ensure_ascii=False))

    # 没有文件的让人类处理
    if noFileTxt != '':
        writeToFile(m3udir + "noFile.txt", noFileTxt)

    # 写播放列表文件
    writeToFile(m3udir + m3uName + ".m3u", m3uText)
