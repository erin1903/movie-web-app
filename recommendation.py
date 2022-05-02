import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

movie_data = pd.read_csv('data/movie_data.csv')
ratings = pd.read_csv('data/my_ratings_small.csv')
links = pd.read_csv('data/my_links_small.csv')

merged_data = links.merge(movie_data, on='tmdbId')

# creates a sparse matrix of ratings
ratings_pivot = ratings.pivot_table(index='movieId', columns='userId', values='rating').fillna(0)
ratings_table = ratings_pivot[ratings_pivot.index.isin(merged_data['movieId'])]


def get_recommendation1(tmdb_id, data=movie_data):
    """The first weighted recommendation system.
    Calculates cosine similarities of the queried movie with every other movies based on the overview and combined
    features (generes, actors, director) from movie dataset. Both calculations are given the same weight and sorted
    to take top 30 similar movies.

    :param tmdb_id: TMDB id of the queried movie.
    :param data: The dataset with the general information about movies.
    :return: TMDB ids of 30 most similar movies.
    """

    indx = data[data['tmdbId'] == tmdb_id].index

    tf_idf_scores = TfidfVectorizer(stop_words='english').fit_transform(data['overview'])
    cosine_similarities = cosine_similarity(tf_idf_scores[indx], tf_idf_scores)

    count_scores = CountVectorizer(stop_words='english').fit_transform(data['comb'])
    cosine_similarities2 = cosine_similarity(count_scores[indx], count_scores)

    weighted_similarities = cosine_similarities * 0.5 + cosine_similarities2 * 0.5

    sim_movies_indx = np.argsort(-1 * weighted_similarities)[0][1:30]  # 1st element is the queried movie itself
    sim_m_df = data.loc[sim_movies_indx].sort_values(by=['weighted_rating'], ascending=False)
    rec_movies = sim_m_df['tmdbId'].to_list()[:30]

    return rec_movies


def k_similar(movie_id):
    """
    Uses NearestNeighbors class (Pearson correlation metric) from scikit-learn library
    and ratings dataset to find 30 most similar movies.

    :param movie_id: movieId of the queried movie.
    :return: list of movieIds of top 30 similar movies and list of their similarity scores.
    """
    m_ids = []
    idx = ratings_table.index.get_loc(movie_id)
    ratings_arrayed = ratings_table.to_numpy()

    model = NearestNeighbors(metric='correlation', algorithm='brute')
    model.fit(ratings_arrayed)
    distances, indices = model.kneighbors(ratings_arrayed[idx].reshape(1, -1), n_neighbors=30)

    similarities = 1 - distances.flatten()
    for i in indices.flatten():  # gives position of rows with similar movies
        m_ids.append(ratings_table.index[i])  # their movieIds

    return similarities[1:], m_ids[1:]  # 1st element is the queried movie itself with full similarity of 1


def get_recommendation2(tmdb_id, data=movie_data):
    """The second weighted recommendation system.
    Calculates cosine similarities of movies based on the overview and combined features (genres, actors, director).
    Calls k_similar function and gives weight to every scores to find top 30 similar movies.

    :param tmdb_id: TMDB id of the queried movie.
    :param data: The dataset with the general information about movies.
    :return: TMDB ids of 30 most similar movies.
    """

    indx = data[data['tmdbId'] == tmdb_id].index
    movie_id = merged_data[merged_data['tmdbId'] == tmdb_id]['movieId']

    tf_idf_scores = TfidfVectorizer(stop_words='english').fit_transform(data['overview'])
    cosine_similarities = cosine_similarity(tf_idf_scores[indx], tf_idf_scores)

    count_scores = CountVectorizer(stop_words='english').fit_transform(data['comb'])
    cosine_similarities2 = cosine_similarity(count_scores[indx], count_scores)

    knn_similarities, knn_movieIds = k_similar(int(movie_id))

    # the following array will contain knn similarity scores in their corresponding positions
    knn_sim = [0] * 45432 # 45432 movies in movie_data - array needed to add knn_similarities to cosine similarities
    for movieId, sim in zip(knn_movieIds, knn_similarities):
        tmdbId = links[links['movieId'] == movieId]['tmdbId']
        idx = data[data['tmdbId'] == int(tmdbId)].index[0]
        knn_sim[idx] = sim
    # then give these scores a weight of 0.3
    for i, el in enumerate(knn_sim):
        knn_sim[i] = el * 0.3

    weighted_similarities = cosine_similarities * 0.3 + cosine_similarities2 * 0.4
    weighted_similarities += knn_sim

    sim_movies_indx = np.argsort(-1 * weighted_similarities)[0][1:30]  # 1st element is the queried movie itself
    sim_m_df = data.loc[sim_movies_indx].sort_values(by=['weighted_rating'], ascending=False)
    rec_movies = sim_m_df['tmdbId'].to_list()[:30]

    return rec_movies


def get_recommendation(tmdb_id):
    """
    Decides which recommendation system to use. If the searched movie exists in ratings_table, then use
    the second recommendation system. Otherwise, the first.
    :param tmdb_id: TMDB id of the queried movie.
    :return: TMDB ids of 30 recommendations for the queried movie.
    """

    if tmdb_id in merged_data.tmdbId.values:
        m_id = int(merged_data[merged_data['tmdbId'] == tmdb_id]['movieId'])
        if m_id in ratings_table.index:
            return get_recommendation2(tmdb_id)
    return get_recommendation1(tmdb_id)
