import pandas as pd
import numpy as np
import requests
import urllib
import urllib3
import certifi
import json
import sqlite3
import os
import re

from bs4 import BeautifulSoup
import unidecode

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# prep 'http'
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

spot_id = '4263d6a900e94f1599974e3c90c28aa5'
spot_sec = '26333e019ca149a4b8f0f1633168dddd'
rc_url = 'http://api.spotify.com/v1/users/spotify/playlists/37i9dQZF1DX0XUsuxWHRQd'

client_credentials_manager = SpotifyClientCredentials(spot_id, spot_sec)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

uri = 'spotify:user:spotify:playlist:37i9dQZF1DX0XUsuxWHRQd'
username = uri.split(':')[2]
playlist_id = uri.split(':')[4]

results = sp.user_playlist(username, playlist_id)
rc_j = json.dumps(results, indent=4)
rc_jd = (json.loads(rc_j))

ats = {}
trax = []
for n in range(50):
    a = rc_jd['tracks']['items'][n]['track']['artists'][0]['name']
    trax.append(rc_jd['tracks']['items'][n]['track']['name'])
    
    if a not in ats:
        ats[a] = {'count':1}
    else:
        ats[a]['count'] += 1
        
for t in trax:
    if 'feat.' in t:
        feat = re.findall('(?<=feat. ).*[^)]', t)
    elif 'ft.' in t:
        feat = re.findall('(?<=ft. ).*[^)]', t)
    else:
        continue
    for n in re.split('[,&]', feat[0]):
        name = n.strip()
        if name not in ats:
            ats[name] = {'count':1}
        else:
            ats[name]['count'] += 1
    
group_members = False
for name in ats.keys():
#     print(name)
    
    # pull bio
    bio = searchy(name)
    
    # if no bio, tag as None
    if bio == None:
        ats[name]['gender'] = None
    
    # else run pronoun test
    else:
        g_zult = pnoun_test(bio)
#         print(g_zult)
    
        # if tied, pull members to re-run
        if g_zult[0] == g_zult[1]:
            members = searchy(name, group=True)
            if not group_members:
                group_members = []
            for m in members:
                group_members.append(unidecode.unidecode(m))
            ats[name]['gender'] = None
            continue
         
        # else, score and tag
        else:
            if g_zult[0] > g_zult[1]:
                ats[name]['gender'] = 'M'
            elif g_zult[1] > g_zult[0]:
                ats[name]['gender'] = 'F'
                
# if group_members, re-run
if group_members:
    for name in group_members:
        
        # if already in list, just advance counter
        if name in ats:
            ats[name]['count'] += 1
            
        # else, run the whole damn gendering script
        else:
            # pull bio
            bio = searchy(name)

            # if no bio, tag as None
            if bio == None:
                ats[name]['gender'] = None
                
            # else run pronoun test
            # i guess ill have to figure out if groups end up here at some point but wtv
            else:
                g_zult = pnoun_test(bio)
                if g_zult[0] > g_zult[1]:
                    ats[name] = {'count':1, 'gender':'M'}
                elif g_zult[1] > g_zult[0]:
                    ats[name] = {'count':1, 'gender':'F'}
    
# calculate stats
total = 0
M_tot = 0
F_tot = 0
for k, v in ats.items():
    c = v['count']
    total += c
    if v['gender'] == 'M':
        M_tot += c
    elif v['gender'] == 'F':
        F_tot += c
    
print(f'male credits: {M_tot}')
print(f'female credits: {F_tot}')
print(f'total credits: {total}')

def pnoun_test(t):
    m_count = 0
    f_count = 0
    m = ['he', 'him', 'his', 'himself']
    f = ['she', 'her', 'hers', 'herself']
    for w in t.split():
        if w in m: 
            m_count += 1
        if w in f:
            f_count += 1
    return([m_count, f_count])

# returns a bio or NaN if none exists
def searchy(name, group=False):
    # execute search
    url = f'https://www.allmusic.com/search/artists/{"%20".join(name.split())}'

    # make request
    r = http.request('GET', url)

    # if response is good, scrape biography
    if r.status == 200:
        soup = BeautifulSoup(r.data, 'lxml')
        link = soup.find('div', {'class':'name'}).find('a')['href']
        
        r2 = http.request('GET', (link + '/biography/'))
        if r2.status == 200:
            soup2 = BeautifulSoup(r2.data, 'lxml')
            
            # if group, pull group members instead of bio
            if group:
                try:
                    members = []
                    for m in soup2.find('div', {'class':'group-members'}).find_all('a'):
                        members.append(m.text.strip())
                    return members
                
                # return NaN if no members
                except AttributeError:
                    return None
            
            # else pull bio
            else:
                try:
                    return soup2.find('div', {'itemprop':'reviewBody'}).text

                # return NaN if no biography entry
                except AttributeError:
                    return None

