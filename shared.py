import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
import json

# Initialize Firebase
try:
    # Firebase Admin SDK for Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    
    # Pyrebase for Authentication
    firebase_config = json.load(open("firebase_config.json"))
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firestore.client()
except Exception as e:
    st.error(f"Firebase initialization error: {e}")