#!/usr/bin/python

import json
import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import urllib3
import certifi
import cgi, cgitb 

from rcg_func import pnoun_test, searchy, sql_rcg

# prep 'http'
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

# credentialing
spot_id = '4263d6a900e94f1599974e3c90c28aa5'
spot_sec = '26333e019ca149a4b8f0f1633168dddd'
# rc_url = 'http://api.spotify.com/v1/users/spotify/playlists/37i9dQZF1DX0XUsuxWHRQd'
client_credentials_manager = SpotifyClientCredentials(spot_id, spot_sec)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# addressing
uri = 'spotify:user:spotify:playlist:37i9dQZF1DX0XUsuxWHRQd'
username = uri.split(':')[2]
playlist_id = uri.split(':')[4]
results = sp.user_playlist(username, playlist_id)
rc_j = json.dumps(results, indent=4)
rc_jd = (json.loads(rc_j))

# cgi prep
form = cgi.FieldStorage()
week_in = form.getvalue('week')

# gender counts
counts = sql_rcg(week=week_in, test=False)

print("Content-type:text/html\r\n\r\n")
print("<html>")
print("<head>")
print("<title>RCG</title>")
print("</head>")
print("<body>")
print("<h2> Male credits: ?</h2>", counts[0])
print("<h2> Female credits: ?</h2>", counts[1])
print("<h2> Undefined credits: ?</h2>", counts[2])
print("<h2> Total credits: ?</h2>", counts[3])
print("</body>")
print("</html>")
