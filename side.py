from bs4 import BeautifulSoup
import requests
import pprint
import sqlite3
import os

# for the graphing
import matplotlib.pyplot as plt
import seaborn as sns  # for the linear charts
import networkx as nx  # for the networks
import secrets # to chose a color theme for the network graphs

import pandas as pd # for dataframes

from collections import defaultdict # for a dict of appendable lists

from datetime import datetime

import re


master = 0 # used for emergency pathing stop

cid = '9388b60e9dbc4a1ba26d013fcf84d951' # client ID
secret = '85bfc336314d4fa8a808d5250b5452eb' # client secret

AUTH_URL = 'https://accounts.spotify.com/api/token'

# AUTH TOKEN
auth_response = requests.post(AUTH_URL, {'grant_type': 'client_credentials', 'client_id': cid, 'client_secret': secret,})

# convert the response to JSON
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']

# provides authentications
headers = {'Authorization': 'Bearer {token}'.format(token=access_token)}

# creates a new database
def initialize_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


# creates a table with artist data
def create_table(cur, conn, table_name):
    cur.execute('DROP TABLE IF EXISTS ' + table_name)
    cur.execute('CREATE TABLE IF NOT EXISTS ' + table_name + ' (name TEXT PRIMARY KEY, id TEXT, followers INTEGER, popularity INTEGER, genre TEXT, parent TEXT)')
    conn.commit()


# appends the table with new data
def append_table(cur, conn, table_name, data):
    
    if len(data) == 5: # handles the root case
        data.append(None)
    cur.execute('INSERT OR REPLACE INTO ' + table_name + ' (name, id, followers, popularity, genre, parent) VALUES (?,?,?,?,?,?)', (data[0], data[1], data[2], data[3], data[4], data[5]))
    conn.commit()


# builds the url from the artist name or id
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
        if data:
            append_table(cur, conn, table_name, data)
        else:
            print('>>> REQUEST FAILED! UNABLE TO PULL DATA FOR URL: ' + url)

    # [append_table(cur, conn, table_name, get_artist_data(url)) for url in urls]


# gets a set of up to 20 related artists from a artist recomendation
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

    run = True
    while len(discovered) < 100 and run and len(data):
        cutoff = 0
        for entry in data:
            if entry[0] not in discovered:
                discovered.append(entry[0])
                next_url = build_url(entry[1], 'id')
                append_table(cur, conn, table_name, entry)
                data = get_related_artists(next_url, discovered[-1])
                
                break
            else:
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


# prints the entire aggregate data plot
def net_plot(data, enabled = True):
    if enabled: 
        df = pd.DataFrame(data)
        df.columns = ['genres', 'frequency']
 
        plt.figure(figsize=(25,8))

        ax = sns.scatterplot(data=df, x='genres', y='frequency', 
                            hue='genres', palette='rainbow', size='frequency', sizes=(50,1000), 
                            alpha=0.7)

        # display legend without `size` attribute
        h,labs = ax.get_legend_handles_labels()
        ax.legend(h[1:10], labs[1:10], loc='best', title=None)

        ax.axes.set_title("Genre Frequency from recommendations via Spotify",fontsize=15)
        ax.set_xlabel("Genres",fontsize=10)
        ax.set_ylabel("Frequency",fontsize=10) 
        sns.despine(ax=ax)
        plt.rcParams["xtick.major.size"] = 0
        plt.xticks(rotation=90, fontsize=2)
        plt.legend([],[], frameon=False)
        plt.savefig('GenreFreq', bbox_inches="tight", dpi=500)


# this aggregrates all the genre data
def aggregate_data(cur,conn, table_names):
    # gathers all of the table names from PATH and store them into table_names
    graph = defaultdict(list)
    for table in table_names:
        if table != 'genres' and table != 'root':
            cur.execute('SELECT * FROM ' + table + ' WHERE genre!=""')
            recomendations = list(cur) # stores the cur pointer in a list
            # TURNS THE GENRE tokens in a list of genres per artist
            genres_per_artist = [artist[4].split(',') for artist in recomendations]
            
            for i in range(len(genres_per_artist) - 1):
                # var unique = all elems that are in set a but not in set b
                unique = set(genres_per_artist[i]) - set(genres_per_artist[i + 1])
                for item in unique:
                    for val in genres_per_artist[i + 1]:
                        if val not in graph[item]:
                            graph[item].append(val)

    # tabulates the frequency of the genres
    frequency = []
    for genre in graph.keys():
        frequency.append((genre, len(graph[genre])))

    net_plot(frequency)


def main():
    p0 = datetime.now()
    """
        Part 1:
        1. The Billboard top 100 artists list is scraped and stored into a list
        2. The new artist list is compared to the existing artists to determine which to add to the ROOT if any
        3. If a ROOT table does not exist in the path database, the ROOT file is created to store the path heads in path.db
        4. The ROOT table is appended with the new artist list (name, id, followers, popularity, genres, NULL)
        
    """
    # init the database
    print('>>> INITIALIZING THE PATH.DB DATATBASE')
    cur, conn = initialize_database('path.db')

    print('>>> GENERATING/USING A NEW ROOT TABLE')
    billboard_url = "https://www.billboard.com/charts/artist-100"
    billboard_list = scrape_billboard_artists(billboard_url)
    # Following two lists used to determine what to add to existing root file
    billboard_tables = [('SUBPATH_' + item.replace(' ', '_').replace('+', '').replace('/', '').replace('?', '')
    .replace('.', '').replace('*', '').replace('\'', '').replace('!', '')) for item in billboard_list]
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [table[0] for table in list(cur.fetchall())]
    # determines the new items needed
    difference_list = [re.sub(' +', ' ',item[7:].replace('_', ' ')).lstrip() for item in list(set(billboard_tables) - set(existing_tables))]

    start = 0
    if 'root' not in existing_tables:
        create_table(cur, conn, 'root')
        new_urls = [build_url(artist, 'name') for artist in  billboard_list] 
        make_append_root_requests(cur, conn, 'root', new_urls)
    elif difference_list:
        print ('>>> ' + str(len(difference_list)) + ' DISCREPANCIES DETECTED IN BILLBOARD LIST AND EXISTING TABLE LIST: ' + str(difference_list))
        new_urls = [build_url(artist, 'name') for artist in difference_list] 
        # creates a new root table incase it doesnt exist
        make_append_root_requests(cur, conn, 'root', new_urls)
        start = len(list(cur.execute('SELECT * FROM root'))) - 2
        print('>>> UPDATED THE ROOT TABLE')
        # lst = list(cur.execute('SELECT * FROM root'))
    else:
        print('>>> USING THE ALREADY EXISTING ROOT TABLE')
        # lst = list(cur.execute('SELECT * FROM root'))
    
    p1 = datetime.now()

    """
        Part 2:
        1. Sets the start position of the recently appended potion of the root as "start" to avoid path regeneration for paths that already exist
        2. Iterates from "start" to the end of ROOT and builds a SpotifyAPI call using the artistID gathered from the ROOT
        3. Creates a new table for each new artist in ROOT that is compatible with sqlite3's formatting regulations
        4. Builds a 100 item long path per new artist within ROOT using linear pathfinding and appends data to each new artist's table

    """
    table_names = []
    row_data = list(cur.execute('SELECT * FROM root'))[start:]
    print('>>> STARTING PATHFINDING FOR NEW ARTISTS')
    for row in row_data:
        ROOT_NAME = row[0]
        ROOT_ID = row[1]
        ROOT_URL = 'https://api.spotify.com/v1/artists/' + ROOT_ID +'/related-artists'

        # cleans the artist name and removes all unnessary chars and replaces with a space
        table_name = 'SUBPATH_' + ROOT_NAME.replace(' ', '_').replace('+', '').replace('/', '').replace('?', '').replace('.', '').replace('*', '').replace('\'', '').replace('!', '')
        create_table(cur, conn, table_name)
        table_names.append(table_name)

        path_length = generate_path(cur, conn, table_name, ROOT_URL, ROOT_NAME)
        print ('>>>>>> {completed: ' + ROOT_NAME + ' -> ' + str(path_length) + '}')
    print('>>> CONCLUDED PATHFINDING FOR NEW ARTISTS')
    
    p2 = datetime.now()
   
    """
        Part 3:
        1. Creates a directory called graphs to store all the graphs generated in the following part
        2. Using python secrets, a random theme is selected and pushed to the graph builder function
        3. A graph is created by mapping recomended genres stemming from ROOT artist on to one another and generated with the networkx module
        4. The graphs are saved in .graphs/ directory
        
    """
    # list of graph themes for the build graph options functions
    themes = ['spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia']

    # removing the root table from the list of names
    # this generates a table per artist and stores the graphs in the graph folder
    os.mkdir('graphs')
    for table in table_names:
        if table != 'genre' and table != 'root':
            build_graph_network(cur, conn, table, secrets.choice(themes))
            print(">>>>>> CONTRUCTED GRAPH NETWORK ROOTING FROM " + table)

    p3 = datetime.now()
    """
        Part 4: 
        1. This creates a cumulative graph network of all artist's genres interconnection using the data provided by the SpotifyAPI recomendations feature
        2. The graph shows the weightage of each recomendation and the frequency with which its recomended
        3. The graph is diplayed and stored in the project directory
        4. A runtime summary message is printed
    """
    aggregate_data(cur, conn, table_names)
    
  
    print()
    print("*************************************************")
    print("The total runtime was: " + str(datetime.now() - p0))
    print("The ROOT generation portion: " + str(p1 - p0))
    print("The PATHFINDING portion: " + str(p2 - p1))
    print("The GRAPHING portion: " + str(p3 - p2))
    print("The AGGREGATION portion: " + str(datetime.now() - p3))
    print("*************************************************")

    
    
    # cur.execute('CREATE TABLE IF NOT EXISTS genres (category TEXT, edges TEXT)')

    # for i in graph.keys():
    #     cur.execute('INSERT INTO genres (category, edges) VALUES (?,?)', (i, len(graph[i])))
    #     print(i + " " + str(len(graph[i])))
            

    # plt.figure(figsize=(10,10))

    # ax = sns.scatterplot(data=df, x='popularity', y='followers', 
    #                     hue='name', palette='rainbow', 
    #                     size='ranking', sizes=(50,1000), 
    #                     alpha=0.7)

    # # display legend without `size` attribute
    # h,labs = ax.get_legend_handles_labels()
    # ax.legend(h[1:10], labs[1:10], loc='best', title=None)

    # ax.axes.set_title("Popularity vs Followers via Spotify",fontsize=15)
    # ax.set_xlabel("Popularity",fontsize=2)
    # ax.set_ylabel("Followers",fontsize=10) 
    # sns.despine(ax=ax)
    # plt.legend([],[], frameon=False)

    # plt.show()




    # edges = []
    # for i in graph.keys():
    #     for j in range(len(graph[i])):
    #         edges.append((i, graph[i][j]))
    
    # # intializing the graph
    # G = nx.DiGraph()
    # G.add_edges_from(edges)

    # # creating a frequency dictionary for edges for node sizing
    # degrees = dict(G.degree)

    # # the color map is created here:
    # colors = [(i/len(G.nodes)) for i in range(len(G.nodes))]

    # # setting the layout type
    # pos = nx.spring_layout(G, k=0.5, iterations=20)
    # nx.set_node_attributes(G, val, 'val')
    
    # # printing properties
    # plt.autoscale(True)
    # plt.margins(0.025)
    # plt.figure(figsize=(25,15))

    # # drawing the graph componenets
    # nx.draw_networkx_nodes(G, pos, node_color = colors, node_size = [v * 75 for v in degrees.values()], cmap=plt.get_cmap('winter'), alpha=0.45, linewidths=9)
    # nx.draw_networkx_labels(G, pos, font_size=8, horizontalalignment='center', verticalalignment='center_baseline')
    # # nx.draw_networkx_edges(G, pos, edge_color='lightgray', arrows=False)

    # plt.axis('off')
    # plt.title('complete', fontsize=15)
    # plt.savefig('graphs/Complete.png', bbox_inches="tight", dpi=500)
    # # plt.show()
    # plt.close()



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
