from bs4 import BeautifulSoup
import requests
import pprint
import sqlite3
import os

import matplotlib.pyplot as plt
import seaborn as sns   

import pandas as pd

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


# Scrapes a list of artist names off the billboard website
# returns list (names)
def scrape_billboard_artists(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    tags = soup.find_all('div', class_='chart-details')

    lst = []
    for item in tags:
        for sub in item.find_all('a'):
            lst.append(sub.text.strip())
            
    return lst


# takes in master and constructs artist api urls
# returns list (list montly urls, list followers urls)
def construct_api_urls(data):
    base_url = "https://api.spotify.com/v1/search?q="
    post_url = "&type=artist&offset=0&limit=1"
    return [base_url + artist.replace(' ', '?') + post_url for artist in data]


# takes in a single artist URL and returns a list of relevent components
def fetch_data(req_url):
    r = requests.get(req_url, headers=headers)
    dic = r.json()

    for item in dic['artists']['items']:
        name = item['name']
        # rtype = item['type']
        followers = item['followers']['total']
        genres = item['genres']
        rid = item['id']
        popularity = item['popularity']
    return [name, rid, followers, genres, popularity]


# processes all of the request
# returns a list (list)
def make_requests(urls):
    full = []
    for url in urls:
        out = fetch_data(url)
        full.append(out)
    return full

def make_requests_dict(urls):
    full = []
    count = 0
    for url in urls:
        out = fetch_data(url)
        temp = {
            'ranking' : count,
            'name' : out[0],
            'key' : out[1],
            'followers' : out[2],
            'categories' : out[3],
            'popularity' : out[4]

        }
        count += 1
        
        full.append(temp)
    return full


# inits the database
def initialize_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


# creates a new table
def create_table(cur, conn, table_name, data, spec = None):

    cur.execute('DROP TABLE IF EXISTS ' + table_name)
    cur.execute('CREATE TABLE ' + table_name + ' (name TEXT, id TEXT PRIMARY KEY, followers INTEGER, genres BLOB, popularity INTEGER, wiki REAL)')

    if spec is None:
        spec = [None] * 25

    for i in range(len(data)):
        cur.execute('INSERT INTO ' + table_name + ' (name, id, followers, genres, popularity, wiki) VALUES (?,?,?,?,?,?)', (data[i][0], data[i][1], data[i][2], ','.join(data[i][3]), data[i][4], spec[i]))
    conn.commit()


# appends the existings tables
def append_table(cur, conn, table_name, data, spec = None):

    if spec is None:
        spec = [None] * 25

    for i in range(len(data)):
        cur.execute('INSERT INTO ' + table_name + ' (name, id, followers, genres, popularity, wiki) VALUES (?,?,?,?,?,?)', (data[i][0], data[i][1], data[i][2], ','.join(data[i][3]), data[i][4], spec[i]))
    conn.commit()

def plot(data, enabled = True):
    if enabled: 
        df = pd.DataFrame(data)
        print(df)
        # print (df)


        plt.figure(figsize=(10,10))

        ax = sns.scatterplot(data=df, x='popularity', y='followers', 
                            hue='name', palette='rainbow', 
                            size='ranking', sizes=(50,1000), 
                            alpha=0.7)

        # display legend without `size` attribute
        h,labs = ax.get_legend_handles_labels()
        ax.legend(h[1:10], labs[1:10], loc='best', title=None)

        ax.axes.set_title("Popularity vs Followers via Spotify",fontsize=15)
        ax.set_xlabel("Popularity",fontsize=2)
        ax.set_ylabel("Followers",fontsize=10) 
        sns.despine(ax=ax)
        plt.legend([],[], frameon=False)

        plt.show()
        return

def merge(cur, conn):
    cur.execute('SELECT * FROM billboard_rankings JOIN monthly_listeners ON billboard_rankings.id = monthly_listeners.id') # loads entire table into 
    for row in cur:
        print (row)

# diff between popularity and followers in all of the mediums
def variance():
    pass

# differnece between popularity and followers in spotify
def compare():
    pass

# artist type of music randomly choose artist per run
def specifics():
    pass

# compare popularity between the groups
def understand_popularity():
    pass 

def get_frequency(cur, conn, enabled = True): 
    if enabled:
        lst = []
        cur.execute('SELECT * FROM billboard_rankings')
        for row in cur:
            lst.append(row[3].split(','))

        # print(lst)

        freq = {}
        for item in lst:
            for sub in item:
                if sub in freq:
                    freq[sub] += 1
                else:
                    freq[sub] = 1

        form = []
        for item in freq:
            temp = {
                'name': item,
                'frequency' : freq[item]
            }
            form.append(temp)

        # tips = sns.load_dataset(form)
        # sns.displot(tips, x="name")
        # plt.show()
        df = pd.DataFrame(form)
        plt.figure(figsize=(10,10))
        ax = sns.scatterplot(data=df, x='name', y='frequency', 
                            hue='frequency', palette='rainbow', 
                            sizes=(50,1000), 
                            alpha=0.7)

        # display legend without `size` attribute
        h,labs = ax.get_legend_handles_labels()
        ax.legend(h[1:10], labs[1:10], loc='best', title=None)
        # ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
        ax.axes.set_title("Frequency of Genres for Top 100 Bilboard Artist via Spotify",fontsize=15)
        ax.set_xlabel("Names",fontsize=2)
        ax.set_ylabel("Frequencies",fontsize=10) 
        plt.xticks(rotation=90)
        sns.despine(ax=ax)
        plt.legend([],[], frameon=False)
        plt.show()
        return





def main():
    wikipedia_url = "https://en.wikipedia.org/wiki/List_of_most-streamed_artists_on_Spotify"
    billboard_url = "https://www.billboard.com/charts/artist-100"

    data = get_artist_names(wikipedia_url)
    wikipedia_urls_monthly = construct_api_urls(data[0]) # 0 -> names monthly
    wikipedia_urls_followers = construct_api_urls(data[2]) # 2 -> followers monthly

    # grabs artist information from Billboard and grabs additional data from SPOTIFY
    billboard_list = scrape_billboard_artists(billboard_url)
    billboard_urls  = construct_api_urls(billboard_list)
    
    # artist profile from SPOTIFY
    api_monthly = make_requests(wikipedia_urls_monthly)
    api_followers = make_requests(wikipedia_urls_followers)
    api_rankings = make_requests(billboard_urls)
    api_rankings_dict = make_requests_dict(billboard_urls)
    print(api_rankings_dict)

    # initilizes the database pointers
    cur, conn = initialize_database('spotify_data.db')

    # commits the SPOTIFY monthly listener data to a database
    monthly_table_name = 'monthly_listeners'
    create_table(cur, conn, monthly_table_name, api_monthly[:20], data[1])
    
    # commits the SPOTIFY monthly follower data to a database
    followers_table_name = 'total_followers'
    create_table(cur, conn, followers_table_name, api_followers[:20], data[3])

    # create a table for the billboard rankings
    billboard_table_name = 'billboard_rankings'
    create_table(cur, conn, billboard_table_name, api_rankings[0:25])
    append_table(cur, conn, billboard_table_name, api_rankings[25:50])
    append_table(cur, conn, billboard_table_name, api_rankings[50:75])
    append_table(cur, conn, billboard_table_name, api_rankings[75:])

    #plots
    plot(api_rankings_dict, True)
    
    print ("hello")
    # merge(cur, conn)
    get_frequency(cur, conn, True)

    

    # cur.execute('SELECT * FROM billboard_rankings')
   
    

    

    
    


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