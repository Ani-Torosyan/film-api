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
avg_reviews = reviews_df.groupby("film_id")["rating"].mean().reset_index()
avg_reviews.rename(columns={"rating": "avg_rating"}, inplace=True)
films_df = films_df.merge(avg_reviews, on="film_id", how="left")
films_df["avg_rating"] = films_df["avg_rating"].fillna(0)

# Get unique genres
unique_genres = sorted(set(g for genres in films_df["Genres"].dropna() for g in genres.split(", ")))

class RecommendationRequest(BaseModel):
    genres: list[str]

@app.post("/recommend")
async def recommend(request: RecommendationRequest):
    genres = request.genres

    # Filter films by genres
    filtered = films_df[
        films_df["Genres"].apply(lambda x: any(g in x for g in genres))
    ]

    if filtered.empty:
        return {"success": True, "data": []}

    # Sort by average rating descending
    filtered = filtered.sort_values("avg_rating", ascending=False)

    return {
        "success": True,
        "data": filtered[["film_id", "Title", "Genres", "avg_rating", "Image_URL", "Film_URL"]].to_dict(orient="records")
    }

