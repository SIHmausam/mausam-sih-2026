import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# File paths
# ============================================================

TRAIN_FILE = "data/processed/train_phase2_sample.csv"
TEST_FILE = "data/processed/test_phase2.csv"

MODEL_FILE = "models/personalization_model_phase2.pkl"


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
    "card",
]


numerical_features = [
    # Weather
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "showers",
    "precipitation_probability",
    "precipitation_hours",
    "weather_code",
    "cloud_cover",
    "visibility",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",

    # Agriculture
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
    "soil_moisture_100_to_255cm",
    "soil_temperature_0_to_7cm",
    "soil_temperature_7_to_28cm",
    "soil_temperature_28_to_100cm",
    "soil_temperature_100_to_255cm",
    "et0_fao_evapotranspiration",

    # Air quality + UV
    "us_aqi",
    "european_aqi",
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "carbon_monoxide",
    "ozone",
    "uv_index",
    "uv_index_clear_sky",

    # Marine
    "wave_height",
    "wave_direction",
    "wave_period",
    "swell_wave_height",
    "swell_wave_direction",
    "swell_wave_period",
    "sea_level_height_msl",
    "sea_surface_temperature",

    # Context
    "marine_data_available",
    "is_daylight",

    # Temporal
    "hour",
    "day_of_week",
    "month",
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
            Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                ]
            ),
            numerical_features
        )
    ]
)


# ============================================================
# Random Forest model
# ============================================================

model = RandomForestRegressor(
    n_estimators=100,
    max_depth=18,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    verbose=1
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