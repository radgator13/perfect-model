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
    log_msg(f"=== {label} ===")
    if script:
        start = time.time()
        result = subprocess.run(["python", script])
        elapsed = round(time.time() - start, 2)
        if result.returncode != 0:
            log_msg(f"❌ Error in {script} (⏱ {elapsed}s). Halting pipeline.")
            break
        else:
            log_msg(f"✅ Completed {script} (⏱ {elapsed}s)")
else:
    log_msg("🚀 All steps completed successfully.")

    # === Timestamp this run ===
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("predictions", exist_ok=True)
    last_updated_path = "predictions/last_updated.txt"
    with open(last_updated_path, "w") as f:
        f.write(timestamp_str)
    log_msg(f"📌 Updated timestamp in {last_updated_path}: {timestamp_str}")

    # === Remote (GitHub Actions) check: skip if data is stale ===
    if os.getenv("GITHUB_ACTIONS") == "true":
        try:
            log_msg("🤖 GitHub Actions: Checking for stale data before push...")
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)

            with open(last_updated_path, "r") as f:
                new_time = datetime.strptime(f.read().strip(), "%Y-%m-%d %H:%M:%S")

            result = subprocess.run(
                ["git", "show", "origin/main:predictions/last_updated.txt"],
                capture_output=True,
                text=True
            )
            remote_time = datetime.strptime(result.stdout.strip(), "%Y-%m-%d %H:%M:%S")

            if new_time <= remote_time:
                log_msg(f"⚠️ Remote data is newer or equal (remote: {remote_time}, new: {new_time}). Skipping push.")
                exit(0)
            else:
                log_msg(f"✅ This run is newer (new: {new_time} > remote: {remote_time}). Proceeding to push.")

        except Exception as e:
            log_msg("⚠️ Timestamp check failed. Proceeding to push just in case.")
            log_msg(str(e))

    # === Local or approved push ===
    log_msg("📡 Syncing changes to GitHub...")

    subprocess.run(["git", "add", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    commit = subprocess.run(
        ["git", "commit", "-m", "🔄 Auto-update: latest predictions and backfills"],
        capture_output=True,
        text=True
    )

    if "nothing to commit" not in commit.stdout:
        log_msg("📦 Committing new changes...")

        pull = subprocess.run(["git", "pull", "--rebase", "origin", "main"])
        if pull.returncode == 0:
            push = subprocess.run(["git", "push", "origin", "main"])
            if push.returncode == 0:
                log_msg("✅ Pushed to GitHub successfully.")
            else:
                log_msg("⚠️ Git push failed. Check remote settings or authentication.")
        else:
            log_msg("❌ Git pull failed. Resolve merge conflicts manually.")
    else:
        log_msg("✅ No changes to commit. Git push skipped.")

# === Final Summary Log ===
print("\n📄 Execution Summary:")
print("\n".join(log))
