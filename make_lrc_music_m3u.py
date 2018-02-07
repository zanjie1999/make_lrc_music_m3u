# -*- encoding:utf-8 -*-

# 网易云音乐 lrc歌曲m3u生成器
# 版本: 4.1
import sys
import codecs
import hashlib
import json
import os
import urllib
import urllib2
from sys import argv


if len(argv) < 2:
    print "请传入歌单id"
    sys.exit()

# 歌单id设置 设置为 argv[1] 将使用 " python make_lrc_music_m3u.py 歌单id " 这种方式传入
playlistId = argv[1]

# 播放列表存放位置
m3udir = u"./播放列表/"

# 相对于播放列表存放位置的 音乐存放位置
mp3dir_in_m3udir = u"../音乐/"

# 是否按m3u分类
if len(argv) > 2:
    sortBym3u = True
else:
    sortBym3u = False

# 是否下载歌词
downLrc = True


# 半角转全角
def half2full(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:
            inside_code += 65248

        rstring += unichr(inside_code)
    return rstring


# 发送请求
def urlGetJsonLoad(url):
    headers = {
        'Accept':
            '*/*',
        'Accept-Language':
            'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
        'Connection':
            'keep-alive',
        'Content-Type':
            'application/x-www-form-urlencoded',
        'Referer':
            'http://music.163.com',
        'Host':
            'music.163.com',
        'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'
    }
    req = urllib2.Request(url, headers=headers)
    return json.load(urllib2.urlopen(req))


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
    return name.strip()


# 获取歌词
def getLrc(tracksId):
    url = 'http://music.163.com/api/song/lyric?lv=-1&tv=-1&id=' + tracksId
    dataS = urlGetJsonLoad(url)
    if dataS['code'] != 200:
        ecode = bytes(dataS['code'])
        print 'errorCode: ' + ecode
    else:
        if not dataS.has_key('lrc') or not dataS['lrc'].has_key('lyric') or dataS['lrc']['lyric'] == None:
            return ''

        if not dataS.has_key('tlyric') or not dataS['tlyric'].has_key('lyric') or dataS['tlyric']['lyric'] == None:
            return dataS['lrc']['lyric']

        # 按换行分割
        lrcL = dataS['lrc']['lyric'].splitlines()
        tlyricL = dataS['tlyric']['lyric'].splitlines()
        tlyricD = {}
        lrcStr = ''

        # 分割翻译
        for tlyric in tlyricL:
            tl = tlyric.split(u']', 1)
            # 防止有时间但翻译为空
            if len(tl) > 1:
                tlyricD[tl[0]] = tl[1]

        # 合并歌词
        for lrc in lrcL:
            l = lrc.split(u']', 1)
            if tlyricD.has_key(l[0]):
                lrcStr += l[0] + u']' + l[1] + u'\t' + tlyricD[l[0]] + u'\n'
            else:
                lrcStr += lrc + u'\n'

        return lrcStr


# 下载歌曲
def dowmMusic(tracksId, fileName):
    url = 'http://music.163.com/song/media/outer/url?id=' + tracksId + '.mp3'
    try:
        print 'Download music: ' + fileName.replace(m3udir, '').replace(mp3dir, '')
    except:
        print 'Download music: '
    try:
        urllib.urlretrieve(url, fileName)
    except:
        print 'error'


# 写出文件
def writeToFile(name, text):
    try:
        print 'Write to file: ' + name.replace(m3udir, '').replace(mp3dir, '')
    except:
        print 'Write to file: '
    try:
        file = codecs.open(name, "w", "utf-8")
        file.write(text)
        file.close()
    except:
        print 'error'


# 生成播放列表
m3uText = "#EXTM3U"


def addPlaylist(mp3Title, mp3Name):
    global m3uText
    m3uText += u"\n#EXTINF:" + mp3Title + u"\n" + mp3dir.replace("/", "\\") + mp3Name


# 确保需要的文件夹
if not os.path.isdir(m3udir):
    os.mkdir(m3udir)

if not os.path.isdir(m3udir + mp3dir_in_m3udir):
    os.mkdir(m3udir + mp3dir_in_m3udir)

# 获取歌单
url = 'http://music.163.com/api/playlist/detail?id=' + playlistId
dataL = urlGetJsonLoad(url)
if dataL['code'] != 200:
    ecode = bytes(dataL['code'])
    print 'errorCode: ' + ecode
else:
    m3uName = replaceName(dataL['result']['name'])
    allNum = len(dataL['result']['tracks'])
    nowNum = 0
    # 循环歌单
    for tracks in dataL['result']['tracks']:
        nowNum += 1
        print bytes(nowNum) + '/ ' + bytes(allNum)
        fileName = ''
        # 循环歌手
        i = len(tracks['artists']) - 1
        for artist in tracks['artists']:
            if i > 0:
                fileName += artist['name'] + u","
                i -= 1
            else:
                fileName += artist['name']

        # 如按歌单分文件夹,不存在文件夹就创建
        if sortBym3u:
            mp3dir = mp3dir_in_m3udir + m3uName + u"/"
            if not os.path.isdir(m3udir + mp3dir):
                os.mkdir(m3udir + mp3dir)

        else:
            mp3dir = mp3dir_in_m3udir

        fileName += u" - " + tracks['name']
        fileName = replaceName(fileName)
        tid = bytes(tracks['id'])
        # 存在歌曲文件跳过
        if not os.path.isfile(m3udir + mp3dir + fileName + u".mp3"):
            dowmMusic(tid, m3udir + mp3dir + fileName + u".mp3")

        # 如果需要下载歌词,不存在歌词就下载
        if downLrc:
            if not os.path.isfile(m3udir + mp3dir + fileName + u".lrc"):
                lrcS = getLrc(tid)
                if len(lrcS) > 0:
                    writeToFile(m3udir + mp3dir + fileName + u".lrc", lrcS)

        # 添加到播放列表
        addPlaylist(tracks['name'], fileName + u".mp3")

    # 写播放列表文件
    writeToFile(m3udir + m3uName + u".m3u", m3uText)
