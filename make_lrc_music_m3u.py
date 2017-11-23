# -*- encoding:utf-8 -*-

# 网易云音乐 lrc歌曲m3u生成器
# 版本: 2.3
import codecs
import hashlib
import json
import os
import urllib
import urllib2
from sys import argv

# 歌单id设置 设置为 argv[1] 将使用 " python make_lrc_music_m3u.py 歌单id " 这种方式传入
playlistId = argv[1]

# 播放列表存放位置
m3udir = u"./播放列表/"

# 相对于播放列表存放位置的 音乐存放位置
mp3dir = u"../音乐/"

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
    req = urllib2.Request(url)
    req.add_header('Referer',url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36')
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
    url = 'http://music.163.com/api/song/media?id=' + tracksId
    dataS = urlGetJsonLoad(url)
    if dataL['code'] != 200:
        ecode = bytes(dataL['code'])
        print 'errorCode: ' + ecode
    else:
        # 判断是否有歌词
        if dataS.has_key('lyric'):
            return dataS['lyric']
        else:
            return ''


# 下载歌曲
def dowmMusic(tracksId, fileName):
    url = 'http://music.163.com/song/media/outer/url?id=' + tracksId + '.mp3'
    try:
        print 'Download music: ' + fileName.replace(m3udir,'').replace(mp3dir,'')
    except:
        print 'Download music: '
    try:
        urllib.urlretrieve(url, fileName)
    except:
        print 'error'


# 写出文件
def writeToFile(name, text):
    try:
        print 'Write to file: ' + name.replace(m3udir,'').replace(mp3dir,'')
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
    m3uText += u"\n#EXTINF:" + mp3Title + u"\n" + mp3dir + mp3Name


# 获取歌单
url = 'http://music.163.com/api/playlist/detail?id=' + playlistId
dataL = urlGetJsonLoad(url)
if dataL['code'] != 200:
    ecode = bytes(dataL['code'])
    print 'errorCode: ' + ecode
else:
    # 循环歌单
    allNum = len(dataL['result']['tracks'])
    nowNum = 0
    for tracks in dataL['result']['tracks']:
        nowNum += 1
        print bytes(nowNum) + '/ ' + bytes(allNum)
        fileName = ''
        i = len(tracks['artists']) - 1
        for artist in tracks['artists']:
            if i > 0:
                fileName += artist['name'] + u","
                i -= 1
            else:
                fileName += artist['name']
        fileName += u" - " + tracks['name']
        fileName = replaceName(fileName)
        tid = bytes(tracks['id'])
        # 存在歌曲文件跳过
        if not os.path.isfile(m3udir + mp3dir + fileName + u".mp3"):
            dowmMusic(tid, m3udir + mp3dir + fileName + u".mp3")
        # 存在歌词文件就跳过
        if not os.path.isfile(m3udir + mp3dir + fileName + u".lrc"):
            lrcS = getLrc(tid)
            if len(lrcS) > 0:
                writeToFile(m3udir + mp3dir + fileName + u".lrc", lrcS)
        # 添加到播放列表
        addPlaylist(tracks['name'], fileName + u".mp3")
    # 写播放列表文件
    writeToFile(m3udir + dataL['result']['name'] + u".m3u", m3uText)
