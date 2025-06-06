import pandas as pd
import numpy as np
import joblib
import os

# === Load files ===
pitching = pd.read_csv("data/Stathead_2025_Pitcher_Master.csv")
model = joblib.load("models/pitcher_k_model.joblib")

# === Clean data ===
pitching["Date"] = pd.to_datetime(pitching["Date"].astype(str).str.extract(r"^(\d{4}-\d{2}-\d{2})")[0])
pitching["SO"] = pd.to_numeric(pitching["SO"], errors="coerce")
pitching["IP"] = pd.to_numeric(pitching["IP"], errors="coerce")
pitching["ER"] = pd.to_numeric(pitching["ER"], errors="coerce")
pitching["BB"] = pd.to_numeric(pitching["BB"], errors="coerce")
pitching["BF"] = pd.to_numeric(pitching["BF"], errors="coerce")
pitching["Home"] = pitching["Unnamed: 5"].apply(lambda x: 0 if x == "@" else 1)

# === Convert IP to float
def convert_ip(ip):
    try:
        whole, frac = str(ip).split('.') if '.' in str(ip) else (str(ip), '0')
        return float(whole) + float(frac) / 3
    except:
        return 0.0

pitching["IP_float"] = pitching["IP"].apply(convert_ip)
pitching = pitching.sort_values(["Player", "Date"])

# === Get rolling 3-game averages
rolling = pitching.groupby("Player").rolling(3, on="Date")[["SO", "IP", "ER", "BB", "BF"]].mean().reset_index()
rolling = rolling.rename(columns={
    "SO": "K_last3", "IP": "IP_last3", "ER": "ER_last3",
    "BB": "BB_last3", "BF": "BF_last3"
})

# === Merge back to identify usable starts
pitching = pitching.merge(rolling, on=["Player", "Date"], how="left")

# === Filter to starting pitchers (IP ≥ 3.5)
pitching["Is_SP"] = pitching["IP_float"] >= 3.5
pitching_starts = pitching[pitching["Is_SP"]]

# === Build feature matrix
pitching_starts = pitching_starts.dropna(subset=["K_last3", "IP_last3", "ER_last3", "BB_last3", "BF_last3"])
features = ["K_last3", "IP_last3", "ER_last3", "BB_last3", "BF_last3", "Home"]

X = pitching_starts[features]
y = pitching_starts["SO"]
dates = pitching_starts["Date"]
pitchers = pitching_starts["Player"]
teams = pitching_starts["Team"]
opponents = pitching_starts["Opp"]

# === Predict K’s
predicted_ks = model.predict(X)

# === Build output
backfill_df = pd.DataFrame({
    "Date": dates,
    "Team": teams,
    "Opponent": opponents,
    "Pitcher": pitchers,
    "Predicted_Ks": np.round(predicted_ks, 2),
    "Actual_Ks": y
})

# === Deduplicate by pitcher/date just in case
backfill_df = backfill_df.drop_duplicates(subset=["Date", "Pitcher"])

# === Save
os.makedirs("data", exist_ok=True)
backfill_df.to_csv("data/backfilled_pitcher_ks.csv", index=False)
print("✅ Backfilled pitcher K predictions saved to data/backfilled_pitcher_ks.csv")
