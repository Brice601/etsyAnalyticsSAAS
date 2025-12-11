import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import json
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
    page_title="Etsy Customer Intelligence",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== NOUVEAU : VÉRIFICATION D'ACCÈS ==========
user_info = check_access()

# Récupérer le customer_id (UUID)
customer_id = user_info.get('id')

# # Vérifier l'accès à ce dashboard spécifique
# if not has_access_to_dashboard(customer_id, 'customer_intelligence'):
#     show_upgrade_message('customer_intelligence', customer_id)
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
    .insight-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #007bff;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .danger-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FONCTIONS DE CHARGEMENT ====================

@st.cache_data
def load_orders_data(uploaded_file):
    """Charge les données de commandes Etsy"""
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        # Mapping des colonnes
        column_mapping = {
            'Date de vente': 'Date',
            'Sale Date': 'Date',
            'Commande n°': 'Order_ID',
            'Order ID': 'Order_ID',
            'Acheteur': 'Buyer',
            'Buyer': 'Buyer',
            'Nom complet': 'Buyer_Name',
            'Full Name': 'Buyer_Name',
            'Pays de livraison': 'Country',
            'Ship Country': 'Country',
            'Ville de livraison': 'City',
            'Ship City': 'City',
            'Total de la commande': 'Total',
            'Order Total': 'Total',
            'Date d\'envoi': 'Ship_Date',
            'Date Shipped': 'Ship_Date',
            'Date Paid': 'Date_Paid'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Conversion des dates
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
        if 'Ship_Date' in df.columns:
            df['Ship_Date'] = pd.to_datetime(df['Ship_Date'], errors='coerce', format='mixed')
        if 'Date_Paid' in df.columns:
            df['Date_Paid'] = pd.to_datetime(df['Date_Paid'], errors='coerce', format='mixed')
        
        # Nettoyage des montants
        if 'Total' in df.columns:
            df['Total'] = (df['Total'].astype(str)
                          .str.replace(',', '.', regex=False)
                          .str.replace(' ', '', regex=False)
                          .str.replace('€', '', regex=False)
                          .str.replace('EUR', '', regex=False))
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
        
        # Nettoyage des pays
        if 'Country' in df.columns:
            country_mapping = {
                'Etats-Unis': 'United States',
                'États-Unis': 'United States',
                'Grande-Bretagne': 'United Kingdom',
                'Royaume-Uni': 'United Kingdom',
                'Allemagne': 'Germany',
                'Espagne': 'Spain',
                'Italie': 'Italy',
                'Pays-Bas': 'Netherlands',
                'Suisse': 'Switzerland',
                'Belgique': 'Belgium',
                'Andorre': 'Andorra',
                'Grèce': 'Greece',
                'Norvège': 'Norway'
            }
            df['Country'] = df['Country'].replace(country_mapping)
        
        df = df.dropna(subset=['Date'])
        
        st.success(f"✅ {len(df)} commandes chargées avec succès !")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        return None

@st.cache_data
def load_items_data(uploaded_file):
    """Charge les données d'items Etsy"""
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        column_mapping = {
            'Sale Date': 'Date',
            'Item Name': 'Product',
            'Price': 'Price',
            'Item Price': 'Price',
            'Quantity': 'Quantity',
            'Order ID': 'Order_ID'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
        
        if 'Price' in df.columns:
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        if 'Quantity' not in df.columns:
            df['Quantity'] = 1
        
        df = df.dropna(subset=['Date'])
        
        st.success(f"✅ {len(df)} items chargés avec succès !")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        return None

@st.cache_data
def load_reviews_data(uploaded_file):
    """Charge les données de reviews (JSON ou CSV)"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'json':
            # Charger depuis JSON
            reviews_data = json.load(uploaded_file)
            df = pd.DataFrame(reviews_data)
            
            # Mapping des colonnes JSON
            column_mapping = {
                'reviewer': 'Reviewer',
                'date_reviewed': 'Date',
                'star_rating': 'Rating',
                'message': 'Review_Text',
                'order_id': 'Order_ID'
            }
            
            df = df.rename(columns=column_mapping)
            
        else:
            # Charger depuis CSV
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            
            column_mapping = {
                'Date': 'Date',
                'Review Date': 'Date',
                'Rating': 'Rating',
                'Star Rating': 'Rating',
                'Review': 'Review_Text',
                'Comment': 'Review_Text',
                'Message': 'Review_Text',
                'Reviewer': 'Reviewer',
                'Buyer': 'Reviewer',
                'Order ID': 'Order_ID'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col not in df.columns:
                    df = df.rename(columns={old_col: new_col})
        
        # Conversion des dates
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
        
        # S'assurer que Rating est numérique
        if 'Rating' in df.columns:
            df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        
        # Remplir les reviews vides
        if 'Review_Text' in df.columns:
            df['Review_Text'] = df['Review_Text'].fillna('')
        
        df = df.dropna(subset=['Date', 'Rating'])
        
        st.success(f"✅ {len(df)} avis chargés avec succès !")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des reviews : {e}")
        return None

# ==================== FONCTIONS D'ANALYSE ====================

def analyze_geography(orders_df):
    """Analyse géographique des clients"""
    
    if 'Country' not in orders_df.columns:
        return None, None
    
    # Analyse par pays
    country_analysis = orders_df.groupby('Country').agg({
        'Order_ID': 'count',
        'Total': 'sum'
    }).reset_index()
    country_analysis.columns = ['Country', 'Orders', 'Revenue']
    country_analysis['Avg_Basket'] = country_analysis['Revenue'] / country_analysis['Orders']
    country_analysis = country_analysis.sort_values('Revenue', ascending=False)
    
    # Analyse par ville
    city_analysis = None
    if 'City' in orders_df.columns:
        city_analysis = orders_df.groupby('City').agg({
            'Order_ID': 'count',
            'Total': 'sum'
        }).reset_index()
        city_analysis.columns = ['City', 'Orders', 'Revenue']
        city_analysis = city_analysis.sort_values('Orders', ascending=False).head(10)
    
    return country_analysis, city_analysis

def analyze_customer_retention(orders_df):
    """Analyse de la fidélisation clients"""
    
    if 'Buyer' not in orders_df.columns:
        return None
    
    customer_analysis = orders_df.groupby('Buyer').agg({
        'Order_ID': 'count',
        'Total': 'sum',
        'Date': ['min', 'max']
    }).reset_index()
    
    customer_analysis.columns = ['Buyer', 'Num_Orders', 'Total_Spent', 'First_Order', 'Last_Order']
    
    # Calcul du délai entre achats
    customer_analysis['Days_Between_Orders'] = (
        customer_analysis['Last_Order'] - customer_analysis['First_Order']
    ).dt.days / (customer_analysis['Num_Orders'] - 1)
    
    customer_analysis['Days_Between_Orders'] = customer_analysis['Days_Between_Orders'].fillna(0)
    
    # Lifetime Value
    customer_analysis['LTV'] = customer_analysis['Total_Spent']
    
    # Clients à risque (pas d'achat depuis 90+ jours)
    customer_analysis['Days_Since_Last'] = (datetime.now() - customer_analysis['Last_Order']).dt.days
    customer_analysis['Churn_Risk'] = customer_analysis['Days_Since_Last'] > 90
    
    return customer_analysis

def analyze_reviews_sentiment(reviews_df):
    """Analyse de sentiment des reviews"""
    
    if reviews_df is None or 'Review_Text' not in reviews_df.columns:
        return None, None
    
    # Mots-clés positifs et négatifs (français et anglais)
    positive_keywords = [
        'parfait', 'super', 'excellent', 'magnifique', 'beautiful', 'love', 'great',
        'rapide', 'soigné', 'qualité', 'quality', 'recommande', 'recommend', 'joli',
        'conforme', 'ravie', 'ravi', 'merci', 'thank', 'top', 'perfect'
    ]
    
    negative_keywords = [
        'déçue', 'déçu', 'disappointed', 'abîme', 'broken', 'bad', 'poor',
        'retard', 'late', 'delay', 'problème', 'problem', 'mauvais', 'petit',
        'small', 'pas reçu', 'not received', 'scam', 'fraude'
    ]
    
    # Compter les occurrences
    positive_counts = Counter()
    negative_counts = Counter()
    
    for text in reviews_df['Review_Text']:
        if pd.notna(text) and text:
            text_lower = str(text).lower()
            
            for keyword in positive_keywords:
                if keyword in text_lower:
                    positive_counts[keyword] += text_lower.count(keyword)
            
            for keyword in negative_keywords:
                if keyword in text_lower:
                    negative_counts[keyword] += text_lower.count(keyword)
    
    return positive_counts, negative_counts

def extract_all_words(reviews_df):
    """Extrait tous les mots significatifs des reviews"""
    
    if reviews_df is None or 'Review_Text' not in reviews_df.columns:
        return Counter()
    
    all_words = []
    
    # Mots à ignorer (stop words)
    stop_words = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'à', 'a', 'au',
        'pour', 'avec', 'dans', 'sur', 'par', 'est', 'qui', 'que', 'the', 'and',
        'for', 'with', 'in', 'on', 'at', 'to', 'a', 'of', 'is', 'it', 'my', 'i',
        'très', 'bien', 'pas', 'très', 'c', 'il', 'j', 'ai', 'me', 'ma', 'mon'
    }
    
    for text in reviews_df['Review_Text']:
        if pd.notna(text) and text:
            # Nettoyer et tokenizer
            words = re.findall(r'\b[a-zàâäéèêëïîôùûüÿç]{3,}\b', str(text).lower())
            # Filtrer les stop words
            words = [w for w in words if w not in stop_words]
            all_words.extend(words)
    
    return Counter(all_words)

def calculate_shipping_delays(orders_df):
    """Calcule les délais de livraison"""
    
    if 'Date_Paid' not in orders_df.columns or 'Ship_Date' not in orders_df.columns:
        return None
    
    orders_df['Shipping_Delay'] = (
        orders_df['Ship_Date'] - orders_df['Date_Paid']
    ).dt.days
    
    return orders_df

# ==================== GÉNÉRATION PDF ====================

def generate_customer_intelligence_pdf(orders_df, reviews_df, customer_analysis):
    """Génère un rapport PDF Customer Intelligence"""
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
    story.append(Paragraph("👥 Rapport Customer Intelligence", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date
    date_text = f"Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    story.append(Paragraph(date_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # KPIs principaux
    story.append(Paragraph("📊 Indicateurs Clés", styles['Heading2']))
    
    total_customers = orders_df['Buyer'].nunique() if 'Buyer' in orders_df.columns else 0
    total_orders = len(orders_df)
    avg_rating = reviews_df['Rating'].mean() if reviews_df is not None and 'Rating' in reviews_df.columns else 0
    
    kpi_data = [
        ['Indicateur', 'Valeur'],
        ['Clients uniques', str(total_customers)],
        ['Commandes totales', str(total_orders)],
        ['Note moyenne', f"{avg_rating:.2f}/5" if avg_rating > 0 else 'N/A'],
        ['Pays couverts', str(orders_df['Country'].nunique()) if 'Country' in orders_df.columns else 'N/A']
    ]
    
    if customer_analysis is not None:
        repeat_rate = (customer_analysis['Num_Orders'] > 1).sum() / len(customer_analysis) * 100
        avg_ltv = customer_analysis['LTV'].mean()
        kpi_data.append(['Taux clients récurrents', f"{repeat_rate:.1f}%"])
        kpi_data.append(['LTV moyen', f"{avg_ltv:.2f} €"])
    
    kpi_table = Table(kpi_data, colWidths=[3*inch, 2*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F56400')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Top 5 pays
    if 'Country' in orders_df.columns:
        story.append(Paragraph("🌍 Top 5 Pays", styles['Heading2']))
        
        country_sales = orders_df.groupby('Country')['Total'].sum().nlargest(5)
        
        country_data = [['Pays', 'Chiffre d\'affaires']]
        for country, revenue in country_sales.items():
            country_data.append([country, f"{revenue:.2f} €"])
        
        country_table = Table(country_data, colWidths=[2.5*inch, 2*inch])
        country_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F56400')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(country_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== INTERFACE PRINCIPALE ====================

# En-tête
st.markdown('<p class="main-header">👥 Etsy Customer Intelligence</p>', unsafe_allow_html=True)
st.markdown("### 🎯 Comprenez vos clients et fidélisez-les")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x100/F56400/FFFFFF?text=Customer+Intel", width=200)
    st.markdown("---")
    
    st.markdown("### 📤 Import des données")
    
    orders_file = st.file_uploader(
        "1️⃣ Fichier Commandes (EtsySoldOrders.csv)",
        type=['csv'],
        help="Export Etsy : Shop Manager > Download Data > Orders"
    )
    
    items_file = st.file_uploader(
        "2️⃣ Fichier Items (EtsySoldOrderItems.csv)",
        type=['csv'],
        help="Export Etsy : Shop Manager > Download Data > Order Items"
    )
    
    reviews_file = st.file_uploader(
        "3️⃣ Fichier Reviews (reviews.json ou .csv)",
        type=['json', 'csv'],
        help="Export Etsy : Shop Manager > Download Data > Reviews"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Paramètres")
    
    period = st.selectbox(
        "Période d'analyse",
        ["Tout", "30 derniers jours", "90 derniers jours", "6 mois", "1 an"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📚 Guide")
    
    with st.expander("📥 Comment exporter depuis Etsy ?"):
        st.markdown("""
        **Commandes :**
        1. Shop Manager > Settings > Download Data
        2. Section "Orders" > Download CSV
        
        **Items :**
        1. Shop Manager > Settings > Download Data
        2. Section "Order Items" > Download CSV
        
        **Reviews :**
        1. Shop Manager > Settings > Download Data
        2. Section "Reviews" > Download
        """)

# Corps principal
if orders_file is None:

    # Page d'accueil
    st.info("👆 Commencez par importer vos fichiers CSV Etsy dans la barre latérale")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🌍 Profil Clients")
        st.write("Découvrez d'où viennent vos clients et leur comportement d'achat")
    
    with col2:
        st.markdown("### ⭐ Analyse des Avis")
        st.write("Analysez les sentiments et identifiez les points d'amélioration")
    
    with col3:
        st.markdown("### 🔄 Fidélisation")
        st.write("Calculez la LTV et identifiez les clients à risque de churn")
    
    st.markdown("---")
    
    st.markdown("### 🎯 Ce que vous obtiendrez")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 Analyses détaillées :**
        - Répartition géographique des ventes
        - Comportement d'achat par pays
        - Analyse de sentiment des reviews
        - Taux de clients récurrents
        - Lifetime Value (LTV) par client
        """)
    
    with col2:
        st.markdown("""
        **🤖 Insights actionnables :**
        - Clients VIP à chouchouter
        - Clients à risque de churn
        - Problèmes récurrents à résoudre
        - Opportunités de fidélisation
        - Recommandations marketing personnalisées
        """)

else:
    # Après check_access()
    usage_info = check_usage_limit(customer_id)

    if not usage_info['allowed']:
        show_usage_limit_message(usage_info)
        st.stop()

    # Chargement des données
    orders_df = load_orders_data(orders_file)
    items_df = None
    reviews_df = None
    
    if items_file is not None:
        items_df = load_items_data(items_file)

        # ========== INCRÉMENTER USAGE SI NÉCESSAIRE ==========
        if should_increment_usage(customer_id):
            increment_usage_with_timestamp(customer_id)
            
            # Rafraîchir usage_info
            usage_info = check_usage_limit(customer_id)
            
            # Message discret pour utilisateurs gratuits
            if not has_insights_subscription(customer_id):
                st.info(f"📊 Analyse {usage_info['usage_count']}/{usage_info['limit']} cette semaine (reset dans {usage_info['days_until_reset']} jours)")
        
    
    if reviews_file is not None:
        reviews_df = load_reviews_data(reviews_file)
    
    if orders_df is not None:
        
        # Filtrage par période
        if period != "Tout" and 'Date' in orders_df.columns:
            days_map = {
                "30 derniers jours": 30,
                "90 derniers jours": 90,
                "6 mois": 180,
                "1 an": 365
            }
            if period in days_map:
                cutoff_date = datetime.now() - timedelta(days=days_map[period])
                orders_df = orders_df[orders_df['Date'] >= cutoff_date]
                
                if items_df is not None and 'Date' in items_df.columns:
                    items_df = items_df[items_df['Date'] >= cutoff_date]
                
                if reviews_df is not None and 'Date' in reviews_df.columns:
                    reviews_df = reviews_df[reviews_df['Date'] >= cutoff_date]
        
        # Analyses
        country_analysis, city_analysis = analyze_geography(orders_df)
        customer_analysis = analyze_customer_retention(orders_df)
        
        positive_words, negative_words = None, None
        all_words = Counter()
        if reviews_df is not None:
            positive_words, negative_words = analyze_reviews_sentiment(reviews_df)
            all_words = extract_all_words(reviews_df)

        # ========== NOUVEAU : COLLECTE DE DONNÉES ==========
        # if st.session_state.get('consent_asked', False):
        # Récupérer TOUS les fichiers uploadés
        all_files = {}
        
        # Fichier orders (principal)
        if orders_file is not None:
            all_files['orders'] = orders_file
        
        # Fichier items (optionnel)
        if items_file is not None:
            all_files['items'] = items_file
        
        # Fichier reviews (optionnel)
        if reviews_file is not None:
            all_files['reviews'] = reviews_file
        
        # Collecter
        from data_collection.collector import collect_raw_data
        if all_files:  # Seulement si on a des fichiers
            collect_raw_data(all_files, user_info['email'], 'customer_intelligence')
        # ===================================================
        
        # Onglets
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🌍 Profil Clients",
            "⭐ Analyse des Avis",
            "🛒 Comportement d'Achat",
            "🔄 Fidélisation",
            "📧 Recommandations"
        ])
        
        with tab1:
            st.markdown("## 🌍 Profil Géographique des Clients")
            
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_customers = orders_df['Buyer'].nunique() if 'Buyer' in orders_df.columns else 0
                st.metric("Clients Uniques", total_customers)
            
            with col2:
                total_countries = orders_df['Country'].nunique() if 'Country' in orders_df.columns else 0
                st.metric("Pays Couverts", total_countries)
            
            with col3:
                if customer_analysis is not None:
                    repeat_customers = (customer_analysis['Num_Orders'] > 1).sum()
                    repeat_rate = (repeat_customers / len(customer_analysis) * 100) if len(customer_analysis) > 0 else 0
                    st.metric("Clients Récurrents", f"{repeat_rate:.1f}%")
            
            with col4:
                new_customers = (customer_analysis['Num_Orders'] == 1).sum() if customer_analysis is not None else 0
                st.metric("Nouveaux Clients", new_customers)
            
            st.markdown("---")
            
            # Carte géographique
            if country_analysis is not None:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🗺️ Répartition Mondiale des Ventes")
                    
                    fig = px.choropleth(
                        country_analysis,
                        locations='Country',
                        locationmode='country names',
                        color='Revenue',
                        hover_name='Country',
                        hover_data={'Orders': True, 'Revenue': ':.2f'},
                        color_continuous_scale='Oranges',
                        title="Chiffre d'affaires par pays"
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    st.markdown("### 🏆 Top 10 Pays par CA")
                    
                    top_10_countries = country_analysis.head(10)
                    
                    fig = px.bar(
                        top_10_countries,
                        x='Revenue',
                        y='Country',
                        orientation='h',
                        text='Revenue',
                        color='Orders',
                        color_continuous_scale='Blues'
                    )
                    fig.update_traces(texttemplate='%{text:.2f}€', textposition='outside')
                    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, width='stretch')
                
                # Top villes
                if city_analysis is not None:
                    st.markdown("---")
                    st.markdown("### 🏙️ Top 10 Villes")
                    
                    fig = px.bar(
                        city_analysis,
                        x='Orders',
                        y='City',
                        orientation='h',
                        text='Orders',
                        color='Revenue',
                        color_continuous_scale='Greens'
                    )
                    fig.update_traces(texttemplate='%{text}', textposition='outside')
                    fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, width='stretch')
                
                # Tableau détaillé par pays
                st.markdown("---")
                st.markdown("### 📋 Détail par Pays")
                
                display_country = country_analysis.copy()
                display_country['Revenue'] = display_country['Revenue'].apply(lambda x: f"{x:.2f} €")
                display_country['Avg_Basket'] = display_country['Avg_Basket'].apply(lambda x: f"{x:.2f} €")
                
                st.dataframe(
                    display_country,
                    width='stretch',
                    column_config={
                        "Country": "Pays",
                        "Orders": "Commandes",
                        "Revenue": "Chiffre d'affaires",
                        "Avg_Basket": "Panier moyen"
                    }
                )
        
        with tab2:
            st.markdown("## ⭐ Analyse des Avis Clients")
            
            if reviews_df is not None:
                
                # KPIs
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_rating = reviews_df['Rating'].mean()
                    st.metric("Note Moyenne", f"{avg_rating:.2f}/5")
                
                with col2:
                    total_reviews = len(reviews_df)
                    st.metric("Total Avis", total_reviews)
                
                with col3:
                    excellent_reviews = len(reviews_df[reviews_df['Rating'] >= 4])
                    excellent_pct = (excellent_reviews / total_reviews * 100) if total_reviews > 0 else 0
                    st.metric("Avis 4-5★", f"{excellent_pct:.1f}%")
                
                with col4:
                    negative_reviews = len(reviews_df[reviews_df['Rating'] <= 2])
                    st.metric("Avis 1-2★", negative_reviews, delta=None, delta_color="inverse")
                
                st.markdown("---")
                
                # Distribution des notes
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Distribution des Notes")
                    
                    rating_dist = reviews_df['Rating'].value_counts().sort_index()
                    
                    fig = px.bar(
                        x=rating_dist.index,
                        y=rating_dist.values,
                        labels={'x': 'Note (étoiles)', 'y': 'Nombre d\'avis'},
                        text=rating_dist.values,
                        color=rating_dist.index,
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_traces(textposition='outside')
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    st.markdown("### 📈 Évolution de la Note Moyenne")
                    
                    reviews_df['Month'] = reviews_df['Date'].dt.to_period('M').astype(str)
                    monthly_rating = reviews_df.groupby('Month')['Rating'].mean().reset_index()
                    
                    fig = px.line(
                        monthly_rating,
                        x='Month',
                        y='Rating',
                        markers=True,
                        title="Note moyenne par mois"
                    )
                    fig.update_traces(line_color='#F56400', line_width=3)
                    fig.update_layout(height=400, yaxis_range=[0, 5])
                    st.plotly_chart(fig, width='stretch')
                
                # Analyse de sentiment
                if positive_words and negative_words:
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 😊 Mots-clés Positifs")
                        
                        if positive_words:
                            top_positive = dict(positive_words.most_common(10))
                            
                            fig = px.bar(
                                x=list(top_positive.values()),
                                y=list(top_positive.keys()),
                                orientation='h',
                                text=list(top_positive.values()),
                                color=list(top_positive.values()),
                                color_continuous_scale='Greens'
                            )
                            fig.update_traces(textposition='outside')
                            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'}, showlegend=False)
                            st.plotly_chart(fig, width='stretch')
                        else:
                            st.info("Aucun mot-clé positif détecté")
                    
                    with col2:
                        st.markdown("### 😟 Mots-clés Négatifs")
                        
                        if negative_words:
                            top_negative = dict(negative_words.most_common(10))
                            
                            fig = px.bar(
                                x=list(top_negative.values()),
                                y=list(top_negative.keys()),
                                orientation='h',
                                text=list(top_negative.values()),
                                color=list(top_negative.values()),
                                color_continuous_scale='Reds'
                            )
                            fig.update_traces(textposition='outside')
                            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'}, showlegend=False)
                            st.plotly_chart(fig, width='stretch')
                        else:
                            st.success("✅ Aucun mot-clé négatif détecté !")
                
                # Nuage de mots
                if all_words:
                    st.markdown("---")
                    st.markdown("### ☁️ Nuage de Mots des Avis")
                    
                    top_words = dict(all_words.most_common(30))
                    
                    # Créer un graphique à bulles comme nuage de mots
                    words_df = pd.DataFrame({
                        'word': list(top_words.keys()),
                        'count': list(top_words.values())
                    })
                    
                    fig = px.scatter(
                        words_df,
                        x=np.random.rand(len(words_df)),
                        y=np.random.rand(len(words_df)),
                        size='count',
                        text='word',
                        color='count',
                        color_continuous_scale='Viridis',
                        size_max=60
                    )
                    fig.update_traces(textposition='middle center')
                    fig.update_layout(
                        height=400,
                        showlegend=False,
                        xaxis={'visible': False},
                        yaxis={'visible': False}
                    )
                    st.plotly_chart(fig, width='stretch')
                
                # Avis récents négatifs
                negative_reviews_df = reviews_df[reviews_df['Rating'] <= 2].sort_values('Date', ascending=False)
                
                if len(negative_reviews_df) > 0:
                    st.markdown("---")
                    st.markdown("### ⚠️ Avis Négatifs Récents (Action Requise)")
                    
                    for idx, row in negative_reviews_df.head(5).iterrows():
                        with st.expander(f"⭐{int(row['Rating'])} - {row['Reviewer']} - {row['Date'].strftime('%d/%m/%Y')}"):
                            if row['Review_Text']:
                                st.markdown(f"**Commentaire :** {row['Review_Text']}")
                            else:
                                st.markdown("*Pas de commentaire*")
                            
                            st.markdown(f"**Order ID :** {row['Order_ID']}")
            
            else:
                st.warning("⚠️ Importez le fichier reviews pour voir l'analyse des avis")
        
        with tab3:
            st.markdown("## 🛒 Comportement d'Achat")
            
            # Délais de livraison
            orders_with_delays = calculate_shipping_delays(orders_df)
            
            if orders_with_delays is not None and 'Shipping_Delay' in orders_with_delays.columns:
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_delay = orders_with_delays['Shipping_Delay'].mean()
                    st.metric("Délai Moyen Livraison", f"{avg_delay:.1f} jours")
                
                with col2:
                    median_delay = orders_with_delays['Shipping_Delay'].median()
                    st.metric("Délai Médian", f"{median_delay:.0f} jours")
                
                with col3:
                    max_delay = orders_with_delays['Shipping_Delay'].max()
                    st.metric("Délai Maximum", f"{max_delay:.0f} jours")
                
                st.markdown("---")
                
                # Distribution des délais
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📦 Distribution des Délais")
                    
                    fig = px.histogram(
                        orders_with_delays,
                        x='Shipping_Delay',
                        nbins=20,
                        title="Nombre de commandes par délai",
                        color_discrete_sequence=['#F56400']
                    )
                    fig.update_layout(
                        xaxis_title="Délai (jours)",
                        yaxis_title="Nombre de commandes",
                        height=400
                    )
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    st.markdown("### 🌍 Délai Moyen par Pays")
                    
                    if 'Country' in orders_with_delays.columns:
                        delay_by_country = orders_with_delays.groupby('Country')['Shipping_Delay'].mean().nlargest(10).reset_index()
                        
                        fig = px.bar(
                            delay_by_country,
                            x='Shipping_Delay',
                            y='Country',
                            orientation='h',
                            text='Shipping_Delay',
                            color='Shipping_Delay',
                            color_continuous_scale='Reds'
                        )
                        fig.update_traces(texttemplate='%{text:.1f}j', textposition='outside')
                        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig, width='stretch')
            
            # Saisonnalité
            if 'Date' in orders_df.columns:
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📅 Saisonnalité des Ventes (par mois)")
                    
                    orders_df['Month'] = orders_df['Date'].dt.month
                    monthly_orders = orders_df.groupby('Month').size().reset_index(name='Orders')
                    monthly_orders['Month_Name'] = monthly_orders['Month'].apply(
                        lambda x: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 
                                  'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'][x-1]
                    )
                    
                    fig = px.bar(
                        monthly_orders,
                        x='Month_Name',
                        y='Orders',
                        text='Orders',
                        color='Orders',
                        color_continuous_scale='Blues'
                    )
                    fig.update_traces(textposition='outside')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    st.markdown("### 📊 Ventes par Jour de la Semaine")
                    
                    orders_df['DayOfWeek'] = orders_df['Date'].dt.day_name()
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_names_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
                    
                    daily_orders = orders_df.groupby('DayOfWeek').size().reindex(day_order).reset_index(name='Orders')
                    daily_orders['Day'] = day_names_fr
                    
                    fig = px.bar(
                        daily_orders,
                        x='Day',
                        y='Orders',
                        text='Orders',
                        color='Orders',
                        color_continuous_scale='Greens'
                    )
                    fig.update_traces(textposition='outside')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                
                # Meilleur jour
                best_day_idx = daily_orders['Orders'].idxmax()
                best_day = daily_orders.loc[best_day_idx, 'Day']
                best_day_orders = daily_orders['Orders'].max()
                
                st.markdown(f"""
                <div class="insight-box">
                💡 <strong>Insight :</strong> Le <strong>{best_day}</strong> est votre meilleur jour avec <strong>{best_day_orders}</strong> commandes en moyenne !
                <br>→ Programmez vos nouveaux produits et promotions ce jour-là.
                </div>
                """, unsafe_allow_html=True)
            
            # Panier moyen par pays
            if country_analysis is not None:
                st.markdown("---")
                st.markdown("### 💰 Panier Moyen par Pays (Top 10)")
                
                top_basket = country_analysis.nlargest(10, 'Avg_Basket')
                
                fig = px.bar(
                    top_basket,
                    x='Avg_Basket',
                    y='Country',
                    orientation='h',
                    text='Avg_Basket',
                    color='Avg_Basket',
                    color_continuous_scale='Oranges'
                )
                fig.update_traces(texttemplate='%{text:.2f}€', textposition='outside')
                fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, width='stretch')
        
        with tab4:
            st.markdown("## 🔄 Fidélisation & Lifetime Value")
            
            # Vérifier abonnement Insights
            has_insights = has_insights_subscription(customer_id)
            
            if not has_insights:
                # MODE GRATUIT : TEASER BLURRED
                st.info("""
                💎 **Fonctionnalités Premium disponibles avec Insights 9€/mois :**
                - 📊 Taux de clients récurrents & LTV moyen
                - 👥 Distribution nouveaux vs récurrents  
                - ⚠️ Clients à risque de churn (90+ jours inactifs)
                - 🏆 Top 10 clients VIP par CA
                - ⏱️ Délai moyen entre deux achats
                - 🎯 Actions de réactivation personnalisées
                """)
                
                if customer_analysis is not None:
                    # Calculer les métriques pour le teaser
                    repeat_customers = (customer_analysis['Num_Orders'] > 1).sum()
                    repeat_rate = (repeat_customers / len(customer_analysis) * 100) if len(customer_analysis) > 0 else 0
                    avg_ltv = customer_analysis['LTV'].mean()
                    churn_count = customer_analysis['Churn_Risk'].sum()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📊 Taux Clients Récurrents (preview)")
                        st.markdown(f"""
                        <div style='filter: blur(8px); pointer-events: none; user-select: none;'>
                            <h1 style='text-align: center; font-size: 4rem; color: #28a745;'>{repeat_rate:.1f}%</h1>
                            <p style='text-align: center;'>de vos clients reviennent</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("### 💰 LTV Moyen (preview)")
                        st.markdown(f"""
                        <div style='filter: blur(8px); pointer-events: none; user-select: none;'>
                            <h1 style='text-align: center; font-size: 4rem; color: #F56400;'>{avg_ltv:.0f}€</h1>
                            <p style='text-align: center;'>Lifetime Value moyenne</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("### 🏆 Top Clients VIP (preview)")
                    st.markdown("""
                    <div style='filter: blur(5px); pointer-events: none; user-select: none;'>
                        <table style='width: 100%; border-collapse: collapse;'>
                            <tr style='background: #f0f2f6;'>
                                <th style='padding: 10px; text-align: left;'>Client</th>
                                <th style='padding: 10px; text-align: right;'>CA Total</th>
                                <th style='padding: 10px; text-align: right;'>Achats</th>
                            </tr>
                            <tr>
                                <td style='padding: 10px;'>Client #1</td>
                                <td style='padding: 10px; text-align: right;'>250€</td>
                                <td style='padding: 10px; text-align: right;'>8</td>
                            </tr>
                            <tr style='background: #f0f2f6;'>
                                <td style='padding: 10px;'>Client #2</td>
                                <td style='padding: 10px; text-align: right;'>195€</td>
                                <td style='padding: 10px; text-align: right;'>6</td>
                            </tr>
                            <tr>
                                <td style='padding: 10px;'>Client #3</td>
                                <td style='padding: 10px; text-align: right;'>180€</td>
                                <td style='padding: 10px; text-align: right;'>5</td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if churn_count > 0:
                        st.markdown("---")
                        st.markdown("### ⚠️ Clients à Risque (preview)")
                        st.markdown(f"""
                        <div style='filter: blur(5px); pointer-events: none; user-select: none;'>
                            <div class="warning-box">
                                <strong>{churn_count} clients</strong> n'ont pas commandé depuis 90+ jours
                                <br><br>
                                Actions recommandées :
                                <ul>
                                    <li>Email de réactivation avec -15%</li>
                                    <li>Offre personnalisée</li>
                                    <li>Sondage feedback</li>
                                </ul>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                show_insights_upgrade_cta()
            
            else:
                # MODE PREMIUM : TOUT DÉBLOQUÉ
                st.success("💎 **Insights Premium activé**")
                
                if customer_analysis is not None:
                    
                    # KPIs
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        repeat_customers = (customer_analysis['Num_Orders'] > 1).sum()
                        repeat_rate = (repeat_customers / len(customer_analysis) * 100) if len(customer_analysis) > 0 else 0
                        st.metric("Taux Clients Récurrents", f"{repeat_rate:.1f}%")
                    
                    with col2:
                        avg_ltv = customer_analysis['LTV'].mean()
                        st.metric("LTV Moyen", f"{avg_ltv:.2f} €")
                    
                    with col3:
                        avg_orders = customer_analysis['Num_Orders'].mean()
                        st.metric("Commandes / Client", f"{avg_orders:.1f}")
                    
                    with col4:
                        churn_customers = customer_analysis['Churn_Risk'].sum()
                        st.metric("Clients à Risque", churn_customers, delta=None, delta_color="inverse")
                    
                    st.markdown("---")
                    
                    # Distribution des clients
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 👥 Nouveaux vs Récurrents")
                        
                        customer_types = pd.DataFrame({
                            'Type': ['Nouveaux (1 achat)', 'Récurrents (2+ achats)'],
                            'Count': [
                                (customer_analysis['Num_Orders'] == 1).sum(),
                                (customer_analysis['Num_Orders'] > 1).sum()
                            ]
                        })
                        
                        fig = px.pie(
                            customer_types,
                            values='Count',
                            names='Type',
                            color_discrete_sequence=['#ffc107', '#28a745']
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, width='stretch')
                    
                    with col2:
                        st.markdown("### 📊 Distribution du Nombre d'Achats")
                        
                        order_dist = customer_analysis['Num_Orders'].value_counts().sort_index().head(10)
                        
                        fig = px.bar(
                            x=order_dist.index,
                            y=order_dist.values,
                            labels={'x': 'Nombre d\'achats', 'y': 'Nombre de clients'},
                            text=order_dist.values,
                            color=order_dist.values,
                            color_continuous_scale='Blues'
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(height=400, showlegend=False)
                        st.plotly_chart(fig, width='stretch')
                    
                    # Lifetime Value
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 💎 Distribution de la LTV")
                        
                        fig = px.histogram(
                            customer_analysis,
                            x='LTV',
                            nbins=30,
                            title="Répartition des clients par LTV",
                            color_discrete_sequence=['#F56400']
                        )
                        fig.update_layout(
                            xaxis_title="Lifetime Value (€)",
                            yaxis_title="Nombre de clients",
                            height=400
                        )
                        st.plotly_chart(fig, width='stretch')
                    
                    with col2:
                        st.markdown("### ⏱️ Délai Entre Deux Achats")
                        
                        repeat_customers_df = customer_analysis[customer_analysis['Num_Orders'] > 1]
                        
                        if len(repeat_customers_df) > 0:
                            fig = px.histogram(
                                repeat_customers_df,
                                x='Days_Between_Orders',
                                nbins=20,
                                title="Temps moyen entre 2 commandes",
                                color_discrete_sequence=['#007bff']
                            )
                            fig.update_layout(
                                xaxis_title="Jours entre achats",
                                yaxis_title="Nombre de clients",
                                height=400
                            )
                            st.plotly_chart(fig, width='stretch')
                            
                            avg_days_between = repeat_customers_df['Days_Between_Orders'].mean()
                            
                            st.markdown(f"""
                            <div class="insight-box">
                            💡 <strong>Insight :</strong> Vos clients récurrents rachètent en moyenne tous les <strong>{avg_days_between:.0f} jours</strong>.
                            <br>→ Programmez vos relances marketing à ce rythme.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Pas encore assez de clients récurrents pour cette analyse")
                    
                    # Top clients VIP
                    st.markdown("---")
                    st.markdown("### 🏆 Top 10 Clients VIP (par CA)")
                    
                    top_vip = customer_analysis.nlargest(10, 'LTV')[['Buyer', 'Num_Orders', 'LTV']]
                    
                    # Anonymiser les noms
                    top_vip['Buyer_Display'] = ['Client #' + str(i+1) for i in range(len(top_vip))]
                    
                    fig = px.bar(
                        top_vip,
                        x='LTV',
                        y='Buyer_Display',
                        orientation='h',
                        text='LTV',
                        color='Num_Orders',
                        color_continuous_scale='Greens',
                        hover_data={'Num_Orders': True}
                    )
                    fig.update_traces(texttemplate='%{text:.2f}€', textposition='outside')
                    fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, width='stretch')
                    
                    # Clients à risque
                    churn_risk_df = customer_analysis[customer_analysis['Churn_Risk'] == True].nlargest(10, 'LTV')
                    
                    if len(churn_risk_df) > 0:
                        st.markdown("---")
                        st.markdown("### ⚠️ Clients à Risque de Churn (pas d'achat depuis 90+ jours)")
                        
                        st.markdown(f"""
                        <div class="warning-box">
                        <strong>{len(churn_risk_df)} clients</strong> n'ont pas commandé depuis plus de 90 jours.
                        <br><br>
                        <strong>Action recommandée :</strong>
                        <ul>
                        <li>Envoyez un email de réactivation avec code promo -15%</li>
                        <li>Proposez une offre personnalisée basée sur leurs achats précédents</li>
                        <li>Demandez un feedback pour comprendre pourquoi ils sont partis</li>
                        </ul>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        churn_risk_df['Buyer_Display'] = ['Client #' + str(i+1) for i in range(len(churn_risk_df))]
                        
                        display_churn = churn_risk_df[['Buyer_Display', 'Num_Orders', 'LTV', 'Days_Since_Last']].copy()
                        display_churn.columns = ['Client', 'Achats', 'LTV (€)', 'Jours depuis dernier achat']
                        
                        st.dataframe(display_churn, width='stretch')
        
        with tab5:
            st.markdown("## 🔧 Recommandations Marketing Personnalisées")
            
            # Vérifier abonnement Insights
            has_insights = has_insights_subscription(customer_id)
            
            recommendations = []
            
            # Recommandation 1 : Géographie
            if country_analysis is not None:
                top_country = country_analysis.iloc[0]
                country_name = top_country['Country']
                country_revenue = top_country['Revenue']
                country_pct = (country_revenue / country_analysis['Revenue'].sum() * 100)
                
                recommendations.append({
                    'priority': '🔴 HAUTE',
                    'title': f'Capitaliser sur votre marché principal : {country_name}',
                    'detail': f"{country_name} représente {country_pct:.1f}% de votre CA ({country_revenue:.2f}€)",
                    'actions': [
                        f"Traduire vos listings en langue locale ({country_name})",
                        f"Adapter vos descriptions aux préférences culturelles de {country_name}",
                        f"Proposer des options de livraison premium pour {country_name}",
                        f"Créer une collection spéciale pour le marché de {country_name}",
                        f"Utiliser Etsy Ads ciblées sur {country_name}"
                    ]
                })
            
            # Recommandation 2 : Reviews
            if reviews_df is not None:
                avg_rating = reviews_df['Rating'].mean()
                negative_count = len(reviews_df[reviews_df['Rating'] <= 2])
                
                if negative_count > 0:
                    recommendations.append({
                        'priority': '🔴 HAUTE',
                        'title': 'Traiter les Avis Négatifs en Priorité',
                        'detail': f"Vous avez {negative_count} avis négatifs (1-2★) qui impactent votre réputation.",
                        'actions': [
                            "Répondre personnellement à chaque avis négatif sous 24h",
                            "Proposer une solution (remboursement, remplacement, geste commercial)",
                            "Analyser les causes récurrentes (qualité, délai, taille, etc.)",
                            "Mettre en place des actions correctives immédiates",
                            "Contacter directement les clients mécontents par message privé"
                        ]
                    })
                
                if positive_words:
                    top_positive = positive_words.most_common(3)
                    positive_terms = ", ".join([f"'{word}'" for word, count in top_positive])
                    
                    recommendations.append({
                        'priority': '🟢 OPPORTUNITÉ',
                        'title': 'Exploiter vos Points Forts dans le Marketing',
                        'detail': f"Vos clients apprécient particulièrement : {positive_terms}",
                        'actions': [
                            "Mettre en avant ces qualités dans vos descriptions produits",
                            "Créer des badges/icônes mettant en valeur ces atouts",
                            "Utiliser ces termes dans vos titres SEO",
                            "Partager ces témoignages positifs sur vos réseaux sociaux",
                            "Inclure ces points forts dans vos annonces Etsy Ads"
                        ]
                    })
                
                if negative_words:
                    top_negative = negative_words.most_common(3)
                    negative_terms = ", ".join([f"'{word}'" for word, count in top_negative])
                    
                    recommendations.append({
                        'priority': '🟡 MOYENNE',
                        'title': 'Résoudre les Problèmes Récurrents',
                        'detail': f"Mots négatifs détectés : {negative_terms}",
                        'actions': [
                            "Identifier la cause racine de ces problèmes",
                            "Améliorer la description produit si lié à des attentes erronées",
                            "Renforcer le contrôle qualité avant expédition",
                            "Ajuster les délais de livraison affichés si nécessaire",
                            "Améliorer l'emballage si problèmes de casse/dommages"
                        ]
                    })
            
            # Recommandation 3 : Fidélisation
            if customer_analysis is not None:
                repeat_rate = (customer_analysis['Num_Orders'] > 1).sum() / len(customer_analysis) * 100
                
                if repeat_rate < 25:
                    recommendations.append({
                        'priority': '🔴 HAUTE',
                        'title': 'Améliorer votre Taux de Fidélisation',
                        'detail': f"Seulement {repeat_rate:.1f}% de vos clients reviennent pour un 2e achat.",
                        'actions': [
                            "Créer un programme de fidélité (code promo -10% pour 2e achat)",
                            "Envoyer un email de remerciement 7 jours après livraison",
                            "Proposer des offres exclusives aux anciens clients",
                            "Créer une newsletter mensuelle avec nouveautés",
                            "Inclure un coupon de réduction dans chaque colis"
                        ]
                    })
                else:
                    recommendations.append({
                        'priority': '🟢 INFO',
                        'title': 'Excellent Taux de Fidélisation !',
                        'detail': f"{repeat_rate:.1f}% de vos clients reviennent - c'est excellent !",
                        'actions': [
                            "Continuer vos efforts de fidélisation actuels",
                            "Identifier ce qui fonctionne bien et le dupliquer",
                            "Créer un programme VIP pour vos meilleurs clients",
                            "Demander des témoignages à vos clients récurrents"
                        ]
                    })
                
                # Clients à risque
                churn_count = customer_analysis['Churn_Risk'].sum()
                if churn_count > 0:
                    recommendations.append({
                        'priority': '🟡 MOYENNE',
                        'title': f'Réactiver {churn_count} Clients Inactifs',
                        'detail': f"{churn_count} clients n'ont pas commandé depuis 90+ jours",
                        'actions': [
                            "Campagne email de réactivation avec offre spéciale",
                            "Code promo personnalisé -20% valable 15 jours",
                            "Sondage pour comprendre pourquoi ils sont partis",
                            "Présenter les nouveautés depuis leur dernier achat",
                            "Offrir la livraison gratuite pour leur retour"
                        ]
                    })
            
            # Recommandation 4 : Comportement d'achat
            if 'Date' in orders_df.columns:
                orders_df_temp = orders_df.copy()
                orders_df_temp['DayOfWeek'] = orders_df_temp['Date'].dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
                
                daily_sales = orders_df_temp.groupby('DayOfWeek').size().reindex(day_order)
                best_day_idx = daily_sales.idxmax()
                best_day_name = day_names_fr[day_order.index(best_day_idx)]
                
                recommendations.append({
                    'priority': '🟢 OPPORTUNITÉ',
                    'title': f'Timing Optimal : {best_day_name}',
                    'detail': f"Le {best_day_name} est votre meilleur jour de ventes",
                    'actions': [
                        f"Publier vos nouveaux produits le {best_day_name}",
                        f"Programmer vos promotions le {best_day_name}",
                        f"Renouveler vos listings anciens le {best_day_name}",
                        f"Lancer vos campagnes Etsy Ads le {best_day_name}",
                        "Analyser pourquoi ce jour performe mieux (comportement d'achat)"
                    ]
                })
            
            # MODE GRATUIT vs PAYANT
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
                        
                        st.markdown("---")
                        st.markdown("**📋 Actions recommandées :**")
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
                
                st.markdown("### 🎯 Vos Actions Prioritaires")
                
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"{rec['priority']} - {rec['title']}", expanded=(i==1)):
                        st.markdown(f"**{rec['detail']}**")
                        
                        st.markdown("---")
                        st.markdown("**📋 Actions à prendre :**")
                        for action in rec['actions']:
                            st.markdown(f"- {action}")
                
                # Stratégie globale
                st.markdown("---")
                st.markdown("### 🚀 Stratégie Marketing Globale Recommandée")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div class="success-box">
                    <strong>🎯 Court Terme (30 jours)</strong>
                    <ol>
                    <li>Répondre à tous les avis négatifs</li>
                    <li>Lancer campagne de réactivation clients inactifs</li>
                    <li>Optimiser listings pour marché principal</li>
                    <li>Créer code promo fidélité</li>
                    </ol>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div class="insight-box">
                    <strong>🚀 Long Terme (3-6 mois)</strong>
                    <ol>
                    <li>Développer programme de fidélité structuré</li>
                    <li>Expansion géographique ciblée</li>
                    <li>Amélioration continue qualité produits</li>
                    <li>Construction d'une communauté de clients fidèles</li>
                    </ol>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Checklist
                st.markdown("---")
                st.markdown("### ✅ Checklist d'Actions Immédiates")
                
                checklist = [
                    "J'ai répondu à tous mes avis négatifs",
                    "J'ai créé un code promo pour mes clients récurrents",
                    "J'ai envoyé un email de réactivation aux clients inactifs",
                    "J'ai optimisé mes listings pour mon marché principal",
                    "J'ai analysé les causes de mes avis négatifs",
                    "J'ai mis en avant mes points forts dans mes descriptions",
                    "J'ai programmé mes prochaines publications aux bons jours",
                    "J'ai créé une newsletter pour rester en contact",
                    "J'ai mis en place un suivi des clients VIP",
                    "J'ai un plan d'action pour réduire le churn"
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
    <p><strong>Etsy Customer Intelligence</strong> - Version 1.0</p>
    <p>👥 Comprenez vos clients, analysez leurs avis, et fidélisez-les</p>
    <p style='font-size: 0.9em;'>Questions ? contact@etsy-customer-intelligence.com</p>
</div>
""", unsafe_allow_html=True)