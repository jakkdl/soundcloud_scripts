#!/bin/python3
# -*- coding: utf-8 -*-
import soundcloud
import math
import wget
import os.path
import sys
import eyed3
import pdb
import sqlite3
import argparse

status_table = {'in_database': 0, #1
        'downloaded': 1, #2
        'pruned': 2, #4
        'awesome': 3} #8

basepath = '/data/Media/music/soundcloud_stream'
mpd_basepath = '/data/Media/music'

def download_stream(client, conn, activities, args, count=1):
    db_cursor = conn.cursor()
    for i in range(count):
        for activity in activities.collection:
            #print(activity.type.ljust(len('playlist-repost')+1),end='')
            origin = activity.origin
            
            try:
                if 'track' in activity.type:
                    download_track(client, db_cursor, origin.obj,
                                   activity.type, args)
                elif 'playlist' in activity.type:
                    download_playlist(client, db_cursor, origin.uri,
                                      activity.type, args)
            except:
                print(sys.exc_info())

        next_activity = activities.next_href.split('=')[-1]
        activities = client.get('me/activities/all',
                cursor=next_activity, limit=20)
        conn.commit()
    print('')

    return activities

'''
def add_stream(client, cursor, activities, count=1):
    for i in range(count):
        for activity in activities.collection:
            origin = activity.origin
            
            if 'track' in activity.type:
                add_track(client, origin.obj)
            elif 'playlist' in activity.type:
                add_playlist(client, origin.uri)
        next_activity = activities.next_href.split('=')[-1]
        activities = client.get('me/activities/all',
                cursor=next_activity, limit=20)
    return activities
'''
def download_track(client, cursor, track, track_type, args):
    try:
        stream_url = client.get(track['stream_url'],
            allow_redirects=False)
    except:
        print('failed')
        return False

    url = stream_url.location
    title = clean(track['title'])
    print(title, end=' ', flush=True)
    base = os.path.join(basepath,
            'music',
            track['user']['username'])
    path = os.path.join(base, title + '.mp3')
    os.makedirs(base, exist_ok=True)
    track_status = get_track_status(cursor, track['id'])
    if not track_status['in_database']:
        insert_track(cursor, track, track_type=track_type)
        print('added to database')
    

    if track_status['downloaded']:
        if not os.path.isfile(path) and not track_status['pruned']:
            print('missing file, adding prune and removing downloaded')
            set_track_status(cursor, track['id'], {'pruned':1, 'downloaded':0})
            #raise IndexError('downloaded but missing file (and not pruned),', track)
    elif os.path.isfile(path):
        set_track_status(cursor, track['id'], {'downloaded': True})
        tag_track(track, path)
        print('added missing downloaded status to database')
    elif not track_status['pruned'] and args.download:
        print(track['created_at'], end='\n\n')
        download(url, path)
        print('downloaded')
        tag_track(track, path)
        set_track_status(cursor, track['id'], {'downloaded': True})
    return path

def clean(string):
    return string.replace('/', '_')

#TODO: add genre?
def tag_track(sc_track, path):
    audiofile = eyed3.load(os.path.abspath(path))
    audiofile.initTag()

    audiofile.tag.artist = sc_track['user']['username']
    audiofile.tag.title = sc_track['title']
    audiofile.tag.album = str(sc_track['id'])
    date = sc_track['created_at']
    date = clean_date(date)
    date = date.replace('/', '-')
    audiofile.tag.release_date = eyed3.core.Date.parse(date)
    audiofile.tag.save()

def clean_date(date):
    return date[:date.find(' +0')]

def download_playlist(client, cursor, list_uri, list_type, args):
    playlist = client.get(list_uri)


    playlist = playlist.obj
    m3ulist = []

    playlist_status = get_playlist_status(cursor, playlist['id'])
    if not playlist_status['in_database']:
        insert_playlist(cursor, playlist, list_type=list_type)
        print('playlist added to database')


    for track in playlist['tracks']:
        try:
            path = download_track(client, cursor, track, list_type, args)
        except:
            print(sys.exc_info())
            continue
        if path is not None:
            insert_playlist_entry(cursor,
                    playlist_id = playlist['id'],
                    track_id = track['id'])
            m3ulist.append(path)

    filename = os.path.join(basepath,
            'playlists',
            playlist['permalink'] + '.m3u')
    #status = get_playlist_status(cursor, 
    if not os.path.isfile(filename):
        print('adding playlist', filename)
        with open(filename, 'x') as f:
            for track in m3ulist:
                print(track, file=f)
    set_playlist_status(cursor, playlist['id'], {'in_database': True, 'downloaded': True})

'''
def insert_playlist_entries_tracks(client, cursor, list_uri):
    playlist = client.get(list_uri)
    m3ulist = []
    for track in playlist.tracks:
        path = download_track(client, track)
        if path is not None:
            m3ulist.append(path)

    filename = clean(playlist.title) + '.m3u'
    if os.path.isfile(filename):
        print('playlist', filename, 'exists')
    else:
        with open(filename, 'x') as f:
            for track in m3ulist:
                print(track, file=f)
'''

    

'''
def download_user(client, name):
    uid = client.get('/resolve?url=https://soundcloud.com/' + name).id
    print(uid)
    activities = client.get('/users/' + str(uid) + '/tracks')
    print(activities)
    for track in activities:
        title = track.title.replace('/', '_')
        print("title", title)
        print("user:", track.user['username'])
        print("created at:", track.created_at)
        print("released at:", track.release_day)
        print("track type:", track.track_type)
        try:
            stream_url = client.get(track.stream_url, allow_redirects=False)
        except:
            print('failed')
            continue
        url = stream_url.location
        path = title + '.mp3'
        if os.path.isfile(path):
            print('Already downloaded')
        else:
            #print('dl')
            download(url, path)
            print('')
            #wget.download(url, path)
            #print(os.path.abspath(path))
            tag_track(track, path)
'''





def download(url, path):
    wget.download(url, path)

def get_followers(name):
    followings=[]
    user = client.get('/users/' + name)
    count = user.followings_count
    loop_count = math.ceil(count/50)
    for i in range(loop_count):
        followings.extend(client.get('/users/' + name + '/followings', offset=50*i))
    return followings

def build_table(following):
    freq_table = {}
    for i in following:
        print(i.permalink, end="")
        followings=get_followers(i.permalink)
        #print(i.permalink)
        for j in followings:
            if j.permalink in freq_table:
                print('+', end="")
                freq_table[j.permalink] += 1
            else:
                print('0', end="")
                freq_table[j.permalink] = 1
        print('')
    return freq_table

def print_table(freq_table, followings):
    magic_from_SO = sorted( ((v,k) for k,v in freq_table.items()), reverse=True)
    follow_list=[]

    for i in followings:
        follow_list.append(i.permalink)


    for i in magic_from_SO:
        if i[0] < 3:
            break
        if i[1] not in follow_list:
            print('+', end="")
        print(i[1] , ":" , i[0])

def database_exists(name='music.db'):
    return os.path.isfile(name)

def get_connection(name='music.db'):
    return sqlite3.connect(name)

def insert_track(cursor,
        track,
        track_type='track',
        track_status=1 << status_table['in_database']):

    cursor.execute('''insert into tracks
    values (
    :id,
    :artist_id,
    :created_at,
    :type,
    :title,
    :pretty_title,
    :status,
    :permalink_url,
    :plays
    )''',
    {'id': track['id'],
        'artist_id': track['user_id'],
        'created_at': clean_date(track['created_at']), 
        'type': track_type,
        'title': track['permalink'],
        'pretty_title': track['title'],
        'status': track_status,
        'permalink_url': track['permalink_url'],
        'plays': 0
        })
    insert_artist(cursor, track['user_id'],
            track['user']['permalink'],
            track['user']['username'])

def insert_playlist(cursor,
        playlist,
        list_type='playlist',
        list_status = 1 << status_table['in_database'] ):

    cursor.execute('''insert into playlists
    values (
    :id,
    :user_id,
    :created_at,
    :type,
    :title,
    :pretty_title,
    :status,
    :track_count
    )''',
    {'id': playlist['id'],
        'user_id': playlist['user_id'],
        'created_at': playlist['created_at'],
        'type': list_type,
        'title': playlist['permalink'],
        'pretty_title': playlist['title'],
        'status': list_status,
        'track_count': playlist['track_count']
        })

def insert_artist(cursor, artist_id, name, pretty_name):
    cursor.execute('''select id from artists where
    id = :who''', {'who': artist_id})

    if cursor.fetchone() is None:
        cursor.execute('''insert into artists values
        (:id, :name, :pretty_name)''',
        {'id': artist_id,
            'name': name,
            'pretty_name': pretty_name})

def insert_playlist_entry(cursor,
        playlist_id,
        track_id):
    cursor.execute('''select * from playlist_entry where
    playlist_id = :playlist_id and
    track_id = :track_id''', {'playlist_id': playlist_id,
        'track_id': track_id})
    
    if cursor.fetchone() is None:
        cursor.execute('''insert into playlist_entry values
        (:playlist_id, :track_id)''',
        {'playlist_id': playlist_id,
            'track_id': track_id})

def check_bit(num, bit):
    return bool(num & (1 << bit))

def set_bit(num, bit, value):
    num &= ~(1 << bit)
    num |= value << bit
    return num

def get_playlist_status(cursor, playlist_id):
    return get_status(cursor, playlist_id, 'playlists')

def get_track_status(cursor, track_id):
    return get_status(cursor, track_id, 'tracks')

def clean_string(string):
    import re
    rx = re.compile('\W+')
    return rx.sub(' ', string).strip()

def get_status(cursor, t_id, table):
    table = clean_string(table)
    cursor.execute('''select status from ''' + table + ''' where
    id = :id''', {'id': t_id})
    status = cursor.fetchone()

    if status is None:
        status = 0
    else:
        status = status[0]
    result = {}
    for key,val in status_table.items():
        result[key] = check_bit(status, val)

    return result

def set_track_status(cursor, track_id, statuses):
    set_table_status(cursor, track_id, statuses, 'tracks')

def set_playlist_status(cursor, playlist_id, statuses):
    set_table_status(cursor, playlist_id, statuses, 'playlists')

def set_table_status(cursor, t_id, statuses, table):
    cursor.execute('''select status from ''' + table + ''' where
    id = :id''', {'id': t_id})
    status = cursor.fetchone()
    if status is None:
        status = 0
    else:
        status = status[0]
    for key,val in statuses.items():
        if key not in status_table:
            raise ValueError('key', key, 'not in status_table')
        status = set_bit(status, status_table[key], int(val))


    cursor.execute('''UPDATE ''' + table + '''
    set status = :status
    where id = :id''', {'status': status,
        'id': t_id})



    
def create_tables(cursor):
    cursor.execute('''create table tracks
    (id PRIMARY KEY, artist_id, created_at, type, title,
    pretty_title, status, permalink_url, plays)''')

    cursor.execute('''create table playlists
    (id PRIMARY KEY, user_id, created_at, type, title,
    pretty_title, status, track_count)''')

    cursor.execute('''create table artists
    (id PRIMARY KEY, name, pretty_name)''')

    cursor.execute('''create table playlist_entry
    (playlist_id, track_id, PRIMARY KEY (playlist_id, track_id))''')





def get_client():
    scdl_client_id='74b69a87904e81fab39f4319552a4c9d',
    return soundcloud.Client(
                client_id='74b69a87904e81fab39f4319552a4c9d',
                client_secret='9b860adc16b41862736db68915ef8e22',
                username='hatten@archlinux.us',
                password='sound[{'
                )
#redirect(client.authorize_url())
#client.authorize_url()


#access_token, expires, scope, refresh_token = client.exchange_token(
            #code=request.args.get('code'))

#def prune_track(cursor, track_id):

def prune_current():
    from musicpd import MPDClient
    client = MPDClient()
    client.timeout = 10
    client.connect('localhost', 6600)
    current_song = client.currentsong()

    if 'album' not in current_song:
        print('album missing')
    track_id = int(current_song['album'])
    path = os.path.join(mpd_basepath, current_song['file'])

    client.next()


    conn = get_connection()
    cursor = conn.cursor()

    status = get_track_status(cursor, track_id)
    if status is None:
        raise IndexError('track_id ' + track_id + ' not found')

    os.remove(path)
    set_track_status(cursor, track_id, {'pruned':1, 'downloaded':0})
    conn.commit()
    client.update()

def awesome():
    from mpd import MPDClient
    client = MPDClient()
    client.timeout = 10
    client.connect('localhost', 6600)
    current_song = client.currentsong()

    if 'album' not in current_song:
        print('album missing')
    track_id = int(current_song['album'])


    conn = get_connection()
    cursor = conn.cursor()

    status = get_track_status(cursor, track_id)
    if status is None:
        raise IndexError('track_id ' + track_id + ' not found')

    set_track_status(cursor, track_id, {'awesome':1})
    conn.commit()
    conn.close()
    client.update()

def watcher():
    from musicpd import MPDClient
    mpdclient = MPDClient()
    mpdclient.connect('localhost', 6600)

    last_tracks = 3*[None]

    while mpdclient.idle('player'):
        current_song = mpdclient.currentsong()

        if 'album' not in current_song:
            continue

        track_id = int(current_song['album'])

        if track_id in last_tracks:
            continue

        sqlconn = get_connection()
        sqlcursor = sqlconn.cursor()
        sqlcursor.execute('''select plays from tracks where
        id = :id''', {'id': track_id})
        plays = sqlcursor.fetchone()

        if plays is None:
            plays = 0
        elif plays[0] is None:
            plays = 0
        else:
            plays = plays[0]

        print(plays)

        plays += 1
        sqlcursor.execute('''UPDATE tracks
        set plays = :plays
        where id = :id''', {'plays': plays,
            'id': track_id})
        sqlconn.commit()
        sqlconn.close()

        last_tracks.pop(0)
        last_tracks.append(track_id)


def download_my_stream(num, args):
    client = get_client()
    activities = client.get('/me/activities/all')
    print("Hi There, %s" % client.get('/me').username)
    download_stream(client=client,
                    conn=get_connection('/home/hatten/Code/python/soundcloud/music.db'),
                    activities=activities, args=args, count=num)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', metavar='cmd', type=str,
            help='command')
    parser.add_argument('--download', action='store_true',
            default=False)
    parser.add_argument('--num', type=int,
            dest='num', default=1)
    args = parser.parse_args()
    #cwd = os.getcwd()
    os.chdir('/home/hatten/Code/python/soundcloud')
    if args.cmd == 'prune':
        prune_current()
    elif args.cmd == 'download':
        download_my_stream(args.num, args)
    elif args.cmd == 'watcher':
        watcher()
    elif args.cmd == 'awesome':
        awesome()
    elif args.cmd == 'test':
        print('test')
    elif args.cmd == 'err':
        print(test)
    sys.exit(0)
