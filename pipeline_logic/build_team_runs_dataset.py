import pandas as pd
import numpy as np
from unidecode import unidecode

print(" Starting script...")

# === Load Data ===
pitcher_df = pd.read_csv("data/Stathead_2025_Pitcher_Master.csv")
batting_df = pd.read_csv("data/Stathead_2025_TeamBatting_Master.csv")
team_pitching_df = pd.read_csv("data/Stathead_2025_TeamPitching_Master.csv")

print(f" Loaded pitcher_df: {len(pitcher_df)} rows")
print(f" Loaded batting_df: {len(batting_df)} rows")
print(f" Loaded team_pitching_df: {len(team_pitching_df)} rows")

# === Clean & Parse Dates ===
pitcher_df["Date"] = pd.to_datetime(pitcher_df["Date"].astype(str).str.extract(r"^(\d{4}-\d{2}-\d{2})")[0])
batting_df["Date"] = pd.to_datetime(batting_df["Date"], errors="coerce")
team_pitching_df["Date"] = pd.to_datetime(team_pitching_df["Date"], errors="coerce")

# === Identify Starting Pitchers ===
pitcher_df["Home"] = pitcher_df["Unnamed: 5"].ne("@").astype(int)
ip_parts = pitcher_df["IP"].astype(str).str.extract(r"(?P<whole>\d+)(?:\.(?P<frac>\d))?")
pitcher_df["IP_float"] = ip_parts["whole"].astype(float) + ip_parts["frac"].fillna(0).astype(float) / 3.0
pitcher_df["Is_SP"] = pitcher_df["IP_float"] >= 3.5
starters = pitcher_df[pitcher_df["Is_SP"]].copy()
starters = starters.sort_values("BF", ascending=False).dropna(subset=["BF"])
starters = starters.groupby(["Date", "Team"]).head(1)

print(f" Found {len(starters)} starting pitcher rows")

# === Get SP Rolling Stats ===
def rolling_pitcher_stats(df, window=3):
    df = df.sort_values(["Player", "Date"])
    df["ER"] = pd.to_numeric(df["ER"], errors="coerce").fillna(0)
    df["H"] = pd.to_numeric(df["H"], errors="coerce").fillna(0)
    df["BB"] = pd.to_numeric(df["BB"], errors="coerce").fillna(0)
    ip_parts = df["IP"].astype(str).str.extract(r"(?P<whole>\d+)(?:\.(?P<frac>\d))?")
    df["IP_float"] = ip_parts["whole"].astype(float) + ip_parts["frac"].fillna(0).astype(float) / 3.0

    rolling = df.groupby("Player").rolling(window=window, on="Date").agg({
        "ER": "sum",
        "IP_float": "sum",
        "H": "sum",
        "BB": "sum"
    }).reset_index()

    rolling["ERA_rolling"] = (rolling["ER"] * 9) / rolling["IP_float"].replace(0, np.nan)
    rolling["WHIP_rolling"] = (rolling["H"] + rolling["BB"]) / rolling["IP_float"].replace(0, np.nan)

    return rolling[["Player", "Date", "ERA_rolling", "WHIP_rolling"]]

sp_rolling = rolling_pitcher_stats(pitcher_df)

print(f" sp_rolling generated: {len(sp_rolling)} rows")


# === Normalize names for merge
def normalize_name(name):
    return unidecode(str(name)).lower().strip()

starters["Player"] = starters["Player"].apply(normalize_name)
sp_rolling["Player"] = sp_rolling["Player"].apply(normalize_name)

# === DEBUG: show sample merge keys
print(" Starter Info Keys:")
print(starters[["Player", "Date"]].drop_duplicates().head())

print(" Rolling Stats Keys:")
print(sp_rolling[["Player", "Date"]].drop_duplicates().head())

# === Batting Rolling
batting_df = batting_df.sort_values(["Team", "Date"])
batting_df["Runs"] = pd.to_numeric(batting_df["R"], errors="coerce")
batting_df["OBP"] = pd.to_numeric(batting_df["OBP"], errors="coerce")

batting_rolling = batting_df.groupby("Team").rolling(3, on="Date").agg({
    "Runs": "mean", "OBP": "mean"
}).reset_index().rename(columns={"Runs": "Runs_avg3", "OBP": "OBP_avg3"})

print(f" Team batting rolling: {len(batting_rolling)} rows")

# === Team Pitching Rolling
team_pitching_df["H"] = pd.to_numeric(team_pitching_df["H"], errors="coerce").fillna(0)
team_pitching_df["BB"] = pd.to_numeric(team_pitching_df["BB"], errors="coerce").fillna(0)
team_pitching_df["ER"] = pd.to_numeric(team_pitching_df["ER"], errors="coerce").fillna(0)

ip_parts = team_pitching_df["IP"].astype(str).str.extract(r"(?P<whole>\d+)(?:\.(?P<frac>\d))?")
team_pitching_df["IP_float"] = ip_parts["whole"].astype(float) + ip_parts["frac"].fillna(0).astype(float) / 3.0
team_pitching_df["WHIP"] = (team_pitching_df["H"] + team_pitching_df["BB"]) / team_pitching_df["IP_float"].replace(0, np.nan)

pitching_rolling = team_pitching_df.sort_values(["Team", "Date"]).groupby("Team").rolling(3, on="Date").agg({
    "ER": "mean", "WHIP": "mean"
}).reset_index().rename(columns={"ER": "Team_ER_avg3", "WHIP": "Team_WHIP_avg3"})

print(f" Opponent team pitching rolling: {len(pitching_rolling)} rows")

# === Build Dataset
final_df = batting_df[["Date", "Team", "Opp", "Runs"]].copy()
print(" Initial team-game base:", len(final_df))

final_df = final_df.merge(batting_rolling[["Team", "Date", "Runs_avg3", "OBP_avg3"]], on=["Team", "Date"], how="left")
final_df = final_df.merge(pitching_rolling.rename(columns={"Team": "Opp"}), on=["Opp", "Date"], how="left")

# === Merge SP Info
starter_info = starters[["Date", "Team", "Player", "IP_float", "Home"]].drop_duplicates(subset=["Date", "Team"])
starter_info["Player"] = starter_info["Player"].apply(normalize_name)
starter_info = starter_info.merge(sp_rolling, on=["Player", "Date"], how="left")

final_df = final_df.merge(
    starter_info[["Date", "Team", "Player", "IP_float", "ERA_rolling", "WHIP_rolling", "Home"]],
    on=["Date", "Team"], how="left"
)

# === Opponent SP
opp_starters = pitcher_df[pitcher_df["IP_float"] >= 3.5].copy()
opp_starters = opp_starters.sort_values("BF", ascending=False).dropna(subset=["BF"])
opp_starters = opp_starters.groupby(["Date", "Team"]).head(1)

opp_starters["Player"] = opp_starters["Player"].apply(normalize_name)
opp_starter_info = opp_starters[["Date", "Team", "Player", "IP_float"]].copy()
opp_starter_info = opp_starter_info.merge(sp_rolling, on=["Player", "Date"], how="left")

final_df = final_df.merge(
    opp_starter_info[["Date", "Team", "Player", "IP_float", "ERA_rolling", "WHIP_rolling"]],
    left_on=["Date", "Opp"], right_on=["Date", "Team"], how="left", suffixes=("", "_opp")
)

# === Final Rename
final_df.rename(columns={
    "Runs": "Target_Runs",
    "Player": "Starting_Pitcher",
    "ERA_rolling": "SP_ERA_3g",
    "WHIP_rolling": "SP_WHIP_3g",
    "IP_float": "SP_IP",
    "Player_opp": "Opp_SP_Name",
    "ERA_rolling_opp": "Opp_SP_ERA_3g",
    "WHIP_rolling_opp": "Opp_SP_WHIP_3g",
    "IP_float_opp": "Opp_SP_IP"
}, inplace=True)

# === Final Checks
print(" Columns before dropna:", final_df.columns.tolist())
print(" Null counts before dropna:\n", final_df[[
    "Runs_avg3", "OBP_avg3", "Team_ER_avg3",
    "SP_ERA_3g", "SP_IP",
    "Opp_SP_ERA_3g", "Opp_SP_IP",
    "Home"
]].isna().sum())

print(" Row count before dropna:", len(final_df))
final_df.dropna(subset=[
    "Runs_avg3", "OBP_avg3", "Team_ER_avg3",
    "SP_ERA_3g", "SP_IP",
    "Opp_SP_ERA_3g", "Opp_SP_IP",
    "Home"
], inplace=True)

print(" Final dataset row count:", len(final_df))
print("🧪 Sample with Opponent SP + Home flag:\n", final_df[[
    "Date", "Team", "Opp", "Home", "Opp_SP_Name", "Opp_SP_ERA_3g", "Opp_SP_IP"
]].head())

# === Export
final_df.to_csv("data/team_run_prediction_dataset.csv", index=False)
print(" Dataset exported to 'data/team_run_prediction_dataset.csv'")
