from fastapi import APIRouter, HTTPException
from src.schemas.message import MessageResponse
from fastapi.responses import JSONResponse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd
import os

router = APIRouter()
data_dir = os.path.join(os.path.dirname(__file__), "../../data")

def load_iris_data_as_dataframe():
    iris_file = os.path.join(data_dir, "Iris.csv")
    if not os.path.exists(iris_file):
        raise HTTPException(status_code=404, detail="Dataset not found")
    return pd.read_csv(iris_file)

def preprocess_iris_data(df: pd.DataFrame):
    X = df.drop(columns=["Id", "Species"])
    y = df["Species"]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y

def split_data(X, y, test_size=0.2, random_state=42):
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        return X_train, X_test, y_train, y_test
    except Exception as e:
        raise Exception(f"Error during train-test split: {e}")




# Endpoint pour charger les données
@router.get("/load-iris-data", response_model=MessageResponse)
def load_iris_data():
    try:
        df = load_iris_data_as_dataframe()
        return JSONResponse(content={"message": "Iris dataset loaded successfully", "data": df.to_dict(orient="records")})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint pour prétraiter les données
@router.get("/process-iris-data", response_model=MessageResponse)
def process_iris_data():
    try:
        df = load_iris_data_as_dataframe()
        X_scaled, y = preprocess_iris_data(df)

        X_scaled_df = pd.DataFrame(X_scaled, columns=df.columns[1:-1])
        response_data = {
            "message": "Iris dataset processed successfully",
            "processed_features": X_scaled_df.to_dict(orient="records"),
            "target": y.tolist()
        }
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint pour le split train-test
@router.get("/split-iris-data", response_model=MessageResponse)
def split_iris_data(test_size: float = 0.2, random_state: int = 42):
    try:
        df = load_iris_data_as_dataframe()
        X_scaled, y = preprocess_iris_data(df)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=random_state
        )
        train_data = {
            "features": pd.DataFrame(X_train, columns=df.columns[1:-1]).to_dict(orient="records"),
            "target": y_train.tolist()
        }
        test_data = {
            "features": pd.DataFrame(X_test, columns=df.columns[1:-1]).to_dict(orient="records"),
            "target": y_test.tolist()
        }
        response_data = {
            "message": "Iris dataset split into train and test successfully",
            "train_data": train_data,
            "test_data": test_data
        }
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
