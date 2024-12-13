from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from firebase_admin import firestore, credentials, initialize_app
import os
import firebase_admin
from pydantic import BaseModel, Field
from google.cloud import exceptions

if not firebase_admin._apps:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "../../../../../private_key.json")
    print(f"Using key at: {key_path}")
    cred = credentials.Certificate(key_path)
    initialize_app(cred)

router = APIRouter()

class ParametersRequest(BaseModel):
    new_parameters: dict = Field(
        ..., 
        example={"key1": "value1", "key2": "value2", "key3": "value3"}
    )

class UpdateParametersRequest(BaseModel):
    updated_parameters: dict = Field(
        ..., 
        example={"key1": "new_value1", "key2": "new_value2"}
    )

class DeleteParametersRequest(BaseModel):
    parameters_to_delete: list = Field(
        ..., 
        example=["key1", "key2"]
    )

@router.get("/retrieve-parameters", responses={
    200: {
        "description": "Parameters retrieved successfully",
        "content": {
            "application/json": {
                "example": {
                    "parameters": {"key": "value"}
                }
            }
        }
    },
    404: {
        "description": "Parameters document not found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Parameters document not found in Firestore"
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
def retrieve_parameters():
    """Retrieve parameters from Firestore.

    This function attempts to retrieve parameters stored in Firestore. If the parameters document is found, it returns the parameters as a JSON response.

    Returns:
        dict: A dictionary containing the parameters if found.

    Raises:
        HTTPException: If the parameters document is not found (404) or if there's an error retrieving the document.
    """
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

@router.post("/add-parameters", responses={
    200: {
        "description": "Parameters merged successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Parameters merged successfully",
                    "parameters": {"key": "value"}
                }
            }
        }
    },
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Invalid input data"
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
def add_parameters(request: ParametersRequest):
    """Add new parameters to Firestore.

    This function adds new parameters to Firestore. If the parameters document already exists, it merges the new parameters with the existing ones.

    Args:
        new_parameters (dict): A dictionary of new parameters to add.

    Returns:
        dict: A dictionary containing a success message and the merged parameters.

    Raises:
        HTTPException: If there's an error during the Firestore operation (500).
    """
    try:
        parameters_ref = firestore.client().collection("parameters").document("parameters")
        
        doc = parameters_ref.get()
        
        if doc.exists:
            existing_parameters = doc.to_dict()
            merged_parameters = {**existing_parameters, **request.new_parameters}
            parameters_ref.set(merged_parameters)
            return JSONResponse(content={"message": "Parameters merged successfully", "parameters": merged_parameters})
        else:
            parameters_ref.set(request.new_parameters)
            return JSONResponse(content={"message": "New parameters document created successfully", "parameters": new_parameters})
    
    except exceptions.GoogleCloudError as e:
        raise HTTPException(status_code=500, detail=f"Firestore error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.put("/update-parameters", responses={
    200: {
        "description": "Parameters updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Parameters updated successfully",
                    "parameters": {"key": "value"}
                }
            }
        }
    },
    404: {
        "description": "Parameters document not found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Parameters document not found in Firestore"
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
def update_parameters(request: UpdateParametersRequest):
    """Update existing parameters in Firestore.

    This function updates the existing parameters with new values provided. It raises an error if the parameters document is not found.

    Args:
        updated_parameters (dict): A dictionary of updated parameters.

    Returns:
        dict: A dictionary containing the updated parameters.

    Raises:
        HTTPException: If the parameters document is not found (404) or if there's an error during the update (500).
    """
    try:
        parameters_ref = firestore.client().collection("parameters").document("parameters")
        doc = parameters_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Parameters document not found in Firestore")

        current_parameters = doc.to_dict()
        
        merged_parameters = {**current_parameters, **request.updated_parameters}
        parameters_ref.set(merged_parameters)
        
        return JSONResponse(content={
            "message": "Parameters updated successfully",
            "parameters": merged_parameters
        })

    except exceptions.GoogleCloudError as e:
        raise HTTPException(status_code=500, detail=f"Firestore error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.delete("/delete-parameters", responses={
    200: {
        "description": "Parameters deleted successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Parameters deleted successfully",
                    "deleted_parameters": ["param1", "param2"],
                    "remaining_parameters": {"key": "value"}
                }
            }
        }
    },
    404: {
        "description": "Parameters document not found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Parameters document not found in Firestore"
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
def delete_parameters(request: DeleteParametersRequest):
    """Delete parameters from Firestore.

    This function deletes specified parameters from Firestore. It raises an error if the parameters document is not found.

    Args:
        parameters_to_delete (list): A list of parameters to delete.

    Returns:
        dict: A dictionary containing a success message.

    Raises:
        HTTPException: If the parameters document is not found (404) or if there's an error during the deletion (500).
    """
    try:
        parameters_ref = firestore.client().collection("parameters").document("parameters")
        doc = parameters_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Parameters document not found in Firestore")

        current_parameters = doc.to_dict()
        
        for param in request.parameters_to_delete:
            if param in current_parameters:
                del current_parameters[param]
            
        parameters_ref.set(current_parameters)
        
        return JSONResponse(content={
            "message": "Parameters deleted successfully",
            "deleted_parameters": request.parameters_to_delete,
            "remaining_parameters": current_parameters
        })

    except exceptions.GoogleCloudError as e:
        raise HTTPException(status_code=500, detail=f"Firestore error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")