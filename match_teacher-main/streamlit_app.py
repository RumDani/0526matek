import streamlit as st
from PIL import Image
import sqlite3
import io
import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import pathlib
import textwrap
from IPython.display import display
from google_auth import get_logged_in_user_email, show_login_button
from st_paywall import add_auth

# Adatbázis kapcsolat létrehozása
conn = sqlite3.connect('emails.db')
c = conn.cursor()

# Email táblázat létrehozása, ha még nem létezik
c.execute('''
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL
)
''')
conn.commit()

st.set_page_config(
    page_title="Math Teacher",
    page_icon="🤖"
)
st.title("🤖 AI Matek Tanár")

login_button_text = "Login with Google"
login_button_color = "#FD504D"
login_sidebar = True
user_email = get_logged_in_user_email()

if not user_email:
    show_login_button(
        text=login_button_text, color=login_button_color, sidebar=login_sidebar
    )
    st.stop()

st.session_state.user_subscribed = True

if st.sidebar.button("Logout", type="primary"):
    del st.session_state.email
    del st.session_state.user_subscribed
    st.rerun()

st.write("Bejelentkeztél")
st.write("Email címed: " + str(st.session_state.email))

# Email mentése adatbázisba
def save_email_to_db(email):
    email = email.strip()  # Tisztítás felesleges szóközöktől
    try:
        c.execute("INSERT INTO emails (email) VALUES (?)", (email,))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Hiba történt az adatbázisba írás során: {e}")

save_email_to_db(st.session_state.email)

load_dotenv()
api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

def call_gemini(image):
    model = genai.GenerativeModel(st.secrets["MODEL"])
    model_prompt = st.secrets["PROMPT"]
    with st.spinner("Dolgozok a megoldáson..."):
        response = model.generate_content([model_prompt, image], stream=True)
        response.resolve()
    response_text = response.text
    st.subheader("Megoldás")
    st.write(response_text)

def main():
    st.caption("🚀 Tölts fel egy képet a matematika feladatról!")

    uploaded_file = st.file_uploader("Feladat feltöltése", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        image_display_width = 300
        st.image(image, caption='Feladat', use_column_width=False, width=image_display_width)

        if st.button('Megoldás'):
            call_gemini(image)
        else:
            st.write('Kattints a "Megoldás" gombra!')

if __name__ == "__main__":
    main()

# Meglévő email címek megjelenítése az adatbázisból
st.write("Mentett email címek:")
for row in c.execute("SELECT email FROM emails"):
    st.write(row[0])

# Adatbázis kapcsolat lezárása, ha már nincs rá szükség
conn.close()
