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

    master = []
    master.append(monthly_artists)
    master.append(monthly_popularity)
    master.append(followed_artists)
    master.append(followed_popularity)

    print (master)
    return master

    # for tag in tags:
    #     for sub in tag.find_all('td'):
    #         print (sub)

get_artist_names("https://en.wikipedia.org/wiki/List_of_most-streamed_artists_on_Spotify")
# import requests
# import pprint

# pp = pprint.PrettyPrinter(indent=4)

# cid = '9388b60e9dbc4a1ba26d013fcf84d951' # client ID
# secret = '85bfc336314d4fa8a808d5250b5452eb' # client secret

# AUTH_URL = 'https://accounts.spotify.com/api/token'

# # POST
# auth_response = requests.post(AUTH_URL, {
#     'grant_type': 'client_credentials',
#     'client_id': cid,
#     'client_secret': secret,
# })

# # convert the response to JSON
# auth_response_data = auth_response.json()

# # save the access token
# access_token = auth_response_data['access_token']

# headers = {'Authorization': 'Bearer {token}'.format(token=access_token)}

# # base URL of all Spotify API endpoints
# BASE_URL = 'https://api.spotify.com/v1/'

# # Track ID from the URI
# track_id = '6y0igZArWVi6Iz0rj35c1Y'

# # actual GET request with proper header
# r = requests.get("https://api.spotify.com/v1/artists/{id}", headers=headers)

# r = r.json()

# pp.pprint(r)