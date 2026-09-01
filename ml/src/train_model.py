import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# File paths
# ============================================================

TRAIN_FILE = "data/processed/train.csv"
TEST_FILE = "data/processed/test.csv"

MODEL_FILE = "models/personalization_model.pkl"


# ============================================================
# Load datasets
# ============================================================

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)


# ============================================================
# Separate features and target
# ============================================================

TARGET = "relevance_score"

X_train = train_df.drop(columns=[TARGET])
y_train = train_df[TARGET]

X_test = test_df.drop(columns=[TARGET])
y_test = test_df[TARGET]


# ============================================================
# Feature groups
# ============================================================

categorical_features = [
    "city",
    "persona",
    "card"
]


numerical_features = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "weather_code",
    "wind_speed_10m",
    "soil_moisture_0_to_7cm",
    "us_aqi",
    "european_aqi",
    "uv_index",
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "carbon_monoxide",
    "ozone",
    "hour",
    "day_of_week",
    "month"
]


# ============================================================
# Preprocessing
# ============================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        ),

        (
            "numerical",
            "passthrough",
            numerical_features
        )
    ]
)


# ============================================================
# Random Forest model
# ============================================================

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=18,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)


# ============================================================
# Complete ML pipeline
# ============================================================

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)


# ============================================================
# Train
# ============================================================

print("\n================================")
print("TRAINING MODEL")
print("================================")

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))

pipeline.fit(
    X_train,
    y_train
)


# ============================================================
# Predictions
# ============================================================

predictions = pipeline.predict(X_test)


# Keep predictions inside relevance range
predictions = predictions.clip(0, 1)


# ============================================================
# Evaluation
# ============================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = mean_squared_error(
    y_test,
    predictions
) ** 0.5

r2 = r2_score(
    y_test,
    predictions
)


print("\n================================")
print("MODEL EVALUATION")
print("================================")

print(f"MAE : {mae:.4f}")
print(f"RMSE: {rmse:.4f}")
print(f"R²  : {r2:.4f}")


# ============================================================
# Save model
# ============================================================

joblib.dump(
    pipeline,
    MODEL_FILE
)


print("\n================================")
print("MODEL SAVED")
print("================================")

print(MODEL_FILE)