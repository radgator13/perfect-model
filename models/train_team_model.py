import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import os

# === Load dataset ===
df = pd.read_csv("data/team_run_prediction_dataset.csv")

# === Define features and target ===
features = [
    "Runs_avg3", "OBP_avg3", "Team_ER_avg3", "Team_WHIP_avg3",
    "SP_ERA_3g", "SP_WHIP_3g", "SP_IP",
    "Opp_SP_ERA_3g", "Opp_SP_WHIP_3g", "Opp_SP_IP", "Home"
]
target = "Target_Runs"

X = df[features]
y = df[target]

# === Train/test split ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Train models ===
models = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42)
}

rmse_results = {}

print("\n Training models and evaluating on TEST set...")
for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    rmse_results[name] = rmse
    print(f" {name}: RMSE = {rmse:.3f}")

# === Pick best ===
best_model_name = min(rmse_results, key=rmse_results.get)
best_model = models[best_model_name]

# === Save best model ===
os.makedirs("models", exist_ok=True)
joblib.dump(best_model, "models/final_team_model.joblib")
print(f"\n Saved best model ({best_model_name}) to models/final_team_model.joblib")
from sklearn.model_selection import cross_val_score, KFold
import matplotlib.pyplot as plt
import seaborn as sns

# === Refit best model on all training data
best_model.fit(X, y)

# === K-Fold Cross-Validation on Full Dataset
print("\n K-Fold Cross-Validation (5-fold):")
cv_scores = cross_val_score(best_model, X, y, cv=5, scoring='neg_root_mean_squared_error')
cv_rmse = -cv_scores
print(f"Fold RMSEs: {np.round(cv_rmse, 4)}")
print(f"Mean CV RMSE: {cv_rmse.mean():.4f}")

# === Feature Importance Plot (if supported)
if hasattr(best_model, "feature_importances_"):
    importances = best_model.feature_importances_
    feature_names = X.columns

    fi_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importance", y="Feature", data=fi_df, palette="viridis")
    plt.title(" Feature Importance (Best Model)")
    plt.tight_layout()
    plt.show()
else:
    print(" This model does not support feature_importances_")
