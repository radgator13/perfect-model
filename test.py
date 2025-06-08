import pandas as pd
import glob

archive_files = glob.glob("data/archive/*/stathead_pitching_scrape_*.csv")
all_dfs = []

for f in archive_files:
    df = pd.read_csv(f)
    all_dfs.append(df)

master = pd.concat(all_dfs, ignore_index=True)
master.drop_duplicates(subset=["Player", "Date", "Team", "IP", "Result"], inplace=True)
master.to_csv("data/Stathead_2025_Pitcher_Master.csv", index=False)

print(f"✅ Master rebuilt from {len(archive_files)} archive files: {len(master)} rows.")
