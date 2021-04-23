from bs4 import BeautifulSoup
import requests
import pprint
import sqlite3
import os

import matplotlib.pyplot as plt
import seaborn as sns   

import pandas as pd

master = 0

pp = pprint.PrettyPrinter(indent=4)

cid = '9388b60e9dbc4a1ba26d013fcf84d951' # client ID
secret = '85bfc336314d4fa8a808d5250b5452eb' # client secret

AUTH_URL = 'https://accounts.spotify.com/api/token'

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': cid,
    'client_secret': secret,
})

# convert the response to JSON
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']

# provides authentications
headers = {'Authorization': 'Bearer {token}'.format(token=access_token)}

def initialize_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


def create_table(cur, conn, table_name):
    cur.execute('DROP TABLE IF EXISTS ' + table_name)
    cur.execute('CREATE TABLE ' + table_name + ' (name TEXT PRIMARY KEY, id TEXT, followers INTEGER, popularity INTEGER, genre TEXT, parent TEXT)')
    conn.commit()


def append_table(cur, conn, table_name, data):
    cur.execute('INSERT INTO ' + table_name + ' (name, id, followers, popularity, genre, parent) VALUES (?,?,?,?,?,?)', (data[0], data[1], data[2], data[3], data[4], data[5]))
    conn.commit()

def build_url(artist_id):
    return 'https://api.spotify.com/v1/artists/' + artist_id +'/related-artists'


def get_related_artists(req_url, parent):
    r = requests.get(req_url, headers=headers)
    dic = r.json()

    recommended = []

    if master > 20:
        return

    for item in dic['artists']:
        # pp.pprint(item)
        ID = item['id']
        name = item['name']
        followers = item['followers']['total']
        genres = ','.join(item['genres'])
        popularity = item['popularity']

        recommended.append((name, ID, followers, popularity, genres, parent))
        # print (name, ID, followers, popularity, parent)

    return recommended

def generate_path(cur, conn, url, name):
    # seeds from the first input
    data = get_related_artists(url, name)

    # inits discovered stack
    discovered = []
    discovered.append(name)

    # miss = 0
    # duplicate_profile = []
    run = True
    while (run):
        cutoff = 0
        for entry in data:
            if entry[0] not in discovered:
                print(entry)
                # duplicate_profile.append(miss)
                # miss = 0
                discovered.append(entry[0])
                next_url = build_url(entry[1])
                append_table(cur, conn, 'path', entry)
                data = get_related_artists(next_url, discovered[-1])
                break
            else:
                # miss += 1
                # print("Miss!")
                cutoff += 1
                if (cutoff == 20):
                    run = False



def main():
    # init the database
    cur, conn = initialize_database('path.db')
    create_table(cur, conn, 'path')
    
    # start of the spidering
    STARTIST_NAME = 'Taylor Swift'
    STARTIST_ID = '06HL4z0CvFAxyc27GXpf02'
    STARTIST_URL = 'https://api.spotify.com/v1/artists/' + STARTIST_ID +'/related-artists'

    generate_path(cur, conn, STARTIST_URL, STARTIST_NAME)



    pass

if __name__ == "__main__":
    main()
