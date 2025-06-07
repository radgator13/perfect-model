# ⚾ MLB Run Predictor

This project is a Streamlit-based web app and data pipeline for predicting MLB game totals and strikeouts. It includes scraping, modeling, historical backfilling, and team- or pitcher-level analysis.

## 📁 Project Structure

.
├── app.py                       # Streamlit app entry point
├── pipeline.py                 # Master pipeline script
├── pipeline_logic/             # Data processing & modeling steps
├── scrape_logic/               # Data scraping modules
├── models/                     # Trained model .joblib files + trainers
├── outputs/                    # CSV prediction outputs
├── data/                       # Raw and backfilled data, including archive
├── utilities/                  # .env and helper scripts
├── requirements.txt            # Python dependencies

## 🚀 Quick Start

### 1. Clone the Repo

git clone https://github.com/your-username/mlb-run-predictor.git
cd mlb-run-predictor

### 2. Set Up a Virtual Environment (optional but recommended)

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configure Environment Variables

Create a .env file in utilities/ based on the project’s needs (e.g., API keys, paths):

cp utilities/.env.example utilities/.env

Then fill in your own values.

## 🧠 How to Use

### ▶️ Run the Streamlit App

streamlit run app.py

### 🔁 Run the Full Pipeline

python pipeline.py

This runs all scripts under pipeline_logic/ and pushes updates to outputs/ and data/.

## 📦 Model Details

- Models are stored in models/*.joblib
- Includes classifiers for over 3.5, 4.5, 5.5, and 6.5 run totals
- Uses stats like wRC+, OBP, SLG, K%, etc.

## 📊 Prediction Outputs

- outputs/team_predictions.csv – per-team game totals
- outputs/pitcher_k_predictions.csv – strikeout projections
- data/mlb_backfilled_predictions.csv – model vs actual results

## 📆 Scheduled Execution (GitHub Actions)

This pipeline is set up to auto-run via GitHub Actions at:
- 2:00 AM EST
- 11:00 AM EST
- 10:00 PM EST

## ✅ Requirements

- Python 3.12+

Python packages:

- streamlit >= 1.33
- pandas >= 2.2
- numpy >= 1.26
- scikit-learn
- joblib

## 🙌 Credits

Created by @radgator13  
Data sourced from FanGraphs, Stathead, and ESPN.

## 📄 License

This project is MIT licensed.
