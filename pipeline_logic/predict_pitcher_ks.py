import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from unidecode import unidecode

# === Load model
model = joblib.load("models/pitcher_k_model.joblib")

# === Load input files
games_df = pd.read_csv("data/scheduled_games_and_starters_with_id.csv", parse_dates=["date"])

pitching_df = pd.read_csv("data/Stathead_2025_Pitcher_Master.csv")
pitching_df["Date"] = pd.to_datetime(pitching_df["Date"], errors="coerce")
pitching_df["Player"] = pitching_df["Player"].apply(lambda x: unidecode(str(x)).strip())

# === Normalize pitching stats
for col in ["SO", "IP", "ER", "BB", "BF"]:
    pitching_df[col] = pd.to_numeric(pitching_df[col], errors="coerce")
pitching_df["Home"] = pitching_df["Unnamed: 5"].apply(lambda x: 0 if x == "@" else 1)

# === Loop through BOTH home and away starters
pred_rows = []

def process_pitcher(pitcher_name, game_date, team, opponent, is_home):
    pitcher_name_clean = unidecode(str(pitcher_name)).strip()
    history = pitching_df[(pitching_df["Player"] == pitcher_name_clean) & (pitching_df["Date"] < game_date)]
    history = history.sort_values("Date").tail(3)

    if len(history) < 3:
        print(f" Skipping {pitcher_name_clean}: only {len(history)} appearances before {game_date.date()}")
        return

    features = {
        "K_last3": history["SO"].mean(),
        "IP_last3": history["IP"].mean(),
        "ER_last3": history["ER"].mean(),
        "BB_last3": history["BB"].mean(),
        "BF_last3": history["BF"].mean(),
        "Home": 1 if is_home else 0
    }

    X = pd.DataFrame([features])
    predicted_ks = model.predict(X)[0]

    pred_rows.append({
        "date": game_date,
        "team": team,
        "opponent": opponent,
        "starting_pitcher": pitcher_name_clean,
        "predicted_ks": round(predicted_ks, 2)
    })
    print(f" Predicted Ks for {pitcher_name_clean}: {round(predicted_ks, 2)}")

# === Process all games
for _, row in games_df.iterrows():
    date = row["date"]

    # Away starter
    process_pitcher(
        pitcher_name=row["away_pitcher"],
        game_date=date,
        team=row["away_team"],
        opponent=row["home_team"],
        is_home=False
    )

    # Home starter
    process_pitcher(
        pitcher_name=row["home_pitcher"],
        game_date=date,
        team=row["home_team"],
        opponent=row["away_team"],
        is_home=True
    )

# === Save results
output_df = pd.DataFrame(pred_rows)
os.makedirs("outputs", exist_ok=True)
output_df.to_csv("outputs/pitcher_k_predictions.csv", index=False)
print(f"\n Saved {len(output_df)} predictions to outputs/pitcher_k_predictions.csv")
