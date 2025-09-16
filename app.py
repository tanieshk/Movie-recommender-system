import streamlit as st
import pickle
import pandas as pd
import requests
import random

# --- Load Data ---
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)



# Ensure column is named movie_id
if 'id' in movies.columns and 'movie_id' not in movies.columns:
    movies.rename(columns={'id': 'movie_id'}, inplace=True)

# --- TMDB API Key ---
TMDB_API_KEY = "5614307c4d9b9a3a253698b8464241d1"

# --- Fetch Poster from TMDB ---
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    
    # Try multiple times with different timeouts
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            
            poster_path = data.get('poster_path')
            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path
            else:
                # If no poster_path, try to get backdrop_path as fallback
                backdrop_path = data.get('backdrop_path')
                if backdrop_path:
                    return "https://image.tmdb.org/t/p/w500" + backdrop_path
        except requests.exceptions.RequestException as e:
            if attempt < 2:  # Don't sleep on the last attempt
                import time
                time.sleep(0.5)  # Wait a bit before retrying
            continue
        except Exception as e:
            continue
    
    # If all attempts failed, return placeholder
    return "https://via.placeholder.com/500x750?text=No+Image"

# --- Content-Based Recommendation ---
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movies = []
    recommended_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_posters

# --- Genre Based Recommendation ---
def recommend_by_genre(genre):
    # Check for different possible genre column names
    genre_column = None
    for col in ['genres', 'genre', 'Genre', 'Genres']:
        if col in movies.columns:
            genre_column = col
            break
    
    if genre_column is None:
        st.warning("⚠️ No genres column found in your dataset.")
        return [], []
    
    # Handle different genre formats (string, list, etc.)
    try:
        genre_movies = movies[movies[genre_column].astype(str).str.contains(genre, case=False, na=False)]
    except:
        st.warning("⚠️ Error processing genres column.")
        return [], []
    
    if genre_movies.empty:
        return [], []
    
    genre_movies = genre_movies.sample(min(len(genre_movies), 5))
    names, posters = [], []
    for _, row in genre_movies.iterrows():
        names.append(row['title'])
        posters.append(fetch_poster(row['movie_id']))
    return names, posters

# --- UI ---
st.title("🎬 Movie Recommender System")

option = st.selectbox("Select Movie for Similar Recommendations", movies['title'].values, index=None, placeholder="Choose a movie")

# Only show recommend button and process if a movie is actually selected
if option:
    if st.button('Recommend Similar'):
        with st.spinner('Loading recommendations...'):
            names, posters = recommend(option)
        
        cols = st.columns(len(names))
        for i, col in enumerate(cols):
            with col:
                st.text(names[i])
                # Add error handling for image loading
                try:
                    st.image(posters[i])
                except:
                    st.image("https://via.placeholder.com/500x750?text=No+Image")

# --- Genre Section ---
st.write("---")

# Check for different possible genre column names
genre_column = None
for col in ['genres', 'genre', 'Genre', 'Genres']:
    if col in movies.columns:
        genre_column = col
        break

if genre_column is not None:
    # Extract all unique genres, handling different formats
    try:
        # Handle case where genres might be separated by | or ,
        all_genres = set()
        for genres_str in movies[genre_column].dropna():
            if isinstance(genres_str, str):
                # Split by | or , and clean up
                for delimiter in ['|', ',']:
                    if delimiter in genres_str:
                        genres = [g.strip() for g in genres_str.split(delimiter)]
                        all_genres.update(genres)
                        break
                else:
                    # If no delimiter found, treat as single genre
                    all_genres.add(genres_str.strip())
        
        all_genres = sorted(list(all_genres))
        
        # Create genre selectbox with placeholder
        selected_genre = st.selectbox("Or choose by Genre", all_genres, index=None, placeholder="Choose a genre")

        # Only show recommend button if genre is selected
        if selected_genre:
            if st.button('Recommend by Genre'):
                with st.spinner('Loading genre recommendations...'):
                    names, posters = recommend_by_genre(selected_genre)
                
                if names:
                    cols = st.columns(len(names))
                    for i, col in enumerate(cols):
                        with col:
                            st.text(names[i])
                            # Add error handling for image loading
                            try:
                                st.image(posters[i])
                            except:
                                st.image("https://via.placeholder.com/500x750?text=No+Image")
                else:
                    st.warning("⚠️ No movies found for this genre.")
    
    except Exception as e:
        st.error(f"Error processing genres: {str(e)}")
        st.info("Debug: Please check the format of your genres column.")
else:
    st.info("ℹ️ Your dataset has no 'genres' column. Add it to use genre-based recommendations.")