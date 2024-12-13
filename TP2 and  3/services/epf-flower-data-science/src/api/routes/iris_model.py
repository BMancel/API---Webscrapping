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

@router.post("/train-iris-model", response_model=dict, responses={
    200: {
        "description": "Model trained and saved successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Model trained and saved successfully",
                    "accuracy": 0.9,
                    "model_file": "path/to/model.joblib"
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "An error occurred while training the model"
                }
            }
        }
    }
})
def train_iris_model():
    """
    Train a Random Forest classifier on the Iris dataset.
    
    This endpoint loads the Iris dataset, preprocesses it, splits it into training and testing sets,
    trains a Random Forest model with parameters from the configuration file, and saves both the
    model and the scaler for later use.
    
    Returns:
        JSONResponse: A JSON response containing:
            - message: Success message
            - accuracy: Model's accuracy on the test set
            - model_file: Path where the model is saved
            
    Raises:
        HTTPException: If there's an error during training (500) or if required files are not found
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        params_path = os.path.join(base_dir, "../../config/model_parameters.json")
        
        with open(params_path, "r") as f:
            params = json.load(f)

        df = load_iris_data_as_dataframe()
        X, y = preprocess_iris_data(df)
        X_train, X_test, y_train, y_test = split_data(X, y)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        models_dir = os.path.join(base_dir, "../../models")
        scaler_path = os.path.join(models_dir, "scaler.joblib")
        dump(scaler, scaler_path)

        model = RandomForestClassifier(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            random_state=params["random_state"]
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
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
    """
    Pydantic model for Iris prediction input features.
    
    Attributes:
        features (list[float]): List of 4 float values representing sepal length, sepal width,
                              petal length, and petal width in centimeters
    """
    features: list[float]

@router.post("/predict-iris-model", response_model=dict, responses={
    200: {
        "description": "Successful prediction",
        "content": {
            "application/json": {
                "example": {
                    "prediction": ["setosa"]
                }
            }
        }
    },
    404: {
        "description": "Model or scaler not found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Trained model or scaler not found"
                }
            }
        }
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "features"],
                            "msg": "Field must contain exactly 4 float values",
                            "type": "value_error"
                        }
                    ]
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Error message"
                }
            }
        }
    }
})
def predict_iris_model(data: IrisFeatures):
    """
    Make predictions using the trained Iris model.
    
    This endpoint loads the trained Random Forest model and scaler, preprocesses the input features,
    and returns the predicted Iris species.
    
    Args:
        data (IrisFeatures): Input features for prediction containing:
            - features (list[float]): List of 4 float values for Iris measurements
            
    Returns:
        JSONResponse: A JSON response containing:
            - prediction: List with the predicted Iris species
            
    Raises:
        HTTPException: 
            - 404: If the trained model or scaler is not found
            - 422: If the input data validation fails (e.g., wrong number of features)
            - 500: If there's an error during prediction
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "../../models/iris_classification_model_rf.joblib")
        
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Trained model not found")
        
        if len(data.features) != 4:
            raise HTTPException(
                status_code=422,
                detail="Input must contain exactly 4 features (sepal length, sepal width, petal length, petal width)"
            )

        model = load(model_path)

        df = load_iris_data_as_dataframe()
        X_scaled, _ = preprocess_iris_data(df)
        
        features_array = np.array(data.features).reshape(1, -1)
        
        scaler_path = os.path.join(base_dir, "../../models/scaler.joblib")
        if not os.path.exists(scaler_path):
            raise HTTPException(status_code=404, detail="Scaler not found")

        scaler = load(scaler_path)

        features_array = np.array(data.features).reshape(1, -1)
        features_scaled = scaler.transform(features_array)
        
        prediction = model.predict(features_scaled)
        
        response = {
            "prediction": prediction.tolist()
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))