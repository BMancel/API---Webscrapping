from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from src.schemas.message import MessageResponse

router = APIRouter()
data_dir = os.path.join(os.path.dirname(__file__), "../../data")

@router.get("/process-iris-data", response_model=MessageResponse)
def process_iris_data():
    try:
        # Charger le dataset Iris
        iris_file = os.path.join(data_dir, "Iris.csv")
        if not os.path.exists(iris_file):
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Charger les données dans un DataFrame
        df = pd.read_csv(iris_file)
        
        # Supposons que la colonne 'species' soit la cible (target)
        # Diviser le dataset en caractéristiques (X) et cible (y)
        X = df.drop(columns=["Id", "Species"])
        y = df["species"]
        
        # Normaliser les caractéristiques
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Convertir les données normalisées en DataFrame pour un retour structuré
        X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns)
        
        # Retourner les données normalisées
        result = {
            "features": X_scaled_df.to_dict(orient="records"),
            "target": y.tolist()
        }
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
