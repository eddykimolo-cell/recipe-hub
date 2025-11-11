import streamlit as st
import json, os, random
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

DATA_FILE = "recipes.json"

# -------------------------------
# Utility functions
# -------------------------------
def load_recipes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            recipes = json.load(f)
            # Ensure all recipes have the required fields for backward compatibility
            for recipe in recipes:
                if "category" not in recipe:
                    recipe["category"] = "vegetarisch"  # Default category
                if "calories" not in recipe:
                    recipe["calories"] = ""  # Empty calories if not present
                if "image" not in recipe:
                    recipe["image"] = "🍽️"  # Default emoji
            return recipes
    else:
        # If no file exists, start with empty list
        return []

def save_recipes(recipes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)

def new_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

def get_category_color(category):
    colors = {
        "vegan": "#4CAF50",  # Green
        "vegetarisch": "#8BC34A",  # Light green
        "mit Fleisch": "#F44336"  # Red
    }
    return colors.get(category, "#757575")  # Default gray

def export_recipe_pdf(recipe):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Colors
    primary_color = HexColor("#D32F2F")  # Restaurant red
    secondary_color = HexColor("#5D4037")  # Brown
    text_color = HexColor("#212121")  # Dark gray
    
    y = height - 50
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, y, recipe["title"])
    y -= 30
    
    c.setFillColor(text_color)
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Beschreibung: {recipe['description']}")
    y -= 20
    
    # Recipe details in a row
    c.drawString(50, y, f"Zubereitungszeit: {recipe.get('time','')}")
    c.drawString(200, y, f"Kategorie: {recipe.get('category','')}")
    c.drawString(350, y, f"Kalorien: {recipe.get('calories','')} pro Portion")
    y -= 30
    
    # Ingredients
    c.setFillColor(secondary_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Zutaten:")
    y -= 25
    
    c.setFillColor(text_color)
    c.setFont("Helvetica", 12)
    for ing in recipe["ingredients"]:
        c.drawString(60, y, f"• {ing}")
        y -= 18
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFillColor(text_color)
    
    y -= 10
    
    # Preparation steps
    c.setFillColor(secondary_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Zubereitung:")
    y -= 25
    
    c.setFillColor(text_color)
    c.setFont("Helvetica", 12)
    for idx, step in enumerate(recipe["steps"], 1):
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
# App setup with restaurant theme
# -------------------------------
st.set_page_config(
    page_title="Chef's Recipe Hub", 
    page_icon="👨‍🍳", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for restaurant theme
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
    .sidebar .sidebar-content {
        background-color: #FFF5F5;
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
    .stats-card {
        background-color: #FFF9F9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #D32F2F;
        margin-bottom: 1rem;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">👨‍🍳 Chef\'s Recipe Hub</h1>', unsafe_allow_html=True)
st.markdown("**Professionelle Rezepte für Ihre Küche**")

# Load recipes from external JSON file
recipes = load_recipes()

# -------------------------------
# Sidebar - Filters and Add recipe form
# -------------------------------
with st.sidebar:
    st.markdown("### 🔍 Rezept-Filter")
    
    # Search
    search = st.text_input("Rezepte durchsuchen", placeholder="Name, Zutaten oder Kategorie...")
    
    # Category filter
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
    
    # Time filter
    time_filter = st.selectbox(
        "Maximale Zubereitungszeit",
        options=["Beliebig", "≤ 15 min", "≤ 30 min", "≤ 45 min", "≤ 60 min"]
    )
    
    # Calories filter
    calories_filter = st.selectbox(
        "Maximale Kalorien",
        options=["Beliebig", "≤ 200 kcal", "≤ 300 kcal", "≤ 400 kcal", "≤ 500 kcal"]
    )
    
    # Favorites filter
    only_favorites = st.checkbox("Nur Favoriten anzeigen")
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📊 Rezept-Statistiken")
    total_recipes = len(recipes)
    
    if recipes:
        # Count recipes by category
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
    
    # Add recipe form
    st.markdown("### 👨‍🍳 Neues Rezept")
    with st.expander("Rezept hinzufügen", expanded=False):
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
            
            # Emoji selection for recipe
            emoji_options = ["🍽️", "🍛", "🍝", "🥑", "🥧", "🍲", "🍗", "🧀", "🌯", "🥔", "🥬", "🍳", "🥗", "🍅", "🥞", "🌮", "🍡", "🍚", "🥣", "🐟", "🥩", "🌶️", "🍆"]
            selected_emoji = st.selectbox("Rezept-Emoji", emoji_options, index=0)
            
            submitted = st.form_submit_button("Rezept speichern")

            if submitted:
                if title.strip() and description.strip() and ingredients.strip() and steps.strip() and time.strip():
                    new_recipe = {
                        "id": new_id(),
                        "title": title.strip(),
                        "description": description.strip(),
                        "ingredients": [i.strip() for i in ingredients.split("\n") if i.strip()],
                        "steps": [s.strip() for s in steps.split("\n") if s.strip()],
                        "time": time.strip(),
                        "category": category,
                        "calories": calories.strip(),
                        "favorite": False,
                        "image": selected_emoji
                    }
                    recipes.insert(0, new_recipe)
                    save_recipes(recipes)
                    st.success(f"Rezept **{title}** wurde hinzugefügt!")
                    st.rerun()
                else:
                    st.error("Bitte füllen Sie alle mit * markierten Felder aus!")

# -------------------------------
# Main area - Controls and Display
# -------------------------------
# Quick actions
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
            # Clear all special filters
            for key in ["show_random", "show_favorites", "show_vegan"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# -------------------------------
# Filter recipes
# -------------------------------
filtered = []

for r in recipes:
    # Quick filters from buttons
    if st.session_state.get("show_favorites") and not r.get("favorite", False):
        continue
    if st.session_state.get("show_vegan") and r.get("category") != "vegan":
        continue
    
    # Category filter
    if selected_categories and r.get("category", "vegetarisch") not in selected_categories:
        continue
    
    # Time filter
    if time_filter != "Beliebig":
        try:
            recipe_time_str = r.get("time", "0")
            # Extract numbers from time string (e.g., "20 min" -> 20)
            recipe_time = int(''.join(filter(str.isdigit, recipe_time_str.split()[0] if recipe_time_str else "0")))
            max_time = int(''.join(filter(str.isdigit, time_filter)))
            if recipe_time > max_time:
                continue
        except:
            pass
    
    # Calories filter
    if calories_filter != "Beliebig" and r.get("calories"):
        try:
            recipe_calories_str = r.get("calories", "0")
            recipe_calories = int(''.join(filter(str.isdigit, recipe_calories_str.split()[0] if recipe_calories_str else "0")))
            max_calories = int(''.join(filter(str.isdigit, calories_filter)))
            if recipe_calories > max_calories:
                continue
        except:
            pass
    
    # Favorite filter
    if only_favorites and not r.get("favorite", False):
        continue
    
    # Search filter
    search_lower = search.lower()
    if (not search_lower or 
        search_lower in r["title"].lower() or 
        any(search_lower in i.lower() for i in r["ingredients"]) or
        search_lower in r.get("category", "").lower() or
        search_lower in r.get("description", "").lower()):
        filtered.append(r)

selected_id = st.session_state.get("show_random", None)

# Show filter results
st.markdown(f"### 📋 Gefundene Rezepte: {len(filtered)}")

# -------------------------------
# Display recipes
# -------------------------------
if not recipes:
    st.info("Willkommen beim Chef's Recipe Hub! Fügen Sie Ihr erstes Rezept hinzu, um zu beginnen.")
elif not filtered and not selected_id:
    st.info("Keine Rezepte gefunden. Passen Sie Ihre Filterkriterien an oder fügen Sie ein neues Rezept hinzu.")
else:
    for recipe in filtered:
        if selected_id and recipe["id"] != selected_id:
            continue
            
        # Create a recipe card
        with st.container():
            st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Recipe header with emoji
                st.markdown(f"### {recipe.get('image', '🍽️')} {recipe['title']}")
                
                # Description
                st.write(recipe["description"])
                
                # Recipe metadata
                col1a, col2a, col3a = st.columns(3)
                with col1a:
                    st.markdown(f'<div class="time-badge">⏱️ {recipe.get("time", "")}</div>', unsafe_allow_html=True)
                with col2a:
                    category_color = get_category_color(recipe.get("category", "vegetarisch"))
                    category_name = recipe.get("category", "vegetarisch")
                    st.markdown(f'<div class="category-tag" style="background-color: {category_color}; color: white;">{category_name}</div>', unsafe_allow_html=True)
                with col3a:
                    if recipe.get("calories"):
                        st.markdown(f'<div class="calories-badge">🔥 {recipe.get("calories", "")} kcal</div>', unsafe_allow_html=True)
            
            with col2:
                # Favorite status
                favorite_status = "💔 Entfernen" if recipe.get("favorite", False) else "⭐ Favorit"
                if st.button(favorite_status, key=f"fav_{recipe['id']}", use_container_width=True):
                    recipe["favorite"] = not recipe.get("favorite", False)
                    save_recipes(recipes)
                    st.rerun()
            
            # Ingredients and steps in tabs
            tab1, tab2 = st.tabs(["🧂 Zutatenliste", "👨‍🍳 Zubereitungsschritte"])
            
            with tab1:
                st.markdown("#### Zutaten")
                for ingredient in recipe["ingredients"]:
                    st.markdown(f"- {ingredient}")
            
            with tab2:
                st.markdown("#### Zubereitung")
                for idx, step in enumerate(recipe["steps"], 1):
                    st.markdown(f"**{idx}.** {step}")
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🗑️ Löschen", key=f"del_{recipe['id']}", use_container_width=True):
                    recipes = [r for r in recipes if r["id"] != recipe["id"]]
                    save_recipes(recipes)
                    st.rerun()
            
            with col2:
                if st.button("✏️ Bearbeiten", key=f"edit_{recipe['id']}", use_container_width=True):
                    st.session_state["edit_recipe"] = recipe["id"]
                    st.info("Bearbeitungsfunktion kommt bald!")
            
            with col3:
                if st.button("📄 PDF", key=f"pdf_{recipe['id']}", use_container_width=True):
                    pdf = export_recipe_pdf(recipe)
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
