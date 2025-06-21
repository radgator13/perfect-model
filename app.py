import streamlit as st
import pandas as pd
import urllib.parse
import numpy as np


st.set_page_config(page_title="MLB All Stats Predictor", layout="wide")
params = st.query_params

#  Safely decode and store once
if "pitcher" in params and params.get("tab", ["0"])[0] == "3":
    pitcher_param_raw = params["pitcher"][0]
    if "selected_pitcher" not in st.session_state:
        st.session_state.selected_pitcher = pitcher_param_raw
# === Load Data ===
@st.cache_data
def load_predictions():
    pred = pd.read_csv("data/predicted_runs.csv", parse_dates=["date"])
    hist = pd.read_csv("data/backfilled_predictions.csv", parse_dates=["Date"])
    return pred.sort_values(["date", "team"]), hist.sort_values("Date")

pred_df, hist_df = load_predictions()

# === Shared Helpers ===
def get_confidence(pred, line):
    level = min(int(abs(pred - line) / 0.5), 5)
    return "" * level

def fireball_confidence(pred, threshold, side="over"):
    diff = pred - threshold if side == "over" else threshold - pred
    score = min(max(int(diff / 0.5), 0), 5)
    return "" * score if score > 0 else "No Pick"

# === Tab Logic with State ===
tab_labels = [
    " Upcoming Game Totals Predictions",                # 0
    " Historical Results For  Game Totals",             # 1
    " Fireball Performance For  Game Totals",           # 2
    " Single Team Game Predictions",                   # 3
    " Historical Results For Single-Team Predictions", # 4
    " Fireball Performance For Single-Team Predictions", # 5
    "🧠 Predicted Strikeouts (K’s)",                      # 6
    " Historical Strikeout Accuracy",                  # 7
    " Fireball Performance For Strikeout Predictions",   # 8  NEW
    "🧠 Predicted Game Spreads",                          #9
    " Historical Spread Accuracy",                      #10
    " Fireball Performance For Spread Predictions"      #11


]





params = st.query_params

if "tab" in params:
    try:
        st.session_state.active_tab = int(params["tab"][0])
    except:
        st.session_state.active_tab = 0

if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

tab_selection = st.radio(" Select View", tab_labels, index=st.session_state.active_tab, horizontal=True)
st.session_state.active_tab = tab_labels.index(tab_selection)

# === Tab: Upcoming Predictions ===
if st.session_state.active_tab == 0:
    st.markdown("##  Upcoming Game Total Predictions")
    st.subheader("Daily Game Totals Predictions")

    col1, col2 = st.columns([1, 3])

    with col1:
        run_line = st.slider(" Run line", 0.0, 17.0, 8.5, 0.1, key="run_line_tab0")
        dates = pred_df["date"].dt.date.unique()
        selected_date = st.selectbox(" Select date", options=dates, key="date_tab0")
        selected_team = st.selectbox(" Filter by team", ["All"] + sorted(pred_df["team"].unique()), key="team_tab0")

    with col2:
        # === Filter by selected date
        df = pred_df[pred_df["date"].dt.date == selected_date].copy()

        if selected_team != "All":
            df = df[(df["team"] == selected_team) | (df["opponent"] == selected_team)]

        # === Create unique matchup key (team1|team2 sorted alphabetically)
        df["matchup"] = df.apply(lambda row: "|".join(sorted([row["team"], row["opponent"]])), axis=1)

        # === Deduplicate and aggregate
        grouped = df.groupby("matchup").agg({
            "date": "first",
            "team": "first",
            "opponent": "first",
            "starting_pitcher": "first",
            "opponent_pitcher": "first",
            "predicted_runs": "sum"
        }).reset_index()

        # === Derived logic
        grouped["Predicted_Total"] = grouped["predicted_runs"]
        grouped["Direction"] = grouped["Predicted_Total"].apply(lambda x: "Over" if x > run_line else "Under")
        grouped["Confidence"] = grouped["Predicted_Total"].apply(lambda x: get_confidence(x, run_line))

        st.dataframe(grouped.rename(columns={
            "team": "Home Team",
            "opponent": "Opponent",
            "starting_pitcher": "Home SP",
            "opponent_pitcher": "Opponent SP",
            "Predicted_Total": "Predicted Runs"
        })[[
            "date", "Home Team", "Opponent", "Home SP", "Opponent SP",
            "Predicted Runs", "Direction", "Confidence"
        ]], use_container_width=True)



# === Tab: Historical Results ===
elif st.session_state.active_tab == 1:
    st.markdown("##  Historical Results For Game Totals With Predictions")
    st.subheader("Compare Model vs Actual Results")

    col1, col2 = st.columns([1, 3])

    with col1:
        hist_line = st.slider(" Run line", 0.0, 20.0, 8.5, 0.5, key="hist_line_tab1")
        hist_selected_date = st.date_input(" Filter by date", value=None, key="date_tab1")

    with col2:
        hist_df_all = hist_df.copy()
        hist_df_all["Direction"] = hist_df_all["Predicted_Total"].apply(lambda x: "Over" if x > hist_line else "Under")
        hist_df_all["Actual_Direction"] = hist_df_all["Actual_Total"].apply(lambda x: "Over" if x > hist_line else "Under")
        hist_df_all["Hit"] = hist_df_all["Direction"] == hist_df_all["Actual_Direction"]
        hist_df_all["Confidence"] = hist_df_all["Predicted_Total"].apply(lambda x: get_confidence(x, hist_line))

        daily = hist_df_all.copy()
        if hist_selected_date:
            daily["match_date"] = pd.to_datetime(daily["Date"]).dt.date
            daily = daily[daily["match_date"] == hist_selected_date]

        st.dataframe(daily[[
            "Date", "Home_Team", "Away_Team", "Home_SP", "Away_SP",
            "Predicted_Home", "Predicted_Away", "Predicted_Total", "Actual_Total",
            "Direction", "Actual_Direction", "Hit", "Confidence"
        ]], use_container_width=True)

        total_daily = len(daily)
        hits_daily = daily["Hit"].sum()
        pct_daily = round(100 * hits_daily / total_daily, 1) if total_daily else 0

        rolling = hist_df_all.copy()
        if hist_selected_date:
            rolling["match_date"] = pd.to_datetime(rolling["Date"]).dt.date
            rolling = rolling[rolling["match_date"] <= hist_selected_date]

        total_all = len(rolling)
        hits_all = rolling["Hit"].sum()
        pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

        colA, colB = st.columns(2)
        with colA:
            st.markdown(f" **Daily:** {hits_daily}/{total_daily} correct ({pct_daily}%)")
        with colB:
            st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")

# === Tab: Fireball Performance ===
elif st.session_state.active_tab == 2:
    st.markdown("##  Fireball Performance for Game Total Predictions")
    st.subheader("Model Accuracy at High Confidence")

    col1, col2 = st.columns([1, 3])

    with col1:
        fire_line = st.slider(" Run line", 0.0, 20.0, 8.5, 0.5, key="fire_line_tab2")
        fire_level = st.slider(" Confidence Level", 1, 5, 3, key="fire_level_tab2")
        fire_date = st.date_input(" Filter by date", value=None, key="date_tab2")

    with col2:
        hist_df["Fire_Level"] = hist_df["Predicted_Total"].apply(lambda x: min(int(abs(x - fire_line) / 0.5), 5))
        hist_df["Direction"] = hist_df["Predicted_Total"].apply(lambda x: "Over" if x > fire_line else "Under")
        hist_df["Actual_Direction"] = hist_df["Actual_Total"].apply(lambda x: "Over" if x > fire_line else "Under")
        hist_df["Hit"] = hist_df["Direction"] == hist_df["Actual_Direction"]

        filtered = hist_df[hist_df["Fire_Level"] == fire_level]
        if fire_date:
            filtered = filtered[filtered["Date"].dt.date == fire_date]

        st.dataframe(filtered[[
            "Date", "Home_Team", "Away_Team", "Predicted_Total", "Actual_Total",
            "Direction", "Actual_Direction", "Hit"
        ]], use_container_width=True)

        total_day = len(filtered)
        hits_day = filtered["Hit"].sum()
        pct_day = round(100 * hits_day / total_day, 1) if total_day else 0

        up_to = hist_df[(hist_df["Fire_Level"] == fire_level) &
                        (hist_df["Date"] <= pd.to_datetime(fire_date))] if fire_date else hist_df[hist_df["Fire_Level"] == fire_level]

        total_all = len(up_to)
        hits_all = up_to["Hit"].sum()
        pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f" **Daily:** {hits_day}/{total_day} correct ({pct_day}%)")
        with col2:
            st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")


# === Tab 3: Team Game Total Predictions ===
elif st.session_state.active_tab == 3:
    import urllib.parse
    import datetime

    st.markdown("##  Team Game Total Predictions")
    st.subheader("Over/Under Confidence for Team Totals")

    try:
        team_df = pd.read_csv("outputs/team_predictions.csv")
        pitcher_df = pd.read_csv("data/Stathead_2025_Pitcher_Master.csv")

        team_df["date"] = pd.to_datetime(team_df["date"]).dt.date
        pitcher_df["Date"] = pitcher_df["Date"].astype(str).str.extract(r"^(\d{4}-\d{2}-\d{2})")[0]
        pitcher_df["Date"] = pd.to_datetime(pitcher_df["Date"], errors="coerce")

        # === Read query params
        params = st.query_params

        # Decode and store pitcher in session
        if "pitcher" in params and params.get("tab", ["0"])[0] == "3":
            pitcher_raw = params.get("pitcher")
            if isinstance(pitcher_raw, list):
                decoded_name = urllib.parse.unquote(pitcher_raw[0])
            else:
                decoded_name = urllib.parse.unquote(pitcher_raw)
            st.session_state.selected_pitcher = decoded_name

        # Parse date from query string (if any)
        default_date = datetime.date.today()
        if "date" in params:
            try:
                default_date = datetime.datetime.fromisoformat(params["date"]).date()
            except:
                pass

        # === Game Log FIRST
        if "selected_pitcher" in st.session_state:
            selected_name = st.session_state.selected_pitcher
            st.markdown(f"##  Game Log for {selected_name}")

            try:
                pitcher_log_df = pd.read_csv("data/Stathead_2025_Pitcher_Master.csv")
                pitcher_log_df["Date"] = pitcher_log_df["Date"].astype(str).str.extract(r"^(\d{4}-\d{2}-\d{2})")[0]
                pitcher_log_df["Date"] = pd.to_datetime(pitcher_log_df["Date"], errors="coerce")

                filtered_log = pitcher_log_df[pitcher_log_df["Player"] == selected_name]
                if filtered_log.empty:
                    st.info("No games found for this pitcher.")
                else:
                    st.dataframe(filtered_log.sort_values("Date", ascending=False), use_container_width=True)

                if st.button(" Clear pitcher view"):
                    del st.session_state.selected_pitcher
                    st.query_params.clear()
                    st.rerun()

            except FileNotFoundError:
                st.error("Pitcher game log not found.")

        # === Controls
        team_date = st.date_input(" Select date", value=default_date, key="team_date_tab3")
        threshold = st.slider(" Threshold (runs)", 0.0, 10.0, 4.5, step=0.5, key="threshold_slider_tab3")
        sort_choice = st.radio(" Sort by", ["Over ", "Under "], horizontal=True, key="sort_choice_tab3")

        # === Filter and enrich data
        filtered_df = team_df.copy()
        if team_date:
            filtered_df = filtered_df[filtered_df["date"] == team_date]

        def fireball_confidence(pred, threshold, side="over"):
            diff = pred - threshold if side == "over" else threshold - pred
            score = min(max(int(diff / 0.5), 0), 5)
            return "" * score if score > 0 else "No Pick"

        filtered_df["Over_Conf"] = filtered_df["predicted_runs"].apply(lambda x: fireball_confidence(x, threshold, "over"))
        filtered_df["Under_Conf"] = filtered_df["predicted_runs"].apply(lambda x: fireball_confidence(x, threshold, "under"))
        filtered_df["Over_Score"] = filtered_df["Over_Conf"].apply(lambda x: len(x) if "" in x else 0)
        filtered_df["Under_Score"] = filtered_df["Under_Conf"].apply(lambda x: len(x) if "" in x else 0)

        sort_col = "Over_Score" if sort_choice == "Over " else "Under_Score"
        filtered_df = filtered_df.sort_values(by=sort_col, ascending=False)

        # === Link builder
        def make_clickable(name, selected_date):
            encoded = urllib.parse.quote(name)
            date_part = f"&date={selected_date.isoformat()}" if selected_date else ""
            return f'<a href="?pitcher={encoded}&tab=3{date_part}" target="_self">{name}</a>'

        filtered_df["starting_pitcher_link"] = filtered_df["starting_pitcher"].apply(lambda name: make_clickable(name, team_date))

        base_cols = ["date", "team", "opponent", "starting_pitcher_link", "opponent_pitcher", "predicted_runs"]
        display_cols = base_cols + ["Over_Conf", "Under_Conf"]
        rename_columns = {
            "starting_pitcher_link": "SP (click to view)",
            "Over_Conf": f"Over {threshold} ",
            "Under_Conf": f"Under {threshold} "
        }

        st.markdown(f"**Confidence at selected threshold: {threshold} runs**")

        # === Styling
        st.markdown("""
        <style>
        .centered-table-container {
            display: flex;
            justify-content: center;
        }
        .centered-table-container table {
            width: 90%;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(
            f'<div class="centered-table-container">{filtered_df[display_cols].rename(columns=rename_columns).to_html(escape=False, index=False)}</div>',
            unsafe_allow_html=True
        )

    except FileNotFoundError:
        st.warning("Team predictions or pitcher log not found.")

elif st.session_state.active_tab == 4:
    st.markdown("##  Historical Results For Single-Team Predictions")
    st.subheader("Compare model predictions with actual results (by team)")

    import datetime

    try:
        # === Load predictions
        df = pd.read_csv("data/backfilled_predictions.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # === Controls
        col1, col2 = st.columns([1, 3])

        with col1:
            hist_line = st.slider(" Run line", 0.0, 7.0, 3.5, 0.5, key="hist_line_tab5")
            hist_selected_date = st.date_input(" Filter by date", value=None, key="date_tab5")

        with col2:
            # === Derived fields
            df["Direction"] = df["Predicted_Total"].apply(lambda x: "Over" if x > hist_line else "Under")
            df["Actual_Direction"] = df["Actual_Total"].apply(lambda x: "Over" if x > hist_line else "Under")
            df["Hit"] = df["Direction"] == df["Actual_Direction"]
            df["Confidence"] = df["Predicted_Total"].apply(lambda x: get_confidence(x, hist_line))

            daily = df.copy()
            if hist_selected_date:
                daily["match_date"] = df["Date"].dt.date
                daily = daily[daily["match_date"] == hist_selected_date]

            if daily.empty:
                st.warning(" No data matches the selected date.")
            else:
                st.dataframe(daily[[ 
                    "Date", "Home_Team", "Away_Team", "Home_SP", "Away_SP",
                    "Predicted_Home", "Predicted_Away", "Predicted_Total", "Actual_Total",
                    "Direction", "Actual_Direction", "Hit", "Confidence"
                ]], use_container_width=True)

            # === Accuracy summary
            total_daily = len(daily)
            hits_daily = daily["Hit"].sum()
            pct_daily = round(100 * hits_daily / total_daily, 1) if total_daily else 0

            rolling = df.copy()
            if hist_selected_date:
                rolling["match_date"] = rolling["Date"].dt.date
                rolling = rolling[rolling["match_date"] <= hist_selected_date]

            total_all = len(rolling)
            hits_all = rolling["Hit"].sum()
            pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

            colA, colB = st.columns(2)
            with colA:
                st.markdown(f" **Daily:** {hits_daily}/{total_daily} correct ({pct_daily}%)")
            with colB:
                st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")

    except FileNotFoundError:
        st.error("Missing file: `data/backfilled_predictions.csv`")
    except Exception as e:
        st.exception(e)

elif st.session_state.active_tab == 5:
    st.markdown("##  Fireball Performance for Single-Team Predictions")
    st.subheader("Model Accuracy at High Confidence (Per Team)")

    import datetime

    try:
        df = pd.read_csv("data/backfilled_predictions.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        col1, col2 = st.columns([1, 3])

        with col1:
            fire_line = st.slider(" Run line", 0.0, 7.0, 3.5, 0.5, key="fire_line_tab5")
            fire_level = st.slider(" Confidence Level", 1, 5, 3, key="fire_level_tab5")
            fire_date = st.date_input(" Filter by date", value=None, key="date_tab5")

        with col2:
            df["Fire_Level"] = df["Predicted_Total"].apply(lambda x: min(int(abs(x - fire_line) / 0.5), 5))
            df["Direction"] = df["Predicted_Total"].apply(lambda x: "Over" if x > fire_line else "Under")
            df["Actual_Direction"] = df["Actual_Total"].apply(lambda x: "Over" if x > fire_line else "Under")
            df["Hit"] = df["Direction"] == df["Actual_Direction"]

            filtered = df[df["Fire_Level"] == fire_level]
            if fire_date:
                filtered = filtered[filtered["Date"].dt.date == fire_date]

            st.dataframe(filtered[[ 
                "Date", "Home_Team", "Away_Team", "Predicted_Home", "Predicted_Away",
                "Predicted_Total", "Actual_Total", "Direction", "Actual_Direction", "Hit"
            ]], use_container_width=True)

            total_day = len(filtered)
            hits_day = filtered["Hit"].sum()
            pct_day = round(100 * hits_day / total_day, 1) if total_day else 0

            up_to = df[(df["Fire_Level"] == fire_level)]
            if fire_date:
                up_to = up_to[up_to["Date"] <= pd.to_datetime(fire_date)]

            total_all = len(up_to)
            hits_all = up_to["Hit"].sum()
            pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

            colA, colB = st.columns(2)
            with colA:
                st.markdown(f" **Daily:** {hits_day}/{total_day} correct ({pct_day}%)")
            with colB:
                st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")

    except FileNotFoundError:
        st.error("Missing file: `data/backfilled_predictions.csv`")
    except Exception as e:
        st.exception(e)

elif st.session_state.active_tab == 6:
    st.markdown("## 🧠 Predicted Strikeouts (K’s)")
    st.subheader("Projected strikeouts for today's starting pitchers")

    import datetime

    try:
        # Load predictions
        k_df = pd.read_csv("outputs/pitcher_k_predictions.csv")
        k_df["date"] = pd.to_datetime(k_df["date"]).dt.date

        col1, col2 = st.columns([1, 3])

        with col1:
            dates = k_df["date"].unique()
            selected_date = st.selectbox(" Select date", options=sorted(dates), key="date_tab6")
            selected_team = st.selectbox(" Filter by team", ["All"] + sorted(k_df["team"].unique()), key="team_tab6")
            threshold = st.slider(" Confidence Threshold (K’s)", 0.0, 15.0, 6.0, step=0.5, key="ks_threshold_tab6")

        with col2:
            filtered = k_df[k_df["date"] == selected_date]
            if selected_team != "All":
                filtered = filtered[(filtered["team"] == selected_team) | (filtered["opponent"] == selected_team)]

            def k_confidence(pred, threshold):
                diff = abs(pred - threshold)
                score = min(int(diff // 0.5), 5)
                return "" * score if score > 0 else "No Pick"

            filtered["Confidence"] = filtered["predicted_ks"].apply(lambda x: k_confidence(x, threshold))

            st.dataframe(filtered.rename(columns={
                "team": "Team",
                "opponent": "Opponent",
                "starting_pitcher": "Pitcher",
                "predicted_ks": "Predicted K’s"
            })[[
                "date", "Team", "Opponent", "Pitcher", "Predicted K’s", "Confidence"
            ]], use_container_width=True)

    except FileNotFoundError:
        st.error("Missing file: outputs/pitcher_k_predictions.csv")
    except Exception as e:
        st.exception(e)

elif st.session_state.active_tab == 7:
    st.markdown("##  Historical Strikeout Accuracy")
    st.subheader("Compare model predictions with actual results per pitcher")

    import datetime

    try:
        df = pd.read_csv("data/backfilled_pitcher_ks.csv")
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

        col1, col2 = st.columns([1, 3])

        with col1:
            # === UI Controls
            threshold = st.slider(" Confidence Threshold (K’s)", 0.0, 15.0, 6.0, step=0.5, key="ks_threshold_tab7")
            selected_date = st.date_input(" Filter by date", value=df["Date"].max(), key="ks_date_tab7")
            selected_pitcher = st.selectbox(" Filter by pitcher", ["All"] + sorted(df["Pitcher"].dropna().unique()), key="ks_pitcher_tab7")

        with col2:
            # === Derived logic
            df["Direction"] = df["Predicted_Ks"].apply(lambda x: "Over" if x > threshold else "Under")
            df["Actual_Direction"] = df["Actual_Ks"].apply(lambda x: "Over" if x > threshold else "Under")
            df["Hit"] = df["Direction"] == df["Actual_Direction"]

            def fireball_confidence(pred, threshold):
                diff = abs(pred - threshold)
                score = min(max(int(diff / 0.5), 0), 5)
                return "" * score if score > 0 else "No Pick"

            df["Confidence"] = df["Predicted_Ks"].apply(lambda x: fireball_confidence(x, threshold))

            # === Filter
            filtered = df.copy()
            if selected_date:
                filtered = filtered[filtered["Date"] == selected_date]
            if selected_pitcher != "All":
                filtered = filtered[filtered["Pitcher"] == selected_pitcher]

            st.dataframe(filtered[[
                "Date", "Team", "Opponent", "Pitcher",
                "Predicted_Ks", "Actual_Ks", "Direction", "Actual_Direction", "Hit", "Confidence"
            ]], use_container_width=True)

            # === Accuracy stats
            total_daily = len(filtered)
            hits_daily = filtered["Hit"].sum()
            pct_daily = round(100 * hits_daily / total_daily, 1) if total_daily else 0

            rolling = df.copy()
            if selected_date:
                rolling = rolling[rolling["Date"] <= selected_date]
            if selected_pitcher != "All":
                rolling = rolling[rolling["Pitcher"] == selected_pitcher]

            total_all = len(rolling)
            hits_all = rolling["Hit"].sum()
            pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

            colA, colB = st.columns(2)
            with colA:
                st.markdown(f" **Daily:** {hits_daily}/{total_daily} correct ({pct_daily}%)")
            with colB:
                st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")

    except FileNotFoundError:
        st.error("Missing file: `data/backfilled_pitcher_ks.csv`")
    except Exception as e:
        st.exception(e)

elif st.session_state.active_tab == 8:
    st.markdown("##  Fireball Performance for Pitcher Strikeout Predictions")
    st.subheader("Model Accuracy at High Confidence (K Totals)")

    import datetime
    import numpy as np

    try:
        df = pd.read_csv("data/backfilled_pitcher_ks.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        col1, col2 = st.columns([1, 3])

        with col1:
            fire_line = st.slider(" Strikeout Line", 0.0, 15.0, 6.5, 0.5, key="ks_fire_line_tab8")
            fire_level = st.slider(" Confidence Level", 1, 5, 3, key="ks_fire_level_tab8")
            fire_date = st.date_input(" Filter by date", value=None, key="ks_fire_date_tab8")

        with col2:
            # === Derived metrics
            df["Fire_Level"] = df["Predicted_Ks"].apply(lambda x: min(int(abs(x - fire_line) / 0.5), 5))
            df["Pick"] = df["Predicted_Ks"].apply(lambda x: "Over" if x > fire_line else "Under")
            df["Outcome"] = df["Actual_Ks"].apply(lambda x: "Over" if x > fire_line else "Under")
            df["Hit"] = df["Pick"] == df["Outcome"]
            df["K_Diff"] = abs(df["Predicted_Ks"] - df["Actual_Ks"])

            # Filter
            filtered = df[df["Fire_Level"] == fire_level]
            if fire_date:
                filtered = filtered[filtered["Date"].dt.date == fire_date]

            st.dataframe(filtered[[
                "Date", "Team", "Opponent", "Pitcher",
                "Predicted_Ks", "Actual_Ks", "K_Diff",
                "Pick", "Outcome", "Hit", "Fire_Level"
            ]].rename(columns={"Fire_Level": "Confidence"}), use_container_width=True)

            # === Accuracy summary
            total_day = len(filtered)
            hits_day = filtered["Hit"].sum()
            pct_day = round(100 * hits_day / total_day, 1) if total_day else 0

            up_to = df[df["Fire_Level"] == fire_level]
            if fire_date:
                up_to = up_to[up_to["Date"].dt.date <= fire_date]

            total_all = len(up_to)
            hits_all = up_to["Hit"].sum()
            pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

            colA, colB = st.columns(2)
            with colA:
                st.markdown(f" **Daily:** {hits_day}/{total_day} correct ({pct_day}%)")
            with colB:
                st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")

    except FileNotFoundError:
        st.error("Missing file: data/backfilled_pitcher_ks.csv")
    except Exception as e:
        st.exception(e)

elif st.session_state.active_tab == 9:
    st.markdown("## 🧠 Predicted Game Spreads")
    st.subheader("Projected run spreads based on predicted team totals")

    import datetime

    try:
        df = pred_df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date

        col1, col2 = st.columns([1, 3])

        with col1:
            spread_date = st.selectbox(" Select date", sorted(df["date"].unique()), key="spread_date_tab9")
            selected_team = st.selectbox(" Filter by team", ["All"] + sorted(df["team"].unique()), key="spread_team_tab9")

        with col2:
            df = df[df["date"] == spread_date]

            if selected_team != "All":
                df = df[(df["team"] == selected_team) | (df["opponent"] == selected_team)]

            # Create matchup key (regardless of home/away)
            df["matchup"] = df.apply(lambda row: "|".join(sorted([row["team"], row["opponent"]])), axis=1)

            # Pair team + opponent predictions
            grouped = df.groupby("matchup").agg({
                "date": "first",
                "team": "first",
                "opponent": "first",
                "predicted_runs": list
            }).reset_index()

            grouped = grouped[grouped["predicted_runs"].apply(lambda x: len(x) == 2)]

            # Compute spread
            def calc_spread(row):
                home_pred, away_pred = row["predicted_runs"]
                if row["team"] < row["opponent"]:
                    return home_pred - away_pred
                else:
                    return away_pred - home_pred

            grouped["Predicted_Spread"] = grouped["predicted_runs"].apply(lambda x: round(x[0] - x[1], 2))
            grouped = grouped.rename(columns={
                "team": "Team",
                "opponent": "Opponent"
            })

            st.dataframe(grouped[[
                "date", "Team", "Opponent", "Predicted_Spread"
            ]], use_container_width=True)

    except Exception as e:
        st.exception(e)

elif st.session_state.active_tab == 10:
    st.markdown("##  Historical Spread Accuracy")
    st.subheader("Compare predicted vs actual spreads")

    import datetime
    import numpy as np

    try:
        df = pd.read_csv("data/backfilled_predictions.csv")
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

        col1, col2 = st.columns([1, 3])

        with col1:
            spread_line = st.slider(" Spread line", -5.0, 5.0, 1.5, 0.5, key="spread_line_tab10")
            selected_date = st.date_input(" Filter by date", value=df["Date"].max(), key="spread_date_tab10")

        with col2:
            # === Compute predicted and actual spreads
            df["Predicted_Spread"] = df["Predicted_Home"] - df["Predicted_Away"]
            df["Actual_Margin"] = df["Home_R"] - df["Away_R"]

            # === Build final score column
            df["Final Score"] = df["Home_R"].astype(int).astype(str) + " - " + df["Away_R"].astype(int).astype(str)

            # === Over/Under logic
            df["Pick"] = df["Predicted_Spread"].apply(lambda x: "Over" if x > spread_line else "Under")
            df["Outcome"] = df["Actual_Margin"].apply(lambda x: "Over" if x > spread_line else "Under")
            df["Hit"] = df["Pick"] == df["Outcome"]

            def spread_confidence(pred_spread, line):
                diff = abs(pred_spread - line)
                score = min(int(diff / 0.5), 5)
                return "" * score if score > 0 else "No Pick"

            df["Confidence"] = df["Predicted_Spread"].apply(lambda x: spread_confidence(x, spread_line))

            # === Filter by date
            filtered = df[df["Date"] == selected_date].copy()

            st.dataframe(filtered[[
                "Date", "Home_Team", "Away_Team",
                "Predicted_Home", "Predicted_Away", "Final Score",
                "Predicted_Spread", "Pick", "Outcome", "Hit", "Confidence"
            ]], use_container_width=True)

            # === Accuracy summary
            total = len(filtered)
            hits = filtered["Hit"].sum()
            pct_daily = round(100 * hits / total, 1) if total else 0

            rolling = df[df["Date"] <= selected_date]
            total_all = len(rolling)
            hits_all = rolling["Hit"].sum()
            pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

            colA, colB = st.columns(2)
            with colA:
                st.markdown(f" **Daily:** {hits}/{total} correct ({pct_daily}%)")
            with colB:
                st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")

    except FileNotFoundError:
        st.error("Missing file: data/backfilled_predictions.csv")
    except Exception as e:
        st.exception(e)







elif st.session_state.active_tab == 11:
    st.markdown("##  Fireball Performance for Spread Predictions")
    st.subheader("Model Accuracy at High Confidence (Run Spreads)")

    import datetime
    import numpy as np

    try:
        df = pd.read_csv("data/backfilled_predictions.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        col1, col2 = st.columns([1, 3])

        with col1:
            fire_line = st.slider(" Spread Line", -5.0, 5.0, 1.5, 0.5, key="spread_fire_line_tab11")
            fire_level = st.slider(" Confidence Level", 1, 5, 3, key="spread_fire_level_tab11")
            fire_date = st.date_input(" Filter by date", value=None, key="spread_fire_date_tab11")

        with col2:
            df["Predicted_Spread"] = df["Predicted_Home"] - df["Predicted_Away"]
            df["Game_Margin"] = df.get("Home_R", np.nan) - df.get("Away_R", np.nan)  # Real game result
            df["Actual_Spread"] = fire_line  # Show the slider line as in all  tabs

            df["Fire_Level"] = df["Predicted_Spread"].apply(lambda x: min(int(abs(x - fire_line) / 0.5), 5))
            df["Direction"] = df["Predicted_Spread"].apply(lambda x: "Cover" if x > fire_line else "Miss")
            df["Actual_Direction"] = df["Game_Margin"].apply(lambda x: "Cover" if x > fire_line else "Miss")
            df["Hit"] = df["Direction"] == df["Actual_Direction"]

            filtered = df[df["Fire_Level"] == fire_level]
            if fire_date:
                filtered = filtered[filtered["Date"].dt.date == fire_date]

            st.dataframe(filtered[[ 
                "Date", "Home_Team", "Away_Team",
                "Predicted_Home", "Predicted_Away",
                "Predicted_Spread", "Actual_Spread", "Game_Margin",
                "Direction", "Actual_Direction", "Hit"
            ]], use_container_width=True)

            total_day = len(filtered)
            hits_day = filtered["Hit"].sum()
            pct_day = round(100 * hits_day / total_day, 1) if total_day else 0

            up_to = df[df["Fire_Level"] == fire_level]
            if fire_date:
                up_to = up_to[up_to["Date"].dt.date <= fire_date]

            total_all = len(up_to)
            hits_all = up_to["Hit"].sum()
            pct_all = round(100 * hits_all / total_all, 1) if total_all else 0

            colA, colB = st.columns(2)
            with colA:
                st.markdown(f" **Daily:** {hits_day}/{total_day} correct ({pct_day}%)")
            with colB:
                st.markdown(f" **Rolling:** {hits_all}/{total_all} correct ({pct_all}%)")

    except FileNotFoundError:
        st.error("Missing file: `data/backfilled_predictions.csv`")
    except Exception as e:
        st.exception(e)

















