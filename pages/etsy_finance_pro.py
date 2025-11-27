import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
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
from auth.access_manager import check_access, has_access_to_dashboard, show_upgrade_message
from data_collection.collector import show_data_opt_in

# Configuration de la page
st.set_page_config(
    page_title="Etsy Analytics Pro - Bijoux",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== NOUVEAU : VÉRIFICATION D'ACCÈS ==========
user_info = check_access()

# Récupérer le customer_id (UUID depuis Supabase)
customer_id = user_info.get('id')

# Vérifier l'accès à ce dashboard spécifique
if not has_access_to_dashboard(customer_id, 'finance_pro'):
    show_upgrade_message('finance_pro', customer_id)
    st.stop()
# ====================================================

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
    </style>
""", unsafe_allow_html=True)

# Fonction pour charger les données
@st.cache_data
def load_data(uploaded_file):
    """Charge et prépare les données depuis un CSV Etsy"""
    try:
        # Essayer de détecter l'encodage
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        # Mapping complet des colonnes Etsy vers nos colonnes standardisées
        column_mapping = {
            # Dates (format Etsy réel - anglais)
            'Sale Date': 'Date',
            'Order Date': 'Date',
            'date': 'Date',
            'order_date': 'Date',
            'Date Paid': 'Date',
            
            # Dates (format Etsy français)
            'Date de vente': 'Date',
            'Date de commande': 'Date',
            
            # Produits (format Etsy réel - anglais)
            'Item Name': 'Product',
            'item_name': 'Product',
            'Product': 'Product',
            'product': 'Product',
            'Title': 'Product',
            
            # Prix (format Etsy réel - anglais)
            'Item Price': 'Price',
            'item_price': 'Price',
            'Price': 'Price',
            'price': 'Price',
            
            # Prix (format Etsy français)
            'Valeur de la commande': 'Price',
            'Total de la commande': 'Price',
            
            # Quantité (anglais et français)
            'Quantity': 'Quantity',
            'quantity': 'Quantity',
            "Nombre d'articles": 'Quantity',
            
            # Coûts (ajouté manuellement par l'utilisateur)
            'Cost': 'Cost',
            'cost': 'Cost',
            'Cout': 'Cost',
            'Coût': 'Cost',
            
            # Frais de livraison (format Etsy - anglais)
            'Shipping Price': 'Shipping',
            'shipping_price': 'Shipping',
            'Order Shipping': 'Shipping',
            
            # Frais de livraison (format Etsy - français)
            'Frais de livraison': 'Shipping',
            
            # Catégorie (ajouté manuellement)
            'Category': 'Category',
            'category': 'Category',
            'Catégorie': 'Category',
            'Categorie': 'Category'
        }
        
        # Renommer les colonnes avec priorité (éviter les doublons)
        columns_to_rename = {}
        target_columns_used = set()
        
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                if new_name not in target_columns_used:
                    columns_to_rename[old_name] = new_name
                    target_columns_used.add(new_name)
        
        # Appliquer le renommage
        if columns_to_rename:
            df = df.rename(columns=columns_to_rename)
            st.info(f"📋 Colonnes mappées : {', '.join([f'{k}→{v}' for k, v in columns_to_rename.items()])}")
        
        # Vérifier les colonnes essentielles
        required_columns = ['Date', 'Product', 'Price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Colonnes obligatoires manquantes : {', '.join(missing_columns)}")
            st.info("""
            💡 **Format CSV attendu (minimum requis):**
            - **Date** : 'Sale Date', 'Order Date', ou 'Date'
            - **Produit** : 'Item Name', 'Product', ou 'Title'  
            - **Prix** : 'Item Price' ou 'Price'
            
            **Colonnes optionnelles mais recommandées:**
            - 'Quantity' (défaut: 1)
            - 'Cost' (coûts matières - défaut: 0)
            - 'Category' (catégorie produit)
            """)
            return None
        
        # Conversion des colonnes de dates
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
            invalid_dates = df['Date'].isna().sum()
            if invalid_dates > 0:
                st.warning(f"⚠️ {invalid_dates} lignes avec dates invalides ont été ignorées")
            df = df.dropna(subset=['Date'])
        
        # Nettoyage des colonnes numériques
        numeric_columns = ['Price', 'Quantity', 'Cost', 'Shipping']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    else:
                        df[col] = (df[col].fillna('0')
                                  .astype(str)
                                  .str.replace('€', '', regex=False)
                                  .str.replace('$', '', regex=False)
                                  .str.replace('USD', '', regex=False)
                                  .str.replace('EUR', '', regex=False)
                                  .str.replace(' ', '', regex=False)
                                  .str.replace(',', '.', regex=False)
                                  .str.strip())
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                except Exception as e:
                    st.warning(f"⚠️ Problème de nettoyage pour la colonne {col}: {e}")
                    df[col] = 0
        
        # Ajouter Quantity si manquant
        if 'Quantity' not in df.columns:
            df['Quantity'] = 1
            st.info("ℹ️ Colonne 'Quantity' absente - Quantité fixée à 1 par défaut")
        
        # Ajouter Cost si manquant
        if 'Cost' not in df.columns:
            df['Cost'] = 0
            st.warning("""
            ⚠️ **Colonne 'Cost' non trouvée** 
            
            Les marges sont calculées sans coûts matières (Cost = 0€).
            
            **Pour ajouter vos coûts :**
            1. Utilisez le module "Gestion des coûts" dans la barre latérale
            2. Ou ajoutez une colonne 'Cost' à votre CSV
            """)
        
        # Ajouter Category si manquant
        if 'Category' not in df.columns:
            df['Category'] = 'Non catégorisé'
            st.info("ℹ️ Colonne 'Category' absente - Tous les produits classés en 'Non catégorisé'")
        
        # Supprimer les lignes avec prix invalides
        invalid_prices = (df['Price'].isna()) | (df['Price'] <= 0)
        if invalid_prices.sum() > 0:
            st.warning(f"⚠️ {invalid_prices.sum()} lignes avec prix invalides ont été ignorées")
        df = df[~invalid_prices]
        
        # Vérifier qu'il reste des données
        if len(df) == 0:
            st.error("❌ Aucune donnée valide trouvée après nettoyage !")
            return None
        
        # Afficher un résumé détaillé
        st.success(f"""
        ✅ **{len(df)} ventes chargées avec succès !**
        
        📊 Période : {df['Date'].min().strftime('%d/%m/%Y')} → {df['Date'].max().strftime('%d/%m/%Y')}
        💰 CA Total : {df['Price'].sum():.2f} €
        """)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        st.info("💡 Vérifiez que votre fichier est bien au format CSV et qu'il contient les colonnes nécessaires.")
        return None

# Fonction pour calculer les KPIs - VERSION AMÉLIORÉE avec frais Etsy détaillés
def calculate_kpis(df, etsy_fees_config=None):
    """Calcule tous les KPIs essentiels avec frais Etsy réalistes"""
    kpis = {}
    
    # CA total
    kpis['ca_total'] = df['Price'].sum() if 'Price' in df.columns else 0
    
    # Nombre de ventes
    kpis['nb_ventes'] = len(df)
    
    # Panier moyen
    kpis['panier_moyen'] = kpis['ca_total'] / kpis['nb_ventes'] if kpis['nb_ventes'] > 0 else 0
    
    # CALCUL DES FRAIS ETSY - NOUVELLE LOGIQUE
    if etsy_fees_config and etsy_fees_config.get('statement_file'):
        # MODE 1 : Relevé mensuel (frais exacts)
        try:
            statement_df = pd.read_csv(etsy_fees_config['statement_file'], encoding='latin1')
            
            # Nettoyer et extraire les frais par type
            def clean_fees(series):
                return abs(series.str.replace(',', '.').str.replace(' €', '').str.replace('', '').str.strip().astype(float).sum())
            
            frais_transaction = clean_fees(statement_df[statement_df['Type'] == 'Transaction']['Frais Et Taxes'])
            frais_marketing = clean_fees(statement_df[statement_df['Type'] == 'Marketing']['Frais Et Taxes'])
            frais_listing = clean_fees(statement_df[statement_df['Type'] == 'Fiche produit']['Frais Et Taxes'])
            frais_vat = clean_fees(statement_df[statement_df['Type'] == 'VAT']['Frais Et Taxes'])
            frais_tva = clean_fees(statement_df[statement_df['Type'] == 'TVA']['Frais Et Taxes'])
            frais_abonnement = clean_fees(statement_df[statement_df['Type'] == 'Abonnement']['Frais Et Taxes'])
            
            kpis['frais_etsy_detail'] = {
                'Transaction (6,5%)': frais_transaction,
                'Marketing (Ads)': frais_marketing,
                'Mise en vente (0,20€)': frais_listing,
                'Traitement paiement': frais_vat,
                'TVA (20%)': frais_tva,
                'Abonnement': frais_abonnement
            }
            
            kpis['frais_etsy'] = sum(kpis['frais_etsy_detail'].values())
            kpis['fees_source'] = "Relevé mensuel (frais réels)"
            
        except Exception as e:
            # En cas d'erreur, retomber sur l'estimation
            kpis['frais_etsy'] = kpis['ca_total'] * 0.12
            kpis['frais_etsy_detail'] = {}
            kpis['fees_source'] = f"Estimation (erreur)"
    
    elif etsy_fees_config and etsy_fees_config.get('method') == "Configurateur détaillé (recommandé)":
        # MODE 2 : Configurateur détaillé
        ca = kpis['ca_total']
        nb = kpis['nb_ventes']
        
        # Frais de base
        frais_transaction = ca * 0.065
        frais_listing = nb * 0.20
        frais_payment = ca * 0.04 + nb * 0.30
        
        # Frais optionnels
        frais_offsite = ca * etsy_fees_config.get('offsite_ads_rate', 0) if etsy_fees_config.get('use_offsite_ads') else 0
        frais_etsy_ads = etsy_fees_config.get('etsy_ads_budget', 0)
        frais_plus = etsy_fees_config.get('etsy_plus_fee', 0)
        
        # TVA (20% sur tous les frais hors Etsy Ads qui a déjà la TVA)
        total_before_vat = frais_transaction + frais_listing + frais_payment + frais_offsite + frais_plus
        frais_tva = total_before_vat * 0.20
        
        kpis['frais_etsy_detail'] = {
            'Transaction (6,5%)': frais_transaction,
            'Mise en vente (0,20€)': frais_listing,
            'Traitement paiement': frais_payment,
            'Offsite Ads': frais_offsite,
            'Etsy Ads': frais_etsy_ads,
            'Abonnement': frais_plus,
            'TVA (20%)': frais_tva
        }
        
        kpis['frais_etsy'] = sum(kpis['frais_etsy_detail'].values())
        kpis['fees_source'] = "Configurateur détaillé"
    
    else:
        # MODE 3 : Estimation standard (rapide)
        ca = kpis['ca_total']
        nb = kpis['nb_ventes']
        
        frais_transaction = ca * 0.065
        frais_listing = nb * 0.20
        frais_payment = ca * 0.04 + nb * 0.30
        
        total_before_vat = frais_transaction + frais_listing + frais_payment
        frais_tva = total_before_vat * 0.20
        
        kpis['frais_etsy_detail'] = {
            'Transaction (6,5%)': frais_transaction,
            'Mise en vente (0,20€)': frais_listing,
            'Traitement paiement': frais_payment,
            'TVA (20%)': frais_tva
        }
        
        kpis['frais_etsy'] = total_before_vat + frais_tva
        kpis['fees_source'] = "Estimation standard (~12%)"
    
    # Coûts matières (si fournis)
    if 'Cost' in df.columns:
        kpis['couts_matieres'] = df['Cost'].sum()
    else:
        kpis['couts_matieres'] = 0
    
    # Marge brute
    kpis['marge_brute'] = kpis['ca_total'] - kpis['frais_etsy'] - kpis['couts_matieres']
    kpis['taux_marge'] = (kpis['marge_brute'] / kpis['ca_total'] * 100) if kpis['ca_total'] > 0 else 0
    
    return kpis

# Fonction pour l'analyse produits
def analyze_products(df):
    """Analyse avancée des produits"""
    if 'Product' not in df.columns:
        return None
    
    # Construction de l'agrégation dynamique
    agg_dict = {
        'Price': ['sum', 'count', 'mean']
    }
    
    # Ajouter Cost seulement s'il existe
    if 'Cost' in df.columns:
        agg_dict['Cost'] = 'sum'
    
    product_analysis = df.groupby('Product').agg(agg_dict).reset_index()
    
    # Renommer les colonnes proprement
    if 'Cost' in df.columns:
        product_analysis.columns = ['Product', 'CA', 'Ventes', 'Prix_moyen', 'Cout_total']
    else:
        product_analysis.columns = ['Product', 'CA', 'Ventes', 'Prix_moyen']
        product_analysis['Cout_total'] = 0  # Ajouter colonne Cost à 0 si absente
    
    # Calculs de marges
    product_analysis['Marge'] = product_analysis['CA'] - product_analysis['Cout_total']
    product_analysis['Taux_marge'] = (product_analysis['Marge'] / product_analysis['CA'] * 100).round(2)
    
    # Convertir en types compatibles
    product_analysis['Ventes'] = product_analysis['Ventes'].astype(int)
    
    return product_analysis.sort_values('CA', ascending=False)

# Fonction pour générer le PDF
def generate_pdf_report(kpis, df, product_analysis):
    """Génère un rapport PDF avec les principales métriques"""
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
    story.append(Paragraph("Rapport Etsy Analytics Pro", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date du rapport
    date_text = f"Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    story.append(Paragraph(date_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # KPIs principaux
    story.append(Paragraph("Indicateurs Financiers", styles['Heading2']))
    kpi_data = [
        ['Indicateur', 'Valeur'],
        ['Chiffre d\'affaires', f"{kpis['ca_total']:.2f} EUR"],
        ['Nombre de ventes', str(kpis['nb_ventes'])],
        ['Panier moyen', f"{kpis['panier_moyen']:.2f} EUR"],
        ['Frais Etsy', f"{kpis['frais_etsy']:.2f} EUR"],
        ['Coûts matières', f"{kpis['couts_matieres']:.2f} EUR"],
        ['Marge brute', f"{kpis['marge_brute']:.2f} EUR"],
        ['Taux de marge', f"{kpis['taux_marge']:.1f} %"]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[3*inch, 2*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F56400')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Top produits
    if product_analysis is not None and len(product_analysis) > 0:
        story.append(Paragraph("Top 5 Produits par CA", styles['Heading2']))
        top_products = product_analysis.head(5)
        product_data = [['Produit', 'CA', 'Ventes', 'Marge']]
        for _, row in top_products.iterrows():
            product_data.append([
                row['Product'][:30],
                f"{row['CA']:.2f} EUR",
                str(int(row['Ventes'])),
                f"{row['Marge']:.2f} EUR"
            ])
        
        product_table = Table(product_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1.5*inch])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F56400')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(product_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# En-tête de l'application
st.markdown('<p class="main-header">💎 Etsy Analytics Pro - Bijoux Fantaisie</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x100/F56400/FFFFFF?text=Etsy+Analytics", width=200)
    st.markdown("---")
    
    st.markdown("### 📤 Import des données")
    uploaded_file = st.file_uploader(
        "Importez votre export CSV Etsy (EtsySoldOrderItems.csv)",
        type=['csv'],
        help="Exportez vos données depuis Etsy > Boutique Manager > Statistiques"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Paramètres")
    
    # Filtres de période
    period = st.selectbox(
        "Période d'analyse",
        ["Tout", "7 derniers jours", "30 derniers jours", "90 derniers jours", "1 an"],
        index=0  # "Tout" par défaut
    )
    
    st.markdown("---")
    
    # MODULE GESTION DES COÛTS
    st.markdown("### 💰 Gestion des coûts")
    
    cost_method = st.radio(
        "Comment voulez-vous gérer les coûts ?",
        ["Sans coûts (Cost = 0)", "Coût moyen par produit", "Upload CSV avec coûts détaillés"]
    )
    
    if cost_method == "Coût moyen par produit":
        avg_cost = st.number_input("Coût moyen par produit (€)", min_value=0.0, value=5.0, step=0.5)
        st.info("💡 Ce coût sera appliqué à tous les produits")
    
    elif cost_method == "Upload CSV avec coûts détaillés":
        st.markdown("""
        **Format CSV attendu :**
        - Colonne 1: `Product` (nom exact du produit)
        - Colonne 2: `Cost` (coût unitaire en €)
        """)
        
        cost_file = st.file_uploader(
            "Fichier CSV avec coûts",
            type=['csv'],
            key='cost_file'
        )
        
        # Template de coûts
        if st.button("📥 Télécharger template coûts"):
            template_costs = pd.DataFrame({
                'Product': ['Bracelet exemple 1', 'Bracelet exemple 2'],
                'Cost': [5.00, 7.50]
            })
            st.download_button(
                label="⬇️ Télécharger",
                data=template_costs.to_csv(index=False).encode('utf-8'),
                file_name='template_couts_produits.csv',
                mime='text/csv'
            )
    
    st.markdown("---")
    
    # MODULE GESTION DES FRAIS ETSY - NOUVEAU
    st.markdown("### 💳 Gestion des frais Etsy")
    
    fees_method = st.radio(
        "Comment calculer les frais Etsy ?",
        ["Estimation standard (rapide)", "Configurateur détaillé (recommandé)", "Relevé mensuel Etsy (précis)"],
        help="Plus vous êtes précis, plus vos marges seront justes"
    )
    
    # Initialiser les variables de frais
    etsy_fees_config = {
        'method': fees_method,
        'use_offsite_ads': False,
        'offsite_ads_rate': 0.15,
        'use_etsy_ads': False,
        'etsy_ads_budget': 0.0,
        'has_etsy_plus': False,
        'etsy_plus_fee': 0.0,
        'statement_file': None
    }
    
    if fees_method == "Estimation standard (rapide)":
        st.info("""
        ℹ️ **Estimation simplifiée** : ~12% du CA
        - Frais de transaction : 6,5%
        - Frais de mise en vente : 0,20€/vente
        - Frais de traitement : 4% + 0,30€
        - TVA : 20% sur les frais
        """)
    
    elif fees_method == "Configurateur détaillé (recommandé)":
        with st.expander("⚙️ Configurer mes frais Etsy", expanded=True):
            st.markdown("**Frais de base** (toujours applicables)")
            st.write("✓ Transaction : 6,5% du CA")
            st.write("✓ Mise en vente : 0,20€ par vente")
            st.write("✓ Traitement paiement : 4% + 0,30€")
            st.write("✓ TVA : 20% sur tous les frais")
            
            st.markdown("---")
            st.markdown("**Publicité externe (Offsite Ads)**")
            etsy_fees_config['use_offsite_ads'] = st.checkbox(
                "J'utilise Offsite Ads",
                help="Etsy promeut vos produits sur Google, Facebook, etc."
            )
            
            if etsy_fees_config['use_offsite_ads']:
                ca_estimate = st.number_input(
                    "Votre CA sur les 12 derniers mois ($)",
                    min_value=0,
                    value=5000,
                    step=1000,
                    help="Pour déterminer si vous payez 12% ou 15%"
                )
                
                if ca_estimate >= 10000:
                    etsy_fees_config['offsite_ads_rate'] = 0.12
                    st.success("✓ CA ≥ 10 000$ → Taux Offsite Ads : **12%** (obligatoire)")
                else:
                    etsy_fees_config['offsite_ads_rate'] = 0.15
                    st.warning("⚠ CA < 10 000$ → Taux Offsite Ads : **15%** (désactivable)")
            
            st.markdown("---")
            st.markdown("**Publicité interne (Etsy Ads)**")
            etsy_fees_config['use_etsy_ads'] = st.checkbox(
                "J'utilise Etsy Ads",
                help="Publicité dans les résultats de recherche Etsy"
            )
            
            if etsy_fees_config['use_etsy_ads']:
                daily_budget = st.slider(
                    "Budget quotidien (€)",
                    min_value=1.0,
                    max_value=50.0,
                    value=10.0,
                    step=1.0
                )
                etsy_fees_config['etsy_ads_budget'] = daily_budget * 30  # Budget mensuel
                st.info(f"📊 Budget mensuel estimé : {etsy_fees_config['etsy_ads_budget']:.2f}€")
            
            st.markdown("---")
            st.markdown("**Abonnement**")
            etsy_fees_config['has_etsy_plus'] = st.checkbox(
                "J'ai Etsy Plus ou Premium",
                help="Abonnement payant mensuel"
            )
            
            if etsy_fees_config['has_etsy_plus']:
                plus_type = st.selectbox("Type d'abonnement", ["Etsy Plus (10€/mois)", "Etsy Premium (20€/mois)"])
                etsy_fees_config['etsy_plus_fee'] = 10.0 if "Plus" in plus_type else 20.0
            else:
                etsy_fees_config['etsy_plus_fee'] = 0.0
    
    elif fees_method == "Relevé mensuel Etsy (précis)":
        st.markdown("""
        📊 **Upload votre relevé mensuel** pour des frais au centime près !
        
        **Comment l'obtenir :**
        1. Etsy.com → Gestionnaire de boutique
        2. **Finances** → **Compte de paiement**
        3. **Voir tous les relevés mensuels**
        4. Sélectionner le mois → **"Générer fichier CSV"**
        5. Télécharger le fichier reçu par email
        """)
        
        statement_file = st.file_uploader(
            "Relevé mensuel Etsy (CSV)",
            type=['csv'],
            key='statement_file',
            help="Format : Date, Type, Titre, Info, Devise, Montant, Frais Et Taxes, Net"
        )
        
        etsy_fees_config['statement_file'] = statement_file
        
        if statement_file:
            st.success("✅ Relevé mensuel chargé ! Les frais réels seront calculés.")
        else:
            st.warning("⚠️ Sans relevé mensuel, une estimation sera utilisée")
    
    st.markdown("---")
    
    st.markdown("### 📚 Aide")
    with st.expander("🔥 Comment exporter depuis Etsy ?"):
        st.markdown("""
        **Étapes simples (3 minutes) :**
        
        1. Allez sur **Etsy.com** > Cliquez sur votre profil
        2. **Shop Manager** > **Settings** > **Options**
        3. Onglet **"Download Data"**
        4. Section **"Orders"** :
           - **CSV Type** : Sélectionnez **"Order Items"**
           - **Period** : Choisissez le mois/année
        5. Cliquez sur **"Download CSV"**
        6. Importez le fichier ici
        """)

# Corps principal
if uploaded_file is None:
    # Page d'accueil sans données
    st.info("👆 Commencez par importer votre fichier CSV Etsy dans la barre latérale")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Vue d'ensemble")
        st.write("Suivez votre CA, vos marges et vos produits top performers en temps réel")
    
    with col2:
        st.markdown("### 🎯 Optimisation")
        st.write("Identifiez les produits à promouvoir et ceux à optimiser")
    
    with col3:
        st.markdown("### 🤖 Recommandations IA")
        st.write("Recevez des suggestions personnalisées pour augmenter vos ventes")
    
    st.markdown("---")
    
    # Exemple de données
    st.markdown("### 📝 Format CSV Etsy")
    st.markdown("""
    **Colonnes Etsy attendues** (export "Order Items") :
    - `Sale Date` → Date de vente
    - `Item Name` → Nom du produit
    - `Item Price` → Prix unitaire
    - `Quantity` → Quantité (optionnel)
    """)
    
    st.markdown("**Exemple de format compatible :**")
    example_df = pd.DataFrame({
        'Sale Date': ['11/01/2024', '11/02/2024', '11/03/2024'],
        'Item Name': ['Bracelet perles bleues', 'Boucles oreilles dorées', 'Collier argent'],
        'Item Price': [25.00, 18.50, 45.00],
        'Quantity': [1, 2, 1]
    })
    st.dataframe(example_df, width='stretch')
    
    # Bouton pour télécharger un template
    st.download_button(
        label="📥 Télécharger un template CSV complet",
        data=example_df.to_csv(index=False).encode('utf-8'),
        file_name='template_etsy_analytics.csv',
        mime='text/csv'
    )

else:
    # Chargement des données
    df = load_data(uploaded_file)
    
    if df is not None:

        # Appliquer la méthode de coûts choisie
        if cost_method == "Coût moyen par produit":
            df['Cost'] = avg_cost
            st.success(f"✅ Coût moyen de {avg_cost}€ appliqué à tous les produits")
        
        elif cost_method == "Upload CSV avec coûts détaillés" and 'cost_file' in st.session_state and cost_file is not None:
            try:
                cost_df = pd.read_csv(cost_file)
                if 'Product' in cost_df.columns and 'Cost' in cost_df.columns:
                    # Nettoyer la colonne Cost pour accepter format français (virgules)
                    cost_df['Cost'] = (cost_df['Cost']
                                      .astype(str)
                                      .str.replace(',', '.', regex=False)
                                      .str.replace(' ', '', regex=False)
                                      .str.strip())
                    cost_df['Cost'] = pd.to_numeric(cost_df['Cost'], errors='coerce').fillna(0)
                    
                    # Merger les coûts avec les données principales
                    df = df.merge(cost_df[['Product', 'Cost']], on='Product', how='left', suffixes=('', '_new'))
                    if 'Cost_new' in df.columns:
                        df['Cost'] = df['Cost_new'].fillna(df.get('Cost', 0))
                        df = df.drop('Cost_new', axis=1)
                    df['Cost'] = df['Cost'].fillna(0)
                    st.success(f"✅ Coûts importés pour {df[df['Cost'] > 0]['Product'].nunique()} produits")
                else:
                    st.error("❌ Le CSV doit contenir les colonnes 'Product' et 'Cost'")
            except Exception as e:
                st.error(f"❌ Erreur lors de l'import des coûts : {e}")
        
        # Filtrage par période
        if period != "Tout" and 'Date' in df.columns:
            days_map = {
                "7 derniers jours": 7,
                "30 derniers jours": 30,
                "90 derniers jours": 90,
                "1 an": 365
            }
            if period in days_map:
                cutoff_date = datetime.now() - timedelta(days=days_map[period])
                df_filtered = df[df['Date'] >= cutoff_date]
                
                if len(df_filtered) == 0:
                    st.warning(f"⚠️ Aucune donnée dans la période '{period}'. Affichage de toutes les données disponibles.")
                else:
                    df = df_filtered
        
        # Calcul des KPIs avec configuration des frais Etsy
        kpis = calculate_kpis(df, etsy_fees_config)

        # ========== NOUVEAU : COLLECTE DE DONNÉES ==========
        # Collecter si l'utilisateur a donné son consentement
        # if st.session_state.get('data_consent', False):  # ✅ Changé : consent_asked → data_consent
        # Récupérer TOUS les fichiers uploadés
        all_files = {}
        
        # Fichier principal (orderitems)
        if uploaded_file is not None:
            all_files['orderitems'] = uploaded_file
        
        # Fichier costs (si uploadé)
        if cost_method == "Upload CSV avec coûts détaillés" and cost_file is not None:
            all_files['costs'] = cost_file
        
        # Fichier relevé Etsy (si uploadé)
        if fees_method == "Relevé mensuel Etsy (précis)" and statement_file is not None:
            all_files['etsy_statement'] = statement_file
        
        # Collecter
        from data_collection.collector import collect_raw_data
        if all_files:  # Seulement si on a des fichiers
            collect_result = collect_raw_data(all_files, user_info['email'], 'finance_pro')
            
            # 🔍 DEBUG : Afficher le résultat
            if collect_result:
                print("✅ Collecte réussie")
            else:
                print("⚠️ Collecte échouée ou ignorée")
        # ===================================================
        
        # Onglets principaux
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Vue d'ensemble",
            "🏆 Analyse Produits",
            "📈 Évolution",
            "🤖 Recommandations IA"
        ])
        
        with tab1:
            st.markdown("## 💰 Indicateurs Financiers")
            
            # KPIs en colonnes
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Chiffre d'affaires",
                    f"{kpis['ca_total']:.2f} €",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Nombre de ventes",
                    kpis['nb_ventes'],
                    delta=None
                )
            
            with col3:
                st.metric(
                    "Panier moyen",
                    f"{kpis['panier_moyen']:.2f} €",
                    delta=None
                )
            
            with col4:
                marge_color = "normal" if kpis['taux_marge'] >= 30 else "inverse"
                st.metric(
                    "Taux de marge",
                    f"{kpis['taux_marge']:.1f} %",
                    delta=None,
                    delta_color=marge_color
                )
            
            st.markdown("---")
            
            # Détails financiers
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 💵 Détail des coûts")
                cost_df = pd.DataFrame({
                    'Poste': ['Chiffre d\'affaires', 'Frais Etsy', 'Coûts matières', 'Marge brute'],
                    'Montant (€)': [
                        kpis['ca_total'],
                        -kpis['frais_etsy'],
                        -kpis['couts_matieres'],
                        kpis['marge_brute']
                    ]
                })
                
                fig = go.Figure(go.Waterfall(
                    x=cost_df['Poste'],
                    y=cost_df['Montant (€)'],
                    text=[f"{val:.2f} €" for val in cost_df['Montant (€)']],
                    textposition="outside",
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    decreasing={"marker": {"color": "#F56400"}},
                    increasing={"marker": {"color": "#28a745"}},
                    totals={"marker": {"color": "#007bff"}}
                ))
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                st.markdown("### 📊 Répartition des revenus")
                revenue_breakdown = pd.DataFrame({
                    'Catégorie': ['Marge nette', 'Frais Etsy', 'Coûts matières'],
                    'Montant': [
                        kpis['marge_brute'],
                        kpis['frais_etsy'],
                        kpis['couts_matieres']
                    ]
                })
                
                fig = px.pie(
                    revenue_breakdown,
                    values='Montant',
                    names='Catégorie',
                    color_discrete_sequence=['#28a745', '#F56400', '#ffc107']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
            
            # Détail des frais Etsy - NOUVEAU
            if kpis.get('frais_etsy_detail'):
                st.markdown("---")
                st.markdown("### 💳 Détail des frais Etsy")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Badge de source des frais
                    source = kpis.get('fees_source', 'Non spécifié')
                    if "Relevé mensuel" in source:
                        st.success(f"✅ **Source** : {source}")
                    elif "Configurateur" in source:
                        st.info(f"ℹ️ **Source** : {source}")
                    else:
                        st.warning(f"⚠️ **Source** : {source}")
                    
                    # Tableau détaillé des frais
                    fees_data = []
                    for categorie, montant in kpis['frais_etsy_detail'].items():
                        if montant > 0:
                            pct = (montant / kpis['ca_total'] * 100) if kpis['ca_total'] > 0 else 0
                            fees_data.append({
                                'Catégorie': categorie,
                                'Montant': f"{montant:.2f} €",
                                '% du CA': f"{pct:.1f}%"
                            })
                    
                    if fees_data:
                        fees_df = pd.DataFrame(fees_data)
                        st.dataframe(fees_df, width='stretch', hide_index=True)
                    
                    # Total des frais
                    total_fees_pct = (kpis['frais_etsy'] / kpis['ca_total'] * 100) if kpis['ca_total'] > 0 else 0
                    st.metric(
                        "Total frais Etsy",
                        f"{kpis['frais_etsy']:.2f} €",
                        delta=f"{total_fees_pct:.1f}% du CA",
                        delta_color="inverse"
                    )
                
                with col2:
                    # Graphique camembert des frais
                    if fees_data:
                        fig = px.pie(
                            fees_df,
                            values=[float(x.replace(' €', '')) for x in fees_df['Montant']],
                            names=fees_df['Catégorie'],
                            title="Répartition des frais"
                        )
                        fig.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig, width='stretch')
            
            # Alerte si marge faible
            if kpis['taux_marge'] < 30:
                st.markdown(f"""
                <div class="warning-box">
                ⚠️ <strong>Attention</strong> : Votre taux de marge est de {kpis['taux_marge']:.1f}%, 
                en dessous du seuil recommandé de 30% pour un business rentable.
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("## 🏆 Analyse des Produits")
            
            product_analysis = analyze_products(df)
            
            if product_analysis is not None and len(product_analysis) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 💎 Top 10 produits par CA")
                    top_10_ca = product_analysis.head(10)
                    
                    fig = px.bar(
                        top_10_ca,
                        x='CA',
                        y='Product',
                        orientation='h',
                        text='CA',
                        color='Taux_marge',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_traces(texttemplate='%{text:.2f}€', textposition='outside')
                    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    st.markdown("### 📊 Top 10 produits par marge")
                    top_10_marge = product_analysis.nlargest(10, 'Taux_marge')
                    
                    fig = px.bar(
                        top_10_marge,
                        x='Taux_marge',
                        y='Product',
                        orientation='h',
                        text='Taux_marge',
                        color='CA',
                        color_continuous_scale='Blues'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, width='stretch')
                
                st.markdown("---")
                st.markdown("### 📋 Tableau détaillé des produits")
                
                # Formater le dataframe pour l'affichage
                display_df = product_analysis.copy()
                display_df['CA'] = display_df['CA'].apply(lambda x: f"{x:.2f} €")
                display_df['Prix_moyen'] = display_df['Prix_moyen'].apply(lambda x: f"{x:.2f} €")
                display_df['Marge'] = display_df['Marge'].apply(lambda x: f"{x:.2f} €")
                display_df['Taux_marge'] = display_df['Taux_marge'].apply(lambda x: f"{x:.1f} %")
                
                st.dataframe(
                    display_df,
                    width='stretch',
                    column_config={
                        "Product": "Produit",
                        "CA": "Chiffre d'affaires",
                        "Ventes": "Nombre de ventes",
                        "Prix_moyen": "Prix moyen",
                        "Marge": "Marge totale",
                        "Taux_marge": "Taux de marge"
                    }
                )
                
                # Analyse ABC (80/20)
                st.markdown("### 📊 Analyse ABC (Pareto)")
                product_analysis['CA_cumul_pct'] = (product_analysis['CA'].cumsum() / product_analysis['CA'].sum() * 100)
                products_80 = product_analysis[product_analysis['CA_cumul_pct'] <= 80]
                
                st.info(f"💡 **{len(products_80)} produits** (sur {len(product_analysis)}) génèrent **80% de votre CA** !")
            
            else:
                st.warning("Aucune donnée produit à afficher")
        
        with tab3:
            st.markdown("## 📈 Évolution dans le temps")
            
            if 'Date' in df.columns and len(df) > 0:
                # Évolution du CA
                daily_sales = df.groupby(df['Date'].dt.date)['Price'].sum().reset_index()
                daily_sales.columns = ['Date', 'CA']
                
                fig = px.line(
                    daily_sales,
                    x='Date',
                    y='CA',
                    title='Évolution quotidienne du chiffre d\'affaires',
                    markers=True
                )
                fig.update_traces(line_color='#F56400', line_width=3)
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
                
                # Évolution du nombre de ventes
                daily_count = df.groupby(df['Date'].dt.date).size().reset_index()
                daily_count.columns = ['Date', 'Ventes']
                
                fig = px.bar(
                    daily_count,
                    x='Date',
                    y='Ventes',
                    title='Nombre de ventes par jour',
                    color='Ventes',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
                
                # Analyse jour de la semaine
                df['DayOfWeek'] = df['Date'].dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
                
                weekly_sales = df.groupby('DayOfWeek')['Price'].sum().reindex(day_order).reset_index()
                weekly_sales['DayOfWeek'] = day_names_fr
                weekly_sales.columns = ['Jour', 'CA']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        weekly_sales,
                        x='Jour',
                        y='CA',
                        title='CA par jour de la semaine',
                        color='CA',
                        color_continuous_scale='Oranges'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    if not weekly_sales.empty and weekly_sales['CA'].sum() > 0:
                        valid_days = weekly_sales[weekly_sales['CA'] > 0]
                        
                        if not valid_days.empty:
                            best_day_idx = valid_days['CA'].idxmax()
                            best_day = valid_days.loc[best_day_idx, 'Jour']
                            best_day_ca = valid_days['CA'].max()
                            
                            st.markdown("### 🎯 Meilleur jour")
                            st.markdown(f"""
                            <div class="success-box">
                            Le <strong>{best_day}</strong> est votre meilleur jour avec <strong>{best_day_ca:.2f} €</strong> de CA !
                            <br><br>
                            💡 Conseil : Publiez vos nouveaux produits le {best_day} pour maximiser leur visibilité.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("ℹ️ Pas assez de données pour déterminer le meilleur jour de vente.")
                    else:
                        st.info("ℹ️ Pas assez de données pour déterminer le meilleur jour de vente.")
            else:
                st.warning("Les données de date ne sont pas disponibles pour l'analyse temporelle.")
        
        with tab4:
            st.markdown("## 🤖 Recommandations personnalisées")
            
            recommendations = []
            
            # Recommandation 1 : Marge
            if kpis['taux_marge'] < 30:
                recommendations.append({
                    'priority': '🔴 HAUTE',
                    'action': 'Augmenter vos marges',
                    'detail': f"Votre taux de marge actuel ({kpis['taux_marge']:.1f}%) est en dessous du seuil de rentabilité. Objectif : atteindre 35-40%.",
                    'suggestions': [
                        "Négociez avec vos fournisseurs pour réduire les coûts matières de 10-15%",
                        "Augmentez vos prix de 5-10% sur les produits à forte demande",
                        "Optimisez vos coûts d'expédition (emballages groupés)"
                    ]
                })
            else:
                recommendations.append({
                    'priority': '🟢 INFO',
                    'action': 'Maintenir vos marges',
                    'detail': f"Excellent ! Votre taux de marge ({kpis['taux_marge']:.1f}%) est sain.",
                    'suggestions': [
                        "Continuez à suivre vos coûts mensuellement",
                        "Identifiez de nouvelles opportunités d'optimisation"
                    ]
                })
            
            # Recommandation 2 : Produits top
            if product_analysis is not None and len(product_analysis) > 0:
                top_3 = product_analysis.head(3)
                
                suggestions = []
                
                if len(top_3) > 0:
                    product_name = top_3.iloc[0]['Product']
                    suggestions.append(f"Créez des variantes de '{product_name}' (nouvelles couleurs, tailles)")
                
                suggestions.extend([
                    "Augmentez votre stock sur ces produits pour éviter les ruptures",
                    "Utilisez Etsy Ads pour promouvoir ces produits",
                    "Proposez des bundles avec vos best-sellers"
                ])
                
                recommendations.append({
                    'priority': '🟡 MOYENNE',
                    'action': 'Capitaliser sur vos best-sellers',
                    'detail': f"{len(top_3)} produit(s) génèrent une part importante de votre CA.",
                    'suggestions': suggestions
                })
                
                # Recommandation 3 : Produits sous-performants
                low_performers = product_analysis[product_analysis['Ventes'] < 2]
                if len(low_performers) > 0:
                    recommendations.append({
                        'priority': '🟡 MOYENNE',
                        'action': 'Optimiser les produits sous-performants',
                        'detail': f"{len(low_performers)} produits ont moins de 2 ventes.",
                        'suggestions': [
                            "Améliorez leurs photos (5 photos minimum, fond blanc)",
                            "Optimisez les titres avec des mots-clés recherchés",
                            "Testez une baisse de prix temporaire (-20%)",
                            "Envisagez de retirer les produits sans vente depuis 90 jours"
                        ]
                    })
            
            # Recommandation 4 : Panier moyen
            if kpis['panier_moyen'] < 30:
                recommendations.append({
                    'priority': '🟡 MOYENNE',
                    'action': 'Augmenter votre panier moyen',
                    'detail': f"Votre panier moyen est de {kpis['panier_moyen']:.2f}€. Objectif : 35-40€.",
                    'suggestions': [
                        "Créez des offres bundles (Ex: 'Parure complète -15%')",
                        "Proposez la livraison gratuite à partir de 40€",
                        "Ajoutez des produits complémentaires (boîtes cadeaux, pochettes)",
                        "Mettez en avant vos produits premium"
                    ]
                })
            
            # Affichage des recommandations
            for i, rec in enumerate(recommendations, 1):
                with st.expander(f"**{rec['priority']}** - {rec['action']}", expanded=(i==1)):
                    st.markdown(f"**{rec['detail']}**")
                    st.markdown("**Actions recommandées :**")
                    for suggestion in rec['suggestions']:
                        st.markdown(f"- {suggestion}")
            
            st.markdown("---")
            
            # Prévision simple (moyenne mobile)
            if 'Date' in df.columns and len(df) > 7:
                st.markdown("### 📊 Prévision des ventes")
                
                daily_sales = df.groupby(df['Date'].dt.date)['Price'].sum()
                moving_avg_7 = daily_sales.rolling(window=7).mean().iloc[-1]
                
                next_month_prediction = moving_avg_7 * 30
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "CA prévu sur 30 jours",
                        f"{next_month_prediction:.2f} €",
                        delta=f"{(next_month_prediction - kpis['ca_total']) / kpis['ca_total'] * 100:.1f}%"
                    )
                
                with col2:
                    st.metric(
                        "Marge prévue (estimation)",
                        f"{next_month_prediction * kpis['taux_marge'] / 100:.2f} €"
                    )
                
                st.info("💡 Cette prévision est basée sur la moyenne mobile des 7 derniers jours. Ajustez votre stock en conséquence !")
        
        # Bouton d'export PDF
        st.markdown("---")
        st.markdown("## 📄 Exporter le rapport")
        
        if st.button("🔥 Générer le rapport PDF", type="primary", width='stretch'):
            with st.spinner("Génération du rapport en cours..."):
                pdf_buffer = generate_pdf_report(kpis, df, product_analysis)
                
                st.download_button(
                    label="⬇️ Télécharger le rapport PDF",
                    data=pdf_buffer,
                    file_name=f"rapport_etsy_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    width='stretch'
                )
                
                st.success("✅ Rapport généré avec succès !")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Etsy Analytics Pro</strong> - Version 2.0 (Frais Etsy détaillés)</p>
    <p>💎 Optimisez votre boutique Etsy de bijoux fantaisie</p>
    <p style='font-size: 0.9em;'>Besoin d'aide ? contact@etsy-analytics.com</p>
</div>
""", unsafe_allow_html=True)