import subprocess
import os
from datetime import datetime
import time

log = []  # Collect log entries

def log_msg(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    log.append(entry)
    print(entry)

steps = [
    (" Step 1: Scrape latest data", "pipeline_logic/Step1_Scrape_All.py"),
    ("🧱 Step 2: Build training dataset", "pipeline_logic/build_team_runs_dataset.py"),
    ("🧠 Step 3: Predict upcoming games", "pipeline_logic/predict_runs.py"),
    (" Step 4: Backfill historical predictions", "pipeline_logic/backfill_predictions.py"),
    (" Step 5: Backfill pitcher K predictions", "pipeline_logic/backfill_pitcher_ks.py"),
    (" Step 6: Predict pitcher strikeouts (future)", "pipeline_logic/predict_pitcher_ks.py"),
    (" Step 7: Predict team over/under picks", "pipeline_logic/predict_team_overs_and_unders.py"),
    (" DONE! Now run: streamlit run app.py", None),
]

# Run pipeline steps
for label, script in steps:
    log_msg(f"=== {label} ===")
    if script:
        start = time.time()
        result = subprocess.run(["python", script])
        elapsed = round(time.time() - start, 2)
        if result.returncode != 0:
            log_msg(f" Error in {script} (⏱ {elapsed}s). Halting pipeline.")
            break
        else:
            log_msg(f" Completed {script} (⏱ {elapsed}s)")
else:
    log_msg(" All steps completed successfully.")

    # === Timestamp this run ===
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("predictions", exist_ok=True)
    last_updated_path = "predictions/last_updated.txt"
    with open(last_updated_path, "w") as f:
        f.write(timestamp_str)
    log_msg(f" Updated timestamp in {last_updated_path}: {timestamp_str}")

    # === Remote (GitHub Actions) check: skip timestamp logic, always force push ===
if os.getenv("GITHUB_ACTIONS") == "true":
    log_msg("🤖 GitHub Actions: Skipping timestamp check. Forcing push.")

# === Local or CI push ===
log_msg(" Syncing changes to GitHub...")

subprocess.run(["git", "add", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

commit = subprocess.run(
    ["git", "commit", "-m", " Auto-update: latest predictions and backfills"],
    capture_output=True,
    text=True
)

if "nothing to commit" not in commit.stdout:
    log_msg(" Committing new changes...")

    # Force push to ensure local changes overwrite remote
    push = subprocess.run(["git", "push", "--force", "origin", "main"])

    if push.returncode == 0:
        log_msg(" Force pushed to GitHub successfully.")
    else:
        log_msg(" Git push failed. Check remote settings or authentication.")
else:
    log_msg(" No changes to commit. Git push skipped.")

