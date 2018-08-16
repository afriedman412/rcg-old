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
from IPython.display import clear_output

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

# returns a bio or None if none exists
def searchy(name, group=False, test=True):
    # remove accents
    name = unidecode.unidecode(name)
    
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

def write_gender(name, zult):
    try:
        len(zult) == 2
    except TypeError:
        print('zult type error')
        return
    conn = sqlite3.connect('rcg_test.db')
    c = conn.cursor()
    if zult[0] > zult[1]:
        c.execute('INSERT INTO genders VALUES (name, "M")')
        conn.commit()
    elif zult[1] > zult[0]:
        c.execute('INSERT INTO genders VALUES (name, "F")')
        conn.commit()
    conn.close()
    return

def pull_gender_sql(artist, week='this_week', test=True):
    if test:
        print(artist)
    q = (artist,)
    
    conn = sqlite3.connect('rcg_test.db')
    c = conn.cursor()
    
    gen_test = c.execute('SELECT gender FROM genders WHERE name=?', q)
    try:
        gender = gen_test.fetchone()[0]
    except TypeError:
        gender = None
    
    gp_test = c.execute('SELECT members FROM groups WHERE name=?', q)
    try:
        members = gp_test.fetchone()[0]
    except TypeError:
        members = None
    
    conn.commit()
    
    if test:
        print(f'gender: {gender}')
        print(f'members: {members}')
    
    # check if known group, pull members and re-run
    if members != None:
        if test:
            print('known group')
        for m in (members).split(', '):
            if test:
                print(f'member: {m}')
            conn.close()
            pull_gender_sql(m, week=week, test=test)
        return

    # if no gender...
    if gender not in ['M', 'F', 'missing']:
        # check group status
        if test:
            print('check group status')
        new_members = searchy(artist, group=True)

        # if it's a group, add new members to database and re-run for all members
        if new_members != None:
            if test:
                print('new group')
            t = (artist, ', '.join(new_members))
            c.execute('INSERT INTO groups VALUES (?, ?)', t)
            conn.commit()
            for m in new_members:
                conn.close()
                pull_gender_sql(m, week=week, test=test)
            return

        else:
            # pull bio
            bio = searchy(artist)

            # if no bio, tag as None
            if bio == None:
                if test:
                    print('no bio')
                t = (artist, 'missing')

            # otherwise, gender
            else:
                if test:
                    print('running gender')
                zult = pnoun_test(bio)

                # if it's a tie, tag as None
                if zult[0] == zult[1]:
                    t = (artist, 'missing')

                # otherwise score it   
                elif zult[0] > zult[1]:
                    if test:
                        print('male!')
                    t = (artist, 'M')

                elif zult[1] > zult[0]:
                    if test:
                        print('female!')
                    t = (artist, 'F')

        if test:
            print('adding gender')
        c.execute('INSERT INTO genders VALUES (?, ?)', t)
        conn.commit()
        
        if test:
            print('updating counts')
        t2 = (artist, 1,)
        c.execute('INSERT INTO stats (name, {0}) VALUES (?,?)'.format(week), t2)
        conn.close()
        return
    
    # if there is gender, return it
    else:
        if test:
            print('poop')
        master_test = c.execute('SELECT name FROM stats WHERE name=?', q)
        try:
            gender = master_test.fetchone()[0]
            c.execute('UPDATE stats SET {0}= {0} + 1 WHERE name=?;'.format(week), (artist,))
        except TypeError:
            t2 = (artist, 1,)
            c.execute('INSERT INTO stats (name, {0}) VALUES (?,?)'.format(week), t2)
        conn.commit()
        conn.close()
        return

def sql_rcg(week, test=False):
    clear_output()
    conn1 = sqlite3.connect('rcg_test.db')
    c1 = conn1.cursor()
    week = week
    c1.execute('ALTER TABLE stats ADD COLUMN {0} INTEGER DEFAULT 0'.format(week))
    conn1.commit()

    trax = []
    for n in range(50):

        # pull artist name
        a = rc_jd['tracks']['items'][n]['track']['artists'][0]['name']

        # collect track names for feature parsing
        trax.append(rc_jd['tracks']['items'][n]['track']['name'])

        # process genders
        pull_gender_sql(a, week=week, test=test)


    # process names parsed from features
    for t in trax:
        if 'feat.' in t:
            feat = re.findall('(?<=feat. ).*[^)]', t)
        elif 'ft.' in t:
            feat = re.findall('(?<=ft. ).*[^)]', t)
        else:
            continue
        for n in re.split('[,&]', feat[0]):
            name = n.strip()
            if test:
                print(f're-running {name}')
            pull_gender_sql(name, week=week, test=test)

    ### sum stats across tables
    data = c1.execute('SELECT name, {0} FROM stats WHERE {0} > 0'.format(week))
    conn1.commit()

    total = 0
    M_tot = 0
    F_tot = 0
    X_tot = 0

    for d in data.fetchall():
        t = d[0]
        num = d[1]
        gen_call = c1.execute('SELECT gender FROM genders WHERE name =?', (t,))
        gender = gen_call.fetchone()[0]

        total += num

        if gender == 'F':
            F_tot += num
        elif gender == 'M':
            M_tot += num
        else:
            X_tot += num

    conn1.close()
    # print(f'male credits: {M_tot}')
    # print(f'female credits: {F_tot}')
    # print(f'missing credits: {X_tot}')
    # print(f'total credits: {total}')
    return(M_tot, F_tot, X_tot, total)