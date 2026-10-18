from fastapi import (

    FastAPI,

    UploadFile,

    File,

    HTTPException,

    Depends,

)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.security import (

    HTTPAuthorizationCredentials,

    HTTPBearer,

)



from pydantic import BaseModel



import joblib
import pickle
import tensorflow as tf

import pandas as pd

import numpy as np



from pathlib import Path

from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv



from pymongo import MongoClient

from pymongo.errors import PyMongoError



from jose import JWTError, jwt



import os

import uuid

import hashlib

import hmac

from backend.email_service import send_critical_threat_email



# ============================================================

# SECURESENSE API

# AI-Based Cyber Threat Detection and Incident Response

# ============================================================



app = FastAPI(

    title="SecureSense API",

    description="AI-Based Cyber Threat Detection and Incident Response Platform",

    version="2.1.0",

)





# ============================================================

# CORS

# ============================================================



app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)





# ============================================================

# PROJECT PATHS

# ============================================================



BASE_DIR = Path(__file__).resolve().parent.parent



MODEL_PATH = BASE_DIR / "models" / "primary_dnn.keras"
SCALER_PATH = BASE_DIR / "models" / "primary_dnn_scaler.pkl"
THRESHOLD_PATH = BASE_DIR / "models" / "primary_dnn_threshold.pkl"

FEATURES_PATH = BASE_DIR / "models" / "final_feature_names.pkl"





# ============================================================

# LOAD ENVIRONMENT VARIABLES

# ============================================================



load_dotenv(BASE_DIR / ".env")





# ============================================================

# MONGODB CONFIGURATION

# ============================================================



MONGODB_URI = os.getenv("MONGODB_URI")



MONGODB_DATABASE = os.getenv(

    "MONGODB_DATABASE",

    "securesense",

)



MONGODB_COLLECTION = os.getenv(

    "MONGODB_COLLECTION",

    "incidents",

)





if not MONGODB_URI:

    raise RuntimeError(

        "MONGODB_URI is missing. "

        "Please configure it in the .env file."

    )





# ============================================================

# AUTHENTICATION CONFIGURATION

# ============================================================



JWT_SECRET_KEY = os.getenv(

    "JWT_SECRET_KEY",

    "securesense-development-secret-change-before-production",

)



JWT_ALGORITHM = "HS256"



ACCESS_TOKEN_EXPIRE_MINUTES = int(

    os.getenv(

        "ACCESS_TOKEN_EXPIRE_MINUTES",

        "60",

    )

)



SECURESENSE_USERNAME = os.getenv(

    "SECURESENSE_USERNAME",

    "admin",

)



SECURESENSE_PASSWORD = os.getenv(

    "SECURESENSE_PASSWORD",

    "SecureSense\@123",

)



# Password hashing salt.

# Put a custom value in .env for your project.

PASSWORD_SALT = os.getenv(

    "SECURESENSE_PASSWORD_SALT",

    "securesense-demo-salt-change-before-production",

)





# ============================================================

# AUTHENTICATION SECURITY

# ============================================================



security = HTTPBearer()





def hash_password(password: str) -> str:

    """

    Hash password using PBKDF2-HMAC-SHA256.

    Uses a project-specific salt.

    """



    return hashlib.pbkdf2_hmac(

        "sha256",

        password.encode("utf-8"),

        PASSWORD_SALT.encode("utf-8"),

        120_000,

    ).hex()





STORED_PASSWORD_HASH = hash_password(

    SECURESENSE_PASSWORD

)





def verify_password(password: str) -> bool:

    """

    Verify supplied password against configured password hash.

    """



    supplied_hash = hash_password(password)



    return hmac.compare_digest(

        supplied_hash,

        STORED_PASSWORD_HASH,

    )





def create_access_token(username: str) -> str:

    """

    Create JWT access token.

    """



    expire = datetime.now(timezone.utc) + timedelta(

        minutes=ACCESS_TOKEN_EXPIRE_MINUTES

    )



    payload = {

        "sub": username,

        "exp": expire,

    }



    return jwt.encode(

        payload,

        JWT_SECRET_KEY,

        algorithm=JWT_ALGORITHM,

    )





def get_current_user(

    credentials: HTTPAuthorizationCredentials = Depends(

        security

    ),

):

    """

    Validate JWT token and return authenticated user.

    """



    token = credentials.credentials



    try:



        payload = jwt.decode(

            token,

            JWT_SECRET_KEY,

            algorithms=[JWT_ALGORITHM],

        )



        username = payload.get("sub")



        if not username:



            raise HTTPException(

                status_code=401,

                detail="Invalid authentication token.",

            )



        if username != SECURESENSE_USERNAME:



            raise HTTPException(

                status_code=401,

                detail="Invalid authentication user.",

            )



        return {

            "username": username,

        }



    except JWTError:



        raise HTTPException(

            status_code=401,

            detail="Invalid or expired authentication token.",

        )





# ============================================================

# LOGIN MODEL

# ============================================================



class LoginRequest(BaseModel):

    username: str

    password: str





# ============================================================

# LOAD ML ARTIFACTS

# ============================================================



print("=" * 70)

print("SECURESENSE - STARTING BACKEND")

print("=" * 70)



print(f"Loading model: {MODEL_PATH}")

print(f"Loading features: {FEATURES_PATH}")





dnn_model = tf.keras.models.load_model(MODEL_PATH)

with open(SCALER_PATH, "rb") as f:
    dnn_scaler = pickle.load(f)

with open(THRESHOLD_PATH, "rb") as f:
    dnn_threshold = float(pickle.load(f))

with open(FEATURES_PATH, "rb") as f:
    feature_names = pickle.load(f)

feature_names = list(feature_names)

if len(feature_names) != 69:
    raise RuntimeError(f"Expected 69 model features, found {len(feature_names)}.")

if not (0.0 < dnn_threshold < 1.0):
    raise RuntimeError(f"Invalid DNN threshold: {dnn_threshold}")

print("DNN model loaded successfully.")
print(f"Number of features: {len(feature_names)}")
print(f"Detection threshold: {dnn_threshold:.4f}")

# ============================================================

# MODEL FEATURE IMPORTANCE

# Used for threat explanation

# ============================================================

@app.get("/threat-explanation")
def threat_explanation(
    current_user: dict = Depends(get_current_user),
):
    """Return DNN-based explanation information for the current SecureSense model."""
    return {
        "success": True,
        "explanation_type": "dnn_model_information",
        "model": "Deep Neural Network",
        "architecture": "MLP / DNN",
        "total_features": len(feature_names),
        "decision_threshold": round(dnn_threshold, 4),
        "message": (
            "SecureSense uses a Deep Neural Network to analyze "
            "69 validated network-flow features. "
            "The traffic is classified as an attack when the predicted "
            "attack probability reaches or exceeds the configured decision threshold."
        ),
    }

# ============================================================

# MONGODB CONNECTION

# ============================================================



print("Connecting to MongoDB...")



try:



    mongo_client = MongoClient(

        MONGODB_URI,

        serverSelectionTimeoutMS=5000,

    )



    # Test connection

    mongo_client.admin.command("ping")



    mongo_db = mongo_client[

        MONGODB_DATABASE

    ]



    incidents_collection = mongo_db[

        MONGODB_COLLECTION

    ]



    print("MongoDB connected successfully!")

    print(f"Database: {MONGODB_DATABASE}")

    print(f"Collection: {MONGODB_COLLECTION}")





except PyMongoError as e:



    print("MongoDB connection failed!")

    print(str(e))



    raise RuntimeError(

        "Could not connect to MongoDB. "

        "Check your MONGODB_URI and Atlas network access."

    )





# ============================================================

# CREATE MONGODB INDEXES

# ============================================================



try:



    incidents_collection.create_index(

        "incident_id",

        unique=True,

    )



    incidents_collection.create_index(

        "timestamp",

    )



    incidents_collection.create_index(

        "status",

    )



    incidents_collection.create_index(

        "risk_level",

    )



    print("MongoDB indexes ready.")





except PyMongoError as e:



    print(

        f"MongoDB index warning: {e}"

    )





# ============================================================

# ROOT ENDPOINT

# PUBLIC

# ============================================================



@app.get("/")

def root():



    return {

        "message": "SecureSense API is running!",

        "status": "success",

        "version": "2.1.0",

        "database": "MongoDB",

        "model": "Deep Neural Network",

        "authentication": "JWT",

    }





# ============================================================

# HEALTH CHECK

# PUBLIC

# ============================================================



@app.get("/health")

def health():



    mongo_status = "connected"



    try:



        mongo_client.admin.command(

            "ping"

        )



    except Exception:



        mongo_status = "disconnected"



    return {



        "status": "healthy",



        "model": {

            "loaded": True,

            "name": "Deep Neural Network",

            "features": len(feature_names),

            "threshold": dnn_threshold,

        },



        "database": {

            "type": "MongoDB",

            "status": mongo_status,

        },



    }





# ============================================================

# MODEL INFORMATION

# PUBLIC

# ============================================================



@app.get("/model-info")
def model_info():
    return {
        "success": True,
        "model": "Deep Neural Network",
        "architecture": "MLP / DNN",
        "number_of_features": len(feature_names),
        "feature_names": feature_names,
        "decision_threshold": round(dnn_threshold, 4),
        "status": "loaded",
    }

# ============================================================

# THREAT EXPLANATION

# ============================================================

# Returns the most important features used by the trained

# Random Forest model for threat explanation.



@app.get("/threat-explanation")
def threat_explanation(
    current_user: dict = Depends(get_current_user),
):
    """Return honest DNN model information without fabricated feature importance."""
    return {
        "success": True,
        "explanation_type": "dnn_model_information",
        "model": "Deep Neural Network",
        "total_features": len(feature_names),
        "decision_threshold": round(dnn_threshold, 4),
        "message": (
            "The DNN uses all 69 validated model features. "
            "Random-Forest-style feature_importances_ are not available for this model."
        ),
    }

# ============================================================

# LOGIN

# PUBLIC

# ============================================================



@app.post("/auth/login")

def login(request: LoginRequest):



    username = request.username.strip()



    if username != SECURESENSE_USERNAME:



        raise HTTPException(

            status_code=401,

            detail="Invalid username or password.",

        )



    if not verify_password(

        request.password

    ):



        raise HTTPException(

            status_code=401,

            detail="Invalid username or password.",

        )



    access_token = create_access_token(

        username

    )



    return {



        "success": True,



        "access_token":

            access_token,



        "token_type":

            "bearer",



        "username":

            username,



        "expires_in":

            ACCESS_TOKEN_EXPIRE_MINUTES * 60,



    }





# ============================================================

# CURRENT USER

# PROTECTED

# ============================================================



@app.get("/auth/me")

def current_user(

    current_user: dict = Depends(

        get_current_user

    ),

):



    return {



        "success": True,



        "user":

            current_user,



    }





# ============================================================

# RISK CALCULATION

# ============================================================



def calculate_risk(

    prediction,

    confidence,

):



    # BENIGN traffic

    if prediction == 0:



        return "LOW"



    # ATTACK traffic

    if confidence >= 0.90:



        return "CRITICAL"



    elif confidence >= 0.75:



        return "HIGH"



    elif confidence >= 0.50:



        return "MEDIUM"



    else:



        return "LOW"





# ============================================================

# CREATE INCIDENT

# ============================================================



def create_incident(

    prediction,

    confidence,

    risk_level,

    row_number=None,

):



    # Only ATTACK traffic creates incidents

    if prediction == 0:



        return None



    incident = {



        "incident_id":

            "INC-" +

            uuid.uuid4().hex[:8].upper(),



        "timestamp":

            datetime.now(

                timezone.utc

            ).isoformat(),



        "prediction":

            "ATTACK",



        "confidence":

            round(

                confidence * 100,

                2,

            ),



        "risk_level":

            risk_level,



        "status":

            "OPEN",



        "source_row":

            row_number,



    }



    try:



           incidents_collection.insert_one(

            incident.copy()

           )



    except PyMongoError as e:



           raise HTTPException(

              status_code=500,

              detail=(

                f"Failed to save incident: {str(e)}"

            ),

        )



    # Send email only for CRITICAL threats

    if risk_level == "CRITICAL":

        email_sent = send_critical_threat_email(incident)



        # Store email notification status in the incident

        incident["email_notification_sent"] = email_sent



        try:

            incidents_collection.update_one(

                {

                    "incident_id": incident["incident_id"]

                },

                {

                    "$set": {

                        "email_notification_sent": email_sent

                    }

                }

            )

        except PyMongoError as e:

            print(

                f"Warning: Could not update email notification status: {e}"

            )



    return incident





# ============================================================

# PREPARE SINGLE INPUT

# ============================================================



def prepare_single_input(

    data: dict

):



    missing_features = [



        feature



        for feature in feature_names



        if feature not in data



    ]



    if missing_features:



        raise HTTPException(



            status_code=400,



            detail={



                "message":

                    "Missing required features",



                "missing_features":

                    missing_features,



            },



        )



    values = []



    for feature in feature_names:



        value = data[feature]



        try:



            value = float(value)



        except (

            TypeError,

            ValueError,

        ):



            raise HTTPException(



                status_code=400,



                detail={



                    "message":

                        f"Feature '{feature}' must be numeric",



                },



            )



        if not np.isfinite(value):



            raise HTTPException(



                status_code=400,



                detail={



                    "message":

                        f"Feature '{feature}' contains an invalid value",



                },



            )



        values.append(value)



    return np.array(

        [values],

        dtype=np.float64,

    )





# ============================================================

# SINGLE FLOW PREDICTION

# PROTECTED

# ============================================================



@app.post("/predict")

def predict(

    data: dict,

    current_user: dict = Depends(

        get_current_user

    ),

):



    try:



        X_input = prepare_single_input(

            data

        )



        # Prediction

        X_scaled = dnn_scaler.transform(X_input).astype(np.float32)

        attack_probability = float(
            dnn_model.predict(X_scaled, verbose=0)[0][0]
        )

        prediction = int(attack_probability >= dnn_threshold)

        confidence = (
            attack_probability
            if prediction == 1
            else 1.0 - attack_probability
        )



        result = (

            "BENIGN"

            if prediction == 0

            else "ATTACK"

        )



        risk_level = calculate_risk(

            prediction,

            confidence,

        )



        # Create incident if attack

        incident = create_incident(

            prediction,

            confidence,

            risk_level,

        )



        return {



            "success":

                True,



            "prediction":

                result,



            "prediction_code":

                int(prediction),



            "confidence":

                round(

                    confidence * 100,

                    2,

                ),



            "risk_level":

                risk_level,



            "incident":

                incident,



        }



    except HTTPException:



        raise



    except Exception as e:



        raise HTTPException(

            status_code=500,

            detail=str(e),

        )





# ============================================================

# CSV THREAT DETECTION

# PROTECTED

# ============================================================



@app.post("/predict-csv")

async def predict_csv(

    file: UploadFile = File(...),

    current_user: dict = Depends(

        get_current_user

    ),

):



    try:



        # Read CSV

        df = pd.read_csv(

            file.file

        )



        if df.empty:



            raise HTTPException(

                status_code=400,

                detail="CSV file is empty.",

            )



        # Check required features

        missing_features = [



            feature



            for feature in feature_names



            if feature not in df.columns



        ]



        if missing_features:



            raise HTTPException(



                status_code=400,



                detail={



                    "message":

                        "CSV is missing required features",



                    "missing_features":

                        missing_features,



                },



            )



        # Select model features

        X_input = df[

            feature_names

        ].copy()



        # Convert all features to numeric

        for feature in feature_names:



            X_input[feature] = pd.to_numeric(

                X_input[feature],

                errors="coerce",

            )



        # Check invalid values

        invalid_columns = []



        for feature in feature_names:



            if X_input[

                feature

            ].isna().any():



                invalid_columns.append(

                    feature

                )



        if invalid_columns:



            raise HTTPException(



                status_code=400,



                detail={



                    "message":

                        "CSV contains missing or non-numeric values",



                    "invalid_features":

                        invalid_columns,



                },



            )



        # Check infinite values

        if not np.isfinite(

            X_input.to_numpy()

        ).all():



            raise HTTPException(

                status_code=400,

                detail="CSV contains infinite values.",

            )



        # Predictions

        X_scaled = dnn_scaler.transform(
            X_input.to_numpy(dtype=np.float32)
        ).astype(np.float32)

        attack_probabilities = dnn_model.predict(
            X_scaled,
            batch_size=8192,
            verbose=0
        ).ravel()

        predictions = (
            attack_probabilities >= dnn_threshold
        ).astype(np.int32)



        # Counters

        total_rows = len(df)



        benign_count = int(

            np.sum(

                predictions == 0

            )

        )



        attack_count = int(

            np.sum(

                predictions == 1

            )

        )



        threat_rate = (



            attack_count /

            total_rows *

            100



            if total_rows > 0



            else 0



        )



        low_count = 0

        medium_count = 0

        high_count = 0

        critical_count = 0



        results = []



        # Process each flow

        for i, prediction in enumerate(

            predictions

        ):



            attack_probability = float(attack_probabilities[i])

            confidence = (
                attack_probability
                if int(prediction) == 1
                else 1.0 - attack_probability
            )



            result = (



                "BENIGN"



                if prediction == 0



                else "ATTACK"



            )



            risk_level = calculate_risk(

                prediction,

                confidence,

            )



            # Risk counters

            if risk_level == "LOW":



                low_count += 1



            elif risk_level == "MEDIUM":



                medium_count += 1



            elif risk_level == "HIGH":



                high_count += 1



            elif risk_level == "CRITICAL":



                critical_count += 1



            # Create incident

            incident = create_incident(



                prediction,



                confidence,



                risk_level,



                i + 1,



            )



            results.append({



                "row":

                    i + 1,



                "prediction":

                    result,



                "prediction_code":

                    int(prediction),



                "confidence":

                    round(

                        confidence * 100,

                        2,

                    ),



                "risk_level":

                    risk_level,



                "incident_id":

                    (

                        incident["incident_id"]

                        if incident

                        else None

                    ),



            })



        # Overall security status

        if critical_count > 0:



            overall_status = "CRITICAL"



        elif high_count > 0:



            overall_status = "HIGH"



        elif medium_count > 0:



            overall_status = "MEDIUM"



        elif attack_count > 0:



            overall_status = (

                "LOW - ATTACK DETECTED"

            )



        else:



            overall_status = "SECURE"



        # Security summary

        security_summary = {



            "total_flows":

                total_rows,



            "benign_flows":

                benign_count,



            "attack_flows":

                attack_count,



            "threat_rate":

                round(

                    threat_rate,

                    2,

                ),



            "risk_distribution": {



                "LOW":

                    low_count,



                "MEDIUM":

                    medium_count,



                "HIGH":

                    high_count,



                "CRITICAL":

                    critical_count,



            },



            "overall_status":

                overall_status,



        }



        return {



            "success":

                True,



            "filename":

                file.filename,



            "security_summary":

                security_summary,



            "results":

                results,



        }



    except HTTPException:



        raise



    except Exception as e:



        raise HTTPException(

            status_code=500,

            detail=str(e),

        )





# ============================================================

# GET ALL INCIDENTS

# PROTECTED

# ============================================================



@app.get("/incidents")

def get_incidents(

    current_user: dict = Depends(

        get_current_user

    ),

):



    try:



        incidents = list(



            incidents_collection.find(



                {},



                {

                    "_id": 0

                },



            ).sort(



                "timestamp",

                -1,



            )



        )



        return {



            "success":

                True,



            "total_incidents":

                len(incidents),



            "incidents":

                incidents,



        }



    except PyMongoError as e:



        raise HTTPException(

            status_code=500,

            detail=str(e),

        )





# ============================================================

# GET OPEN INCIDENTS

# PROTECTED

# ============================================================



@app.get("/incidents/open")

def get_open_incidents(

    current_user: dict = Depends(

        get_current_user

    ),

):



    try:



        open_incidents = list(



            incidents_collection.find(



                {

                    "status": "OPEN"

                },



                {

                    "_id": 0

                },



            ).sort(



                "timestamp",

                -1,



            )



        )



        return {



            "success":

                True,



            "total_open_incidents":

                len(open_incidents),



            "incidents":

                open_incidents,



        }



    except PyMongoError as e:



        raise HTTPException(

            status_code=500,

            detail=str(e),

        )





# ============================================================

# GET SINGLE INCIDENT

# PROTECTED

# ============================================================



@app.get("/incidents/{incident_id}")

def get_incident(

    incident_id: str,

    current_user: dict = Depends(

        get_current_user

    ),

):



    try:



        incident = incidents_collection.find_one(



            {

                "incident_id":

                    incident_id

            },



            {

                "_id": 0

            },



        )



        if incident is None:



            raise HTTPException(

                status_code=404,

                detail="Incident not found",

            )



        return {



            "success":

                True,



            "incident":

                incident,



        }



    except HTTPException:



        raise



    except PyMongoError as e:



        raise HTTPException(

            status_code=500,

            detail=str(e),

        )





# ============================================================

# RESOLVE INCIDENT

# PROTECTED

# ============================================================



@app.put("/incidents/{incident_id}/resolve")

def resolve_incident(

    incident_id: str,

    current_user: dict = Depends(

        get_current_user

    ),

):



    try:



        # Find incident

        incident = incidents_collection.find_one(



            {

                "incident_id":

                    incident_id

            }



        )



        if incident is None:



            raise HTTPException(

                status_code=404,

                detail="Incident not found",

            )



        # Already resolved

        if incident.get(

            "status"

        ) == "RESOLVED":



            incident.pop(

                "_id",

                None,

            )



            return {



                "success":

                    True,



                "message":

                    "Incident is already resolved",



                "incident":

                    incident,



            }



        # Resolve incident

        resolved_at = (

            datetime.now(

                timezone.utc

            ).isoformat()

        )



        incidents_collection.update_one(



            {

                "incident_id":

                    incident_id

            },



            {



                "$set": {



                    "status":

                        "RESOLVED",



                    "resolved_at":

                        resolved_at,



                }



            },



        )



        # Get updated incident

        updated_incident = (



            incidents_collection.find_one(



                {

                    "incident_id":

                        incident_id

                },



                {

                    "_id": 0

                },



            )



        )



        return {



            "success":

                True,



            "message":

                "Incident resolved successfully",



            "incident":

                updated_incident,



        }



    except HTTPException:



        raise



    except PyMongoError as e:



        raise HTTPException(

            status_code=500,

            detail=str(e),

        )





# ============================================================

# START SERVER

# ============================================================



if __name__ == "__main__":



    import uvicorn



    uvicorn.run(

        "backend.main:app",

        host="127.0.0.1",

        port=8000,

        reload=True,

    )