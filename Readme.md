# SIPY

This project was created to satisfy the final project requirements for the SI206 class in Winter 2021.

This project works by using Billboard's top 100 Artist list and construing a path of 100 related artists for each of the artists on the the site. By using each root artist to generate a list or related artist, it was possible to see a correlation between the artists that were recomended and the genres that they were know to create in.

## Modules that you will need

We will mainly be utilizing many of python's built in default libraries including, requests, sqlite3, beautifulSoup, matplotlib, networkx for the code portion of this project. External technololgies that will be utilized include Billboard's hot 100 artists website data, as well as the spotifyAPI

Some libraries will need to be installed, by entereing the following commands in your terminal

```
    pip install beautifulsoup4
    pip install plotly
    pip install
```

This program makes use of the following modules for the following tasks:

- [Seaborn](https://seaborn.pydata.org) is a Python data visualization library based on matplotlib. It provides a high-level interface for drawing attractive and informative statistical graphics. We used Seaborn to 
- [Networkx](https://networkx.org) is a Python package for the creation, manipulation, and study of the structure, dynamics, and functions of complex networks. We used NetworkX to 
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) is a Python library for pulling data out of HTML and XML files. It works with your favorite parser to provide idiomatic ways of navigating, searching, and modifying the parse tree. It commonly saves programmers hours or days of work. We used Beautiful Soup to 
- The [PPrint](https://github.com/python/cpython/blob/3.9/Lib/pprint.py) module provides a capability to “pretty-print” arbitrary Python data structures in a form which can be used as input to the interpreter. We used pprint to 
- [Pandas](https://pandas.pydata.org/) is a fast, powerful, flexible and easy to use open source data analysis and manipulation tool, built on top of the Python programming language. We used pandas to 
- [Secrets](https://pypi.org/project/python-secrets/) Generate unique values for variables, or use a single value per type to simplify use of secrets in access control of services while supporting a “break-glass” process to quickly regenerate secrets when needed. We used secrets to 

## Goals

Our oiginal goals before we had started any work or even meeting for more than a few minute were as follows
THREE API’s: Spotify, Soundcloud, Apple Music
We will be collecting song rankings per year for the last 3 years.
We will calculate the difference in genre types between the top songs on each platform
We will be using Plotly
We will create a simple mapping of all genres and total streams and mark each platform

After some further brainstorming we refined our vision and modified our original goals:
A program using Spotify’s API and also was capable of scraping [Billboard Artist 100](https://www.billboard.com/charts/artist-100)
Our second goal was to utilize Spotify’s API artist recommendation feature to analyze recommendations by genre.
Our third goal was to use a Directed Graph Network to model the recommendations by genre for each artist on the Billboard Artist 100 list.
Our fourth goal was to create an aggregate visualizations of all genre networks for the top 100 artists the was both readable and understandable.
Our fifth goal was to create code that was reusable and multipurpose with sufficient documentation.
Our sixth goal was to develop a write-up that sufficiently explains all the aspects of our code and all decisions made.
In consideration of the goals we set out to accomplish we achieved almost all of them in holistic fashion.

## running instructions

## sample run

The program will start out by constructing a list of existing databases in `path.db` and compare it to a list gathered by scraping Billboard's (link) website using Beautiful Soup 4. By comparing these two lists

1. The list generated from Billboard and the local Path database are compared
2. For all of the missing artist within the database, the program will create a new table and append these new artist names to them
3. The program will then generate 100 `pathed` recomendations for each new artist added to the root database
4. For each new artist a genre dictionary will be constructed and saved to the graps folder highlighting Graph network of Spotify genres for that artist
5. A cumulative Graph network will be created for all artists using that subdictionary details that were discovered per artist
6. This final plot will be displayed


## Methods

With this program we aimed to determine how genres are recomended to users on Spotify. To accomplish this, we utilized the SpotifyAPI's recomended artist functionality to generate a series of related artists scraped from the `Billboard Artists 100` list most popular artist list to generate a series of starting points to begin pathfinding from.

The `Billboard Artists 100` list  is scraped with `BeautifulSoup4` and the most relevant artist on the date the program is accessed is generated and stored into the `root` (labeled part 1 in the program) . Using each row in `root`:
| artist  | id  | followers  | popularity  | genres  |  parent  |
|---|---|---|---|---| ---|
| Kanye West  | 5K4W6rqBFWDnAN6FQUkS6x  | 13761535  | 92  | chicago rap,rap  |  null  |
| J. Cole  | 6l3HvQ5sa6mXTsMTB19rO5  | 13121708  | 88  | conscious hip hop,hip hop,north carolina hip hop,rap  |  null  |
| blackbear  | 2cFrymmkijnjDg9SS92EPM  | 4099377  | 87  | electropop,pop,pop rap  | null  |

a call is made to SpotifyAPI's related artist feature and a dictionary of up to 20 related artists is returned. The related artist dictionary is parsed in order and compared to the list of discovered artists for stemming from this artist and appended to this artists `SUBPATH` table if the recomended artist is newly discovered. If the topmost artist returned from the API already exists within the `discovered artist` list then the subsequent item is chosed from the API call list and is counted as a miss. The pathfinding concludes when the number of misses is equivalent to the number of related artists returned by the SpotifyAPI or the path reaches 100 Entries. For the completion of each generated path a completion message is printed as which states the artist's name and the length of the generated list: 

```
>>>>>> {completed: Khalid -> 100}
>>>>>> {completed: Imagine Dragons -> 87}
>>>>>> {completed: Tom Petty and the Heartbreakers -> 100}
```

After each artist within the `root` table has a path generated for them (labeled part 2 in the program) , the next portion of the program begins. For each artist path, the genres are parsed and mapped to one another using the following logic and assumption that succesive entry in an artists path call is directly related to the one preceding it.

1. A set of items found in SUBPATH entry n and a set for items SUBPATH  n + 1 are created
2. By taking the difference of these two sets, set (n) - set (n + 1) and add every entry appearing in this set to a dictionary of lists into the following format {n : a, b, c , d}
3. The dictionary is then converted into a series of edges in the format of a directed graph network as follows {(n, a), (n, b), (n,C), (n,d)}. In this case n, a, b, c , d all function as nodes and the paths (n, a), (n, b), (n,C), (n,d) are the edges that connect these nodes.
4. Using the created edgelist from above and the `NetworkX` python module, a directed graph is created with a scalar colormap, nodesize dependent on the number of paths to that node. While the a directed graph is created the arrows are ommited for the visuals. 

After each graph is created, it is stored in the graphs folder using the naming convention <artist_name>.png. After all of the graphs are created, part 3 of the code is complete.

The next part of the program aggregates all of the genre data from all of the artists and constructs a treemap using `plotly.express` of the relationship between artist's popularity, recomendation-parent, follower count using the genre to group related artist by types of music that they are associated with.

The data is parsed from everyfile with the following sqlite commands:
```
a) cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
b) cur.execute('SELECT * FROM ' + table + ' WHERE genre!=""')
```

The first query gathers a list of all of the database names within the `path.db` database and passes them to the second query prompt which selects all rows which have a non-empty genre from the table it is parsing. Together these two functions gather all of the data stored from the SpotifyAPI

With the help of a `pandas` dataframe wrapper the data is converted into to form that works well with the plotly express treemap module. For the generated graph, the size of each artists square is relative to the their popularity scores and the coloring is related to the the number of followers that they have on instagram. When looking at the categories, a couple duplicate artists might be observed, due to to the fact that each artist generated path was genereated irrespective to any other artists path meaning that duplicates were tabluted in this process. 

While this generated graph is robust, it is a simplification of the true nature of the data collected. It would be nearly impossible to effectively graph each artist within each genre they were associated with as can be seen in the J. Cole example above. He is associated with "conscious hip hop,hip hop,north carolina hip hop,rap". Using the python `secrets` module, just one of these genres is picked for the creation of the graph which makes the final graph an imperfect representation of the data. However, allowing duplicate J. Coles allows for the chance for him to be picked for multiple genres creating a truer representation of the aggregated data.  

## calculations

## code documentation 

## problems encountered

Problems we faced included extensive run times- with a total length of about 15 minutes for two of the 3 portions of our project (database generation 8900 api calls, and the data visualization 89 directed graph networks). Due to the batch processing nature of our program, testing the functionality of one aspect meant running tests on the entire set of Artist via Billboard often making if difficult to complete portions of code very fast. This coupled with poor Python documentation for many libraries including Seaborn and Networkx led to hours of research and problematic halts. Thankfully, these issues were offset by the nature of our working relationship; tasks could easily be split between members and separately implemented reducing total project work time. Overall the large datasets that we created ad hoc were difficult to parse with SQLite (we needed to learn obscure portions of the module to achieve desired functionality) , additionally, by constructing a huge database (8900 API Calls, each taking approximately . Furthermore, the nature of the rubric handcuffed our ability to create a truly interesting project that mirrored exactly what we wanted and led to early feelings of burnout and slow progress, leading us to completely change the nature of our project (see updated goals above). Aspects including the JOIN command and the length of the database conflicted with the goals we hoped to achieve and the portions of our project that address these tasks is functionally useless (see useless https://www.merriam-webster.com/dictionary/useless). Finally, the poor existing documentation on the API’s provided by the class itself prevented us from moving in an efficient manner.





