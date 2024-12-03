from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json
import os
import numpy as np
from joblib import load
from joblib import dump
from pydantic import BaseModel
from sklearn.preprocessing import StandardScaler
from src.api.routes.data import load_iris_data_as_dataframe, preprocess_iris_data, split_data

router = APIRouter()

# Endpoint to train the model
@router.post("/train-iris-model", response_model=dict)
def train_iris_model():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        params_path = os.path.join(base_dir, "../../config/model_parameters.json")
        
        with open(params_path, "r") as f:
            params = json.load(f)

        df = load_iris_data_as_dataframe()
        X_scaled, y = preprocess_iris_data(df)
        X_train, X_test, y_train, y_test = split_data(X_scaled, y)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = RandomForestClassifier(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            random_state=params["random_state"]
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        models_dir = os.path.join(base_dir, "../../models")
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, "iris_classification_model_rf.joblib")
        dump(model, model_path)
        
        response = {
            "message": "Model trained and saved successfully",
            "accuracy": accuracy,
            "model_file": model_path
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IrisFeatures(BaseModel):
    features: list[float]

# Endpoint to make predictions with the trained model
@router.post("/predict-iris-model", response_model=dict)
def predict_iris_model(data: IrisFeatures):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "../../models/iris_classification_model_rf.joblib")
        
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Trained model not found")

        model = load(model_path)

        df = load_iris_data_as_dataframe()
        X_scaled, _ = preprocess_iris_data(df)
        
        features_array = np.array(data.features).reshape(1, -1)
        
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(X_scaled)
        features_scaled = scaler.transform(features_array)
        
        prediction = model.predict(features_scaled)
        
        response = {
            "prediction": prediction.tolist()
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))