import streamlit as st
import json, os, random, bcrypt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

DATA_FILE = "recipes.json"
USERS_FILE = "users.json"

# -------------------------------
# Benutzerverwaltung
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

def passwort_hashen(passwort):
    return bcrypt.hashpw(passwort.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def pruefe_passwort(passwort, hashed):
    try:
        return bcrypt.checkpw(passwort.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

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
    
    neuer_benutzer = {
        "username": benutzername,
        "password": passwort_hashen(passwort),
        "email": email,
        "joined_date": datetime.now().strftime("%Y-%m-%d")
    }
    benutzer.append(neuer_benutzer)
    if speichere_benutzer(benutzer):
        return True, "Registrierung erfolgreich!"
    return False, "Fehler bei der Registrierung."

# -------------------------------
# Rezeptfunktionen
# -------------------------------
def lade_rezepte():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                rezepte = json.load(f)
                for rezept in rezepte:
                    rezept.setdefault("category", "vegetarisch")
                    rezept.setdefault("calories", "")
                    rezept.setdefault("image", "🍽️")
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

def neues_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

def kategoriefarbe(kategorie):
    farben = {
        "vegan": "#4CAF50",
        "vegetarisch": "#8BC34A",
        "mit Fleisch": "#F44336"
    }
    return farben.get(kategorie, "#757575")

def exportiere_rezept_pdf(rezept):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        primary_color = HexColor("#D32F2F")
        secondary_color = HexColor("#5D4037")
        text_color = HexColor("#212121")
        y = height - 50

        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(50, y, rezept["title"])
        y -= 30

        c.setFillColor(text_color)
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Beschreibung: {rezept['description']}")
        y -= 20
        c.drawString(50, y, f"Zubereitungszeit: {rezept.get('time','')}")
        c.drawString(200, y, f"Kategorie: {rezept.get('category','')}")
        c.drawString(350, y, f"Kalorien: {rezept.get('calories','')} pro Portion")
        y -= 30

        c.setFillColor(secondary_color)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Zutaten:")
        y -= 25

        c.setFillColor(text_color)
        c.setFont("Helvetica", 12)
        for ing in rezept["ingredients"]:
            c.drawString(60, y, f"• {ing}")
            y -= 18
            if y < 100:
                c.showPage()
                y = height - 50
                c.setFillColor(text_color)

        y -= 10
        c.setFillColor(secondary_color)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Zubereitung:")
        y -= 25

        c.setFillColor(text_color)
        c.setFont("Helvetica", 12)
        for idx, step in enumerate(rezept["steps"], 1):
            c.drawString(60, y, f"{idx}. {step}")
            y -= 18
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFillColor(text_color)

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Fehler beim PDF-Export: {e}")
        return None

# -------------------------------
# Seitenkonfiguration
# -------------------------------
st.set_page_config(page_title="G8 Rezept Hub", page_icon="👨‍🍳", layout="wide")

# -------------------------------
# Sitzungsstatus
# -------------------------------
if "authentifiziert" not in st.session_state:
    st.session_state.authentifiziert = False
if "aktueller_benutzer" not in st.session_state:
    st.session_state.aktueller_benutzer = None
if "zeige_login" not in st.session_state:
    st.session_state.zeige_login = True

# -------------------------------
# Login / Registrierung
# -------------------------------
if not st.session_state.authentifiziert:
    st.title("👨‍🍳 Group8 Recipe Hub")
    st.markdown("**Professionelle Rezepte für Ihre Küche**")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrierung"])

    with tab1:
        st.subheader("Anmeldung")
        with st.form("login_form"):
            benutzername = st.text_input("Benutzername")
            passwort = st.text_input("Passwort", type="password")
            login_btn = st.form_submit_button("Login")
            if login_btn:
                if benutzername and passwort:
                    user = authentifiziere_benutzer(benutzername, passwort)
                    if user:
                        st.session_state.authentifiziert = True
                        st.session_state.aktueller_benutzer = user
                        st.rerun()
                    else:
                        st.error("Ungültiger Benutzername oder Passwort.")
                else:
                    st.warning("Bitte alle Felder ausfüllen.")

    with tab2:
        st.subheader("Neues Konto erstellen")
        with st.form("register_form"):
            neuer_benutzer = st.text_input("Benutzername")
            neues_passwort = st.text_input("Passwort", type="password")
            passwort2 = st.text_input("Passwort bestätigen", type="password")
            email = st.text_input("E-Mail (optional)")
            reg_btn = st.form_submit_button("Registrieren")
            if reg_btn:
                if neuer_benutzer and neues_passwort == passwort2:
                    ok, msg = registriere_benutzer(neuer_benutzer, neues_passwort, email)
                    if ok:
                        st.success(msg)
                        st.session_state.authentifiziert = True
                        st.session_state.aktueller_benutzer = {
                            "username": neuer_benutzer,
                            "email": email
                        }
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Passwörter stimmen nicht überein.")
    st.stop()

# -------------------------------
# Hauptinhalt (nach Login)
# -------------------------------
rezepte = lade_rezepte()

st.markdown('<h1 style="text-align:center;color:#D32F2F;">👨‍🍳 Group8 Recipe Hub</h1>', unsafe_allow_html=True)
st.markdown("**Professionelle Rezepte für Ihre Küche**")

# Sidebar
with st.sidebar:
    st.success(f"👋 Willkommen, **{st.session_state.aktueller_benutzer['username']}**!")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authentifiziert = False
        st.session_state.aktueller_benutzer = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Filter")
    suche = st.text_input("Suche...")
    kategorien = list(set([r.get("category", "vegetarisch") for r in rezepte]))
    kategorien.sort()
    ausgewählte_kategorien = st.multiselect("Kategorien", kategorien, default=kategorien)

# -------------------------------
# 🔁 Menü-Buttons
# -------------------------------
col1, col2, col3, col4 = st.columns(4)

# ✅ FIXED: Zufälliges Rezept (no crash)
with col1:
    if st.button("🎲 Zufälliges Rezept", use_container_width=True):
        if rezepte:
            zuf = random.choice(rezepte)
            st.session_state["zufaellig"] = zuf["id"]
            st.experimental_rerun()
        else:
            st.warning("Keine Rezepte verfügbar!")

with col2:
    if st.button("⭐ Favoriten", use_container_width=True):
        st.session_state["zeige_favoriten"] = True
        st.experimental_rerun()

with col3:
    if st.button("🌱 Nur Vegan", use_container_width=True):
        st.session_state["zeige_vegan"] = True
        st.experimental_rerun()

with col4:
    if st.button("📋 Alle Rezepte", use_container_width=True):
        for k in ["zufaellig", "zeige_favoriten", "zeige_vegan"]:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()

# -------------------------------
# Filterlogik
# -------------------------------
gefiltert = []
for r in rezepte:
    if st.session_state.get("zeige_favoriten") and not r.get("favorite", False):
        continue
    if st.session_state.get("zeige_vegan") and r.get("category") != "vegan":
        continue
    if ausgewählte_kategorien and r.get("category") not in ausgewählte_kategorien:
        continue
    if suche.lower() in r["title"].lower() or suche.lower() in r["description"].lower():
        gefiltert.append(r)

st.markdown(f"### 📋 Gefundene Rezepte: {len(gefiltert)}")

# Anzeige
if not rezepte:
    st.info("Noch keine Rezepte vorhanden. Fügen Sie eines hinzu!")
elif not gefiltert:
    st.info("Keine passenden Rezepte gefunden.")
else:
    for rezept in gefiltert:
        if st.session_state.get("zufaellig") and rezept["id"] != st.session_state["zufaellig"]:
            continue

        with st.container():
            st.markdown(f"### {rezept['image']} {rezept['title']}")
            st.write(rezept["description"])
            st.caption(f"Kategorie: {rezept.get('category')} | Zeit: {rezept.get('time','')} | Kalorien: {rezept.get('calories','')}")
            
            if st.button("📄 PDF", key=f"pdf_{rezept['id']}"):
                pdf = exportiere_rezept_pdf(rezept)
                if pdf:
                    st.download_button(
                        "Herunterladen",
                        pdf,
                        file_name=f"{rezept['title']}.pdf",
                        mime="application/pdf"
                    )
