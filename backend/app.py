import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
# from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler

from cosine_sim import *
from svd import *
from filters import *
import pandas as pd
import nltk
# from nltk.tokenize import TreebankWordTokenizer


# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))
print(os.environ['ROOT_PATH'])

# precompute inverted index and idf
pd.set_option('max_colwidth', 600)
songs_df = pd.read_csv("clean_spotify.csv")

# movies_df = pd.read_csv("clean_movie_dataset.csv")
movies_df = pd.read_pickle("clean_movie_dataset.pkl")


# Movie Genre List
genre_df = pd.read_csv('genre_lst.csv')
dataset_genres = (genre_df['genres']).to_list()
# num_movies = (genre_lst['more than 75 movies']).to_list()

# extract lyrics and movie tokens as list of strings
songs_df['tokens'] = songs_df["clean lyrics"].apply(eval)
movies_df['tokens'] = movies_df["clean about"].apply(eval)

# build inverted index of song lyrics
inverted_lyric_index = build_inverted_index(songs_df['tokens'])

# build idf
n_docs = songs_df.shape[0]
lyric_idf = compute_idf(inverted_lyric_index, n_docs)

# build norms
doc_norms = compute_doc_norms(inverted_lyric_index, lyric_idf, n_docs)


# # build movie feature matrix using svd
# TODO
# movie_feature_matrix = movie_svd(movies_df, 75)
# movie_sim_rankings = movie_feature_cosine_sim(movie_feature_matrix)

# create popular and niche song dataframes and indices
niche_songs_df = filter_by_popularity(songs_df, 1)
inverted_niche_index = build_inverted_index(niche_songs_df['tokens'])
n_niche_docs = niche_songs_df.shape[0]
niche_lyric_idf = compute_idf(inverted_niche_index, n_niche_docs)
niche_doc_norms = compute_doc_norms(
    inverted_niche_index, niche_lyric_idf, n_niche_docs)

popular_songs_df = filter_by_popularity(songs_df, 3)
inverted_popular_index = build_inverted_index(popular_songs_df['tokens'])
n_popular_docs = popular_songs_df.shape[0]
popular_lyric_idf = compute_idf(inverted_popular_index, n_popular_docs)
popular_doc_norms = compute_doc_norms(
    inverted_popular_index, popular_lyric_idf, n_popular_docs)

# create short and long song dataframes and indices
short_songs_df = filter_by_song_length(songs_df, 1)
inverted_short_index = build_inverted_index(short_songs_df['tokens'])
n_short_docs = short_songs_df.shape[0]
short_lyric_idf = compute_idf(inverted_short_index, n_short_docs)
short_doc_norms = compute_doc_norms(
    inverted_short_index, short_lyric_idf, n_short_docs)

long_songs_df = filter_by_song_length(songs_df, 3)
inverted_long_index = build_inverted_index(long_songs_df['tokens'])
n_long_docs = long_songs_df.shape[0]
long_lyric_idf = compute_idf(inverted_long_index, n_long_docs)
long_doc_norms = compute_doc_norms(
    inverted_long_index, long_lyric_idf, n_long_docs)

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
# MYSQL_USER = "root"
# MYSQL_USER_PASSWORD = "MayankRao16Cornell.edu"
# MYSQL_PORT = 3306
# MYSQL_DATABASE = "kardashiandb"

# mysql_engine = MySQLDatabaseHandler(
#     MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# # Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
# mysql_engine.load_file_into_db()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)

# Sample search, the LIKE operator in this case is hard-coded,
# but if you decide to use SQLAlchemy ORM framework,
# there's a much better and cleaner way to do this


@app.route('/get_output/<movie>/<director>/<genre>/<popularity>/<length>')
def sql_search(movie, director, genre, popularity, length):
    movie_lower = movie.lower()
    director = director.lower()
    genre = genre.lower()

    # (1) Filter songs according to user's popularity & length selection
    df = songs_df
    idf = lyric_idf
    inverted = inverted_lyric_index
    norms = doc_norms

    if popularity == "1":
        df = niche_songs_df
        idf = niche_lyric_idf
        inverted = inverted_niche_index
        norms = niche_doc_norms
    elif popularity == "3":
        df = popular_songs_df
        idf = popular_lyric_idf
        inverted = inverted_popular_index
        norms = popular_doc_norms

    if length == "1":
        df = short_songs_df
        idf = short_lyric_idf
        inverted = inverted_short_index
        norms = short_doc_norms
    elif length == "3":
        df = long_songs_df
        idf = long_lyric_idf
        inverted = inverted_long_index
        norms = long_doc_norms

    # 1. find matching movies in the database
    dataset_titles = movies_df['title']
    matching_movies = movies_df[dataset_titles == movie_lower]

    edit_dist_genres = np.array(
        [nltk.edit_distance(genre, genres) for genres in dataset_genres])

    genre = dataset_genres[np.argmin(edit_dist_genres)]
    mov_df_by_genre = movies_df[movies_df[genre]]

    # if genre_df[genre_df['genres'] == genre]['more than 75 movies'].bool():

    movie_feature_matrix = movie_svd(mov_df_by_genre, 75)
    movie_sim_rankings = movie_feature_cosine_sim(movie_feature_matrix)

    # else:
    #     k = np.min(mov_df_by_genre.shape)
    #     movie_feature_matrix = movie_svd(mov_df_by_genre, k)
    #     movie_sim_rankings = movie_feature_cosine_sim(movie_feature_matrix)

    # 2. If the movie has no matches:
    if matching_movies.shape[0] == 0:

        edit_dist = np.array([nltk.edit_distance(movie_lower, title)
                             for title in dataset_titles])

        # If edit distance <= 5 use the closest matching movie
        if np.min(edit_dist) <= 5:
            matched_title = dataset_titles[np.argmin(edit_dist)]
            return result_json(df, inverted, idf, norms, movies_df[dataset_titles == matched_title], mov_df_by_genre, movie_sim_rankings)

        else:
            # if genre != "select a genre":

            # edit_dist_genres = np.array(
            #     [nltk.edit_distance(genre, genres) for genres in dataset_genres])
            # genre = dataset_genres[np.argmin(edit_dist_genres)]

            # if director field is empty
            if director == 'a':
                # genres_of_movies = movies_df['genre']
                # bool_lst = [genre in lst for lst in genres_of_movies]

                return result_json(df, inverted, idf, norms, mov_df_by_genre, mov_df_by_genre, movie_sim_rankings)

            else:
                dataset_directors = movies_df['director']
                edit_dist_directors = np.array(
                    [nltk.edit_distance(director, directors) for directors in dataset_directors])
                director = dataset_directors[np.argmin(
                    edit_dist_directors)]

                matched_director = movies_df[dataset_directors == director]

                # genres_of_director_movies = matched_director['genre']
                # bool_lst = [
                #     genre in lst for lst in genres_of_director_movies]
                bool_lst = matched_director[genre].to_list()

                if sum(bool_lst) == 0:
                    movie_feature_matrix = movie_svd(matched_director, 75)
                    movie_sim_rankings = movie_feature_cosine_sim(
                        movie_feature_matrix)
                    return result_json(df, inverted, idf, norms, matched_director, matched_director, movie_sim_rankings)

                movie_feature_matrix = movie_svd(
                    matched_director[bool_lst], 75)
                movie_sim_rankings = movie_feature_cosine_sim(
                    movie_feature_matrix)
                return result_json(df, inverted, idf, norms, matched_director[bool_lst], matched_director[bool_lst], movie_sim_rankings)

            # else:
            #     if director == 'a':
            #         matched_title = dataset_titles[np.argmin(edit_dist)]
            #         return result_json(df, inverted, idf, norms, movies_df[dataset_titles == matched_title])

            #     else:
            #         dataset_directors = movies_df['director']
            #         edit_dist_directors = np.array(
            #             [nltk.edit_distance(director, directors) for directors in dataset_directors])
            #         director = dataset_directors[np.argmin(
            #             edit_dist_directors)]
            #         return result_json(df, inverted, idf, norms, movies_df[dataset_directors == director])

    # 3. If the movie has matches:
    else:
        return result_json(df, inverted, idf, norms, matching_movies, mov_df_by_genre, movie_sim_rankings)


def result_json(df, inverted, idf, norms, matching_movies, mov_df, movie_sim_rankings):
    target_movie = matching_movies.iloc[0]
    movie_about = target_movie['about']

    ranked_cosine_score, song_keywords = svd_weighted_index_search(
        target_movie['title'],
        movie_about,
        50,
        mov_df,
        movie_sim_rankings,
        inverted,
        idf,
        norms
    )

    first_25 = ranked_cosine_score[:25]
    first_25_index = [ind for _, ind in first_25]
    first_25_songs = df.iloc[first_25_index].to_dict('index')
    song_list = result_to_json(first_25_songs)
    data = {
        "song": song_list,
        "keywords": construct_top_keywords(song_keywords, first_25_index)
    }
    return json.dumps(data)


MOVIEGENRELIST = ["Action", "Adventure", "Biography", "Comedy", "Drama", "Family",
                  "Fantasy", "History", "Horror", "Mystery", "Romance", "Sci-fi", "Thriller", "Other"]


@app.route("/")
def home():
    return render_template('base.html', movieGenres=MOVIEGENRELIST)


@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    return sql_search(text)


#app.run(debug=True)
