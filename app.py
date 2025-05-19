# JADI No SAVE

import streamlit as st
import face_recognition
import pandas as pd
import pickle
import io
import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials

# === Google Sheets Setup ===
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("drive_credentials.json", scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/18NEDc77-a2TJYPY3BwN1PIXaGj4y08OK9NK2qA7rOis/edit?usp=sharing").sheet1

# === Load Encodings ===
try:
    with open("known_faces.pkl", "rb") as f:
        known_data = pickle.load(f)
        known_faces = known_data["encodings"]
        known_metadata = known_data["metadata"]
except FileNotFoundError:
    known_faces = []
    known_metadata = []

# === Streamlit App ===
st.set_page_config(page_title="Lab Access System", page_icon="🔐")
st.markdown("<h1 style='font-size: 32px;'>🔐 Lab Face Access System</h1>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🧑‍🎓 Register Face", "🚪 Access Lab"])

# === Tab 1: Registration ===
with tab1:
    st.markdown("<h3>Register Face</h3>", unsafe_allow_html=True)
    with st.form("register_form"):
        name = st.text_input("Full Name")
        student_id = st.text_input("Student ID")
        image_data = st.camera_input("Capture Your Face")
        submitted = st.form_submit_button("Register")

        if submitted:
            if not name or not student_id:
                st.error("Please enter your name and student ID.")
            elif not image_data:
                st.error("Please capture your face.")
            else:
                image = face_recognition.load_image_file(io.BytesIO(image_data.getvalue()))
                locations = face_recognition.face_locations(image)
                encodings = face_recognition.face_encodings(image, locations)

                if not encodings:
                    st.error("No face detected. Try again.")
                else:
                    known_faces.append(encodings[0])
                    known_metadata.append({"name": name, "student_id": student_id})
                    with open("known_faces.pkl", "wb") as f:
                        pickle.dump({"encodings": known_faces, "metadata": known_metadata}, f)
                    st.success(f"✅ {name} registered successfully!")

# === Tab 2: Access Lab ===
with tab2:
    st.markdown("<h3>Face Recognition Access</h3>", unsafe_allow_html=True)
    face_img = st.camera_input("Scan Your Face")

    if st.button("🔓 Request Access"):
        if not face_img:
            st.error("Please capture your face.")
        else:
            image = face_recognition.load_image_file(io.BytesIO(face_img.getvalue()))
            locations = face_recognition.face_locations(image)
            encodings = face_recognition.face_encodings(image, locations)

            if not encodings:
                st.error("❌ No face detected.")
            else:
                face_encoding = encodings[0]
                distances = face_recognition.face_distance(known_faces, face_encoding)

                if not distances.any():
                    st.error("⚠️ No registered faces found.")
                else:
                    min_distance = min(distances)
                    best_match_index = distances.tolist().index(min_distance)
                    TOLERANCE = 0.45

                    if min_distance < TOLERANCE:
                        matched = known_metadata[best_match_index]
                        name = matched["name"]
                        student_id = matched["student_id"]
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # === Virtual Access Granted ===
                        st.success(f"✅ Welcome {name} ({student_id}) – Virtual Door Unlocked 🚪💻")

                        # === Log Access to Google Sheets ===
                        sheet.append_row([timestamp, name, student_id, "Lab Access", "Granted"])
                    else:
                        st.error("❌ Face not recognized. Access denied.")


