from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os

router = APIRouter()
data_dir = os.path.join(os.path.dirname(__file__), "../../data")

def load_iris_data_as_dataframe():
    """
    Load the Iris dataset from a CSV file into a pandas DataFrame.

    This function attempts to read the Iris dataset from a CSV file located in the data directory.
    If the file is not found, it raises an appropriate HTTP exception.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the Iris dataset with features and target variable.

    Raises:
        HTTPException: If the dataset file is not found (404) or if there's an error reading the file.
    """
    iris_file = os.path.join(data_dir, "Iris.csv")
    if not os.path.exists(iris_file):
        raise HTTPException(status_code=404, detail="Dataset not found")
    return pd.read_csv(iris_file)

def preprocess_iris_data(df: pd.DataFrame):
    """
    Preprocess the Iris dataset by separating features and target variable.

    Args:
        df (pd.DataFrame): The input DataFrame containing the Iris dataset.

    Returns:
        tuple: A tuple containing:
            - X (np.ndarray): Feature matrix
            - y (pd.Series): Target variable series
    """
    X = df.drop(columns=["Id", "Species"])
    y = df["Species"]
    return X, y

def split_data(X, y, test_size=0.2, random_state=42):
    """
    Split the dataset into training and testing sets.

    Args:
        X (np.ndarray): Feature matrix
        y (pd.Series): Target variable
        test_size (float, optional): Proportion of the dataset to include in the test split. 
            Defaults to 0.2.
        random_state (int, optional): Random state for reproducibility. Defaults to 42.

    Returns:
        tuple: A tuple containing:
            - X_train (np.ndarray): Training features
            - X_test (np.ndarray): Testing features
            - y_train (pd.Series): Training target
            - y_test (pd.Series): Testing target

    Raises:
        Exception: If an error occurs during the train-test split
    """
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        return X_train, X_test, y_train, y_test
    except Exception as e:
        raise Exception(f"Error during train-test split: {e}")

@router.get("/load-iris-data", responses={
    200: {
        "description": "Iris dataset loaded successfully",
        "content": {
            "application/json": {
                "example": {
                    "status": "success",
                    "message": "Iris dataset loaded successfully",
                    "data": []
                }
            }
        }
    },
    404: {
        "description": "Dataset not found",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Iris dataset file not found"
                }
            }
        }
    },
    400: {
        "description": "Bad request",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Error processing the request"
                }
            }
        }
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Internal server error occurred"
                }
            }
        }
    }
})
def load_iris_data():
    """
    API endpoint to load the Iris dataset.

    This endpoint retrieves the Iris dataset and returns it in a JSON format.
    It includes proper error handling for various scenarios like file not found,
    empty dataset, and unexpected errors.

    Returns:
        JSONResponse: A JSON response containing:
            - status: Success status of the operation
            - message: Description of the operation result
            - data: The Iris dataset in JSON format

    Raises:
        HTTPException: In case of various errors with appropriate status codes:
            - 404: Dataset not found
            - 400: Empty dataset
            - 500: Unexpected server error
    """
    try:
        df = load_iris_data_as_dataframe()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Iris dataset loaded successfully",
                "data": df.to_dict(orient="records")
            }
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": "Iris dataset file not found"
            }
        )
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "The dataset file is empty"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )

@router.get("/process-iris-data", responses={
    200: {
        "description": "Data processed successfully",
        "content": {
            "application/json": {
                "example": {
                    "status": "success",
                    "message": "Data processed successfully",
                    "data": {"X_scaled": [], "y": []}
                }
            }
        }
    },
    400: {
        "description": "Bad request",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Error processing the data"
                }
            }
        }
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Internal server error occurred"
                }
            }
        }
    }
})
def process_iris_data():
    """
    API endpoint to process the Iris dataset.

    This endpoint loads the Iris dataset, preprocesses it by scaling the features,
    and returns both the scaled features and target variables.

    Returns:
        JSONResponse: A JSON response containing:
            - status: Success status of the operation
            - message: Description of the operation result
            - data: Dictionary containing:
                - X_scaled: Scaled feature matrix
                - y: Target variable array

    Raises:
        HTTPException: In case of various errors with appropriate status codes:
            - 400: Data processing error
            - 500: Unexpected server error
    """
    try:
        df = load_iris_data_as_dataframe()
        X, y = preprocess_iris_data(df)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Data processed successfully",
                "data": {
                    "X_scaled": X_scaled.tolist(),
                    "y": y.tolist()
                }
            }
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Error processing the data: {str(ve)}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )

@router.get("/split-iris-data", responses={
    200: {
        "description": "Data split successfully",
        "content": {
            "application/json": {
                "example": {
                    "status": "success",
                    "message": "Data split successfully",
                    "data": {
                        "X_train": [],
                        "X_test": [],
                        "y_train": [],
                        "y_test": []
                    }
                }
            }
        }
    },
    400: {
        "description": "Bad request",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Invalid parameters provided"
                }
            }
        }
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Internal server error occurred"
                }
            }
        }
    }
})
def split_iris_data(test_size: float = 0.2, random_state: int = 42):
    """
    API endpoint to split the Iris dataset into training and testing sets.

    This endpoint loads the dataset, preprocesses it, and splits it into
    training and testing sets based on the provided parameters.

    Args:
        test_size (float, optional): The proportion of the dataset to include
            in the test split. Must be between 0 and 1. Defaults to 0.2.
        random_state (int, optional): Random state for reproducibility. 
            Defaults to 42.

    Returns:
        JSONResponse: A JSON response containing:
            - status: Success status of the operation
            - message: Description of the operation result
            - data: Dictionary containing:
                - X_train: Training features
                - X_test: Testing features
                - y_train: Training target
                - y_test: Testing target

    Raises:
        HTTPException: In case of various errors with appropriate status codes:
            - 400: Invalid parameters or processing error
            - 500: Unexpected server error
    """
    try:
        if not 0 < test_size < 1:
            raise ValueError("test_size must be between 0 and 1")
            
        df = load_iris_data_as_dataframe()
        X, y = preprocess_iris_data(df)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = split_data(X_scaled, y, test_size, random_state)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Data split successfully",
                "data": {
                    "X_train": X_train.tolist(),
                    "X_test": X_test.tolist(),
                    "y_train": y_train.tolist(),
                    "y_test": y_test.tolist()
                }
            }
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Invalid parameters: {str(ve)}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )
