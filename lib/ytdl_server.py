#!/usr/bin/env python
# -*- coding: utf-8 -*-

# youtube-dl-server
# This program is part of the Minimal Kiosk Browser (kweb) system.
# It's main purpose is to supply a faster method to extract web video URLs
# for use with omxplayerGUI and kweb(3)
# version 1.7.9.9

# This program was inspired by
# https://github.com/jaimeMF/youtube-dl-api-server
# and uses a small part of it's code

# Copyright 2015-2016 by Guenter Kreidl
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import os,sys,time,signal,subprocess,threading,random,socket
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
#from SocketServer import ThreadingMixIn
import SocketServer
from urllib import unquote,quote

ytdldir = os.path.expanduser('~')+os.sep+'youtube-dl'
if os.path.exists(ytdldir):
    sys.path.insert(0,ytdldir)
try:
    import youtube_dl
except:
    print "No github youtube-dl version found."
    print "Use ginstall-ytdl to install it."
    sys.exit(0)
# Global options, overwritten by kwebhelper_settings
# from omxplayerGUI
omxplayer_in_terminal_for_video = True
omxplayer_in_terminal_for_audio = True
audioextensions = ['mp3','aac','flac','wav','wma','cda','ogg','ogm','ac3','ape']
videoextensions = ['asf','avi','mpg','mp4','mpeg','m2v','m1v','vob','divx','xvid','mov','m4v','m2p','mkv','m2ts','ts','mts','wmv','webm','flv']
useAudioplayer = True
useVideoplayer = True

# Server options
ytdl_server_port = '9192'
ytdl_server_host = 'localhost'
ytdl_server_format = 'best'

# Media frontend options
player_directories = {}
player_css = ''
enable_remote = False
# End of settings options

settings = '/usr/local/bin/kwebhelper_settings.py'
ytdl_params = {'format': ytdl_server_format,'cachedir': False, 'quiet':True,'ignoreerrors':True}
ydl = None
port = int(ytdl_server_port)
alternate_player = ''
embedded = False

default_style = '''<style>
body
{
background-color: rgb(255,255,255);
font-weight: normal;
font-style: normal;
font-family: SansSerif;
font-size: 12pt;
line-height: 120%;
}
h1
{
font-weight: bold;
font-family: SansSerif;
font-style: normal;
font-size: 1.6em;
line-height: 160%;
margin: 0;
}
h2
{
font-weight: bold;
font-style: normal;
font-family: SansSerif;
font-size: 1.5em;
line-height: 150%;
margin: 0;
}
h3
{
font-weight: bold;
font-style: normal;
font-family: SansSerif;
font-size: 1.4em;
line-height: 140%;
margin: 0;
}
h4
{
font-weight: bold;
font-family: SansSerif;
font-style: normal;
font-size: 1.3em;
line-height: 130%;
margin: 0;
}
h5
{
font-weight: bold;
font-family: SansSerif;
font-style: normal;
font-size: 1.2em;
line-height: 130%;
margin: 0;
}
h6
{
font-weight: bold;
font-style: normal;
font-family: SansSerif;
font-size: 1.1em;
line-height: 130%;
margin: 0;
}
button, input, textarea
{
font-style: normal;
font-family: SansSerif;
font-size: 12pt;
}
iframe
{
border-width: 0px;
}
</style>
'''

base_page = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html><head><meta content="text/html; charset=UTF-8" http-equiv="content-type">
<meta http-equiv="cache-control" content="max-age=0" />
<meta http-equiv="cache-control" content="no-cache" />
<meta http-equiv="expires" content="0" />
<meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />
<meta http-equiv="pragma" content="no-cache" />
<title>$title$</title>
$style$
$script$
</head>
<body>
$content$
</body></html>'''

index_content = '''$localmedia$
<h5>Web Video</h5>
<form enctype="application/x-www-form-urlencoded"  method="get" action="/play">Enter Video Website URL:<br>
  <input size="50" name="url"><br>
  <input value="Extract &amp; Play" type="submit">
</form>
<br>
<h5>Direct Video</h5>
<form enctype="application/x-www-form-urlencoded"  method="get" action="/dplay">Enter URL or File Path:<br>
  <input size="50" name="url"><br>
  <input value="Play" type="submit">
</form>
<br>
<!--control-->
<br>
'''

control_button = '<a href="/control"><button>Media Control</button></a><br>'

play_content = '''<h4>$$play$$</h4>
<a href="javascript:history.back()"><button>Go Back</button></a>
$remotecontrol$
'''

play_content_remote = '''<h4>$$play$$</h4>
<button onclick="javascript: document.location=document.referrer">Go Back</button>
$remotecontrol$
'''

remote_content = '''<hr><h4>Remote Control</h4>
<a href="/omxcmd?cmd=pause" target="command""><button>Play / Pause</button></a>
<a href="/omxcmd?cmd=stop" target="command""><button>Stop / Next</button></a>
<a href="/stopall" target="command""><button>Stop All</button></a><br>
<h5>Seek</h5>
<a href="/omxcmd?cmd=seek&value=10000000" target="command""><button>+10 sec.</button></a>
<a href="/omxcmd?cmd=seek&value=60000000" target="command""><button>+1 min.</button></a>
<a href="/omxcmd?cmd=seek&value=600000000" target="command""><button>+10 min.</button></a><br>
<a href="/omxcmd?cmd=seek&value=-10000000" target="command""><button>-10 sec.</button></a>
<a href="/omxcmd?cmd=seek&value=-60000000" target="command""><button>-1 min.</button></a>
<a href="/omxcmd?cmd=seek&value=-600000000" target="command""><button>-10 min.</button></a><br>
<input type="range" min="0" max="99" value="0" step ="0.2" style="width: 260px" onchange="moveto(this.value)">
<h5>Volume</h5>
<a href="/omxcmd?cmd=volumeup" target="command"><button>+3 db</button></a>
<a href="/omxcmd?cmd=volumedown" target="command"><button>-3 db</button></a><br>
<input type="range" min="0.0" max="1.5" value="1" step="0.125" style="width: 260px" onchange="setvol(this.value)">
<iframe src="/empty.html" width="0" height="0" name="command" style="border-width: 0px;"></iframe>
'''

remote_script = '''<script type="text/javascript">
var vtimer = 0;
var mtimer = 0;
var atimer = 0;
function setvol(val) {
if (vtimer != 0) { clearTimeout(vtimer); } 
vtimer = setTimeout(function () { setvold(val); }, 200);
}
function moveto(val) {
if (mtimer != 0) { clearTimeout(mtimer); } 
mtimer = setTimeout(function () { movetod(val); }, 200);
}
function setalpha(val) {
if (atimer != 0) { clearTimeout(atimer); } 
atimer = setTimeout(function () { setalphad(val); }, 200);
}
function setvold(val) {
document.getElementsByName("command")[0].src = "/omxcmd?cmd=volume&value="+val;
vtimer = 0;
}
function movetod(val){
document.getElementsByName("command")[0].src = "/omxcmd?cmd=moveto&value="+val;
mtimer = 0;
}
function setalphad(val){
document.getElementsByName("command")[0].src = "/omxcmd?cmd=setalpha&value="+val;
atimer = 0;
}
</script>
'''

index_page = ''
play_page = ''
dir_page = ''

class SimpleYDL(youtube_dl.YoutubeDL):
    def __init__(self, params):
        super(SimpleYDL, self).__init__(params)
        self.add_default_info_extractors()

def flatten_result(result):
    r_type = result.get('_type', 'video')
    if r_type == 'video':
        videos = [result]
    elif r_type == 'playlist':
        videos = []
        for entry in result['entries']:
            videos.extend(flatten_result(entry))
    elif r_type == 'compat_list':
        videos = []
        for r in result['entries']:
            videos.extend(flatten_result(r))
    return videos

def start_player(url,opts):
    global preset,alternate_player
    if alternate_player:
        pargs = [alternate_player]
    else:
        pargs = ['omxplayergui']
        if opts:
            pargs.append('--opts='+opts)
        if preset:
            pargs.append('--preset='+preset)
    proc = subprocess.Popen(pargs + [url])
    try:
        os.waitpid(proc.pid,0)
    except:
        pass

def play_video(url,opts):
    if embedded and not alternate_player and not opts:
        sys.stdout.write(url+'\n')
        sys.stdout.flush()
    else:
        t = threading.Timer(0,start_player,args=[url,opts])
        t.daemon = True
        t.start()

def write_flag():
    path = os.path.expanduser('~') + '/.ytdl_server_running'
    f = file(path,'wb')
    f.close()

def delete_flag():
    path = os.path.expanduser('~') + '/.ytdl_server_running'
    if os.path.exists(path):
        os.remove(path)

def get_video(url,firsturi=False):
    global ydl
    res = u''
    try:
        info = ydl.extract_info(url, download=False)
        videos = flatten_result(info)
        if firsturi:
            if videos[0].has_key('url'):
                res = videos[0]['url']
            if videos[0].has_key('title'):
                res += '\n'+videos[0]['title']
        else:
            for v in videos:
                if v.has_key('title'):
                    res += v['title']+'\n' 
                if v.has_key('url'):
                    res += v['url']+'\n'
    except:
         pass
    return res.strip('\n')
    
def usage():
    print "ytdl_server.py [-p=port] [-f=formatstring] [-t=preset] [-s=style] [a-=alternate_player]"

def checknumbers(arr):
    res = True
    for n in arr:
        try:
            x = float(n)
        except:
            res = False
            break
    return res

def send_dbus(cmd,value,dbusadr):
    simplecmds = ['position','canseek','duration','aspect','pause','stop','hidevideo','unhidevideo','volumeup','volumedown','togglesubtitles','hidesubtitles','showsubtitles']
    valuecmds = ['volume','seek','setposition','setalpha','moveto']
    pargs = []
    db = subprocess.Popen(['pgrep','omxplayer.bin'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (res,err) = db.communicate()
    if (not res) or err:
        return 'no player'
    if cmd in simplecmds:
        pargs = ['dbuscontrolm.sh',dbusadr,cmd]
    elif cmd in valuecmds and value and checknumbers([value]):
        if cmd == 'moveto':
            scale = float(value)
            if scale >= 0 and scale <= 99.9:
                pargs2 = ['dbuscontrolm.sh',dbusadr,'duration']
                db = subprocess.Popen(pargs2,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                (res,err) = db.communicate()
                if res and (not err):
                    try:
                        value = str(int(res)*scale/100)
                        cmd = 'setposition'
                        pargs = ['dbuscontrolm.sh',dbusadr,cmd,value]
                    except:
                        pass
        else:
            pargs = ['dbuscontrolm.sh',dbusadr,cmd,value]
    elif cmd in ['setvideopos','setvideocroppos'] and value:
        values = value.split(',')
        if len(values) == 4 and checknumbers(values):
            pargs = ['dbuscontrolm.sh',dbusadr,cmd] + values
    elif cmd == 'setaspectmode' and value in ['letterbox', 'fill', 'stretch']:
        pargs = ['dbuscontrolm.sh',dbusadr,cmd,value]
    if pargs:
        db = subprocess.Popen(pargs,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (res,err) = db.communicate()
        if err:
            return 'error'
        elif res:
            return res.strip()
        else:
            return 'ok'
    else:
        return 'error'

def expandpath(path):
    if path.startswith('/'):
        return ''
    pathl = path.split('/',1)
    rootpath = pathl[0]
    if rootpath not in player_directories:
        return ''
    if len(pathl) > 1:
        fullpath = os.path.join(player_directories[rootpath],pathl[1])
    else:
        fullpath = player_directories[rootpath]
    if not os.path.exists(fullpath):
        return ''
    if not os.path.isdir(fullpath):
        return ''
    return fullpath

def get_m3u(path,mode):
    fullpath = expandpath(path)
    if not fullpath:
        return ''
    media = []
    extlist = audioextensions + videoextensions
    if mode in ['o','s']:
        for f in os.listdir(fullpath):
            ff = os.path.join(fullpath,f)
            if os.path.isdir(ff):
                pass
            else:
                if f.split('.')[-1].lower() in extlist:
##                    media.append(ff)
                    if alternate_player == 'vlc':
                        media.append('file://' + ff.replace(' ','%20'))
                    else:
                        media.append(ff)
    elif mode in ['or','sr']:
        for root, dirs, files in os.walk(fullpath):
            for f in files:
                if f.lower().split('.')[-1] in extlist:
##                    media.append(os.path.join(root, f))
                    if alternate_player == 'vlc':
                        media.append('file://' + os.path.join(root, f).replace(' ','%20'))
                    else:
                        media.append(os.path.join(root, f))
    if not media:
        return ''
    if mode in ['o','or']:
        media.sort(key=str.lower)
    elif mode in ['s','sr']:
        count = len(media)
        for i in xrange(count):
            j = random.randrange(count)
            media[i], media[j] = media[j], media[i]
    return '\n'.join(media).decode('utf-8')

def get_dirpage(path):
    fullpath = expandpath(path)
    if not fullpath:
        return ''
    dirs = []
    files = []
    playlists = []
    extlist = audioextensions + videoextensions
    for f in os.listdir(fullpath):
        ff = os.path.join(fullpath,f)
        if os.path.isdir(ff) and not f.startswith('.'):
            dirs.append(os.path.join(path,f))
        else:
            ext = f.split('.')[-1].lower()
            if ext in extlist:
                files.append(ff)
            elif ext in ['m3u','m3u8','pls']:
                playlists.append(ff)
    dirs.sort(key=str.lower)
    files.sort(key=str.lower)
    playlists.sort(key=str.lower)
    dirheader = '<h4><a href="/index">Home</a> / '
    pathl = path.split('/')
    if len(pathl) == 1:
        dirheader += pathl[0]
    else:
        currentpath = ''
        for pindex in range(0,len(pathl)-1):
            currentpath = os.path.join(currentpath,pathl[pindex])
            dirheader += '<a href="/dir?path='+quote(currentpath)+'">'+pathl[pindex]+'</a> / '
        dirheader += pathl[-1] + '</h4>'
    dircontent = ''
    if dirs:
        dircontent += '<h5>Directories</h5>'
        for d in dirs:
            dircontent += '<a href="/dir?path='+quote(d)+'">'+d.split('/')[-1]+'</a><br>\n'
    if files:
        dircontent += '<h5>Media</h5>'
        for f in files:
            dircontent += '<a href="/dplay?url='+quote(f)+'">'+f.split('/')[-1]+'</a><br>\n'
    if files or dirs:
        dircontent += '<br><h6>Play: '
        if files:
            dircontent += '<a href="/dplay?url=http://localhost:'+ytdl_server_port+'/playlist?path='+quote(path)+'&mode=o&name=pl.m3u">Files</a>'
        if dirs:
            dircontent += ' <a href="/dplay?url=http://localhost:'+ytdl_server_port+'/playlist?path='+quote(path)+'&mode=or&name=pl.m3u">Recursive</a>'
        dircontent += '</h6><h6>Shuffle: '
        if files:
            dircontent += '<a href="/dplay?url=http://localhost:'+ytdl_server_port+'/playlist?path='+quote(path)+'&mode=s&name=pl.m3u">Files</a>'
        if dirs:
            dircontent += ' <a href="/dplay?url=http://localhost:'+ytdl_server_port+'/playlist?path='+quote(path)+'&mode=sr&name=pl.m3u">Recursive</a>'
        dircontent += '</h6><br>'
    if playlists:
        dircontent += '<h5>Playlists</h5>'
        for f in playlists:
            dircontent += '<a href="/dplay?url='+quote(f)+'">'+f.split('/')[-1]+'</a><br>\n'
    return dir_page.replace('$dirheader$',dirheader.decode('utf-8')).replace('$dircontent$',dircontent.decode('utf-8')).replace('$title$',path.split('/')[-1].decode('utf-8'))

def stopall():
    db = subprocess.Popen(['pgrep','omxplayergui'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (res,err) = db.communicate()
    if res and not err:
        db = subprocess.Popen(['killall','omxplayergui'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (r,e) = db.communicate()
    db = subprocess.Popen(['pgrep','omxplayer.bin'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (res,err) = db.communicate()
    if res and not err:
        db = subprocess.Popen(['killall','omxplayer.bin'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (r,e) = db.communicate()
    return 'OK'

class ytdlHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def do_GET(s):
        global alternate_player
        rstring = u''
        redir = False
        stop = False
        path = s.path
        ctype = "text/plain"
        if not path:
            path = '/index'
        if path in ['/','/index','/index.html']:
            if not alternate_player:
                curplayer = 'omxplayerGUI'
            else:
                curplayer = 'VLC'
            rstring = index_page.replace('$player$',curplayer)
            ctype = "text/html"
        elif path == '/switchplayer':
            if not alternate_player:
                alternate_player = 'vlc'
                curplayer = 'VLC'
            else:
                alternate_player = ''
                curplayer = 'omxplayerGUI'
            rstring = index_page.replace('$player$',curplayer)
            ctype = "text/html"
            
        elif path.startswith('/info?url='):
            url = unquote(path.replace('/info?url=','',1))
            if url and 'http' in url and '://' in url:
                rstring = get_video(url)
        elif path in ['/empty','/empty.html']:
            rstring = u'<html><head></head><body></body></html>'
            ctype = "text/html"
        elif path == '/running':
           rstring = 'OK'
        elif path == '/stopall':
            rstring = stopall()
        elif path == '/stop':
            rstring = base_page.replace('$content$','Shutting down server').replace('$script$','').replace('$title$','Shutting down server')
            ctype = "text/html"
            stop = True
        elif path == '/control':
            rstr = 'Media Control'
            rstring = play_page.replace('$$play$$',rstr).replace('$title$',rstr)
            ctype = "text/html"
        elif path.startswith('/play?url='):
            opts = ''
            playargs = unquote(path.replace('/play?url=','',1))
            if '&omxoptions=' in playargs:
                url = playargs.split('&omxoptions=')[0]
                opts = playargs.split('&omxoptions=')[1]
            else:
                url = playargs               
            if url and 'http' in url: # and '://' in url:
                if embedded and not alternate_player and not opts:
                    sys.stdout.write('ytdl '+url+'\n')
                    sys.stdout.flush()
                    rstr = "Extracting video(s) from: " + url
                else:
                    res = get_video(url,firsturi=True).split('\n')
                    uri = res[0]
                    if len(res) > 1:
                        name = res[1]
                    else:
                        name = '...'
                    if uri:
                        play_video(uri,opts)
                        rstr = "Playing: " + name
                    else:
                        rstr = "No video found!"
                rstring = play_page.replace('$$play$$',rstr).replace('$title$',rstr)
                ctype = "text/html"
        elif path.startswith('/dplay?url='):
            opts = ''
            playargs = unquote(path.replace('/dplay?url=','',1))
            if '&omxoptions=' in playargs:
                url = playargs.split('&omxoptions=')[0]
                opts = playargs.split('&omxoptions=')[1]
            else:
                url = playargs               
            if url and '://' in url:
                play_video(url.replace(' ','%20'),opts)
                rstr = "Playing: " + unquote(url).split('/')[-1].split('?')[0].split('&')[0]
            elif url and url.startswith('/') and os.path.exists(url.replace('+',' ')):
                url = url.replace('+',' ')
                play_video(url,opts)
                rstr = "Playing: " + url.split('/')[-1]
            else: 
                rstr = "Media not found!"
            try:
                rstr = rstr.decode('utf-8')
            except:
                pass
            rstring = play_page.replace('$$play$$',rstr).replace('$title$',rstr)
            ctype = "text/html"

        elif path.startswith('/omxcmd?cmd='):
            cmd = ''
            value = ''
            dbusadr = 'org.mpris.MediaPlayer2.omxplayer'
            rstring = 'error'
            cmdstr = unquote(path.replace('/omxcmd?cmd=','',1))
            if cmdstr:
                cmdl = cmdstr.split('&')
                cmd = cmdl[0]
                if len(cmdl) > 1:
                    for arg in cmdl[1:]:
                        if arg.startswith('value='):
                            value = arg.replace('value=','',1)
                        elif arg.startswith('dbusadr=org.mpris.MediaPlayer2.omxplayer'):
                            dbusadr = arg.replace('dbusadr=','',1)
                if cmd:
                    rstring = send_dbus(cmd,value,dbusadr)
                            
        elif path.startswith('/redir?url='):
            url = unquote(path.replace('/redir?url=','',1))
            if url and 'http' in url and '://' in url:
                res = get_video(url,firsturi=True).split('\n')
                uri = res[0]
                if uri:
                    rstring = uri
                    redir = True

        elif path.startswith('/dir?path='):
            path = unquote(path.replace('/dir?path=','',1))
            if path:
                rstring = get_dirpage(path)
                if rstring:
                    ctype = "text/html"

        elif path.startswith('/playlist?path='):
            mode = ''
            m3uargs = unquote(path.replace('/playlist?path=','',1).replace('&name=pl.m3u','',-1))
            if m3uargs:
                m3ul = m3uargs.split('&mode=')
                path = m3ul[0]
                if len(m3ul) > 1:
                    mode =  m3ul[1]
                if not mode or mode not in ['o','s','or','sr']:
                    mode = 'o'
                if path:
                    rstring = get_m3u(path, mode)
                    if rstring:
                        ctype = "audio/x-mpegurl"

        if rstring:
            if redir:
                s.send_response(302)
                s.send_header("Content-Length", "0")
                s.send_header("Location",rstring)
                s.end_headers()
                s.wfile.write('')
            else:
                s.send_response(200)
                s.send_header("Content-Type", ctype)
                try:
                    out = rstring.encode('utf-8')
                except:
                    out = rstring
                s.send_header("Content-Length", str(len(out)))
                s.send_header('Last-Modified', time.strftime("%a, %d %b %Y %H:%M:%S GMT",time.gmtime()))
                s.end_headers()
                s.wfile.write(out)
        else:
            s.send_response(404)
            s.send_header("Content-Type", ctype)
            s.send_header("Content-Length", '0')
            s.end_headers()
        if stop:
            if not alternate_player and not embedded:
                stopall()
            tim = threading.Timer(1,stop_server,args=[s.server])
            tim.daemon = True
            tim.start()
##            time.sleep(0.5)
##            s.server.shutdown()

def stop_server(server):
    server.shutdown()

class mixin(SocketServer.ThreadingMixIn):
    daemon_threads = True

class MultiThreadedHTTPServer(mixin,SocketServer.TCPServer):
    allow_reuse_address = True

preset = ''
if len(sys.argv) > 1:
    for opt in sys.argv[1:]:
        if opt.startswith('-t='):
            pr = opt.replace('-t=','',1)
            if pr and os.path.exists('/usr/local/share/kweb/'+pr+'.preset'):
                preset = pr
                settings = '/usr/local/share/kweb/'+pr+'.preset'
                break

if os.path.exists(settings):
    try:
        execfile(settings)
    except:
        pass

if len(sys.argv) > 1:
    for opt in sys.argv[1:]:
        if opt in ['-h','--help']:
            usage()
            sys.exit(0)
        elif opt.startswith('-p='):
            pt = opt.replace('-p=','',1)
            if pt:
                try:
                    port = int(pt)
                    ytdl_server_port = pt
                except:
                    pass
        elif opt.startswith('-f='):
            fm = opt.replace('-f=','',1)
            if fm:
                ytdl_server_format = fm
        elif opt.startswith('-s='):
            sm = opt.replace('-s=','',1)
            if sm and sm.endswith('.css'):
                player_css = sm
        elif opt.startswith('-a='):
            am = opt.replace('-a=','',1)
            if am and am == 'vlc':
                alternate_player = am
        elif opt == '-embedded':
            embedded = True

style = default_style
if player_css and os.path.exists('/usr/local/share/kweb/'+player_css):
    try:
        f = file('/usr/local/share/kweb/'+player_css,'rb')
        stl = f.read().decode('utf-8')
        f.close()
        style = '<style>\n'+stl+'\n</style>'
    except:
        pass
base_page = base_page.replace('$style$',style)
localmedia = u''
if player_directories:
    names = player_directories.keys()
    names.sort()
    for name in names:
        path = player_directories[name]
        try:
            if os.path.exists(path) and os.path.isdir(path):
                localmedia += '<a href="/dir?path='+quote(name).replace(' ','%20')+'">'+name+'</a> '
        except:
            pass
    if localmedia:
        localmedia = '<h4>Local Media: ' + localmedia.strip() + '<h4><hr>'
index_content = index_content.replace('$localmedia$',localmedia)
if embedded:
    ptitle = 'omxplayerGUI Web Interface'
else:
    ptitle = 'Youtube-DL-Server'
    index_content += 'Current player: $player$ <a href="/switchplayer"><button>Switch Player</button></a><br><br>'
    index_content += '<a href="/stop"><button>Stop Server</button></a>'
    
index_page = base_page.replace('$script$','').replace('$title$',ptitle).replace('$content$',index_content)
##if not embedded:
##    index_page += '<a href="/stop"><button>Stop Server</button></a>'
dir_page = base_page.replace('$script$','').replace('$content$','$dirheader$\n$dircontent$')
if enable_remote and not(omxplayer_in_terminal_for_video or omxplayer_in_terminal_for_audio or useAudioplayer or useVideoplayer):
    play_content_remote =  play_content_remote.replace('$remotecontrol$',remote_content)
    play_page = base_page.replace('$script$',remote_script).replace('$content$',play_content_remote)
    index_page = index_page.replace('<!--control-->',control_button)
else:
    play_content =  play_content.replace('$remotecontrol$','')
    play_page = base_page.replace('$script$','').replace('$content$',play_content)
    index_page = index_page.replace('<!--control-->','')

try:
    port = int(ytdl_server_port)
except:
    port = 9192
if ytdl_server_format:
    ytdl_params['format'] = ytdl_server_format

ydl = SimpleYDL(ytdl_params)
server_address = ('', port)

if port == 9192 and ytdl_server_host == 'localhost':
    write_flag()

try:
    httpd = MultiThreadedHTTPServer(server_address,ytdlHandler)
    if not embedded:
        print "Starting youtube-dl-server on port " + str(port)
except:
    if not embedded:
        print 'There is already a server instance running'
    delete_flag()
    sys.exit(0)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
try:
    httpd.socket.shutdown(socket.SHUT_RDWR)
    httpd.socket.close()
except:
    pass
try:
    httpd.server_close()
except:
    pass
if not embedded:
    print 'Shutting down server'
delete_flag()
sys.exit(0)
