from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from firebase_admin import firestore, credentials, initialize_app
import os
import firebase_admin
from google.cloud import exceptions

# Initialize Firebase Admin SDK if it's not already done
if not firebase_admin._apps:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "../../../../../private_key.json")
    print(f"Using key at: {key_path}")
    cred = credentials.Certificate(key_path)
    initialize_app(cred)

router = APIRouter()

# Endpoint to retrieve parameters from Firestore
@router.get("/retrieve-parameters", response_model=dict)
def retrieve_parameters():
    try:
        parameters_ref = firestore.client().collection("parameters").document("parameters")
        doc = parameters_ref.get()

        if doc.exists:
            parameters = doc.to_dict()
            return JSONResponse(content={"parameters": parameters})
        else:
            raise HTTPException(status_code=404, detail="Parameters document not found in Firestore")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to add new parameters to Firestore
@router.post("/add-parameters", response_model=dict)
def add_parameters(new_parameters: dict):
    try:
        # Reference to the Firestore document
        parameters_ref = firestore.client().collection("parameters").document("parameters")
        
        # Get existing parameters
        doc = parameters_ref.get()
        
        if doc.exists:
            # If document exists, merge new parameters with existing ones
            existing_parameters = doc.to_dict()
            merged_parameters = {**existing_parameters, **new_parameters}
            parameters_ref.set(merged_parameters)
            return JSONResponse(content={"message": "Parameters merged successfully", "parameters": merged_parameters})
        else:
            # If document doesn't exist, create it with new parameters
            parameters_ref.set(new_parameters)
            return JSONResponse(content={"message": "New parameters document created successfully", "parameters": new_parameters})
    
    except exceptions.GoogleCloudError as e:
        # Handle Firestore specific errors
        raise HTTPException(status_code=500, detail=f"Firestore error: {str(e)}")
    except Exception as e:
        # Handle all other types of errors
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Endpoint to update parameters in Firestore
@router.put("/update-parameters", response_model=dict)
def update_parameters(updated_parameters: dict):
    try:
        parameters_ref = firestore.client().collection("parameters").document("parameters")
        doc = parameters_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Parameters document not found in Firestore")

        # Get current parameters
        current_parameters = doc.to_dict()
        
        # Update parameters
        merged_parameters = {**current_parameters, **updated_parameters}
        parameters_ref.set(merged_parameters)  # Using set instead of update to ensure complete update
        
        return JSONResponse(content={
            "message": "Parameters updated successfully",
            "parameters": merged_parameters
        })

    except exceptions.GoogleCloudError as e:
        # Handle Firestore specific errors
        raise HTTPException(status_code=500, detail=f"Firestore error: {str(e)}")
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Handle all other types of errors
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Endpoint to delete specific parameters from Firestore
@router.delete("/delete-parameters", response_model=dict)
def delete_parameters(parameters_to_delete: list):
    try:
        parameters_ref = firestore.client().collection("parameters").document("parameters")
        doc = parameters_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Parameters document not found in Firestore")

        # Get current parameters
        current_parameters = doc.to_dict()
        
        # Remove specified parameters
        for param in parameters_to_delete:
            if param in current_parameters:
                del current_parameters[param]
            
        # Update document with remaining parameters
        parameters_ref.set(current_parameters)
        
        return JSONResponse(content={
            "message": "Parameters deleted successfully",
            "deleted_parameters": parameters_to_delete,
            "remaining_parameters": current_parameters
        })

    except exceptions.GoogleCloudError as e:
        # Handle Firestore specific errors
        raise HTTPException(status_code=500, detail=f"Firestore error: {str(e)}")
    except Exception as e:
        # Handle all other types of errors
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")