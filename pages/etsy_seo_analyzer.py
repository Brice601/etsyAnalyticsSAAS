import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
from collections import Counter
import re
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOUVEAUX IMPORTS
from auth.access_manager import (
    check_access, 
    has_access_to_dashboard, 
    show_upgrade_message,
    has_insights_subscription,
    show_insights_upgrade_cta,
    show_locked_recommendation,
    check_usage_limit,
    increment_usage,
    show_usage_limit_message,
    should_increment_usage,
    increment_usage_with_timestamp
)
from data_collection.collector import show_data_opt_in

# Configuration de la page
st.set_page_config(
    page_title="Etsy SEO & Traffic Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Masquer les pages home, dashboard et signup dans la navigation */
    [data-testid="stSidebarNav"] li:has(a[href*="home"]),
    [data-testid="stSidebarNav"] li:has(a[href*="dashboard"]),
    [data-testid="stSidebarNav"] li:has(a[href*="signup"]) {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ========== NOUVEAU : VÉRIFICATION D'ACCÈS ==========
user_info = check_access()

# Récupérer le customer_id (UUID)
customer_id = user_info.get('id')

# # Vérifier l'accès à ce dashboard spécifique
# if not has_access_to_dashboard(customer_id, 'seo_analyzer'):
#     show_upgrade_message('seo_analyzer', customer_id)
#     st.stop()
# # ====================================================

# ========== AFFICHAGE POP-UP CONSENTEMENT ==========
show_data_opt_in(user_info['email'])
# ===================================================

# Styles CSS personnalisés
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #F56400;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #F56400;
    }
    .seo-score-high {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .seo-score-medium {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
    .seo-score-low {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
    .recommendation-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #007bff;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FONCTIONS DE CHARGEMENT ====================

@st.cache_data
def load_listings(uploaded_file):
    """Charge les listings Etsy"""
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        # Mapping des colonnes
        column_mapping = {
            'TITRE': 'Title',
            'Title': 'Title',
            'DESCRIPTION': 'Description',
            'Description': 'Description',
            'PRIX': 'Price',
            'Price': 'Price',
            'TAGS': 'Tags',
            'Tags': 'Tags',
            'QUANTITÉ': 'Quantity',
            'Quantity': 'Quantity',
            'RÉFÉRENCE': 'SKU',
            'SKU': 'SKU',
            'Reference': 'SKU'
        }
        
        # Renommer les colonnes
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Vérifier les colonnes essentielles
        required = ['Title', 'Price']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            st.error(f"❌ Colonnes manquantes : {', '.join(missing)}")
            return None
        
        # Nettoyer les données
        if 'Price' in df.columns:
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        # Compter le nombre d'images
        image_cols = [col for col in df.columns if 'IMAGE' in col.upper()]
        df['Num_Images'] = df[image_cols].notna().sum(axis=1)
        
        st.success(f"✅ {len(df)} listings chargés avec succès !")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        return None

@st.cache_data
def load_sales_data(uploaded_file):
    """Charge les données de ventes"""
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        # Mapping colonnes ventes
        column_mapping = {
            'Sale Date': 'Date',
            'Date de vente': 'Date',
            'Item Name': 'Product',
            'Price': 'Price',
            'Item Price': 'Price',
            'Quantity': 'Quantity'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
            df = df.dropna(subset=['Date'])
        
        if 'Price' in df.columns:
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        if 'Quantity' not in df.columns:
            df['Quantity'] = 1
        
        st.success(f"✅ {len(df)} ventes chargées avec succès !")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        return None

# ==================== FONCTIONS D'ANALYSE SEO ====================

def calculate_title_seo_score(title):
    """Calcule le score SEO d'un titre (0-100)"""
    score = 0
    issues = []
    recommendations = []
    
    if pd.isna(title):
        return 0, ["❌ Titre manquant"], ["Ajoutez un titre descriptif"]
    
    title_len = len(str(title))
    
    # Longueur optimale (140 caractères max Etsy)
    if 100 <= title_len <= 140:
        score += 30
    elif 80 <= title_len < 100:
        score += 20
        recommendations.append("📏 Augmentez la longueur du titre (optimal: 100-140 caractères)")
    elif title_len < 80:
        score += 10
        issues.append("❌ Titre trop court")
        recommendations.append("📏 Allongez votre titre à 100-140 caractères")
    else:
        score += 15
        issues.append("⚠️ Titre trop long")
        recommendations.append("✂️ Réduisez à 140 caractères maximum")
    
    # Nombre de mots
    words = str(title).split(',')
    num_words = len(words)
    
    if num_words >= 3:
        score += 25
    elif num_words >= 2:
        score += 15
        recommendations.append("📝 Ajoutez plus de mots-clés séparés par des virgules")
    else:
        score += 5
        issues.append("❌ Pas assez de mots-clés")
        recommendations.append("📝 Utilisez des virgules pour séparer les mots-clés")
    
    # Présence de mots-clés importants pour bijoux
    jewelry_keywords = ['bracelet', 'bague', 'collier', 'boucles', 'bijou', 'argent', 
                       'or', 'protection', 'cadeau', 'femme', 'homme', 'sterling']
    
    title_lower = str(title).lower()
    keywords_found = sum(1 for kw in jewelry_keywords if kw in title_lower)
    
    if keywords_found >= 2:
        score += 25
    elif keywords_found >= 1:
        score += 15
        recommendations.append("🎯 Ajoutez plus de mots-clés pertinents")
    else:
        score += 5
        issues.append("❌ Manque de mots-clés pertinents")
        recommendations.append("🎯 Incluez des mots comme 'bracelet', 'argent', 'cadeau', etc.")
    
    # Utilisation de caractères spéciaux attrayants
    if any(char in str(title) for char in ['✨', '💎', '🎁', '❤️']):
        score += 10
    
    # Première lettre en majuscule
    if str(title)[0].isupper():
        score += 10
    else:
        recommendations.append("🔤 Mettez la première lettre en majuscule")
    
    return min(score, 100), issues, recommendations

def analyze_tags(tags_str):
    """Analyse les tags d'un listing"""
    if pd.isna(tags_str):
        return []
    
    # Séparer les tags (par virgule ou point-virgule)
    tags = re.split(r'[,;]', str(tags_str))
    tags = [tag.strip().lower() for tag in tags if tag.strip()]
    
    return tags

def get_seo_category(score):
    """Retourne la catégorie SEO en fonction du score"""
    if score >= 80:
        return "🟢 Excellent", "seo-score-high"
    elif score >= 60:
        return "🟡 Bon", "seo-score-medium"
    elif score >= 40:
        return "🟠 Moyen", "seo-score-medium"
    else:
        return "🔴 Faible", "seo-score-low"

# ==================== FONCTIONS D'ANALYSE AVANCÉE ====================

def analyze_listing_performance(listings_df, sales_df):
    """Croise les listings avec les ventes pour identifier les performances"""
    
    if sales_df is None or 'Product' not in sales_df.columns:
        return None
    
    # Compter les ventes par produit
    sales_count = sales_df.groupby('Product').agg({
        'Quantity': 'sum',
        'Price': 'sum'
    }).reset_index()
    sales_count.columns = ['Title', 'Sales_Count', 'Revenue']
    
    # Merger avec les listings
    performance = listings_df.merge(sales_count, on='Title', how='left')
    performance['Sales_Count'] = performance['Sales_Count'].fillna(0)
    performance['Revenue'] = performance['Revenue'].fillna(0)
    
    return performance

def extract_keywords_from_titles(titles):
    """Extrait les mots-clés les plus fréquents des titres"""
    all_words = []
    
    for title in titles:
        if pd.notna(title):
            # Séparer par virgules et espaces
            words = re.split(r'[,\s]+', str(title).lower())
            # Filtrer les mots courts et communs
            words = [w.strip() for w in words if len(w) > 3 and w not in 
                    ['pour', 'avec', 'dans', 'the', 'and', 'for', 'with']]
            all_words.extend(words)
    
    return Counter(all_words)

# ==================== GÉNÉRATION PDF ====================

def generate_seo_pdf_report(listings_df, seo_analysis, sales_df=None):
    """Génère un rapport PDF avec l'analyse SEO"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#F56400'),
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("🔍 Rapport SEO Etsy", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date
    date_text = f"Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    story.append(Paragraph(date_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Score SEO global
    avg_score = seo_analysis['SEO_Score'].mean()
    story.append(Paragraph("📊 Score SEO Global", styles['Heading2']))
    
    score_data = [
        ['Indicateur', 'Valeur'],
        ['Score SEO moyen', f"{avg_score:.1f}/100"],
        ['Listings excellents (≥80)', f"{len(seo_analysis[seo_analysis['SEO_Score'] >= 80])}"],
        ['Listings à optimiser (<60)', f"{len(seo_analysis[seo_analysis['SEO_Score'] < 60])}"]
    ]
    
    score_table = Table(score_data, colWidths=[3*inch, 2*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F56400')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Top 5 listings à optimiser
    story.append(Paragraph("🎯 Top 5 Listings à Optimiser", styles['Heading2']))
    
    worst_listings = seo_analysis.nsmallest(5, 'SEO_Score')
    
    for idx, row in worst_listings.iterrows():
        title_short = row['Title'][:50] + "..." if len(row['Title']) > 50 else row['Title']
        story.append(Paragraph(f"<b>{title_short}</b> - Score: {row['SEO_Score']:.0f}/100", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== INTERFACE PRINCIPALE ====================

# En-tête
st.markdown('<p class="main-header">🔍 Etsy SEO & Traffic Analyzer</p>', unsafe_allow_html=True)
st.markdown("### 🎯 Optimisez votre visibilité et explosez vos ventes !")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x100/F56400/FFFFFF?text=SEO+Analyzer", width=200)
    st.markdown("---")
    
    st.markdown("### 📤 Import des données")
    
    listings_file = st.file_uploader(
        "1️⃣ Fichier Listings (EtsyListingsDownload.csv)",
        type=['csv'],
        help="Export Etsy : Shop Manager > Settings > Download Data > Listings"
    )
    
    sales_file = st.file_uploader(
        "2️⃣ Fichier Ventes (optionnel - EtsySoldOrderItems.csv)",
        type=['csv'],
        help="Pour croiser les performances SEO avec les ventes réelles"
    )
    
    st.markdown("---")
    st.markdown("### 📚 Guide rapide")
    
    with st.expander("📥 Comment exporter depuis Etsy ?"):
        st.markdown("""
        **Pour les Listings :**
        1. Etsy.com > Shop Manager
        2. Settings > Options > Download Data
        3. Section "Listings" > Download CSV
        
        **Pour les Ventes (optionnel) :**
        1. Shop Manager > Settings > Download Data
        2. Section "Orders" > Order Items
        3. Download CSV
        """)
    
    with st.expander("🎯 Que va analyser l'outil ?"):
        st.markdown("""
        ✅ Score SEO de chaque listing
        ✅ Optimisation des titres
        ✅ Efficacité des tags
        ✅ Impact des photos
        ✅ Performance des listings
        ✅ Recommandations personnalisées
        """)

# Corps principal
if listings_file is None:

    # Page d'accueil
    st.info("👆 Commencez par importer votre fichier de listings Etsy dans la barre latérale")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 Score SEO")
        st.write("Évaluez la qualité SEO de chaque listing avec un score 0-100")
    
    with col2:
        st.markdown("### 🔍 Analyse des titres")
        st.write("Optimisez vos titres pour maximiser votre visibilité")
    
    with col3:
        st.markdown("### 🏷️ Efficacité des tags")
        st.write("Identifiez les tags qui convertissent le mieux")
    
    st.markdown("---")
    
    # Exemple de données
    st.markdown("### 📊 Exemple de rapport SEO")
    
    example_data = pd.DataFrame({
        'Listing': ['Bracelet rouge protection', 'Bague argent sterling', 'Collier perles'],
        'Score SEO': [85, 62, 45],
        'Longueur titre': [132, 98, 67],
        'Nb tags': [13, 8, 5],
        'Nb photos': [10, 7, 3]
    })
    
    st.dataframe(example_data, width='stretch')
    
    st.markdown("### 🎁 Ce que vous obtiendrez")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📈 Analyses détaillées :**
        - Score SEO par listing
        - Distribution des performances
        - Comparaison best-sellers vs non-vendeurs
        - Analyse temporelle des ventes
        """)
    
    with col2:
        st.markdown("""
        **🤖 Recommandations IA :**
        - Actions prioritaires à prendre
        - Listings à optimiser en urgence
        - Stratégie de tags personnalisée
        - Timing optimal pour nouveaux produits
        """)

else:
    # Après check_access()
    usage_info = check_usage_limit(customer_id)

    if not usage_info['allowed']:
        show_usage_limit_message(usage_info)
        st.stop()

    # Chargement des données
    listings_df = load_listings(listings_file)
    sales_df = None
    
    if sales_file is not None:
        sales_df = load_sales_data(sales_file)

        # ========== INCRÉMENTER USAGE SI NÉCESSAIRE ==========
        if should_increment_usage(customer_id):
            increment_usage_with_timestamp(customer_id)
            
            # Rafraîchir usage_info
            usage_info = check_usage_limit(customer_id)
            
            # Message discret pour utilisateurs gratuits
            if not has_insights_subscription(customer_id):
                st.info(f"📊 Analyse {usage_info['usage_count']}/{usage_info['limit']} cette semaine (reset dans {usage_info['days_until_reset']} jours)")
        
    
    if listings_df is not None:
        
        # Analyse SEO de tous les listings
        seo_results = []
        
        with st.spinner("🔍 Analyse SEO en cours..."):
            for idx, row in listings_df.iterrows():
                score, issues, recs = calculate_title_seo_score(row['Title'])
                
                seo_results.append({
                    'Title': row['Title'],
                    'SEO_Score': score,
                    'Price': row.get('Price', 0),
                    'Num_Images': row.get('Num_Images', 0),
                    'Issues': issues,
                    'Recommendations': recs
                })
        
        seo_analysis = pd.DataFrame(seo_results)
        
        # Croiser avec les ventes si disponibles
        if sales_df is not None:
            performance_df = analyze_listing_performance(listings_df, sales_df)
            if performance_df is not None:
                seo_analysis = seo_analysis.merge(
                    performance_df[['Title', 'Sales_Count', 'Revenue']], 
                    on='Title', 
                    how='left'
                )
                seo_analysis['Sales_Count'] = seo_analysis['Sales_Count'].fillna(0)
                seo_analysis['Revenue'] = seo_analysis['Revenue'].fillna(0)

        # ========== NOUVEAU : COLLECTE DE DONNÉES ==========
        # if st.session_state.get('consent_asked', False):
    # Récupérer TOUS les fichiers uploadés
        all_files = {}
        
        # Fichier listings (principal)
        if listings_file is not None:
            all_files['listings'] = listings_file
        
        # Fichier sales (optionnel - pour croiser performances)
        if sales_file is not None:
            all_files['sales'] = sales_file
        
        # Collecter
        from data_collection.collector import collect_raw_data
        if all_files:  # Seulement si on a des fichiers
            collect_raw_data(all_files, user_info['email'], 'seo_analyzer')
        # ===================================================
        
        # Onglets
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Vue d'ensemble SEO",
            "🔍 Analyse des Titres",
            "🏷️ Performance des Tags",
            "📈 Analyse Avancée",
            "🤖 Recommandations IA"
        ])
        
        with tab1:
            st.markdown("## 📊 Vue d'ensemble SEO")
            
            # KPIs
            avg_score = seo_analysis['SEO_Score'].mean()
            excellent_count = len(seo_analysis[seo_analysis['SEO_Score'] >= 80])
            to_optimize_count = len(seo_analysis[seo_analysis['SEO_Score'] < 60])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Score SEO Moyen", f"{avg_score:.1f}/100")
            
            with col2:
                st.metric("Listings Excellents", f"{excellent_count}", 
                         delta=f"{excellent_count/len(seo_analysis)*100:.0f}%")
            
            with col3:
                st.metric("À Optimiser", f"{to_optimize_count}",
                         delta=f"-{to_optimize_count/len(seo_analysis)*100:.0f}%",
                         delta_color="inverse")
            
            with col4:
                avg_images = seo_analysis['Num_Images'].mean()
                st.metric("Photos Moyenne", f"{avg_images:.1f}")
            
            st.markdown("---")
            
            # Distribution des scores
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Distribution des scores SEO")
                
                fig = px.histogram(
                    seo_analysis,
                    x='SEO_Score',
                    nbins=20,
                    title="Répartition des scores SEO",
                    color_discrete_sequence=['#F56400']
                )
                fig.update_layout(
                    xaxis_title="Score SEO",
                    yaxis_title="Nombre de listings",
                    height=400
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                st.markdown("### 🎯 Répartition par catégorie")
                
                categories = pd.cut(seo_analysis['SEO_Score'], 
                                   bins=[0, 40, 60, 80, 100],
                                   labels=['🔴 Faible', '🟠 Moyen', '🟡 Bon', '🟢 Excellent'])
                
                cat_counts = categories.value_counts()
                
                fig = px.pie(
                    values=cat_counts.values,
                    names=cat_counts.index,
                    title="Catégories SEO",
                    color_discrete_sequence=['#dc3545', '#ffc107', '#28a745', "#ff6e0d"]
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
            
            # Tableau des listings
            st.markdown("### 📋 Tous vos listings avec score SEO")
            
            display_df = seo_analysis[['Title', 'SEO_Score', 'Price', 'Num_Images']].copy()
            display_df['SEO_Score'] = display_df['SEO_Score'].apply(lambda x: f"{x:.0f}/100")
            display_df['Price'] = display_df['Price'].apply(lambda x: f"{x:.2f} €")
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "Title": "Titre du listing",
                    "SEO_Score": "Score SEO",
                    "Price": "Prix",
                    "Num_Images": "Nb Photos"
                }
            )
        
        with tab2:
            st.markdown("## 🔍 Analyse Détaillée des Titres")
            
            # Statistiques sur les titres
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_title_len = listings_df['Title'].str.len().mean()
                st.metric("Longueur Moyenne", f"{avg_title_len:.0f} car.")
            
            with col2:
                optimal_titles = len(listings_df[listings_df['Title'].str.len().between(100, 140)])
                st.metric("Titres Optimaux (100-140)", optimal_titles)
            
            with col3:
                short_titles = len(listings_df[listings_df['Title'].str.len() < 80])
                st.metric("Titres Trop Courts (<80)", short_titles)
            
            st.markdown("---")
            
            # Distribution longueur titres
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📏 Distribution des longueurs de titres")
                
                fig = px.histogram(
                    listings_df,
                    x=listings_df['Title'].str.len(),
                    nbins=20,
                    title="Longueur des titres (caractères)",
                    color_discrete_sequence=['#007bff']
                )
                fig.add_vline(x=100, line_dash="dash", line_color="green", 
                             annotation_text="Min optimal (100)")
                fig.add_vline(x=140, line_dash="dash", line_color="red",
                             annotation_text="Max Etsy (140)")
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                st.markdown("### 🎯 Corrélation longueur ↔ Score SEO")
                
                fig = px.scatter(
                    seo_analysis,
                    x=listings_df['Title'].str.len(),
                    y='SEO_Score',
                    title="Impact de la longueur sur le score SEO",
                    color='SEO_Score',
                    color_continuous_scale='RdYlGn',
                    labels={'x': 'Longueur titre (caractères)', 'y': 'Score SEO'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
            
            st.markdown("---")
            
            # Analyse listing par listing
            st.markdown("### 📝 Analyse détaillée par listing")
            
            for idx, row in seo_analysis.iterrows():
                category, css_class = get_seo_category(row['SEO_Score'])
                
                with st.expander(f"{category} - {row['Title'][:60]}... (Score: {row['SEO_Score']:.0f}/100)"):
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Titre complet :** {row['Title']}")
                        st.markdown(f"**Longueur :** {len(row['Title'])} caractères")
                        st.markdown(f"**Prix :** {row['Price']:.2f} €")
                        st.markdown(f"**Photos :** {row['Num_Images']}")
                        
                        if sales_df is not None and 'Sales_Count' in row:
                            st.markdown(f"**Ventes :** {int(row['Sales_Count'])}")
                    
                    with col2:
                        st.metric("Score SEO", f"{row['SEO_Score']:.0f}/100")
                    
                    if row['Issues']:
                        st.markdown("**⚠️ Problèmes détectés :**")
                        for issue in row['Issues']:
                            st.markdown(f"- {issue}")
                    
                    if row['Recommendations']:
                        st.markdown("**💡 Recommandations :**")
                        for rec in row['Recommendations']:
                            st.markdown(f"- {rec}")
        
        with tab3:
            st.markdown("## 🏷️ Analyse des Tags")
            
            # Extraire tous les tags
            all_tags = []
            for idx, row in listings_df.iterrows():
                if 'Tags' in row and pd.notna(row['Tags']):
                    tags = analyze_tags(row['Tags'])
                    all_tags.extend(tags)
            
            if all_tags:
                tag_counter = Counter(all_tags)
                most_common_tags = tag_counter.most_common(20)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🏆 Top 20 Tags les plus utilisés")
                    
                    tags_df = pd.DataFrame(most_common_tags, columns=['Tag', 'Utilisation'])
                    
                    fig = px.bar(
                        tags_df,
                        x='Utilisation',
                        y='Tag',
                        orientation='h',
                        title="Tags les plus fréquents",
                        color='Utilisation',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    st.markdown("### 📊 Statistiques des tags")
                    
                    st.metric("Tags uniques", len(tag_counter))
                    st.metric("Tags total", len(all_tags))
                    st.metric("Moyenne par listing", f"{len(all_tags)/len(listings_df):.1f}")
                    
                    st.markdown("---")
                    
                    st.markdown("### 🎯 Tags recommandés pour bijoux")
                    
                    recommended_tags = [
                        'bracelet', 'silver', 'gift', 'handmade', 'jewelry',
                        'protection', 'minimalist', 'sterling', 'dainty',
                        'adjustable', 'womens', 'mens', 'couple', 'birthday'
                    ]
                    
                    tags_present = [tag for tag in recommended_tags if tag in all_tags]
                    tags_missing = [tag for tag in recommended_tags if tag not in all_tags]
                    
                    st.markdown("**✅ Tags présents :**")
                    st.write(", ".join(tags_present) if tags_present else "Aucun")
                    
                    st.markdown("**❌ Tags manquants (opportunités) :**")
                    st.write(", ".join(tags_missing) if tags_missing else "Tous présents !")
                
                # Tags par listing
                st.markdown("---")
                st.markdown("### 📋 Tags par listing")
                
                tags_by_listing = []
                for idx, row in listings_df.iterrows():
                    tags = analyze_tags(row.get('Tags', ''))
                    tags_by_listing.append({
                        'Title': row['Title'][:50] + "...",
                        'Nb_Tags': len(tags),
                        'Tags': ', '.join(tags[:5]) + ('...' if len(tags) > 5 else '')
                    })
                
                st.dataframe(pd.DataFrame(tags_by_listing), width='stretch')
            
            else:
                st.warning("⚠️ Aucun tag trouvé dans vos listings. Ajoutez des tags pour améliorer votre SEO !")
        
        with tab4:
            st.markdown("## 📈 Analyse Avancée")
            
            # Vérifier abonnement Insights
            has_insights = has_insights_subscription(customer_id)
            
            if not has_insights:
                # MODE GRATUIT : TEASER BLURRED
                st.info("""
                💎 **Fonctionnalités Insights disponibles avec l'abonnement 9€/mois :**
                - 🎯 Corrélation Score SEO vs Ventes réelles
                - 📊 Comparaison Best-sellers vs Non-vendeurs
                - 📸 Impact nombre de photos sur performances
                - 📅 Analyse temporelle (meilleurs jours/heures)
                - ⚠️ Identification produits 0 vente à booster
                - 💡 ROI de vos optimisations SEO
                """)
                
                if sales_df is not None and 'Sales_Count' in seo_analysis.columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 🎯 Score SEO vs Ventes (preview)")
                        st.markdown("""
                        <div style='filter: blur(8px); pointer-events: none; user-select: none;'>
                            <img src='https://via.placeholder.com/400x300/f0f2f6/666?text=Graphique+Score+SEO+vs+Ventes' style='width: 100%; border-radius: 10px;'>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("### 📊 Comparaison Vendus vs Non-Vendus (preview)")
                        st.markdown("""
                        <div style='filter: blur(8px); pointer-events: none; user-select: none;'>
                            <p><strong>Produits vendus :</strong> Score moyen 78/100</p>
                            <p><strong>Produits non vendus :</strong> Score moyen 52/100</p>
                            <p><strong>Écart :</strong> +26 points</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("### 📸 Impact Photos (preview)")
                    st.markdown("""
                    <div style='filter: blur(8px); pointer-events: none; user-select: none;'>
                        <img src='https://via.placeholder.com/800x300/f0f2f6/666?text=Graphique+Photos+vs+Ventes' style='width: 100%; border-radius: 10px;'>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("📊 Importez le fichier de ventes pour débloquer les analyses de performance")
                
                st.markdown("---")
                show_insights_upgrade_cta()
            
            elif sales_df is not None and 'Sales_Count' in seo_analysis.columns:
                # MODE PREMIUM : TOUT DÉBLOQUÉ
                st.success("💎 **Insights Premium activé**")
                
                # Corrélation SEO Score vs Ventes
                st.markdown("### 🎯 Impact du Score SEO sur les Ventes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.scatter(
                        seo_analysis,
                        x='SEO_Score',
                        y='Sales_Count',
                        size='Revenue',
                        color='SEO_Score',
                        hover_data=['Title'],
                        title="Score SEO vs Nombre de Ventes",
                        color_continuous_scale='RdYlGn',
                        labels={'Sales_Count': 'Nombre de ventes', 'SEO_Score': 'Score SEO'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    # Best-sellers vs non-vendeurs
                    best_sellers = seo_analysis[seo_analysis['Sales_Count'] > 0]
                    non_sellers = seo_analysis[seo_analysis['Sales_Count'] == 0]
                    
                    comparison = pd.DataFrame({
                        'Catégorie': ['Produits vendus', 'Produits non vendus'],
                        'Score SEO Moyen': [
                            best_sellers['SEO_Score'].mean() if len(best_sellers) > 0 else 0,
                            non_sellers['SEO_Score'].mean() if len(non_sellers) > 0 else 0
                        ],
                        'Nombre': [len(best_sellers), len(non_sellers)]
                    })
                    
                    fig = px.bar(
                        comparison,
                        x='Catégorie',
                        y='Score SEO Moyen',
                        text='Score SEO Moyen',
                        title="Comparaison Score SEO : Vendus vs Non Vendus",
                        color='Score SEO Moyen',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                
                st.markdown("---")
                
                # Impact du nombre de photos
                st.markdown("### 📸 Impact du Nombre de Photos")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.scatter(
                        seo_analysis,
                        x='Num_Images',
                        y='Sales_Count',
                        size='Revenue',
                        color='SEO_Score',
                        hover_data=['Title'],
                        title="Nombre de Photos vs Ventes",
                        color_continuous_scale='Viridis',
                        labels={'Num_Images': 'Nombre de photos', 'Sales_Count': 'Ventes'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    # Stats photos
                    photo_stats = seo_analysis.groupby('Num_Images').agg({
                        'Sales_Count': 'sum',
                        'Revenue': 'sum'
                    }).reset_index()
                    
                    fig = px.bar(
                        photo_stats,
                        x='Num_Images',
                        y='Sales_Count',
                        title="Ventes par Nombre de Photos",
                        color='Sales_Count',
                        color_continuous_scale='Blues',
                        labels={'Num_Images': 'Nombre de photos', 'Sales_Count': 'Total ventes'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                
                # Analyse temporelle
                if 'Date' in sales_df.columns:
                    st.markdown("---")
                    st.markdown("### 📅 Analyse Temporelle des Ventes")
                    
                    # Meilleurs jours
                    sales_df['DayOfWeek'] = sales_df['Date'].dt.day_name()
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
                    
                    daily_sales = sales_df.groupby('DayOfWeek')['Price'].sum().reindex(day_order).reset_index()
                    daily_sales['DayOfWeek'] = day_names_fr
                    daily_sales.columns = ['Jour', 'CA']
                    
                    fig = px.bar(
                        daily_sales,
                        x='Jour',
                        y='CA',
                        title="Chiffre d'Affaires par Jour de la Semaine",
                        color='CA',
                        color_continuous_scale='Oranges'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                    
                    best_day_idx = daily_sales['CA'].idxmax()
                    best_day = daily_sales.loc[best_day_idx, 'Jour']
                    
                    st.info(f"💡 **Meilleur jour :** {best_day} - Idéal pour publier de nouveaux listings !")
            
            else:
                st.info("📊 Importez le fichier de ventes pour voir les analyses de performance avancées")
        
        with tab5:
            st.markdown("## 🤖 Recommandations IA Personnalisées")
            
            recommendations = []
            
            # Recommandation 1 : Score SEO global
            if avg_score < 60:
                recommendations.append({
                    'priority': '🔴 HAUTE',
                    'title': 'Améliorer votre Score SEO Global',
                    'detail': f"Votre score SEO moyen ({avg_score:.1f}/100) est faible. Objectif : atteindre 70+",
                    'actions': [
                        "Allongez vos titres à 100-140 caractères",
                        "Ajoutez plus de mots-clés séparés par des virgules",
                        "Utilisez 13 tags par listing (maximum autorisé)",
                        f"Optimisez en priorité les {to_optimize_count} listings avec score < 60"
                    ]
                })
            elif avg_score < 75:
                recommendations.append({
                    'priority': '🟡 MOYENNE',
                    'title': 'Optimiser votre Score SEO',
                    'detail': f"Votre score SEO ({avg_score:.1f}/100) est correct mais améliorable.",
                    'actions': [
                        "Peaufinez les titres de vos listings",
                        "Diversifiez vos tags",
                        "Ajoutez plus de photos (10 recommandé)"
                    ]
                })
            else:
                recommendations.append({
                    'priority': '🟢 INFO',
                    'title': 'Excellent Score SEO !',
                    'detail': f"Bravo ! Votre score SEO ({avg_score:.1f}/100) est excellent.",
                    'actions': [
                        "Maintenez cette qualité",
                        "Concentrez-vous sur les nouveaux listings",
                        "Testez de nouveaux mots-clés tendance"
                    ]
                })
            
            # Recommandation 2 : Listings à optimiser
            worst_listings = seo_analysis.nsmallest(3, 'SEO_Score')
            
            if len(worst_listings) > 0:
                listings_text = "\n".join([f"- {row['Title'][:50]}... (Score: {row['SEO_Score']:.0f}/100)" 
                                          for _, row in worst_listings.iterrows()])
                
                recommendations.append({
                    'priority': '🔴 HAUTE',
                    'title': 'Optimiser ces 3 listings en priorité',
                    'detail': f"Ces listings ont les scores SEO les plus faibles :\n{listings_text}",
                    'actions': [
                        "Rallongez les titres à 120+ caractères",
                        "Ajoutez des mots-clés pertinents",
                        "Complétez les tags (13 maximum)",
                        "Ajoutez plus de photos (7-10 recommandé)",
                        "Optimisez les descriptions"
                    ]
                })
            
            # Recommandation 3 : Photos
            avg_photos = seo_analysis['Num_Images'].mean()
            
            if avg_photos < 7:
                listings_low_photos = seo_analysis[seo_analysis['Num_Images'] < 5]
                recommendations.append({
                    'priority': '🟡 MOYENNE',
                    'title': 'Augmenter le Nombre de Photos',
                    'detail': f"Vous avez en moyenne {avg_photos:.1f} photos par listing. Objectif : 7-10 photos",
                    'actions': [
                        f"{len(listings_low_photos)} listings ont moins de 5 photos",
                        "Ajoutez des photos sous différents angles",
                        "Incluez des photos d'utilisation/lifestyle",
                        "Montrez les détails et la qualité",
                        "Utilisez un fond blanc pour la première photo"
                    ]
                })
            
            # Recommandation 4 : Tags
            if all_tags:
                unique_tags = len(set(all_tags))
                avg_tags_per_listing = len(all_tags) / len(listings_df)
                
                if avg_tags_per_listing < 10:
                    recommendations.append({
                        'priority': '🟡 MOYENNE',
                        'title': 'Optimiser votre Stratégie de Tags',
                        'detail': f"Vous utilisez en moyenne {avg_tags_per_listing:.1f} tags par listing. Maximum : 13",
                        'actions': [
                            "Utilisez les 13 tags disponibles sur chaque listing",
                            "Variez vos tags (vous en utilisez seulement {unique_tags} uniques)",
                            "Incluez : nom du produit, matériaux, occasion, style, couleur",
                            "Testez des tags long-tail (ex: 'bracelet argent minimaliste')",
                            "Analysez les tags des concurrents best-sellers"
                        ]
                    })
            
            # Recommandation 5 : Performance si ventes disponibles
            if sales_df is not None and 'Sales_Count' in seo_analysis.columns:
                non_sellers = seo_analysis[seo_analysis['Sales_Count'] == 0]
                
                if len(non_sellers) > 0:
                    recommendations.append({
                        'priority': '🔴 HAUTE',
                        'title': 'Produits Sans Ventes à Booster',
                        'detail': f"{len(non_sellers)} listings n'ont généré aucune vente.",
                        'actions': [
                            "Améliorez leur score SEO (optimisation prioritaire)",
                            "Testez une baisse de prix temporaire (-15%)",
                            "Ajoutez des photos plus attractives",
                            "Réécrivez complètement les titres avec de nouveaux mots-clés",
                            "Promouvez-les avec Etsy Ads",
                            "Envisagez de retirer ceux sans vente depuis 90+ jours"
                        ]
                    })
                
                # Meilleur moment pour publier
                if 'Date' in sales_df.columns:
                    sales_df['Hour'] = sales_df['Date'].dt.hour
                    best_hour = sales_df.groupby('Hour')['Price'].sum().idxmax()
                    
                    # Calculer le meilleur jour
                    sales_df['DayOfWeek'] = sales_df['Date'].dt.day_name()
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
                    
                    daily_sales_rec = sales_df.groupby('DayOfWeek')['Price'].sum().reindex(day_order)
                    best_day_idx = daily_sales_rec.idxmax()
                    best_day = day_names_fr[day_order.index(best_day_idx)]
                    
                    recommendations.append({
                        'priority': '🟢 INFO',
                        'title': 'Timing Optimal pour Nouveaux Listings',
                        'detail': f"L'analyse de vos ventes révèle les meilleurs moments pour publier.",
                        'actions': [
                            f"Publiez vos nouveaux listings autour de {best_hour}h",
                            f"Le {best_day} est votre meilleur jour",
                            "Renouvelez vos listings anciens ces jours-là",
                            "Évitez de publier le week-end si peu de ventes"
                        ]
                    })
            
            # Affichage des recommandations
            st.markdown("### 🎯 Vos Actions Prioritaires")
            
            # Vérifier abonnement Insights
            has_insights = has_insights_subscription(customer_id)
            
            if not has_insights:
                st.info("""
                🎁 **1 recommandation gratuite débloquée**  
                💎 **4+ recommandations premium disponibles avec Insights 9€/mois**
                """)
                
                # Afficher la MEILLEURE recommandation (priorité HAUTE)
                best_rec = None
                for rec in recommendations:
                    if rec['priority'] == '🔴 HAUTE':
                        best_rec = rec
                        break
                
                if best_rec is None and recommendations:
                    best_rec = recommendations[0]
                
                if best_rec:
                    with st.expander(f"✅ {best_rec['priority']} - {best_rec['title']}", expanded=True):
                        st.markdown(f"**{best_rec['detail']}**")
                        st.markdown("**📋 Actions à prendre :**")
                        for action in best_rec['actions']:
                            st.markdown(f"- {action}")
                
                # Afficher les autres LOCKÉES
                st.markdown("---")
                st.markdown("### 🔒 Recommandations Premium")
                
                locked_recs = [r for r in recommendations if r != best_rec][:4]
                
                for rec in locked_recs:
                    show_locked_recommendation(rec['title'], rec['priority'])
                
                # CTA UPGRADE
                st.markdown("---")
                show_insights_upgrade_cta()
            
            else:
                # MODE PAYANT : Toutes les recommandations
                st.success("💎 **Insights Premium activé** - Toutes les recommandations débloquées")
                
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"{rec['priority']} - {rec['title']}", expanded=(i <= 2)):
                        st.markdown(f"**{rec['detail']}**")
                        st.markdown("**📋 Actions à prendre :**")
                        for action in rec['actions']:
                            st.markdown(f"- {action}")
            
            st.markdown("---")
            
            # Checklist actionnable
            st.markdown("### ✅ Checklist d'Optimisation SEO")
            
            checklist = [
                "Tous mes titres font entre 100-140 caractères",
                "J'utilise les 13 tags sur chaque listing",
                "Chaque listing a au moins 7 photos",
                "Mes titres contiennent des mots-clés recherchés",
                "J'ai optimisé les 5 listings avec le score SEO le plus faible",
                "Mes photos ont un fond blanc/neutre",
                "J'ai testé différents mots-clés",
                "Je renouvelle régulièrement mes listings",
                "J'analyse mes concurrents best-sellers",
                "J'ai une stratégie de pricing cohérente"
            ]
            
            for item in checklist:
                st.checkbox(item)
        
        # ========== EXPORT PDF (PREMIUM ONLY) ==========
        # Bouton d'export PDF
        st.markdown("---")
        st.markdown("## 📄 Exporter le rapport")

        # Vérifier abonnement Insights
        has_insights = has_insights_subscription(customer_id)

        if not has_insights:
            # MODE GRATUIT : Bloquer l'export
            st.warning("🔒 **Export PDF réservé aux abonnés Insights Premium**")
            
            # Bouton blurré
            st.markdown("""
            <div style='filter: blur(3px); pointer-events: none;'>
            """, unsafe_allow_html=True)
            st.button("📥 Générer le rapport PDF", type="primary", use_container_width=True, disabled=True)
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            # MODE PAYANT : Export disponible
            if st.button("📥 Générer le rapport PDF", type="primary", use_container_width=True):
                with st.spinner("Génération du rapport en cours..."):
                    pdf_buffer = generate_pdf_report(kpis, df, product_analysis)
                    
                    st.download_button(
                        label="⬇️ Télécharger le rapport PDF",
                        data=pdf_buffer,
                        file_name=f"rapport_etsy_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    st.success("✅ Rapport généré avec succès !")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Etsy SEO & Traffic Analyzer</strong> - Version 1.0</p>
    <p>🔍 Optimisez votre visibilité Etsy et multipliez vos ventes</p>
    <p style='font-size: 0.9em;'>Questions ? contact@etsy-seo-analyzer.com</p>
</div>
""", unsafe_allow_html=True)