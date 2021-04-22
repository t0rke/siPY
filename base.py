# import spotipy
# from spotipy.oauth2 import SpotifyClientCredentials

# import spotipy
# from spotipy.oauth2 import SpotifyClientCredentials
# cid = '9388b60e9dbc4a1ba26d013fcf84d951'
# secret = '85bfc336314d4fa8a808d5250b5452eb'
# client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
# sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

# artist_name = []
# track_name = []
# popularity = []
# track_id = []
# for i in range(0,10000,50):
#     track_results = sp.search(q='year:2018', type='track', limit=50,offset=i)
#     for i, t in enumerate(track_results['tracks']['items']):
#         artist_name.append(t['artists'][0]['name'])
#         track_name.append(t['name'])
#         track_id.append(t['id'])
#         popularity.append(t['popularity'])

# import pandas as pd
# track_dataframe = pd.DataFrame({'artist_name' : artist_name, 'track_name' : track_name, 'track_id' : track_id, 'popularity' : popularity})
# print(track_dataframe.shape)
# track_dataframe.head()

from bs4 import BeautifulSoup
import requests
import pprint
import sqlite3
import os

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

# grabs stats from URL and returns a 2D list with  
# (monthly name, monthly popularity, most followed name, most followed popularity)
def get_artist_names(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    tags = soup.find_all('table', class_='wikitable sortable')

    # COLLECTS most monthly followed
    monthly = [item.text for item in tags[0].find_all('td') if (item.text != '' and '\n' not in item.text)]
    followed = [item.text for item in tags[1].find_all('td') if (item.text != '' and '\n' not in item.text)]
    
    monthly_artists = monthly[::2] # most monthly listened to: artist names
    monthly_popularity = monthly[1:][::2] # most monthly listened to: listeners in millions

    followed_artists = followed[::2] # most followed: artist names
    followed_popularity = followed[1:][::2] # most followed: artist popularity
    
    return [monthly_artists, monthly_popularity, followed_artists, followed_popularity]

# takes in master and constructs artist api urls
# returns list (list montly urls, list followers urls)
def construct_api_urls(data):
    base_url = "https://api.spotify.com/v1/search?q="
    post_url = "&type=artist&offset=0&limit=1"

    monthly = 0
    followed = 2
    
    urls = []
    urls.append([base_url + artist.replace(' ', '?') + post_url for artist in data[monthly]])
    urls.append([base_url + artist.replace(' ', '?') + post_url for artist in data[followed]])
    return urls

# takes in a single artist URL and returns a list of relevent components
def fetch_data(req_url):
    r = requests.get(req_url, headers=headers)
    dic = r.json()

    if dic:
        for item in dic['artists']['items']:
            name = item['name']
            # rtype = item['type']
            followers = item['followers']['total']
            genres = item['genres']
            rid = item['id']
            popularity = item['popularity']
        return [name, rid, followers, genres, popularity]
    else:
        return "requests failed"


def make_requests(urls):
    full = []
    for url in urls:
        out = fetch_data(url)
        full.append(out)
        print(out)
    return full


def initialize_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


def create_table(cur, conn, table_name, data):

    cur.execute('DROP TABLE IF EXISTS ' + table_name)
    cur.execute('CREATE TABLE ' + table_name + ' (name TEXT, id TEXT PRIMARY KEY, followers INTEGER, genres STRING, popularity INTEGER)')

    for item in data:
        cur.execute('INSERT INTO ' + table_name + ' (name, id, followers, genres, popularity) VALUES (?,?,?,?,?)', (item[0], item[1], item[2], ', '.join(item[3]), item[4]))
    conn.commit()


def main():
    wikipedia_url = "https://en.wikipedia.org/wiki/List_of_most-streamed_artists_on_Spotify"
    data = get_artist_names(wikipedia_url)
    artist_urls = construct_api_urls(data)

    # artist profile from WIKIPEDIA
    web_monthly = data[1]
    web_followers = data[3]

    # artist profile from SPOTIFY
    api_monthly = make_requests(artist_urls[0])
    api_followers = make_requests(artist_urls[1])

    # init tables
    table_name = 'spotify_data.db'
    cur, conn = initialize_database(table_name)
    create_table(cur, conn, 'spotify_data', api_monthly)


if __name__ == "__main__":
    main()




# # base URL of all Spotify API endpoints
# BASE_URL = 'https://api.spotify.com/v1/'

# # Track ID from the URI
# track_id = '6y0igZArWVi6Iz0rj35c1Y'

# # actual GET request with proper header
# r = requests.get("https://api.spotify.com/v1/search?q=J+Balvin&type=artist&offset=0&limit=1", headers=headers)

# r = r.json()

# print(type(r))

# pp.pprint(r)