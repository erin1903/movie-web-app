from flask import Flask, render_template, request, jsonify, redirect, url_for, session, json
import pandas as pd
import recommendation

df = pd.read_csv('data/movie_data.csv')

app = Flask(__name__)
app.secret_key = 'neko movies'


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Renders index.html page and redirects to movie.html page on post request
    """
    if request.method == 'POST':
        title = request.form['title']
        poster = request.form['movie_poster_path']
        vote_average = request.form['vote_average']
        release_date = request.form['release_date']
        genres = request.form['genres']
        time = request.form['runtime']
        overview = request.form['overview']
        actors = request.form['actors']
        director = json.loads(request.form['director'])
        rec_movies = json.loads(request.form['rec_movies'])
        rec_m_info = json.loads(request.form['rec_m_info'])
        movie_cards = {rec_movies[i]: rec_m_info[i] for i in range(len(rec_movies))}
        movie_info = json.dumps({"title": title, "poster": poster, "vote_average": vote_average,
                                 "release_date": release_date, "genre": genres, "time": time, "overview": overview,
                                 "actors": actors, "director": director, "movie_cards": movie_cards})
        session['movie_info'] = movie_info
        return redirect(url_for('movie'))
    return render_template('index.html')


@app.route('/movie')
def movie():
    """
    Renders movie.html page
    """
    movie_info = session['movie_info']
    return render_template('movie.html', movie_info=json.loads(movie_info))


@app.route('/suggestions', methods=['GET', 'POST'])
def suggestions():
    """
    Returns to js file titles of movies present in movie_data that matched user input
    """
    if request.method == 'POST':
        user_input = request.form['user_input'].lower()
        df['title'] = df['title'].str.lower()
        new_df = df.loc[df['title'].str.contains(user_input, na=False)]['tmdbId']
        movie_suggestions = new_df.tolist()
        return jsonify(movie_suggestions)


@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    """
    Returns TMDB ids of movie recommendations to js file
    """
    if request.method == 'POST':
        movie_id = int(request.form['movie_id'])
        movie_recommendations = recommendation.get_recommendation(movie_id)
        return jsonify(movie_recommendations)


if __name__ == '__main__':
    app.run(debug=True)
