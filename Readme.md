# SIPY

This project was created to satisfy the final project requirements for the SI206 class.

This project works by using Billboard's top 100 Artist list and construing a path of 100 related artists for each of the artists on the the site.
By using each root artist to generate a list or related artist, it was possible to see a correlation between the artists that were recomended and the genres that they were know to create in.

## things that you will need

We will mainly be utilizing many of python's built in default libraries including, requests, sqlite3, beautifulSoup, matplotlib, networkx for the code portion of this project. External technololgies that will be utilized include Billboard's hot 100 artists website data, as well as the spotifyAPI

Some libraries will need to be installed, by entereing the following commands in your terminal

```
    pip install beautifulsoup4
    pip install
    pip install

```

## sample run

The program will start out by constructing a list of existing databases in `path.db` and compare it to a list gathered by scraping Billboard's (link) website using Beautiful Soup 4. By comparing these two lists

1. The list generated from Billboard and the local Path database are compared
2. For all of the missing artist within the database, the program will create a new table and append these new artist names to them
3. The program will then generate 100 `pathed` recomendations for each new artist added to the root database
4. For each new artist a genre dictionary will be constructed and saved to the graps folder highlighting Graph network of Spotify genres for that artist
5. A cumulative Graph network will be created for all artists using that subdictionary details that were discovered per artist
6. This final plot will be displayed

