import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
import json
from shared import db, auth, firebase
# Firebase configuration is imported from main.py
# These variables are defined there and available globally


def login_signup():
    st.markdown("""
    <div class="header-banner">
        <h1>💰 Smart Budget</h1>
        <p>Take control of your finances</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Welcome Back")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    user_info = auth.get_account_info(user['idToken'])
                    email_verified = user_info['users'][0]['emailVerified']
                    
                    if email_verified:
                        st.success("Login successful!")
                        st.session_state.user = user
                        st.session_state.user_id = user['localId']
                        st.session_state.authenticated = True
                        db.collection("users").document(user['localId']).update({
        "verified": True
    })
                        
                        # Check if user has completed onboarding
                        user_doc = db.collection("users").document(user['localId']).get()
                        if user_doc.exists and user_doc.to_dict().get('profile_set', False):
                            st.session_state.onboarded = True
                        
                        st.rerun()
                    else:
                        st.warning("Please verify your email before logging in.")
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
    
    with tab2:
        with st.form("signup_form"):
            st.subheader("Create an Account")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if not new_email or not new_password:
                    st.warning("Please fill all fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    try:
                        user = auth.create_user_with_email_and_password(new_email, new_password)
                        auth.send_email_verification(user['idToken'])
                        st.success("Account created! Please verify your email before logging in.")
                        
                        # Create user document in Firestore
                        db.collection("users").document(user['localId']).set({
                            "email": new_email,
                            "created_at": firestore.SERVER_TIMESTAMP,
                            "verified": False,
                            "profile_set": False
                        })
                    except Exception as e:
                        st.error(f"Sign up failed: {str(e)}")