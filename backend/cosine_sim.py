import numpy as np
import nltk
import csv
import pandas as pd
from nltk.tokenize import TreebankWordTokenizer
import math
import json

treebank_tokenizer = TreebankWordTokenizer()

def build_inverted_index(msgs):
    """ Builds an inverted index from the messages.
    
    Arguments
    =========
    
    msgs: list of lists.
        Each message in this list is represented as a list of tokens
        in the lyrics.
        e.g. ['eyes', 'transfixed', 'deadly', 'riff', 'future']

    Returns
    =======
    
    inverted_index: dict
        For each term, the index contains 
        a sorted list of tuples (doc_id, count_of_term_in_doc)
        such that tuples with smaller doc_ids appear first:
        inverted_index[term] = [(d1, tf1), (d2, tf2), ...]
        
    Example
    =======
    
    >> test_idx = build_inverted_index([
    ...    ['yeah', 'bro'],
    ...    ['yeah', 'yeah']
    ...])
    
    >> test_idx['yeah']
    [(0, 1), (1, 2)]
    
    >> test_idx['bro']
    [(0, 1)]
    
    """
    # YOUR CODE HERE
    inverted_index = {}
    
    for i, tokens in enumerate(msgs):
        term_count = {}
        for token in tokens:
            if not (token in term_count):
                term_count[token] = 1
            else:
                term_count[token] += 1
        
        for term in term_count:
            if not (term in inverted_index):
                inverted_index[term] = [(i, term_count[term])]
            else:
                inverted_index[term].append((i, term_count[term]))
    
    return inverted_index


def compute_idf(inv_idx, n_docs, min_df=10, max_df_ratio=0.95):
    """ Compute term IDF values from the inverted index.
    Words that are too frequent or too infrequent get pruned.
    
    Hint: Make sure to use log base 2.
    
    Arguments
    =========
    
    inv_idx: an inverted index as above
    
    n_docs: int,
        The number of documents.
        
    min_df: int,
        Minimum number of documents a term must occur in.
        Less frequent words get ignored. 
        Documents that appear min_df number of times should be included.
    
    max_df_ratio: float,
        Maximum ratio of documents a term can occur in.
        More frequent words get ignored.
    
    Returns
    =======
    
    idf: dict
        For each term, the dict contains the idf value.
        
    """
    
    # YOUR CODE HERE
    idf = {}
    
    for term in inv_idx:
        df = len(inv_idx[term])
        df_percent = df / n_docs
        
        if df >= 10 and df_percent <=max_df_ratio:
            # compute IDF
            idf[term] = math.log2(n_docs / (1+df))
    
    return idf

def compute_doc_norms(index, idf, n_docs):
    """ Precompute the euclidean norm of each document.
    
    Arguments
    =========
    
    index: the inverted index as above
    
    idf: dict,
        Precomputed idf values for the terms.
    
    n_docs: int,
        The total number of documents.
    
    Returns
    =======
    
    norms: np.array, size: n_docs
        norms[i] = the norm of document i.
    """
    
    # YOUR CODE HERE
    doc_norms = np.zeros(n_docs)
    
    for term in idf:
        for doc_id, tf in index[term]:
            term_idf = idf[term]
            doc_norms[doc_id] += (tf * term_idf)**2
    
    return np.sqrt(doc_norms)

def accumulate_dot_scores(query_word_counts, index, idf):
    """ Perform a term-at-a-time iteration to efficiently compute the numerator term of cosine similarity across multiple documents.
    
    Arguments
    =========
    
    query_word_counts: dict,
        A dictionary containing all words that appear in the query;
        Each word is mapped to a count of how many times it appears in the query.
        In other words, query_word_counts[w] = the term frequency of w in the query.
        You may safely assume all words in the dict have been already lowercased.
    
    index: the inverted index as above,
    
    idf: dict,
        Precomputed idf values for the terms.
    
    Returns
    =======
    
    doc_scores: dict
        Dictionary mapping from doc ID to the final accumulated score for that doc
    """
    
    # YOUR CODE HERE
    doc_scores = {}
    doc_keywords = {}
    for word in query_word_counts:
        q_i = query_word_counts[word] * idf[word]
        
        for doc_id, tf in index[word]:
            d_ij = tf * idf[word]
            if not (doc_id in doc_scores):
                doc_scores[doc_id] = 0
            if not (doc_id in doc_keywords):
                doc_keywords[doc_id] = []

            doc_scores[doc_id] += q_i * d_ij
            doc_keywords[doc_id].append((word, q_i * d_ij))
    
    return (doc_scores, doc_keywords)

def text_to_term_dict(text):
  text = text.split()
  text_dict = {}
  for token in text:
    if token in text_dict:
      text_dict[token] += 1
    else:
      text_dict[token] = 1
  
  return text_dict

def index_search(query, index, idf, doc_norms, score_func=accumulate_dot_scores, tokenizer=treebank_tokenizer):
    """ Search the collection of documents for the given query
    
    Arguments
    =========
    
    query: string,
        The query we are looking for.
    
    index: an inverted index as above
    
    idf: idf values precomputed as above
    
    doc_norms: document norms as computed above
    
    score_func: function,
        A function that computes the numerator term of cosine similarity (the dot product) for all documents.
        Takes as input a dictionary of query word counts, the inverted index, and precomputed idf values.
        (See Q7)
    
    tokenizer: a TreebankWordTokenizer
    
    Returns
    =======
    
    results, list of tuples (score, doc_id)
        Sorted list of results such that the first element has
        the highest score, and `doc_id` points to the document
        with the highest score.
    
    Note: 
        
    """
    
    # YOUR CODE HERE
    query = query.lower()
    query_words = tokenizer.tokenize(query)
    
    # calculate word count in query
    query_word_count = {}
    for word in query_words:
        if word in idf:
            if not (word in query_word_count):
                query_word_count[word] = 0
            query_word_count[word] += 1
    
    # compute query norm
    q_norm = 0
    for word in query_word_count:
        q_norm += (query_word_count[word] * idf[word]) ** 2
    q_norm = math.sqrt(q_norm)
    
    # compute numerator for all documents
    dot_prods = score_func(query_word_count, index, idf)
    
    # for each document, compute the sim score
    cosine_sim = []
    
    for i, d_norm in enumerate(doc_norms):
        numerator = dot_prods[i] if i in dot_prods else 0 
        score = 0 if d_norm == 0 else numerator / (q_norm * d_norm)
        cosine_sim.append((score, i))
    
    return sorted(cosine_sim, key=lambda x : x[0], reverse=True)

def result_to_json(first_25_songs):
    song_list = []
    for query_result in first_25_songs.values():
        song = {}
        song['title'] = query_result['track_name']
        song['genre'] = query_result['playlist_genre']
        song['duration'] = query_result['duration_ms']
        song['artist'] = query_result['track_artist']

        # process lyrics to a long string with new lines after each lyric line
        lyrics = query_result['lyrics']
        lyrics = lyrics[1:-1] # brute force way to remove [] on both sides
        lyrics = [l.strip()[1:-1] for l in  lyrics.split(',')] # remove beginning and ending quotations marks in the strings
        song['lyrics'] = '\n'.join(lyrics)

        song['popularity'] = query_result['track_popularity']
        features = {}
        features['danceability'] = query_result['danceability']
        features['energy'] = query_result['energy']
        features['key'] = query_result['key']
        features['loudness'] = query_result['loudness']
        features['mode'] = query_result['mode']
        features['speechiness'] = query_result['speechiness']
        features['acousticness'] = query_result['acousticness']
        features['instrumentalness'] = query_result['instrumentalness']
        features['liveness'] = query_result['liveness']
        features['valence'] = query_result['valence']
        features['tempo'] = query_result['tempo']
        song['features'] = features
        song_list.append(song)
    return song_list

# # precompute inverted index and idf
# pd.set_option('max_colwidth', 600)
# songs_df = pd.read_csv("clean_spotify.csv")
# movies_df = pd.read_csv("clean_movie_dataset.csv")

# # extract lyrics and movie tokens as list of strings
# songs_df['tokens'] = songs_df["clean lyrics"].apply(eval)
# movies_df['tokens'] = movies_df["clean about"].apply(eval)

# # build inverted index of song lyrics
# inverted_lyric_index = build_inverted_index(songs_df['tokens'])

# # build idf
# n_docs = songs_df.shape[0]
# lyric_idf = compute_idf(inverted_lyric_index, n_docs)

# # build norms
# doc_norms = compute_doc_norms(inverted_lyric_index, lyric_idf, n_docs)

# target_movie = movies_df[movies_df['title'].str.lower() == "the dark knight"].iloc[0]
# movie_tokens = target_movie['tokens']
# movie_about = target_movie['about'].lower()
# print(movie_about)

# ranked_cosine_score = index_search(
#             movie_about,
#             inverted_lyric_index,
#             lyric_idf,
#             doc_norms
#             )

# first_25_scores = ranked_cosine_score[:25]
# first_25_index = [ind for _, ind in first_25_scores]
# first_25_songs = songs_df.iloc[first_25_index].to_dict('index')

# # return the values as a list of dictionaries
# song_list = result_to_json(first_25_songs)

# print(song_list[0]['lyrics'])




