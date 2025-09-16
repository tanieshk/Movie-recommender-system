import pickle, requests, pandas as pd

TMDB_API_KEY = "5614307c4d9b9a3a253698b8464241d1"
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

bad_ids = []

for idx, row in movies.iterrows():
    movie_id = row['id']
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    resp = requests.get(url)
    if resp.status_code == 404:
        bad_ids.append((movie_id, row['title']))

print("Invalid IDs:")
for mid, title in bad_ids:
    print(mid, "-", title)

print(f"\nTotal broken IDs: {len(bad_ids)}")

