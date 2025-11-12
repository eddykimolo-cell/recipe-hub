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
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def speichere_benutzer(benutzer):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(benutzer, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
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
    
    neuer = {
        "username": benutzername,
        "password": passwort_hashen(passwort),
        "email": email,
        "joined_date": datetime.now().strftime("%Y-%m-%d")
    }
    benutzer.append(neuer)
    if speichere_benutzer(benutzer):
        return True, "Registrierung erfolgreich!"
    else:
        return False, "Fehler beim Speichern der Benutzerdaten."

# -------------------------------
# Rezepte
# -------------------------------
def lade_rezepte():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                rezepte = json.load(f)
                for rezept in rezepte:
                    rezept.setdefault("category", "vegetarisch")
                    rezept.setdefault("calories", "")
                    rezept.setdefault("image", "🍽️")
                return rezepte
        except (json.JSONDecodeError, FileNotFoundError):
            return []
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
    farben = {"vegan": "#4CAF50", "vegetarisch": "#8BC34A", "mit Fleisch": "#F44336"}
    return farben.get(kategorie, "#757575")

def exportiere_rezept_pdf(rezept):
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

# -------------------------------
# Seite
# -------------------------------
st.set_page_config(page_title="G8 Recipe Hub", page_icon="👨‍🍳", layout="wide")

if "authentifiziert" not in st.session_state:
    st.session_state.authentifiziert = False
if "aktueller_benutzer" not in st.session_state:
    st.session_state.aktueller_benutzer = None

# -------------------------------
# LOGIN / REGISTRATION
# -------------------------------
if not st.session_state.authentifiziert:
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            text-align: center;
            color: #D32F2F;
            margin-bottom: 2rem;
        }
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            background-color: #f9f9f9;
        }
        .stButton button {
            width: 100%;
            background-color: #D32F2F;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">👨‍🍳 Group8 Recipe Hub</h1>', unsafe_allow_html=True)
    st.markdown("**Professionelle Rezepte für Ihre Küche**")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrierung"])

    with tab1:
        st.subheader("Login")
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
                        st.success("Erfolgreich eingeloggt!")
                        st.experimental_rerun()
                    else:
                        st.error("Benutzername oder Passwort ungültig!")
                else:
                    st.error("Bitte alle Felder ausfüllen!")

    with tab2:
        st.subheader("Registrierung")
        with st.form("register_form"):
            neuer_benutzer = st.text_input("Benutzername*")
            email = st.text_input("E-Mail (optional)")
            neues_passwort = st.text_input("Passwort*", type="password")
            passwort2 = st.text_input("Passwort bestätigen*", type="password")
            reg_btn = st.form_submit_button("Registrieren")
            if reg_btn:
                if neuer_benutzer and neues_passwort:
                    if neues_passwort == passwort2:
                        ok, msg = registriere_benutzer(neuer_benutzer, neues_passwort, email)
                        if ok:
                            st.success(msg)
                            st.session_state.authentifiziert = True
                            st.session_state.aktueller_benutzer = {
                                "username": neuer_benutzer,
                                "email": email
                            }
                            st.experimental_rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Passwörter stimmen nicht überein.")
                else:
                    st.error("Bitte alle Pflichtfelder (*) ausfüllen.")
    st.stop()

# -------------------------------
# Haupt
# -------------------------------
rezepte = lade_rezepte()

# Custom CSS for main app
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #D32F2F;
        margin-bottom: 1rem;
    }
    .recipe-card {
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #D32F2F;
        background-color: #f9f9f9;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        color: white;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    .stButton button {
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">👨‍🍳 Group8 Recipe Hub</h1>', unsafe_allow_html=True)
st.markdown("**Professionelle Rezepte für Ihre Küche**")

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.success(f"👋 Willkommen, **{st.session_state.aktueller_benutzer['username']}**!")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authentifiziert = False
        st.session_state.aktueller_benutzer = None
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("### 🔍 Filter")
    suche = st.text_input("Suche nach Rezepten")
    kategorien = list(set([r.get("category","vegetarisch") for r in rezepte]))
    kategorien.sort()
    ausgewählte_kategorien = st.multiselect("Kategorien", kategorien, default=kategorien)

    # -------------------------------
    # Neues Rezept hinzufügen
    # -------------------------------
    st.markdown("---")
    st.markdown("### 👨‍🍳 Neues Rezept")

    with st.expander("➕ Rezept hinzufügen", expanded=False):
        with st.form("add_recipe_form", clear_on_submit=True):
            st.markdown("**Grundinformationen**")
            titel = st.text_input("Titel*")
            beschreibung = st.text_area("Kurzbeschreibung*")
            
            col1, col2 = st.columns(2)
            with col1:
                zeit = st.text_input("Zubereitungszeit*", placeholder="z.B. 20 min")
            with col2:
                kategorie = st.selectbox("Kategorie*", ["vegan","vegetarisch","mit Fleisch"])
            
            kalorien = st.text_input("Kalorien (pro Portion)", placeholder="z.B. 350 kcal")
            
            st.markdown("**Zutaten**")
            zutaten = st.text_area("Eine Zutat pro Zeile*", placeholder="z.B.:\n200g Mehl\n2 Eier\n100ml Milch")
            
            st.markdown("**Zubereitung**")
            schritte = st.text_area("Ein Schritt pro Zeile*", placeholder="z.B.:\nOfen auf 180°C vorheizen\nTeig vermengen\n30 Minuten backen")
            
            st.markdown("**Aussehen**")
            emoji_options = ["🍽️","🍛","🍝","🥑","🥧","🍲","🍗","🧀","🌯","🥔","🥬","🍳","🥗","🍅","🥞","🌮","🍡","🍚","🥣","🐟","🥩","🌶️","🍆"]
            ausgewähltes_emoji = st.selectbox("Rezept-Emoji", emoji_options, index=0)
            
            gespeichert = st.form_submit_button("✅ Rezept speichern")

            if gespeichert:
                if titel.strip() and beschreibung.strip() and zutaten.strip() and schritte.strip() and zeit.strip():
                    neues_rezept = {
                        "id": neues_id(),
                        "title": titel.strip(),
                        "description": beschreibung.strip(),
                        "ingredients": [i.strip() for i in zutaten.split("\n") if i.strip()],
                        "steps": [s.strip() for s in schritte.split("\n") if s.strip()],
                        "time": zeit.strip(),
                        "category": kategorie,
                        "calories": kalorien.strip(),
                        "favorite": False,
                        "image": ausgewähltes_emoji,
                        "created_by": st.session_state.aktueller_benutzer["username"],
                        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    rezepte.insert(0, neues_rezept)
                    if speichere_rezepte(rezepte):
                        st.success(f"Rezept **{titel}** erfolgreich hinzugefügt!")
                        st.experimental_rerun()
                    else:
                        st.error("Fehler beim Speichern des Rezepts!")
                else:
                    st.error("Bitte alle mit * markierten Pflichtfelder ausfüllen!")

# -------------------------------
# Top Buttons
# -------------------------------
st.markdown("### Schnellzugriff")
col1, col2, col3, col4 = st.columns(4)
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
        for k in ["zufaellig","zeige_favoriten","zeige_vegan"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()

# -------------------------------
# Filter Rezepte
# -------------------------------
gefiltert = []
for r in rezepte:
    if st.session_state.get("zeige_favoriten") and not r.get("favorite",False):
        continue
    if st.session_state.get("zeige_vegan") and r.get("category") != "vegan":
        continue
    if ausgewählte_kategorien and r.get("category") not in ausgewählte_kategorien:
        continue
    if suche and suche.lower() not in r["title"].lower() and suche.lower() not in r["description"].lower():
        continue
    gefiltert.append(r)

st.markdown(f"### 📋 Rezepte ({len(gefiltert)} gefunden)")

# -------------------------------
# Anzeige Rezepte
# -------------------------------
if not rezepte:
    st.info("📝 Noch keine Rezepte vorhanden! Fügen Sie Ihr erstes Rezept hinzu.")
elif not gefiltert:
    st.warning("🔍 Keine Rezepte gefunden. Passen Sie Ihre Filterkriterien an.")
else:
    for rezept in gefiltert:
        if st.session_state.get("zufaellig") and rezept["id"] != st.session_state["zufaellig"]:
            continue

        with st.container():
            st.markdown(f'<div class="recipe-card">', unsafe_allow_html=True)
            
            # Header with emoji and title
            col_header1, col_header2 = st.columns([1, 20])
            with col_header1:
                st.markdown(f"# {rezept['image']}")
            with col_header2:
                st.markdown(f"### {rezept['title']}")
            
            # Description
            st.write(rezept["description"])
            
            # Metadata
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            with col_meta1:
                kategorie_color = kategoriefarbe(rezept.get('category', 'vegetarisch'))
                st.markdown(f'<span class="category-badge" style="background-color: {kategorie_color};">{rezept.get("category", "vegetarisch")}</span>', unsafe_allow_html=True)
            with col_meta2:
                st.write(f"**Zeit:** {rezept.get('time','')}")
            with col_meta3:
                kalorien = rezept.get('calories', '')
                if kalorien:
                    st.write(f"**Kalorien:** {kalorien}")
                else:
                    st.write("**Kalorien:** -")
            
            # Action buttons
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
            
            with col_btn1:
                if st.button("📄 PDF", key=f"pdf_{rezept['id']}", use_container_width=True):
                    pdf = exportiere_rezept_pdf(rezept)
                    if pdf:
                        st.download_button(
                            "📥 Herunterladen", 
                            pdf, 
                            file_name=f"{rezept['title']}.pdf", 
                            mime="application/pdf",
                            key=f"dl_{rezept['id']}"
                        )
            
            with col_btn2:
                fav_status = "❤️" if rezept.get("favorite", False) else "🤍"
                if st.button(f"{fav_status} Favorit", key=f"fav_{rezept['id']}", use_container_width=True):
                    rezept["favorite"] = not rezept.get("favorite", False)
                    speichere_rezepte(rezepte)
                    st.experimental_rerun()
            
            with col_btn3:
                if st.button("👁️ Ansehen", key=f"view_{rezept['id']}", use_container_width=True):
                    st.session_state[f"details_{rezept['id']}"] = True
            
            with col_btn4:
                if rezept.get("created_by") == st.session_state.aktueller_benutzer["username"]:
                    if st.button("🗑️ Löschen", key=f"del_{rezept['id']}", use_container_width=True):
                        rezepte.remove(rezept)
                        speichere_rezepte(rezepte)
                        st.success(f"Rezept '{rezept['title']}' gelöscht!")
                        st.experimental_rerun()
            
            # Detailed view
            if st.session_state.get(f"details_{rezept['id']}"):
                st.markdown("---")
                st.markdown("#### 📖 Rezept-Details")
                
                col_det1, col_det2 = st.columns(2)
                
                with col_det1:
                    st.markdown("**🥕 Zutaten**")
                    for zutat in rezept["ingredients"]:
                        st.write(f"• {zutat}")
                
                with col_det2:
                    st.markdown("**👨‍🍳 Zubereitung**")
                    for i, schritt in enumerate(rezept["steps"], 1):
                        st.write(f"{i}. {schritt}")
                
                st.markdown(f"*Erstellt von {rezept.get('created_by', 'Unbekannt')} am {rezept.get('created_date', 'Unbekannt')}*")
                
                if st.button("❌ Details schließen", key=f"close_{rezept['id']}"):
                    st.session_state[f"details_{rezept['id']}"] = False
                    st.experimental_rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("")

