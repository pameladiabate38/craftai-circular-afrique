from __future__ import annotations
import math
import sqlite3
import os
import google.generativeai as genai
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable,List,Optional,Tuple,Union

import cv2
import numpy as np
import streamlit as st
from PIL import Image
import requests
# Configuration de la clé API
# Remplacez "VOTRE_CLE_API_GEMINI" par votre vraie clé (laissez les guillemets)

def obtenir_suggestions_ia(materiau, dimensions):
  if "GEMINI_API_KEY" in st.secrets:
    # Remplacez par votre vraie clé API
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
  else:
    st.error("Erreur:la cle GEMINI_API_KEY est introuvable.")
    st.stop() 
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    # Construction du prompt pour l'IA
    prompt = f"Tu es une experte en artisanat au Burkina Faso. Pour {materiau} ayant comme référence {dimensions}, propose 3 idées créatives."
    
    # Structure de la requête API standard
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        # Appel direct à l'API de Google, sans passer par la bibliothèque bloquée
        response = requests.post(url, json=payload)
        data = response.json()
        
        # Extraction du texte de la réponse
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"craftai est prêt, mais il y a un problème de connexion : {e}"

st.set_page_config(
    page_title="CraftAI Circular Afrique",
    page_icon="♻",
    layout="wide",
)


MATERIALS = {
    "Tissu": {
        "unit_weight": 0.018,
        "keywords": ["couture", "tissu africain", "wax", "chute de tissu"],
        "ideas": {
            "petite": [
                ("Boucles d'oreilles eclat d'Afrique", "facile", 30, "Bijou leger a vendre en serie courte."),
                ("Porte-cles textile", "facile", 20, "Petit accessoire utile avec faible perte."),
                ("Patch decoratif", "facile", 15, "Customisation de sacs, vestes ou cahiers."),
            ],
            "moyenne": [
                ("Pochette zippee", "moyen", 60, "Produit pratique pour telephone ou maquillage."),
                ("Serre-tete en tissu", "facile", 35, "Creation rapide pour marche local."),
                ("Mini trousse artisanale", "moyen", 55, "Objet vendable avec doublure simple."),
            ],
            "grande": [
                ("Sac tote mix-matieres", "moyen", 90, "Valorise plusieurs motifs ensemble."),
                ("Coussin decoratif", "moyen", 80, "Produit maison a bonne valeur percue."),
                ("Tablier creatif", "avance", 120, "Utile pour atelier ou cuisine."),
            ],
        },
    },
    "Cuir": {
        "unit_weight": 0.045,
        "keywords": ["cuir", "maroquinerie", "chute de cuir"],
        "ideas": {
            "petite": [
                ("Etiquettes de marque", "facile", 20, "Ajoute une finition professionnelle aux creations."),
                ("Porte-carte minimal", "moyen", 45, "Petit produit premium."),
                ("Boucles d'oreilles cuir", "facile", 30, "Bijou leger avec formes geometriques."),
            ],
            "moyenne": [
                ("Porte-monnaie cuir", "moyen", 70, "Bon usage des morceaux rectangulaires."),
                ("Bracelet ajuste", "facile", 35, "Accessoire rapide a personnaliser."),
                ("Housse de lunettes", "moyen", 75, "Produit utile et durable."),
            ],
            "grande": [
                ("Pochette enveloppe", "moyen", 100, "Creation elegante avec peu de coutures."),
                ("Ceinture patchwork", "avance", 120, "Assemble plusieurs bandes restantes."),
                ("Mini sac bandouliere", "avance", 150, "Produit a forte valeur commerciale."),
            ],
        },
    },
    "Bois": {
        "unit_weight": 0.09,
        "keywords": ["bois", "menuiserie", "chute de bois"],
        "ideas": {
            "petite": [
                ("Sous-verres graves", "facile", 35, "Lot decoratif pour table."),
                ("Pendentif bois", "facile", 30, "Bijou naturel et leger."),
                ("Support telephone simple", "moyen", 45, "Objet pratique pour bureau."),
            ],
            "moyenne": [
                ("Petit cadre photo", "moyen", 75, "Valorise les morceaux droits."),
                ("Boite a bijoux", "avance", 120, "Objet utile pour clientes artisanes."),
                ("Plateau decoratif", "moyen", 90, "Produit maison facile a exposer."),
            ],
            "grande": [
                ("Etagere murale", "avance", 150, "Creation visible pour interieur."),
                ("Lampe artisanale", "avance", 180, "Produit distinctif pour marche creatif."),
                ("Tabouret bas", "avance", 210, "Reutilisation de grandes sections solides."),
            ],
        },
    },
    "Papier / carton": {
        "unit_weight": 0.01,
        "keywords": ["papier", "carton", "upcycling"],
        "ideas": {
            "petite": [
                ("Etiquettes cadeau", "facile", 15, "Valorise les petits restes imprimes."),
                ("Marque-pages", "facile", 20, "Produit simple en lots."),
                ("Fleurs decoratives", "facile", 25, "Decoration pour emballages et evenements."),
            ],
            "moyenne": [
                ("Carnet recycle", "moyen", 50, "Papeterie utile a faible cout."),
                ("Boite cadeau", "moyen", 45, "Emballage artisanal vendable."),
                ("Carte relief", "facile", 35, "Produit personnalisable."),
            ],
            "grande": [
                ("Organiseur de bureau", "moyen", 80, "Objet utile pour maison ou atelier."),
                ("Abat-jour papier", "avance", 110, "Decoration legere et originale."),
                ("Presentoir produit", "avance", 120, "Aide a vendre d'autres creations."),
            ],
        },
    },
    "Metal": {
        "unit_weight": 0.12,
        "keywords": ["metal", "recyclage metal", "artisanat"],
        "ideas": {
            "petite": [
                ("Breloques decoratives", "moyen", 35, "Petites pieces pour bijoux."),
                ("Anneaux porte-cles", "moyen", 40, "Accessoire solide et utile."),
                ("Elements de suspension", "moyen", 45, "Pieces pour mobiles ou lampes."),
            ],
            "moyenne": [
                ("Bougeoir artisanal", "avance", 90, "Objet decoratif durable."),
                ("Poignee decorative", "avance", 80, "Reemploi pour meubles et boites."),
                ("Support bijoux", "avance", 100, "Produit d'exposition utile."),
            ],
            "grande": [
                ("Lampe metal recycle", "avance", 180, "Creation forte pour demonstration."),
                ("Petit presentoir", "avance", 150, "Support pour marche artisanal."),
                ("Decoration murale", "avance", 160, "Assemblage artistique a impact visuel."),
            ],
        },
    },
}

DB_PATH = Path(__file__).with_name("craftai.sqlite3")

REFERENCE_OBJECTS = {
    "Aucune reference": None,
    "Piece 200 FCFA BCEAO (24,5 mm)": 2.45,
    "Piece 500 FCFA BCEAO (28,8 mm)": 2.88,
}


@dataclass
class ImageAnalysis:
    width: int
    height: int
    dominant_colors: List[str]
    object_ratio: float
    contours: int
    estimated_length_cm: float
    estimated_width_cm: float
    estimated_pieces: int
    confidence: str
    reference_label: str
    reference_detected: bool
    pixels_per_cm:Optional[float]


def classify_size(length_cm: float, width_cm: float) -> str:
    area = length_cm * width_cm
    if area < 250:
        return "petite"
    if area < 1200:
        return "moyenne"
    return "grande"


def detect_reference_coin(gray: np.ndarray) ->Optional[Tuple[int, int, int]]:
    height, width = gray.shape[:2]
    blurred = cv2.medianBlur(gray, 5)
    min_radius = max(8, int(min(width, height) * 0.025))
    max_radius = max(min_radius + 4, int(min(width, height) * 0.18))
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min(width, height) / 4,
        param1=90,
        param2=28,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if circles is None:
        return None
    candidates = np.round(circles[0, :]).astype(int)
    return tuple(max(candidates, key=lambda item: item[2]))


def analyze_image(
    image: Image.Image,
    reference_label: str = "Aucune reference",
    reference_diameter_cm:Optional[float]= None,
) -> ImageAnalysis:
    rgb = np.array(image.convert("RGB"))
    height, width = rgb.shape[:2]
    small = cv2.resize(rgb, (80, 80), interpolation=cv2.INTER_AREA)
    pixels = small.reshape((-1, 3)).astype(np.float32)
    _, labels, centers = cv2.kmeans(
        pixels,
        4,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    counts = np.bincount(labels.flatten())
    ordered = centers[np.argsort(counts)[::-1]].astype(int)
    colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in ordered[:3]]

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 60, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    meaningful = [c for c in contours if cv2.contourArea(c) > 250]
    object_area = sum(cv2.contourArea(c) for c in meaningful)
    ratio = min(object_area / max(width * height, 1), 1.0)
    coin = detect_reference_coin(gray) if reference_diameter_cm else None
    pixels_per_cm = None
    reference_detected = False
    fabric_contours = meaningful

    if coin and reference_diameter_cm:
        coin_x, coin_y, coin_radius = coin
        coin_diameter_px = coin_radius * 2
        pixels_per_cm = coin_diameter_px / reference_diameter_cm
        reference_detected = True

        def is_coin_contour(contour: np.ndarray) -> bool:
            x, y, box_width, box_height = cv2.boundingRect(contour)
            center_x = x + box_width / 2
            center_y = y + box_height / 2
            close_to_coin = abs(center_x - coin_x) < coin_radius * 1.5 and abs(center_y - coin_y) < coin_radius * 1.5
            return close_to_coin and box_width < coin_radius * 3.2 and box_height < coin_radius * 3.2

        fabric_contours = [contour for contour in meaningful if not is_coin_contour(contour)] or meaningful

    if fabric_contours:
        largest = max(fabric_contours, key=cv2.contourArea)
        x, y, box_width, box_height = cv2.boundingRect(largest)
        if pixels_per_cm:
            estimated_length = max(1.0, round(box_width / pixels_per_cm, 1))
            estimated_width = max(1.0, round(box_height / pixels_per_cm, 1))
            confidence = "bonne avec reference"
        else:
            workspace_width_cm = 40
            workspace_height_cm = 30
            estimated_length = max(3.0, round((box_width / width) * workspace_width_cm, 1))
            estimated_width = max(3.0, round((box_height / height) * workspace_height_cm, 1))
            confidence = "moyenne sans reference" if ratio > 0.18 else "faible sans reference"
    else:
        estimated_length = 18.0
        estimated_width = 12.0
        confidence = "faible"

    estimated_pieces = max(1, min(len(meaningful), 50))

    return ImageAnalysis(
        width,
        height,
        colors,
        ratio,
        len(meaningful),
        estimated_length,
        estimated_width,
        estimated_pieces,
        confidence,
        reference_label,
        reference_detected,
        pixels_per_cm,
    )


def get_ideas(material: str, size: str) -> List[Tuple[str, str, int, str]]:
    return MATERIALS[material]["ideas"][size]


def local_tutorial_steps(title: str, material: str) -> List[str]:
    material_action = {
        "Tissu": "coupez proprement les bords puis repassez la chute",
        "Cuir": "nettoyez le cuir puis marquez les trous avant assemblage",
        "Bois": "poncez les bords puis retirez la poussiere",
        "Papier / carton": "aplatissez la matiere puis renforcez les plis",
        "Metal": "limez les bords puis verifiez qu'ils ne coupent pas",
    }[material]
    return [
        f"Selectionnez les morceaux adaptes pour: {title}.",
        f"Preparez le materiau: {material_action}.",
        "Dessinez la forme sur la chute avec un crayon ou une craie.",
        "Decoupez ou assemblez progressivement en gardant les chutes restantes.",
        "Ajoutez la finition: couture, colle, poncage, vernis, fermoir ou decoration.",
        "Verifiez la solidite puis prenez une photo pour la vente.",
    ]


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                artisan_name TEXT NOT NULL,
                material TEXT NOT NULL,
                length_cm REAL NOT NULL,
                width_cm REAL NOT NULL,
                pieces INTEGER NOT NULL,
                size_category TEXT NOT NULL,
                ideas TEXT NOT NULL,
                min_price INTEGER NOT NULL,
                max_price INTEGER NOT NULL
            )
            """
        )


def save_analysis(
    artisan_name: str,
    material: str,
    length_cm: float,
    width_cm: float,
    pieces: int,
    size: str,
    ideas: List[Tuple[str, str, int, str]],
    price_range: Tuple[int, int],
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO analyses (
                created_at, artisan_name, material, length_cm, width_cm,
                pieces, size_category, ideas, min_price, max_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                artisan_name,
                material,
                length_cm,
                width_cm,
                pieces,
                size,
                ", ".join(idea[0] for idea in ideas),
                price_range[0],
                price_range[1],
            ),
        )


def load_history() -> list[tuple]:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT created_at, artisan_name, material, length_cm, width_cm,
                   pieces, size_category, ideas, min_price, max_price
            FROM analyses
            ORDER BY id DESC
            LIMIT 30
            """
        ).fetchall()


def estimate_impact(material: str, length_cm: float, width_cm: float, pieces: int) -> tuple[float, int]:
    area = length_cm * width_cm
    saved_kg = area * MATERIALS[material]["unit_weight"] * pieces / 1000
    revenue = max(1000, int(math.ceil(area / 80) * 500 * pieces))
    return round(saved_kg, 2), revenue


def estimate_burkina_price(material: str, length_cm: float, width_cm: float, level: str) -> tuple[int, int]:
    area = length_cm * width_cm
    material_base = {
        "Tissu": 1500,
        "Cuir": 2500,
        "Bois": 3000,
        "Papier / carton": 1000,
        "Metal": 3500,
    }[material]
    level_factor = {"facile": 1.0, "moyen": 1.45, "avance": 2.0}[level]
    size_factor = max(0.8, min(area / 350, 3.2))
    center = material_base * level_factor * size_factor
    min_price = int(round(center * 0.8 / 500) * 500)
    max_price = int(round(center * 1.25 / 500) * 500)
    return max(500, min_price), max(1000, max_price)


def assistant_reply(message: str) -> str:
    text = message.lower()
    material = st.session_state.get("material", "Tissu")
    length_cm = st.session_state.get("length_cm", 18.0)
    width_cm = st.session_state.get("width_cm", 12.0)
    size = classify_size(length_cm, width_cm)
    ideas = get_ideas(material, size)
    if "prix" in text or "vente" in text or "fcfa" in text:
        ranges = [estimate_burkina_price(material, length_cm, width_cm, idea[1]) for idea in ideas]
        return (
            f"Pour le Burkina Faso, je proposerais une fourchette de demonstration entre "
            f"{min(price[0] for price in ranges):,} et {max(price[1] for price in ranges):,} FCFA, "
            "a ajuster selon la finition, le quartier, le temps de travail et le client."
        ).replace(",", " ")
    if "idee" in text or "faire" in text or "creer" in text:
        return "Voici mes 3 pistes: " + ", ".join(idea[0] for idea in ideas) + "."
    if "dimension" in text or "taille" in text:
        analysis = st.session_state.get("analysis")
        if analysis and analysis.reference_detected:
            return (
                f"L'estimation actuelle est {length_cm:g} cm x {width_cm:g} cm. "
                f"Elle utilise la reference: {analysis.reference_label}."
            )
        return f"L'estimation actuelle est {length_cm:g} cm x {width_cm:g} cm. Sans piece ou regle visible, cela reste approximatif."
    if "bonjour" in text or "salut" in text:
        return "Bonjour, je suis l'assistante CraftAI. Je peux aider a choisir une creation, expliquer le prix ou guider les etapes."
    return "Je peux vous aider a choisir une idee, estimer un prix de vente au Burkina Faso ou expliquer comment transformer la chute."

def obtenir_suggestions_ia(materiau: str, dimensions: str) -> str:
    try:
        # Assurez-vous que genai est bien configuré en haut du fichier
        # Et utilisez cette syntaxe précise :

        model = genai.GenerativeModel(model_name="gemini-flash-latest")
        
        prompt = f"""
        Tu es une experte en artisanat au Burkina Faso. 
        Pour une chute de {materiau} de {dimensions}, propose 3 idées originales de création.
        Pour chaque idée, donne : le nom, le niveau de difficulté, et une estimation du prix en FCFA.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return"cratfai:je suis un peu fatiguée aujourdhui (quota dépassé).Revenez me voir dans quelques instants"
        else:
            return f"Une erreur est survenue :{e}"
       # return f"Erreur IA : {str(e)}"

def render_color_swatches(colors: Iterable[str]) -> None:
    chips = "".join(
        f"<span style='display:inline-block;width:34px;height:20px;border-radius:6px;"
        f"border:1px solid #d7c7af;background:{color};margin-right:8px'></span>"
        for color in colors
    )
    st.markdown(chips, unsafe_allow_html=True)


st.markdown(
    """
    <style>
    :root {
      --green: #0f5a2a;
      --rust: #b85614;
      --sand: #f7efe2;
      --ink: #2b2118;
    }
    .stApp {
      background: #fffdf8;
      color: var(--ink);
    }
    .block-container { padding-top: 1.5rem; }
    .hero {
      border-bottom: 3px solid var(--green);
      padding-bottom: 1rem;
      margin-bottom: 1.3rem;
    }
    .hero h1 {
      color: var(--green);
      font-size: clamp(2.1rem, 4vw, 4.2rem);
      line-height: 1;
      margin: 0;
      letter-spacing: 0;
    }
    .hero strong { color: var(--rust); }
    .hero p { color: var(--ink); font-size: 1.08rem; margin-top: .4rem; }
    button[data-baseweb="tab"] p {
      color: var(--ink);
      font-weight: 600;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
      color: var(--rust);
    }
    .impact-card {
      background: #fffaf2;
      border: 1px solid #ead7bd;
      border-radius: 8px;
      padding: 1rem;
      height: 100%;
      color: var(--ink);
    }
    .idea-card {
      border: 1px solid #d9c7aa;
      border-radius: 8px;
      padding: 1rem;
      background: white;
      min-height: 190px;
      color: var(--ink);
    }
    .idea-card h3 { margin: 0 0 .25rem 0; color: var(--green); font-size: 1.15rem; }
    .badge {
      display: inline-block;
      border-radius: 999px;
      padding: .2rem .55rem;
      background: #e8f3ea;
      color: var(--green);
      font-size: .78rem;
      margin-right: .3rem;
    }
    div[data-testid="stMetricValue"] { color: var(--green); }
    </style>
    <div class="hero">
      <h1>CraftAI Circular <strong>Afrique</strong></h1>
      <p>Un prototype IA local pour transformer les chutes artisanales en creations utiles, vendables et durables.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


init_db()

tab_home, tab_scan, tab_results, tab_chat, tab_history = st.tabs(
    ["Accueil", "Scanner", "Idees & tutoriels", "Assistant IA", "Historique"]
)

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "tutorials" not in st.session_state:
    st.session_state.tutorials = {}
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        ("ia", "Bonjour, je peux aider a transformer vos chutes en creations vendables au Burkina Faso.")
    ]


with tab_home:
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        artisan_name = st.text_input("Entrez votre nom", value=st.session_state.get("artisan_name", "Awa"))
        st.session_state.artisan_name = artisan_name.strip() or "artisane"
        st.subheader(f"Bonjour, {st.session_state.artisan_name}")
        st.write(
            "Photographiez vos materiaux restants. L'IA estime les dimensions, reconnait les couleurs dominantes et propose des creations adaptees."
        )

    with right:
        st.markdown(
            """
            <div class="impact-card">
              <b>Comment ca marche ?</b><br><br>
              1. Photographier les chutes<br>
              2. Estimer les dimensions et couleurs<br>
              3. Proposer 3 idees realistes<br>
              4. Trouver des tutoriels<br>
              5. Valoriser ou vendre la creation
            </div>
            """,
            unsafe_allow_html=True,
        )


with tab_scan:
    controls, preview = st.columns([0.9, 1.1], gap="large")
    with controls:
        st.subheader("Cadrez vos materiaux")
        uploaded = st.file_uploader("Photo des chutes", type=["jpg", "jpeg", "png", "webp"])
        material = st.selectbox("Type de materiau", list(MATERIALS.keys()))
        reference_label = st.selectbox(
            "Objet de reference pour mesurer",
            list(REFERENCE_OBJECTS.keys()),
            index=1,
        )
        st.info(
            "Placez la piece choisie a plat a cote du tissu. L'IA utilise son diametre connu pour convertir les pixels en centimetres."
        )

        if st.button("Analyser et proposer", type="primary", use_container_width=True):
            if uploaded is not None:
                image = Image.open(uploaded)
                analysis = analyze_image(image, reference_label, REFERENCE_OBJECTS[reference_label])
                st.session_state.analysis = analysis
                st.session_state.length_cm = analysis.estimated_length_cm
                st.session_state.width_cm = analysis.estimated_width_cm
                st.session_state.pieces = analysis.estimated_pieces
            else:
                st.session_state.analysis = None
                st.session_state.length_cm = 18.0
                st.session_state.width_cm = 12.0
                st.session_state.pieces = 1
            st.session_state.material = material
            size = classify_size(st.session_state.length_cm, st.session_state.width_cm)
            ideas = get_ideas(material, size)
            price_ranges = [
                estimate_burkina_price(material, st.session_state.length_cm, st.session_state.width_cm, idea[1])
                for idea in ideas
            ]
            save_analysis(
                st.session_state.get("artisan_name", "artisane"),
                material,
                st.session_state.length_cm,
                st.session_state.width_cm,
                st.session_state.pieces,
                size,
                ideas,
                (min(price[0] for price in price_ranges), max(price[1] for price in price_ranges)),
            )
            st.success("Analyse terminee. Ouvrez l'onglet Idees & tutoriels.")

    with preview:
        if uploaded is not None:
            image = Image.open(uploaded)
            st.image(image, caption="Photo importee", use_container_width=True)
        else:
            st.info("Importez une photo pour que l'IA estime automatiquement les dimensions.")

        if st.session_state.analysis:
            st.write("Couleurs dominantes detectees")
            render_color_swatches(st.session_state.analysis.dominant_colors)
            m1, m2, m3 = st.columns(3)
            m1.metric("Image", f"{st.session_state.analysis.width} x {st.session_state.analysis.height}")
            m2.metric("Contours", st.session_state.analysis.contours)
            m3.metric("Occupation", f"{st.session_state.analysis.object_ratio:.0%}")
            d1, d2, d3 = st.columns(3)
            d1.metric("Longueur estimee", f"{st.session_state.analysis.estimated_length_cm:g} cm")
            d2.metric("Largeur estimee", f"{st.session_state.analysis.estimated_width_cm:g} cm")
            d3.metric("Confiance", st.session_state.analysis.confidence)
            if st.session_state.analysis.reference_label != "Aucune reference":
                if st.session_state.analysis.reference_detected:
                    st.success(
                        f"Reference detectee: {st.session_state.analysis.reference_label}. "
                        f"Echelle: {st.session_state.analysis.pixels_per_cm:.1f} pixels/cm."
                    )
                else:
                    st.warning(
                        "La piece de reference n'a pas ete detectee clairement. Reprenez la photo de dessus, avec la piece bien visible."
                    )


with tab_results:
    material = st.session_state.get("material", "Tissu")
    length_cm = st.session_state.get("length_cm", 18.0)
    width_cm = st.session_state.get("width_cm", 12.0)
    pieces = st.session_state.get("pieces", 6)
    size = classify_size(length_cm, width_cm)
    ideas = get_ideas(material, size)

    st.subheader("Resultats proposes")
    st.subheader("Suggestions de l'IA (Expertise Artisanale)")
    dims = f"{length_cm} cm x {width_cm} cm"
    suggestions = obtenir_suggestions_ia(material, dims)
    st.markdown(suggestions)
    st.caption(f"Materiau: {material} | Dimensions: {length_cm:g} x {width_cm:g} cm | Categorie: {size}")

    cols = st.columns(3)
    for index, idea in enumerate(ideas):
        title, level, minutes, description = idea
        min_price, max_price = estimate_burkina_price(material, length_cm, width_cm, level)
        with cols[index]:
            st.markdown(
                f"""
                <div class="idea-card">
                  <h3>{title}</h3>
                  <span class="badge">Niveau: {level}</span>
                  <span class="badge">{minutes} min</span>
                  <p>{description}</p>
                  <p><b>Prix estime au Burkina Faso :</b><br>{min_price:,} - {max_price:,} FCFA</p>
                </div>
                """.replace(",", " "),
                unsafe_allow_html=True,
                )


    st.caption(
        "Les prix sont des estimations de demonstration pour le Burkina Faso. Ils doivent etre ajustes selon la qualite, la finition, le temps de travail et le marche local."
    )


with tab_chat:
    st.subheader("Conversation avec l'IA")
    st.write("Posez une question sur les idees, les dimensions, les tutoriels ou le prix de vente au Burkina Faso.")

    for role, message in st.session_state.chat_messages:
        with st.chat_message("assistant" if role == "ia" else "user"):
            st.write(message)

    user_message = st.chat_input("Exemple: quel prix de vente pour cette creation ?")
    if user_message:
        st.session_state.chat_messages.append(("utilisateur", user_message))
        reply = assistant_reply(user_message)
        st.session_state.chat_messages.append(("ia", reply))
        st.rerun()


with tab_history:
    st.subheader("Historique SQLite")
    st.write("Chaque analyse est sauvegardee dans une base SQLite locale et visible ici.")
    st.caption(f"Base de donnees: {DB_PATH}")

    rows = load_history()
    if not rows:
        st.info("Aucune analyse enregistree pour le moment. Lancez une analyse dans l'onglet Scanner.")
    else:
        for row in rows:
            (
                created_at,
                artisan_name,
                material,
                length_cm,
                width_cm,
                pieces,
                size_category,
                ideas_text,
                min_price,
                max_price,
            ) = row
            st.markdown(
                f"""
                <div class="impact-card">
                  <b>{created_at} - {artisan_name}</b><br>
                  Materiau: {material} | Dimensions estimees: {length_cm:g} x {width_cm:g} cm | Morceaux: {pieces}<br>
                  Categorie: {size_category}<br>
                  Idees: {ideas_text}<br>
                  Prix estime Burkina Faso: {min_price:,} - {max_price:,} FCFA
                </div>
                <br>
                """.replace(",", " "),
                unsafe_allow_html=True,
            )
