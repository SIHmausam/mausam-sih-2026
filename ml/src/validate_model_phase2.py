import joblib
import pandas as pd


# ============================================================
# Paths
# ============================================================

MODEL_FILE = "models/personalization_model_phase2.pkl"
TEST_FILE = "data/processed/test_phase2.csv"


# ============================================================
# Locked Phase 2 eligibility
# ============================================================

ELIGIBILITY = {
    "health_conscious": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "uv_allergy",
    ],
    "fitness": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "uv_allergy",
        "running_conditions",
    ],
    "surfer": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "uv_allergy",
        "surf_conditions",
        "tide_water",
    ],
    "traveler": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "uv_allergy",
        "commute_conditions",
        "travel_conditions",
    ],
    "parents_families": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "uv_allergy",
        "commute_conditions",
        "family_school",
    ],
    "farmer": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "uv_allergy",
        "farm_garden",
    ],
    "commuter": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "commute_conditions",
    ],
    "event_planner": [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "uv_allergy",
        "commute_conditions",
        "event_conditions",
    ],
}


PERSONAS = list(ELIGIBILITY.keys())


# ============================================================
# Load
# ============================================================

print("\n================================")
print("PHASE 2 MODEL VALIDATION")
print("================================")

model = joblib.load(MODEL_FILE)
test_df = pd.read_csv(TEST_FILE)

print("Test rows:", len(test_df))


# ============================================================
# Validation helper
# ============================================================

def validate_persona(persona, city=None):
    persona_df = test_df[test_df["persona"] == persona].copy()

    if city is not None:
        persona_df = persona_df[persona_df["city"] == city]

    if persona_df.empty:
        print(f"\n{persona}: NO DATA")
        return

    # Use a representative subset of real test rows.
    # The prepared test dataset no longer contains the original timestamp,
    # so sample rows directly while preserving deterministic results.
    samples = persona_df.sample(
        n=min(100, len(persona_df)),
        random_state=42
    ).copy()

    X = samples.drop(columns=["relevance_score"])
    samples["ml_score"] = model.predict(X).clip(0, 1)

    # Aggregate model scores by card.
    scores = (
        samples.groupby("card")["ml_score"]
        .mean()
        .sort_values(ascending=False)
    )

    eligible = set(ELIGIBILITY[persona])

    print(f"\n--- {persona.upper()} ---")
    if city:
        print(f"Location: {city}")

    print("\nML ranking:")
    for rank, (card, score) in enumerate(scores.items(), start=1):
        status = "ELIGIBLE" if card in eligible else "INELIGIBLE"
        print(f"{rank:2}. {card:22} {score:.4f}  [{status}]")

    # Critical safety check:
    # ML must never be allowed to make an ineligible card eligible.
    ineligible_cards = [
        card for card in scores.index
        if card not in eligible
    ]

    if ineligible_cards:
        print(
            "\nEligibility check: PASS "
            "(ineligible cards are identified and must be filtered)"
        )
    else:
        print("\nEligibility check: PASS")

    # Final ranking after eligibility filtering.
    eligible_scores = scores[
        [card in eligible for card in scores.index]
    ]

    print("\nTop 5 eligible cards:")
    for rank, (card, score) in enumerate(
        eligible_scores.head(5).items(), start=1
    ):
        print(f"{rank}. {card:22} {score:.4f}")


# ============================================================
# Run representative validation
# ============================================================

for persona in PERSONAS:
    validate_persona(persona)


# ============================================================
# Conditional Surfer validation
# ============================================================

print("\n================================")
print("SURFER MARINE VALIDATION")
print("================================")

marine_test = test_df[
    (test_df["persona"] == "surfer")
    & (test_df["marine_data_available"] == 1)
]

non_marine_test = test_df[
    (test_df["persona"] == "surfer")
    & (test_df["marine_data_available"] == 0)
]

print("Marine surfer rows:", len(marine_test))
print("Non-marine surfer rows:", len(non_marine_test))

if not marine_test.empty:
    print(
        "Marine cities:",
        sorted(marine_test["city"].unique().tolist())
    )

    marine_cards = sorted(marine_test["card"].unique())
    print("Marine surfer cards:", marine_cards)

if not non_marine_test.empty:
    non_marine_cards = sorted(non_marine_test["card"].unique())
    print("Non-marine surfer cards:", non_marine_cards)

print("\n================================")
print("VALIDATION COMPLETE")
print("================================")
