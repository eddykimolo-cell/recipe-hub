# app.py
import streamlit as st
import json
import os
import random
import bcrypt
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

# Falls Dateien nicht existieren (z. B. Streamlit Cloud), lege leere JSONs an
for file in (DATA_FILE, USERS_FILE):
    if not os.path.exists(file):
        try:
            with open(file, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception as e:
            # Falls Schreibrechte eingeschränkt sind, zeigen wir einen Hinweis,
            # aber lassen die App weiterlaufen (Streamlit Cloud: temporärer FS)
            st.warning(f"Konnte Datei {file} nicht anlegen: {e}")

# -------------------------------
# Authentifizierungs-Funktionen
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
    try:
        return bcrypt.checkpw(passwort.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def registriere_benutzer(username, passwort, email=""):
    benutzer = lade_benutzer()
    for b in benutzer:
        if b.get("username") == username:
            return False, "Benutzername existiert bereits"
    neuer = {
        "username": username,
        "password": hash_passwort(passwort),
        "email": email,
        "joined_date": datetime.now().strftime("%Y-%m-%d")
    }
    benutzer.append(neuer)
    if speichere_benutzer(benutzer):
        return True, "Registrierung erfolgreich"
    return False, "Fehler beim Speichern des Benutzers"

def authentifiziere_benutzer(username, passwort):
    benutzer = lade_benutzer()
    for b in benutzer:
        if b.get("username") == username and pruefe_passwort(passwort, b.get("password","")):
            return b
    return None

# -------------------------------
# Migration: Falls alte Klartext-Passwörter vorhanden sind
# -------------------------------
def migriere_klartext_passwoerter_once():
    benutzer = lade_benutzer()
    aktualisiert = False
    for b in benutzer:
        pw = b.get("password", "")
        # bcrypt Hash beginnt typischerweise mit $2 (z.B. $2b$)
        if pw and not pw.startswith("$2"):
            try:
                b["password"] = hash_passwort(pw)
                aktualisiert = True
            except Exception:
                # wenn etwas schiefgeht, überspringen wir
                pass
    if aktualisiert:
        speichere_benutzer(benutzer)
        # Hinweis, aber nicht abbrechen — Migration einmalig
        st.info("Alte Klartext-Passwörter wurden einmalig gehasht.")

# Führt Migration still im Start durch (idempotent)
try:
    migriere_klartext_passwoerter_once()
except Exception:
    pass

# -------------------------------
# Utility / Rezept-Funktionen
# -------------------------------
def lade_rezepte():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                recipes = json.load(f)
                # sicherstellen, dass Felder existieren
                for r in recipes:
                    r.setdefault("category", "vegetarisch")
                    r.setdefault("calories", "")
                    r.setdefault("image", "🍽️")
                return recipes
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

def kategorie_farbe(category):
    colors = {
        "vegan": "#4CAF50",
        "vegetarisch": "#8BC34A",
        "mit Fleisch": "#F44336"
    }
    return colors.get(category, "#757575")

def export_recipe_pdf(recipe):
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
        c.drawString(50, y, recipe["title"])
        y -= 30

        c.setFillColor(text_color)
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Beschreibung: {recipe.get('description','')}")
        y -= 20

        c.drawString(50, y, f"Zubereitungszeit: {recipe.get('time','')}")
        c.drawString(250, y, f"Kategorie: {recipe.get('category','')}")
        c.drawString(430, y, f"Kalorien: {recipe.get('calories','')}")
        y -= 30

        c.setFillColor(secondary_color)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Zutaten:")
        y -= 25

        c.setFillColor(text_color)
        c.setFont("Helvetica", 12)
        for ing in recipe.get("ingredients", []):
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
        for idx, step in enumerate(recipe.get("steps", []), 1):
            # einfache Zeilenumbruch-Handling: falls zu lang, splitten wir
            # (einfacher Ansatz)
            text = f"{idx}. {step}"
            c.drawString(60, y, text)
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
        st.error(f"Error generating PDF: {e}")
        return None

# -------------------------------
# Streamlit Setup & CSS
# -------------------------------
st.set_page_config(
    page_title="G8 Recipe Hub",
    page_icon="👨‍🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border-left: 5px solid #D32F2F;
        background-color: #FFF9F9;
    }
    .category-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .time-badge {
        background-color: #FFEBEE;
        padding: 0.25rem 0.5rem;
        border-radius: 10px;
        font-size: 0.8rem;
        display: inline-block;
        margin-right: 0.5rem;
    }
    .calories-badge {
        background-color: #E8F5E9;
        padding: 0.25rem 0.5rem;
        border-radius: 10px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialisieren
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "show_login" not in st.session_state:
    st.session_state.show_login = True

# -------------------------------
# Authentifizierung UI
# -------------------------------
if not st.session_state.authenticated:
    st.markdown('<h1 class="main-header">👨‍🍳 Group8 Recipe Hub</h1>', unsafe_allow_html=True)
    st.markdown("**Professionelle Rezepte für Ihre Küche**")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.subheader("Login to Your Account")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_btn = st.form_submit_button("Login")

            if login_btn:
                if username and password:
                    user = authentifiziere_benutzer(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.session_state.show_login = False
                        st.success(f"Welcome back, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please fill in all fields")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.subheader("Create New Account")

        with st.form("register_form"):
            new_username = st.text_input("Username", placeholder="Choose a username")
            new_password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            email = st.text_input("Email (optional)", placeholder="Your email address")
            register_btn = st.form_submit_button("Register")

            if register_btn:
                if new_username and new_password and confirm_password:
                    if new_password == confirm_password:
                        success, message = registriere_benutzer(new_username, new_password, email)
                        if success:
                            st.success(message)
                            # Auto-login after registration
                            st.session_state.authenticated = True
                            st.session_state.current_user = {
                                "username": new_username,
                                "email": email,
                                "joined_date": datetime.now().strftime("%Y-%m-%d")
                            }
                            st.session_state.show_login = False
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all required fields")
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# -------------------------------
# MAIN APPLICATION (nach Login)
# -------------------------------
st.markdown('<h1 class="main-header">👨‍🍳 Group8 Recipe Hub</h1>', unsafe_allow_html=True)
st.markdown("**Professionelle Rezepte für Ihre Küche**")

# Rezepte laden
recipes = lade_rezepte()

# -------------------------------
# Sidebar (Filter + Neues Rezept)
# -------------------------------
with st.sidebar:
    # Benutzerinfo & Logout
    st.success(f"👋 Welcome, **{st.session_state.current_user['username']}**!")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.show_login = True
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Rezept-Filter")

    search = st.text_input("Rezepte durchsuchen", placeholder="Name, Zutaten oder Kategorie...")

    categories = list(set([r.get("category", "vegetarisch") for r in recipes])) if recipes else []
    categories.sort()

    if categories:
        selected_categories = st.multiselect(
            "Kategorien auswählen",
            options=categories,
            default=categories
        )
    else:
        selected_categories = []
        st.info("Noch keine Kategorien verfügbar")

    time_filter = st.selectbox(
        "Maximale Zubereitungszeit",
        options=["Beliebig", "≤ 15 min", "≤ 30 min", "≤ 45 min", "≤ 60 min"]
    )

    calories_filter = st.selectbox(
        "Maximale Kalorien",
        options=["Beliebig", "≤ 200 kcal", "≤ 300 kcal", "≤ 400 kcal", "≤ 500 kcal"]
    )

    only_favorites = st.checkbox("Nur Favoriten anzeigen")

    st.markdown("---")
    st.markdown("### 📊 Rezept-Statistiken")

    if recipes:
        total_recipes = len(recipes)
        category_counts = {}
        for r in recipes:
            cat = r.get("category", "vegetarisch")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        favorite_count = len([r for r in recipes if r.get("favorite")])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Gesamte Rezepte", total_recipes)
            for cat, count in list(category_counts.items())[:2]:
                st.metric(cat.capitalize(), count)
        with col2:
            for cat, count in list(category_counts.items())[2:]:
                st.metric(cat.capitalize(), count)
            if favorite_count > 0:
                st.metric("Favoriten", favorite_count)
    else:
        st.info("Noch keine Rezepte vorhanden")

    st.markdown("---")
    st.markdown("### 👨‍🍳 Neues Rezept")

    with st.expander("Rezept hinzufügen"):
        with st.form("add_recipe_form", clear_on_submit=True):
            title = st.text_input("Titel*")
            description = st.text_area("Kurzbeschreibung*")

            col1, col2 = st.columns(2)
            with col1:
                time = st.text_input("Zubereitungszeit*", placeholder="z.B. 20 min")
            with col2:
                category = st.selectbox("Kategorie*", ["vegan", "vegetarisch", "mit Fleisch"])

            calories = st.text_input("Kalorien (pro Portion)", placeholder="z.B. 320")

            st.subheader("Zutaten")
            ingredients = st.text_area("Eine Zutat pro Zeile*",
                                      placeholder="300g Hähnchenbrust\n2 Paprika\n1 Zucchini\n2 EL Sojasauce")

            st.subheader("Zubereitungsschritte")
            steps = st.text_area("Ein Schritt pro Zeile*",
                                placeholder="Hähnchen anbraten\nGemüse hinzufügen\nMit Sojasauce ablöschen\n5 Minuten dünsten")

            emoji_options = ["🍽️", "🍛", "🍝", "🥑", "🥧", "🍲", "🍗", "🧀", "🌯", "🥔", "🥬", "🍳", "🥗", "🍅", "🥞", "🌮", "🍡", "🍚", "🥣", "🐟", "🥩", "🌶️", "🍆"]
            selected_emoji = st.selectbox("Rezept-Emoji", emoji_options, index=0)

            submitted = st.form_submit_button("Rezept speichern")

            if submitted:
                if title.strip() and description.strip() and ingredients.strip() and steps.strip() and time.strip():
                    new_recipe = {
                        "id": neue_id(),
                        "title": title.strip(),
                        "description": description.strip(),
                        "ingredients": [i.strip() for i in ingredients.split("\n") if i.strip()],
                        "steps": [s.strip() for s in steps.split("\n") if s.strip()],
                        "time": time.strip(),
                        "category": category,
                        "calories": calories.strip(),
                        "favorite": False,
                        "image": selected_emoji,
                        "created_by": st.session_state.current_user["username"],
                        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    recipes.insert(0, new_recipe)
                    if speichere_rezepte(recipes):
                        st.success(f"Rezept **{title}** wurde hinzugefügt!")
                        st.rerun()
                    else:
                        st.error("Fehler beim Speichern des Rezepts!")
                else:
                    st.error("Bitte füllen Sie alle mit * markierten Felder aus!")

# -------------------------------
# Hauptbereich Buttons (Random / Favorites / Vegan / All)
# -------------------------------
if recipes:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🎲 Zufälliges Rezept", use_container_width=True):
            r = random.choice(recipes)
            st.session_state["show_random"] = r["id"]
            st.rerun()

    with col2:
        if st.button("⭐ Alle Favoriten", use_container_width=True):
            st.session_state["show_favorites"] = True
            st.rerun()

    with col3:
        if st.button("🌱 Nur Vegan", use_container_width=True):
            st.session_state["show_vegan"] = True
            st.rerun()

    with col4:
        if st.button("📋 Alle Rezepte", use_container_width=True):
            for key in ["show_random", "show_favorites", "show_vegan"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# -------------------------------
# Filter-Logik
# -------------------------------
filtered = []
for r in recipes:
    if st.session_state.get("show_favorites") and not r.get("favorite", False):
        continue
    if st.session_state.get("show_vegan") and r.get("category") != "vegan":
        continue
    if selected_categories and r.get("category", "vegetarisch") not in selected_categories:
        continue

    # Suche (Titel, Zutaten, Kategorie, Beschreibung)
    search_lower = search.lower() if search else ""
    if (not search_lower or
        search_lower in r["title"].lower() or
        any(search_lower in i.lower() for i in r["ingredients"]) or
        search_lower in r.get("category","").lower() or
        search_lower in r.get("description","").lower()):
        # Time & calories filter (vereinfachte Logik: nur wenn user Filter gesetzt hat)
        # Zeit-Filter (z.B. "≤ 30 min")
        if time_filter != "Beliebig":
            try:
                max_mins = int(time_filter.split("≤")[1].split()[0])
                # Versuche, aus r["time"] Zahl der Minuten zu extrahieren
                t = r.get("time","")
                num = ''.join(ch for ch in t if ch.isdigit())
                if num:
                    if int(num) > max_mins:
                        continue
            except Exception:
                # bei Fehlern Zeit nicht filtern
                pass

        if calories_filter != "Beliebig" and r.get("calories"):
            try:
                max_kcal = int(calories_filter.split("≤")[1].split()[0])
                kcal = ''.join(ch for ch in r.get("calories","") if ch.isdigit())
                if kcal and int(kcal) > max_kcal:
                    continue
            except Exception:
                pass

        filtered.append(r)

selected_id = st.session_state.get("show_random", None)
st.markdown(f"### 📋 Gefundene Rezepte: {len(filtered)}")

# -------------------------------
# Anzeige der Rezepte
# -------------------------------
if not recipes:
    st.info("Willkommen beim Chef's Recipe Hub! Fügen Sie Ihr erstes Rezept hinzu, um zu beginnen.")
elif not filtered and not selected_id:
    st.info("Keine Rezepte gefunden. Passen Sie Ihre Filterkriterien an.")
else:
    for recipe in filtered:
        if selected_id and recipe["id"] != selected_id:
            continue

        with st.container():
            st.markdown('<div class="recipe-card">', unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {recipe.get('image','🍽️')} {recipe['title']}")
                st.write(recipe.get("description",""))

                col1a, col2a, col3a = st.columns(3)
                with col1a:
                    st.markdown(f'<div class="time-badge">⏱️ {recipe.get("time","")}</div>', unsafe_allow_html=True)
                with col2a:
                    category_color = kategorie_farbe(recipe.get("category","vegetarisch"))
                    category_name = recipe.get("category","vegetarisch")
                    st.markdown(f'<div class="category-tag" style="background-color: {category_color}; color: white;">{category_name}</div>', unsafe_allow_html=True)
                with col3a:
                    if recipe.get("calories"):
                        st.markdown(f'<div class="calories-badge">🔥 {recipe.get("calories","")} kcal</div>', unsafe_allow_html=True)

            with col2:
                favorite_status = "💔 Entfernen" if recipe.get("favorite", False) else "⭐ Favorit"
                if st.button(favorite_status, key=f"fav_{recipe['id']}", use_container_width=True):
                    recipe["favorite"] = not recipe.get("favorite", False)
                    speichere_rezepte(recipes)
                    st.rerun()

            # Ersteller info
            if recipe.get("created_by"):
                st.caption(f"Erstellt von {recipe['created_by']} am {recipe.get('created_date','')}")

            tab1, tab2 = st.tabs(["🧂 Zutatenliste", "👨‍🍳 Zubereitungsschritte"])

            with tab1:
                st.markdown("#### Zutaten")
                for ingredient in recipe.get("ingredients", []):
                    st.markdown(f"- {ingredient}")

            with tab2:
                st.markdown("#### Zubereitung")
                for idx, step in enumerate(recipe.get("steps", []), 1):
                    st.markdown(f"**{idx}.** {step}")

            col1b, col2b, col3b = st.columns([1,1,1])
            with col1b:
                if st.button("🗑️ Löschen", key=f"del_{recipe['id']}", use_container_width=True):
                    recipes = [r for r in recipes if r["id"] != recipe["id"]]
                    if speichere_rezepte(recipes):
                        st.rerun()

            with col2b:
                if st.button("✏️ Bearbeiten", key=f"edit_{recipe['id']}", use_container_width=True):
                    st.session_state["edit_recipe"] = recipe["id"]
                    st.info("Bearbeitungsfunktion kommt bald! (Platzhalter)")

            with col3b:
                if st.button("📄 PDF", key=f"pdf_{recipe['id']}", use_container_width=True):
                    pdf = export_recipe_pdf(recipe)
                    if pdf:
                        st.download_button(
                            label="Herunterladen",
                            data=pdf,
                            file_name=f"{recipe['title']}.pdf",
                            mime="application/pdf",
                            key=f"dl_{recipe['id']}",
                            use_container_width=True
                        )

            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("© 2025 Chef's Recipe Hub — Professionelle Rezeptverwaltung für Feinschmecker")
