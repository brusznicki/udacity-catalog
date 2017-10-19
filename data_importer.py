# Gets dummy data from rotten tomatoes and themoviedb APIs
import datetime
import json
import time
import urllib2
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Category, Item, User

engine = create_engine('sqlite:///catalogapp.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete Categories if exisitng.
session.query(Category).delete()
# Delete Items if exisitng.
session.query(Item).delete()
# Delete Users if exisitng.
session.query(User).delete()

# The MovieDB API KEY
THEMOVIEDB_API_KEY = "2a6289c34c7b843129bed9e9ca50de8b"


def create_admin_user():
    ''' Creates a default user for app, roles implemented later '''
    user = User(name="chris",
                email="chris.brusznicki@gmail.com",
                )
    session.add(user)
    session.commit()
    return


# Create a dummy user for use when importing items
create_admin_user()


# Get the movie categories from the movie DB
def get_genres_from_the_movie_db():
    ''' Populates movie categories from themoviedb '''
    url = "https://api.themoviedb.org/3/genre/movie/list?api_key="
    authenticated_url = url + THEMOVIEDB_API_KEY
    print "trying url: %s\n" % authenticated_url
    try:
        u = urllib2.urlopen(authenticated_url)
        genres = json.load(u)['genres']
        print "Successfully connected to Movie DB Genres"
    except urllib2.HTTPError, err:
        if err.code == 404:
            print "Sorry, the url: %s was not valid. Please check the url \
              and try again" & url
        else:
            print err.code
    except urllib2.URLError, err:
        print err.response
    return genres


def create_categories_from_movie_db_genres(genres):
    '''Create a category for each genre'''
    for genre in genres:
        genre_name = genre['name']
        print "Adding %s..." % genre_name
        user = session.query(User).one()
        user_id = user.id
        category_to_add = Category(name=genre_name,
                                   user_id=user_id)
        session.add(category_to_add)
        session.commit()
    print 'Catalog Categories added to DB'
    return


genres = get_genres_from_the_movie_db()
create_categories_from_movie_db_genres(genres)


def get_top_100_movies_from_rt():
    # Target page to scrape for 100 top films of all time
    rt_url = "https://www.rottentomatoes.com/top/bestofrt/"
    try:
        response = urllib2.urlopen(rt_url)
        html = response.read()
    except urllib2.HTTPError, err:
        if err.code == 404:
            print "Sorry, the url: %s was not valid. Please check the url \
              and try again" & rt_url
            return
        else:
            print err.code
    except urllib2.URLError, err:
        print err.response
        return
    soup = BeautifulSoup(html, 'html.parser')
    # Uses "html.parser" for cross platform compatibility, you can swap out
    # and use whatever parser you'd like.
    if soup:
        # Our return object: a list of links from rt
        # find all the links to the top 100 movies by genre
        table = soup.find("table", "table")
        movie_data = table.find_all("a")
        for datum in movie_data:
            movie_data = datum.get_text().strip()
            movie_name = movie_data[:-7].strip()
            release_date = movie_data[-5:-1].strip()
            create_item_data_from_the_movie_db(movie_name, release_date)
            time.sleep(3)  # Throttle control for The Movie DB API
    else:
        return False


def create_item_data_from_the_movie_db(movie_name,
                                       release_date,
                                       genres=genres):
    '''Quries Movie DB API given a movie name and release date'''

    # Build the movie db url
    url = "https://api.themoviedb.org/3/search/movie?&language=en-US&query="
    url += movie_name.replace(" ", "%20").encode('utf-8')
    url += "&page=1&include_adult=false&year="
    url += release_date.encode('utf-8')
    url += "&api_key=" + THEMOVIEDB_API_KEY
    print "trying url: %s\n" % url
    try:
        u = urllib2.urlopen(url)
        parsed_movie_data = json.load(u)
        print "Successfully connected to the Movie DB"
    except urllib2.HTTPError, err:
        if err.code == 404:
            print "Sorry, the url: %s was not valid. Please check the url \
              and try again" & url
            return
        else:
            print err.code
            return
    except urllib2.URLError, err:
        print err.response
        return
    if parsed_movie_data['total_results'] > 0:
        title = parsed_movie_data['results'][0]['original_title']
        description = parsed_movie_data['results'][0]['overview']
        image_path = "https://image.tmdb.org/t/p/w500"
        image_path += parsed_movie_data['results'][0]['poster_path']
        genre_id = parsed_movie_data['results'][0]['genre_ids'][0]
        print genre_id
        for item in genres:
            if str(item['id']) == str(genre_id):

                category = session.query(Category)\
                                  .filter_by(name=item['name']).one()
                user = session.query(User).one()
                item_to_add = Item(title=title,
                                   description=description,
                                   image_path=image_path,
                                   category_id=category.id,
                                   date_updated=datetime.datetime.now(),
                                   user_id=user.id)
                session.add(item_to_add)
                session.commit()
                print "Added {} to Items".format(title)
                break
    else:
        print "No films found matching {} {}".format(movie_name, release_date)
    return


# Gets top 100 movies from rotten tomatoes and adds as dummy data to DB
get_top_100_movies_from_rt()
