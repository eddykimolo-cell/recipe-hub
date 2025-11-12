import streamlit as st
import json, os, random, bcrypt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# -------------------------------
# Dateipfade & Initialisierung
# -------------------------------
DATA_FILE = os.path.join(os.getcwd(), "recipes.json")
USERS_FILE = os.path.join(os.getcwd(), "users.json")

# Fallback: Leere Dateien erstellen, falls nicht vorhanden (z. B. bei Streamlit Cloud)
for file in [DATA_FILE, USERS_FILE]:
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump([], f)

# -------------------------------
# Authentifizierungsfunktionen
# -------------------------------
def lade_benutzer():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Fehler beim Laden der Benutzer: {e}")
        return []

def speichere_benutzer(benutzer):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(benutzer, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern der Benutzer: {e}")
        return False

def hash_passwort(passwort: str) -> str:
    return bcrypt.hashpw(passwort.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def pruefe_passwort(passwort: str, hashed: str) -> bool:
    return bcrypt.checkpw(passwort.encode("utf-8"), hashed.encode("utf-8"))

def authentifiziere_benutzer(benutzername, passwort):
    benutzer = lade_benutzer()
    for eintrag in benutzer:
        if eintrag["username"] == benutzername and pruefe_passwort(passwort, eintrag["password"]):
            return eintrag
    return None

def registriere_benutzer(benutzername, passwort, email=""):
    benutzer = lade_benutzer()
    for eintrag in benutzer:
        if eintrag["username"] == benutzername:
            return False, "Benutzername existiert bereits."

    hashed_pw = hash_passwort(passwort)
    neuer_benutzer = {
        "username": benutzername,
        "password": hashed_pw,
        "email": email,
        "joined_date": datetime.now().strftime("%Y-%m-%d")
    }
    benutzer.append(neuer_benutzer)
    if speichere_benutzer(benutzer):
        return True, "Registrierung erfolgreich!"
    return False, "Fehler bei der Registrierung."

# -------------------------------
# Rezept-Funktionen
# -------------------------------
def lade_rezepte():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                rezepte = json.load(f)
                for r in rezepte:
                    r.setdefault("category", "vegetarisch")
                    r.setdefault("calories", "")
                    r.setdefault("image", "🍽️")
                return rezepte
        return []
    except Exception as e:
        st.error(f"Fehler beim Laden der Rezepte: {e}")
        return []

def speichere_rezepte(rezepte):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(rezepte, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern der Rezepte: {e}")
        return False

def neue_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

def kategorie_farbe(kategorie):
    farben = {"vegan": "#4CAF50", "vegetarisch": "#8BC34A", "mit Fleisch": "#F44336"}
    return farben.get(kategorie, "#757575")

def exportiere_rezept_pdf(rezept):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4

        prim = HexColor("#D32F2F")
        sec = HexColor("#5D4037")
        text = HexColor("#212121")

        y = h - 50
        c.setFillColor(prim)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(50, y, rezept["title"])
        y -= 30

        c.setFillColor(text)
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Beschreibung: {rezept['description']}")
        y -= 20

        c.drawString(50, y, f"Zubereitungszeit: {rezept.get('time','')}")
        c.drawString(200, y, f"Kategorie: {rezept.get('category','')}")
        c.drawString(350, y, f"Kalorien: {rezept.get('calories','')} kcal")
        y -= 30

        c.setFillColor(sec)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Zutaten:")
        y -= 25

        c.setFillColor(text)
        c.setFont("Helvetica", 12)
        for zutat in rezept["ingredients"]:
            c.drawString(60, y, f"• {zutat}")
            y -= 18
            if y < 100:
                c.showPage()
                y = h - 50
                c.setFillColor(text)

        y -= 10
        c.setFillColor(sec)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Zubereitung:")
        y -= 25

        c.setFillColor(text)
        c.setFont("Helvetica", 12)
        for i, schritt in enumerate(rezept["steps"], 1):
            c.drawString(60, y, f"{i}. {schritt}")
            y -= 18
            if y < 50:
                c.showPage()
                y = h - 50
                c.setFillColor(text)

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Fehler beim PDF-Export: {e}")
        return None

# -------------------------------
# Streamlit-Layout
# -------------------------------
st.set_page_config(page_title="G8 Rezept-Hub", page_icon="👨‍🍳", layout="wide")

st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #D32F2F;
    text-align: center;
    margin-bottom: 1rem;
}
.recipe-card {
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
    border-left: 5px solid #D32F2F;
    background-color: #FFF9F9;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Login / Registrierung
# -------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.authenticated:
    st.markdown('<h1 class="main-header">👨‍🍳 Group8 Rezept-Hub</h1>', unsafe_allow_html=True)
    st.markdown("**Professionelle Rezepte für Ihre Küche**")

    tab1, tab2 = st.tabs(["🔐 Anmelden", "📝 Registrieren"])

    with tab1:
        st.subheader("Anmeldung")
        with st.form("login_form"):
            benutzername = st.text_input("Benutzername")
            passwort = st.text_input("Passwort", type="password")
            login = st.form_submit_button("Login")

            if login:
                if benutzername and passwort:
                    user = authentifiziere_benutzer(benutzername, passwort)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.success(f"Willkommen zurück, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Falscher Benutzername oder Passwort.")
                else:
                    st.error("Bitte alle Felder ausfüllen.")

    with tab2:
        st.subheader("Neuen Account erstellen")
        with st.form("register_form"):
            neu_name = st.text_input("Benutzername")
            neu_pw = st.text_input("Passwort", type="password")
            neu_pw2 = st.text_input("Passwort bestätigen", type="password")
            email = st.text_input("E-Mail (optional)")
            submit = st.form_submit_button("Registrieren")

            if submit:
                if neu_name and neu_pw and neu_pw2:
                    if neu_pw == neu_pw2:
                        ok, msg = registriere_benutzer(neu_name, neu_pw, email)
                        if ok:
                            st.success(msg)
                            st.session_state.authenticated = True
                            st.session_state.current_user = {"username": neu_name, "email": email}
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Passwörter stimmen nicht überein.")
                else:
                    st.error("Bitte alle Pflichtfelder ausfüllen.")
    st.stop()

# -------------------------------
# Hauptbereich (nach Login)
# -------------------------------
st.markdown('<h1 class="main-header">👨‍🍳 Group8 Rezept-Hub</h1>', unsafe_allow_html=True)
rezepte = lade_rezepte()

with st.sidebar:
    st.success(f"👋 Willkommen, **{st.session_state.current_user['username']}**!")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Filter")
    suchtext = st.text_input("Rezeptsuche")
    kategorien = list(sorted(set(r.get("category", "vegetarisch") for r in rezepte)))
    gewaehlte_kategorien = st.multiselect("Kategorien", kategorien, default=kategorien)

# -------------------------------
# Rezepte anzeigen
# -------------------------------
gefiltert = []
for r in rezepte:
    if gewaehlte_kategorien and r.get("category") not in gewaehlte_kategorien:
        continue
    if not suchtext or suchtext.lower() in r["title"].lower() or suchtext.lower() in r["description"].lower():
        gefiltert.append(r)

st.markdown(f"### 📋 Gefundene Rezepte: {len(gefiltert)}")

if not gefiltert:
    st.info("Keine Rezepte gefunden. Fügen Sie ein neues hinzu!")
else:
    for rezept in gefiltert:
        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
        st.markdown(f"### {rezept['image']} {rezept['title']}")
        st.write(rezept["description"])
        st.caption(f"Kategorie: {rezept['category']} | Zeit: {rezept['time']} | Kalorien: {rezept.get('calories','')}")

        with st.expander("🧂 Zutaten & Zubereitung"):
            st.subheader("Zutaten")
            for z in rezept["ingredients"]:
                st.markdown(f"- {z}")
            st.subheader("Zubereitung")
            for i, s in enumerate(rezept["steps"], 1):
                st.markdown(f"**{i}.** {s}")

        if st.button("📄 Als PDF exportieren", key=f"pdf_{rezept['id']}"):
            pdf = exportiere_rezept_pdf(rezept)
            if pdf:
                st.download_button("Herunterladen", data=pdf, file_name=f"{rezept['title']}.pdf", mime="application/pdf")

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("© 2025 Group8 Rezept-Hub — Sichere & professionelle Rezeptverwaltung")
