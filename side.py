from bs4 import BeautifulSoup
import requests
import pprint
import sqlite3
import os

import matplotlib.pyplot as plt
import seaborn as sns   

import pandas as pd

from collections import defaultdict

import networkx as nx
import matplotlib.pyplot as plt

import secrets

# import plotly.offline as py
# import plotly.graph_objects as go

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
    cur.execute('CREATE TABLE IF NOT EXISTS ' + table_name + ' (name TEXT PRIMARY KEY, id TEXT, followers INTEGER, popularity INTEGER, genre TEXT, parent TEXT)')
    conn.commit()


def append_table(cur, conn, table_name, data):
    if len(data) == 5: # handles the root case
        data.append(None)
    cur.execute('INSERT INTO ' + table_name + ' (name, id, followers, popularity, genre, parent) VALUES (?,?,?,?,?,?)', (data[0], data[1], data[2], data[3], data[4], data[5]))
    conn.commit()

def build_url(artist_tag, mode):
    if mode == 'id':
        return 'https://api.spotify.com/v1/artists/' + artist_tag +'/related-artists'
    if mode == 'name':
        return 'https://api.spotify.com/v1/search?q=' + artist_tag.replace(' ', '?') + "&type=artist&offset=0&limit=1"


# gets data from a singular artist URL via SPotify API
def get_artist_data(req_url):
    r = requests.get(req_url, headers=headers)
    dic = r.json()

    for item in dic['artists']['items']:
        name = item['name']
        # rtype = item['type']
        followers = item['followers']['total']
        genres = ','.join(item['genres'])
        rid = item['id']
        popularity = item['popularity']
        return [name, rid, followers, popularity, genres]


# Processes all of the root requests
# returns what it appends -> a list of root artist data
def make_append_root_requests(cur, conn, table_name, urls):
    for url in urls:
        data = get_artist_data(url)
        append_table(cur, conn, table_name, data)

    # [append_table(cur, conn, table_name, get_artist_data(url)) for url in urls]


def get_related_artists(req_url, parent):
    r = requests.get(req_url, headers=headers)
    dic = r.json()

    recommended = []

    if master > 20: # halts if no more recomendations can be made
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


def generate_path(cur, conn, table_name, url, name):
    print (">>> ENTERED GENERATE_PATH")
    # seeds from the first input
    data = get_related_artists(url, name)

    # inits discovered stack
    discovered = []
    discovered.append(name)

    # miss = 0
    # duplicate_profile = []
    run = True
    while len(discovered) < 100 and run and len(data):
        cutoff = 0
        for entry in data:

            if entry[0] not in discovered:
                # print(entry)
                # duplicate_profile.append(miss)
                # miss = 0
                discovered.append(entry[0])
                next_url = build_url(entry[1], 'id')
                append_table(cur, conn, table_name, entry)
                data = get_related_artists(next_url, discovered[-1])
                
                break
            else:
                # miss += 1
                cutoff += 1
                if (cutoff == len(data)):
                    run = False
                    break
    return len(discovered)


def scrape_billboard_artists(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    tags = soup.find_all('div', class_='chart-details')

    lst = []
    for item in tags:
        for sub in item.find_all('a'):
            lst.append(sub.text.strip())
            
    return lst

def build_graph_network(cur, conn, table_name, theme):
     # skips all of the rows with no genre data and begins first step of the pruning process

    cur.execute('SELECT * FROM ' + table_name + ' WHERE genre!=""')
    recomendations = list(cur) # stores the cur pointer in a list

    # TURNS THE GENRE tokens in a list of genres per artist
    genres_per_artist = [artist[4].split(',') for artist in recomendations]

    graph = defaultdict(list)
    for i in range(len(genres_per_artist) - 1):
        # var unique = all elems that are in set a but not in set b
        unique = set(genres_per_artist[i]) - set(genres_per_artist[i + 1])
        for item in unique:
            for val in genres_per_artist[i + 1]:
                if val not in graph[item]:
                    graph[item].append(val)
    
    # This turns the dictionary of lists into graph edges
    # {A : B, C, D} into (A,B), (A, C), (A, D)
    edges = []
    for i in graph.keys():
        for j in range(len(graph[i])):
            edges.append((i, graph[i][j]))

    """ The following are the node attributes and these determine the properties that a node will gave """
    # intializing the graph
    G = nx.DiGraph()
    G.add_edges_from(edges)

    # creating a frequency dictionary for edges for node sizing
    degrees = dict(G.degree)

    # the color map is created here:
    colors = [(i/len(G.nodes)) for i in range(len(G.nodes))]

    # setting the layout type
    pos = nx.spring_layout(G, k=0.5, iterations=20)
    nx.set_node_attributes(G, val, 'val')
    
    # printing properties
    plt.autoscale(True)
    plt.margins(0.025)
    plt.figure(figsize=(25,15))

    # drawing the graph componenets
    nx.draw_networkx_nodes(G, pos, node_color = colors, node_size = [v * 75 for v in degrees.values()], cmap=plt.get_cmap(theme), alpha=0.45, linewidths=9)
    nx.draw_networkx_labels(G, pos, font_size=8, horizontalalignment='center', verticalalignment='center_baseline')
    nx.draw_networkx_edges(G, pos, edge_color='lightgray', arrows=False)

    title = 'Graph Network of Genres via SpotifyAPI stemming from ' + table_name[8:].replace('_', ' ')
    plt.axis('off')
    plt.title(title, fontsize=15)
    plt.savefig('graphs/' + table_name[8:] + '.png', bbox_inches="tight", dpi=500)
    plt.close()


def main():
    # init the database
    print('>>> INITIALIZING THE PATH.DB DATATBASE')
    cur, conn = initialize_database('path.db')

    # start of the spidering
    # STARTIST_NAME = 'Taylor Swift'
    # STARTIST_ID = '06HL4z0CvFAxyc27GXpf02'
    # STARTIST_URL = 'https://api.spotify.com/v1/artists/' + STARTIST_ID +'/related-artists'


    # # TODO: NEED TO FIX THIS FUNCTIONALITY
    # if not cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='root'"):
    #     print ('>>> USING THE ALREADY EXISTING ROOT TABLE')
    # else:
    #     print('>>> CREATING A NEW ROOT TABLE')
    #     billboard_url = "https://www.billboard.com/charts/artist-100"
    #     billboard_list = scrape_billboard_artists(billboard_url)
    #     billboard_urls = [build_url(artist, 'name') for artist in billboard_list] 
    #     create_table(cur, conn, 'root')
    #     make_append_root_requests(cur, conn, 'root', billboard_urls)
    #     print('>>> CREATED THE ROOT TABLE')

    # # # builds the root directory and seeds it with billboard data
    
    # lst = list(cur.execute('SELECT * FROM root'))
    
    # names_of_tables = []
    
    # # generates path for all of artist in root
    # for row in lst[57:]:
    #     ROOT_NAME = row[0]
    #     ROOT_ID = row[1]
    #     ROOT_URL = 'https://api.spotify.com/v1/artists/' + ROOT_ID +'/related-artists'

    #     # cleans the artist name and removes all unnessary chars and replaces with a space
    #     table_name = 'SUBPATH_' + ROOT_NAME.replace(' ', '_').replace('+', '').replace('/', '').replace('?', '').replace('.', '').replace('*', '').replace('\'', '').replace('!', '')
    #     print(table_name)
    #     create_table(cur, conn, table_name)
    #     names_of_tables.append(table_name)

    #     path_length = generate_path(cur, conn, table_name, ROOT_URL, ROOT_NAME)
    #     print ('-----completed: ' + ROOT_NAME + '->' + str(path_length))


    # gathers all of the table names from PATH and store them into table_names
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [table[0] for table in list(cur.fetchall())]

    # list of graph themes for the build graph options functions
    themes = ['spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia']

    # removing the root table from the list of names
    # this generates a table per artist and stores the graphs in the graph folder
    table_names.pop(0)
    for table in table_names:
        build_graph_network(cur, conn, table, secrets.choice(themes))
        print(">>>>>> CONTRUCTED GRAPH NETWORK ROOTING FROM " + table)


    # for tablen in cur:
    #     build_graph_network(cur, conn, 'SUBPATH_Cardi_B')
   





    # G.legend(frameon=False)
    # G.margins(0.0)


        # Customize layout
    # layout = G.Layout(
    #     paper_bgcolor='rgba(0,0,0,0)', # transparent background
    #     plot_bgcolor='rgba(0,0,0,0)', # transparent 2nd background
    #     xaxis =  {'showgrid': False, 'zeroline': False}, # no gridlines
    #     yaxis = {'showgrid': False, 'zeroline': False}, # no gridlines
    # )
    # # Create figure
    # fig = G.Figure(layout = layout)
    # # Add all edge traces
    # # Remove legend
    # fig.update_layout(showlegend = False)
    # # Remove tick labels
    # fig.update_xaxes(showticklabels = False)
    # fig.update_yaxes(showticklabels = False)
    # # Show figure
    # fig.show()

    # plt.show()
    return

    
    
    
"""
import networkx as nx
import matplotlib.pyplot as plt

G = nx.DiGraph()
G.add_edges_from(
    [('A', 'B'), ('A', 'C'), ('D', 'B'), ('E', 'C'), ('E', 'F'),
     ('B', 'H'), ('B', 'G'), ('B', 'F'), ('C', 'G')])

val_map = {'A': 1.0,
           'D': 0.5714285714285714,
           'H': 0.0}

values = [val_map.get(node, 0.25) for node in G.nodes()]

# Specify the edges you want here
red_edges = [('A', 'C'), ('E', 'C')]
edge_colours = ['black' if not edge in red_edges else 'red'
                for edge in G.edges()]
black_edges = [edge for edge in G.edges() if edge not in red_edges]

# Need to create a layout when doing
# separate calls to draw nodes and edges
pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), 
                       node_color = values, node_size = 500)
nx.draw_networkx_labels(G, pos)
nx.draw_networkx_edges(G, pos, edgelist=red_edges, edge_color='r', arrows=True)
nx.draw_networkx_edges(G, pos, edgelist=black_edges, arrows=False)
plt.show()
"""













if __name__ == "__main__":
    main()
