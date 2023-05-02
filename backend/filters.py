import pandas as pd
from enum import Enum
"""
Filtering Functions

This file contains functions that filter song results based on 
user's input. 

Functions take in a pandas data frame, and returns a filtered data
frame.
"""

def filter_by_popularity(df, option, threshold=50):
	if option == 1: # select niche
		return df[df.track_popularity < threshold]
	elif option == 2: # anything
		return df
	elif option == 3: # select popular
		return df[df.track_popularity >= threshold]
	else:
		raise ValueError("The popularity filter selection is invalid")

def filter_by_song_length(df, option, threshold=180000):
	if option == 1: # select short
		return df[df.duration_ms < threshold]
	elif option == 2: # anything
		return df
	elif option == 3: # long
		return df[df.duration_ms >= threshold]
	else:
		raise ValueError("The song length filter selection is invalid")


def filter_by_genre(df, genres=[]):
	return df[df.playlist_genre.isin(genres)]


# # precompute inverted index and idf
# pd.set_option('max_colwidth', 600)
# songs_df = pd.read_csv("clean_spotify.csv")
# movies_df = pd.read_csv("clean_movie_dataset.csv")

# # extract lyrics and movie tokens as list of strings
# songs_df['tokens'] = songs_df["clean lyrics"].apply(eval)
# movies_df['tokens'] = movies_df["clean about"].apply(eval)

# filtered_songs = filter_by_popularity(songs_df, 1)
# print(filtered_songs.index)
