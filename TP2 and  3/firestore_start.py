import firebase_admin
from firebase_admin import credentials, firestore
import os

# Load the service account key
base_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(base_dir, "private_key.json")
cred = credentials.Certificate(path)

# Initialize the Firebase app with the service account
firebase_admin.initialize_app(cred)

# Get a reference to Firestore
db = firestore.client()

# Reference the collection and document
parameters_ref = db.collection('parameters').document('parameters')

data = {
    'n_estimators': 100,  # Example
    'criterion': 'gini'   # Example
}

# Create or update the document
parameters_ref.set(data)

print("The 'parameters' document has been created successfully!")
