from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Data
films_df = pd.read_csv("films_with_genres.csv", encoding="utf-8-sig")
reviews_df = pd.read_csv("reviews.csv", encoding="utf-8-sig")

# Compute average rating
avg_reviews = reviews_df.groupby("movie_id")["rating"].mean().reset_index()
avg_reviews.rename(columns={"rating": "avg_rating"}, inplace=True)

# Merge average rating into films dataframe
# Use 'id' from films_df and 'movie_id' from reviews_df
films_df = films_df.merge(avg_reviews, left_on="id", right_on="movie_id", how="left")
films_df["avg_rating"] = films_df["avg_rating"].fillna(0)

# Get unique genres
unique_genres = sorted(set(g for genres in films_df["genre"].dropna() for g in genres.split(", ")))

class RecommendationRequest(BaseModel):
    genres: list[str]

@app.post("/recommend")
async def recommend(request: RecommendationRequest):
    genres = request.genres

    # Filter films by selected genres
    filtered = films_df[
        films_df["genre"].apply(lambda x: any(g in x for g in genres))
    ]

    if filtered.empty:
        return {"success": True, "data": []}

    # Sort by average rating descending
    filtered = filtered.sort_values("avg_rating", ascending=False)

    # Return relevant fields, matching your CSV naming
    return {
        "success": True,
        "data": filtered[[
            "id",           # film ID
            "title",        # film title
            "genre",        # genres
            "avg_rating",   # average rating
            "poster_url",   # poster image
            "movie_page_url" # film page URL
        ]].to_dict(orient="records")
    }
