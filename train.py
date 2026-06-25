# train.py
import logging
import os
import warnings
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class RentalRiskModel:
    def __init__(self, db_config=None):
        self.db_config = db_config
        self.models = {}
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_importance = {}
        self.feature_names = []
        self.best_model_name = None
        self.target_encoder = LabelEncoder()
        self.class_labels = []

        self.categorical_features = [
            "employment_status",
            "employment_position",
            "property_type",
            "affordability_status",
        ]
        self.numerical_features = [
            "monthly_income",
            "years_at_current_job",
            "previous_rental_history",
            "has_references",
            "credit_score",
            "debt_to_income_ratio",
            "age",
            "family_size",
            "number_of_dependents",
            "previous_late_payments",
            "current_monthly_rent",
            "property_monthly_rent",
            "rent_to_income_ratio",
            "remaining_income",
            "income_after_rent_ratio",
        ]

    def load_dataset(self, path="data/tenant_affordability_dataset.csv"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Training dataset not found: {path}")

        df = pd.read_csv(path)
        df = df.rename(columns={"monthly_salary": "monthly_income"})

        if "risk_category" not in df.columns:
            raise ValueError("Dataset must include a risk_category column.")

        if "number_of_dependents" not in df.columns:
            df["number_of_dependents"] = 0
        df["family_size"] = df["number_of_dependents"].fillna(0).astype(float) + 1

        if "employment_position" in df.columns:
            df["employment_status"] = df["employment_position"].map(self.normalize_employment_status)
        else:
            df["employment_position"] = "Unknown"
            df["employment_status"] = "unknown"

        if "property_type" not in df.columns:
            df["property_type"] = "unknown"

        df["remaining_income"] = df["monthly_income"] - df.get("property_monthly_rent", 0)
        df["income_after_rent_ratio"] = np.where(
            df["monthly_income"] > 0,
            df["remaining_income"] / df["monthly_income"] * 100,
            -100,
        )

        df["risk_category"] = df["risk_category"].astype(str).str.strip().str.lower()
        df = df[df["risk_category"].isin(["low", "medium", "high"])].copy()
        if df.empty:
            raise ValueError("Dataset has no usable low/medium/high risk_category rows.")

        logging.info("Loaded %s training rows from %s", len(df), path)
        logging.info("Risk category counts: %s", df["risk_category"].value_counts().to_dict())
        return df

    @staticmethod
    def normalize_employment_status(value):
        text = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
        if text in {"full time", "part time", "employed"}:
            return "employed"
        if text in {"self employed", "self-employed", "business"}:
            return "self_employed"
        if text == "student":
            return "student"
        if text == "unemployed":
            return "unemployed"
        return text or "unknown"

    def prepare_features(self, df, fit_encoders=True):
        X = pd.DataFrame(index=df.index)

        for feature in self.numerical_features:
            X[feature] = pd.to_numeric(df[feature], errors="coerce").fillna(0) if feature in df.columns else 0

        for feature in self.categorical_features:
            values = df[feature].astype(str).fillna("unknown") if feature in df.columns else pd.Series("unknown", index=df.index)
            if fit_encoders or feature not in self.label_encoders:
                encoder = LabelEncoder()
                X[f"{feature}_encoded"] = encoder.fit_transform(values)
                self.label_encoders[feature] = encoder
                logging.info("Encoder for %s: %s", feature, dict(zip(encoder.classes_, encoder.transform(encoder.classes_))))
            else:
                encoder = self.label_encoders[feature]
                X[f"{feature}_encoded"] = values.map(
                    lambda value: encoder.transform([value])[0] if value in encoder.classes_ else -1
                )

        self.feature_names = X.columns.tolist()
        y = self.target_encoder.fit_transform(df["risk_category"])
        self.class_labels = self.target_encoder.classes_.tolist()
        logging.info("Feature names: %s", self.feature_names)
        logging.info("Target classes: %s", self.class_labels)
        return X, y

    def train_models(self, X, y):
        min_class_count = int(pd.Series(y).value_counts().min())
        stratify = y if min_class_count >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        models = {
            "Random Forest": RandomForestClassifier(
                n_estimators=400,
                max_depth=None,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
            ),
            "Gradient Boosting": GradientBoostingClassifier(
                n_estimators=250,
                learning_rate=0.05,
                max_depth=3,
                random_state=42,
            ),
            "Logistic Regression": LogisticRegression(
                random_state=42,
                max_iter=3000,
                class_weight="balanced",
                multi_class="auto",
            ),
        }

        results = {}
        cv_folds = max(2, min(5, min_class_count))
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average="weighted")
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv_folds, scoring="f1_weighted")

            results[name] = {
                "model": model,
                "accuracy": accuracy,
                "f1": f1,
                "cv_mean": cv_scores.mean(),
                "cv_std": cv_scores.std(),
            }
            logging.info("%s - Accuracy: %.3f, F1: %.3f, CV F1: %.3f", name, accuracy, f1, cv_scores.mean())
            logging.info("\n%s", classification_report(y_test, y_pred, target_names=self.class_labels))

            if hasattr(model, "feature_importances_"):
                self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))
            elif hasattr(model, "coef_"):
                self.feature_importance[name] = dict(zip(X.columns, np.abs(model.coef_).mean(axis=0)))

        self.best_model_name = max(results, key=lambda key: results[key]["f1"])
        best_model_info = results[self.best_model_name]
        self.models = {
            "best_model": best_model_info["model"],
            "all_models": {name: info["model"] for name, info in results.items()},
        }
        logging.info("Best Model: %s", self.best_model_name)
        logging.info("Best weighted F1: %.3f", best_model_info["f1"])
        return best_model_info

    def build_prediction_frame(self, tenant_data):
        data = dict(tenant_data)
        data.setdefault("number_of_dependents", max(float(data.get("family_size", 1)) - 1, 0))
        data.setdefault("current_monthly_rent", 0)
        data.setdefault("property_monthly_rent", data.get("monthly_rent", 0))
        data.setdefault("remaining_income", data.get("monthly_income", 0) - data.get("property_monthly_rent", 0))
        data.setdefault(
            "income_after_rent_ratio",
            (data["remaining_income"] / data["monthly_income"] * 100) if data.get("monthly_income", 0) else -100,
        )
        data.setdefault("employment_position", data.get("employment_status", "unknown"))
        data["employment_status"] = self.normalize_employment_status(data.get("employment_status"))
        data.setdefault("property_type", "unknown")
        data.setdefault("affordability_status", "Unknown")

        frame = pd.DataFrame(index=[0])
        for feature in self.numerical_features:
            frame[feature] = float(data.get(feature, 0) or 0)
        for feature in self.categorical_features:
            value = str(data.get(feature, "unknown"))
            encoder = self.label_encoders.get(feature)
            frame[f"{feature}_encoded"] = encoder.transform([value])[0] if encoder is not None and value in encoder.classes_ else -1
        return frame[self.feature_names]

    def predict_risk(self, tenant_data):
        if not self.models:
            logging.error("Models not trained yet")
            return None

        X_pred = self.build_prediction_frame(tenant_data)
        probabilities = self.models["best_model"].predict_proba(self.scaler.transform(X_pred))[0]
        prob_by_class = dict(zip(self.class_labels, probabilities))
        category = max(prob_by_class, key=prob_by_class.get)
        approval_score = self.approval_score(prob_by_class, category)
        recommendation = self.recommendation_for(category)
        return {
            "risk_score": round(approval_score, 2),
            "risk_category": category,
            "probabilities": {key: round(float(value), 3) for key, value in prob_by_class.items()},
            "recommendation": recommendation,
            "model_used": self.best_model_name,
        }

    @staticmethod
    def approval_score(prob_by_class, category):
        low = prob_by_class.get("low", 0)
        medium = prob_by_class.get("medium", 0)
        high = prob_by_class.get("high", 0)
        score = np.clip((low * 100) + (medium * 55) + (high * 10), 0, 100)
        if category == "low":
            return max(score, 70)
        if category == "medium":
            return min(max(score, 40), 69)
        return min(score, 39)

    @staticmethod
    def recommendation_for(category):
        if category == "low":
            return "Approve - low-risk applicant"
        if category == "medium":
            return "Consider with higher deposit or guarantor"
        return "Reject or require significant guarantees"

    def save_models(self, filepath="models/"):
        os.makedirs(filepath, exist_ok=True)
        joblib.dump(self.models["best_model"], f"{filepath}best_model.pkl")
        joblib.dump(self.scaler, f"{filepath}scaler.pkl")
        joblib.dump(self.label_encoders, f"{filepath}label_encoders.pkl")
        joblib.dump(self.feature_names, f"{filepath}feature_names.pkl")
        joblib.dump(
            {
                "numerical_features": self.numerical_features,
                "categorical_features": self.categorical_features,
            },
            f"{filepath}feature_config.pkl",
        )
        joblib.dump(
            {
                "best_model_name": self.best_model_name,
                "feature_importance": self.feature_importance,
                "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "feature_names": self.feature_names,
                "class_labels": self.class_labels,
                "target_encoder": self.target_encoder,
                "score_type": "approval_score_0_low_to_100_best",
            },
            f"{filepath}model_info.pkl",
        )
        logging.info("Models saved to %s", filepath)

    def load_models(self, filepath="models/"):
        try:
            self.models["best_model"] = joblib.load(f"{filepath}best_model.pkl")
            self.scaler = joblib.load(f"{filepath}scaler.pkl")
            self.label_encoders = joblib.load(f"{filepath}label_encoders.pkl")
            self.feature_names = joblib.load(f"{filepath}feature_names.pkl")
            feature_config = joblib.load(f"{filepath}feature_config.pkl")
            self.numerical_features = feature_config["numerical_features"]
            self.categorical_features = feature_config["categorical_features"]
            model_info = joblib.load(f"{filepath}model_info.pkl")
            self.best_model_name = model_info["best_model_name"]
            self.feature_importance = model_info["feature_importance"]
            self.class_labels = model_info.get("class_labels", ["high", "low", "medium"])
            self.target_encoder = model_info.get("target_encoder", LabelEncoder().fit(self.class_labels))
            logging.info("Models loaded from %s", filepath)
            return True
        except FileNotFoundError:
            logging.warning("No saved models found")
            return False
        except Exception as exc:
            logging.error("Error loading models: %s", exc)
            return False


def main():
    risk_model = RentalRiskModel()
    df = risk_model.load_dataset()

    logging.info("Preparing features...")
    X, y = risk_model.prepare_features(df, fit_encoders=True)

    logging.info("Training models...")
    risk_model.train_models(X, y)

    logging.info("Saving models...")
    risk_model.save_models()

    test_cases = [
        {
            "name": "Low Risk Tenant",
            "data": {
                "monthly_income": 260000,
                "employment_status": "employed",
                "employment_position": "Full time",
                "years_at_current_job": 6,
                "previous_rental_history": 1,
                "has_references": 1,
                "credit_score": 760,
                "debt_to_income_ratio": 15,
                "age": 36,
                "family_size": 2,
                "number_of_dependents": 1,
                "previous_late_payments": 0,
                "current_monthly_rent": 0,
                "property_monthly_rent": 55000,
                "rent_to_income_ratio": 21.15,
                "property_type": "apartment",
                "affordability_status": "Sustainable",
            },
        },
        {
            "name": "Medium Risk Tenant",
            "data": {
                "monthly_income": 125000,
                "employment_status": "self_employed",
                "employment_position": "Self employed",
                "years_at_current_job": 2,
                "previous_rental_history": 1,
                "has_references": 1,
                "credit_score": 610,
                "debt_to_income_ratio": 42,
                "age": 29,
                "family_size": 3,
                "number_of_dependents": 2,
                "previous_late_payments": 1,
                "current_monthly_rent": 25000,
                "property_monthly_rent": 75000,
                "rent_to_income_ratio": 60,
                "property_type": "room",
                "affordability_status": "Manageable with caution",
            },
        },
        {
            "name": "High Risk Tenant",
            "data": {
                "monthly_income": 30000,
                "employment_status": "unemployed",
                "employment_position": "Unemployed",
                "years_at_current_job": 0,
                "previous_rental_history": 0,
                "has_references": 0,
                "credit_score": 430,
                "debt_to_income_ratio": 75,
                "age": 22,
                "family_size": 4,
                "number_of_dependents": 3,
                "previous_late_payments": 5,
                "current_monthly_rent": 45000,
                "property_monthly_rent": 90000,
                "rent_to_income_ratio": 300,
                "property_type": "house",
                "affordability_status": "Not sustainable",
            },
        },
    ]

    logging.info("Testing predictions")
    for test_case in test_cases:
        prediction = risk_model.predict_risk(test_case["data"])
        logging.info("%s: %s", test_case["name"], prediction)

    logging.info("Model training completed successfully.")


if __name__ == "__main__":
    main()
