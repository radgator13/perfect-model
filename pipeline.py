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

# Run pipeline steps
for label, script in steps:
    print(f"\n=== {label} ===")
    if script:
        result = subprocess.run(["python", script])
        if result.returncode != 0:
            print(f"❌ Error in {script}. Halting pipeline.")
            break
else:
    # All steps completed successfully
    print("\n🚀 All steps completed successfully. Committing and pushing to GitHub...")

    subprocess.run(["git", "add", "."])
    commit = subprocess.run(
        ["git", "commit", "-m", "🔄 Auto-update: latest predictions and backfills"],
        capture_output=True,
        text=True
    )

    if "nothing to commit" not in commit.stdout:
        push = subprocess.run(["git", "push", "origin", "main"])
        if push.returncode == 0:
            print("✅ Pushed to GitHub successfully.")
        else:
            print("⚠️ Git push failed. Check your authentication or remote settings.")
    else:
        print("✅ No changes to commit. Git push skipped.")
