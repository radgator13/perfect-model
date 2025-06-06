import subprocess

steps = [
    ("📥 Step 1: Scrape latest data", "pipeline_logic/Step1_Scrape_All.py"),
    ("🧱 Step 2: Build training dataset", "pipeline_logic/build_team_runs_dataset.py"),
    ("🧠 Step 3: Predict upcoming games", "pipeline_logic/predict_runs.py"),
    ("📊 Step 4: Backfill historical predictions", "pipeline_logic/backfill_predictions.py"),
    ("🔥 Step 5: Backfill pitcher K predictions", "pipeline_logic/backfill_pitcher_ks.py"),
    ("🎯 Step 6: Predict pitcher strikeouts (future)", "pipeline_logic/predict_pitcher_ks.py"),
    ("📈 Step 7: Predict team over/under picks", "pipeline_logic/predict_team_overs_and_unders.py"),
    ("✅ DONE! Now run: streamlit run app.py", None),
]

for label, script in steps:
    print(f"\n=== {label} ===")
    if script:
        result = subprocess.run(["python", script])
        if result.returncode != 0:
            print(f"❌ Error in {script}. Halting pipeline.")
            break
