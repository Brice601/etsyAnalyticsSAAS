import streamlit as st
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from auth.access_manager import (
        check_access, 
        has_access_to_dashboard, 
        get_user_products,
        get_user_dashboards,
        PURCHASE_LINKS
    )
except ImportError as e:
    st.error(f"❌ Erreur d'import : {e}")
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="Etsy Analytics Pro - Accueil",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styles CSS personnalisés
st.markdown("""
    <style>
    .main-header {
        font-size: 3.5rem;
        font-weight: bold;
        color: #F56400;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .dashboard-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        transition: transform 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    .dashboard-card.finance {
        background: linear-gradient(135deg, #F56400 0%, #ff8c42 100%);
    }
    .dashboard-card.customer {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .dashboard-card.seo {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .dashboard-card.locked {
        background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
        opacity: 0.7;
    }
    .dashboard-card h3 {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .dashboard-card p {
        font-size: 1.1rem;
        margin-bottom: 1rem;
        opacity: 0.9;
    }
    .user-info {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 2rem;
    }
    .feature-list {
        font-size: 1rem;
        line-height: 1.8;
    }
    .badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        margin-top: 0.5rem;
    }
    .badge.partial {
        background-color: #ffc107;
        color: #000;
    }
    .badge.complete {
        background-color: #28a745;
        color: #fff;
    }
    .buy-button {
        width: 100%;
        padding: 0.75rem;
        background: #28a745;
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 1rem;
        cursor: pointer;
        font-weight: bold;
        text-align: center;
        text-decoration: none;
        display: block;
        margin-top: 1rem;
    }
    .buy-button:hover {
        background: #218838;
    }
    .access-button {
        width: 100%;
        padding: 0.75rem;
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 1rem;
        cursor: pointer;
        font-weight: bold;
        text-align: center;
        text-decoration: none;
        display: block;
        margin-top: 1rem;
    }
    .access-button.finance {
        background: #F56400;
    }
    .access-button.customer {
        background: #667eea;
    }
    .access-button.seo {
        background: #f5576c;
    }
    </style>
""", unsafe_allow_html=True)

# ========== VÉRIFICATION D'ACCÈS ==========
user_info = check_access()

# Récupérer customer_id
customer_id = user_info.get('id')

# Récupérer les produits de l'utilisateur
user_products = get_user_products(customer_id)
user_dashboards = get_user_dashboards(customer_id)

# ========== EN-TÊTE ==========
st.markdown('<p class="main-header">🏠 Etsy Analytics Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Transformez vos données Etsy en décisions rentables</p>', unsafe_allow_html=True)

# ========== INFOS UTILISATEUR ==========
num_dashboards = len(user_dashboards)

if 'bundle' in user_products or num_dashboards >= 3:
    badge_html = '<span class="badge complete">✅ Growth Bundle Complet</span>'
    status_message = f"Vous avez accès aux **3 dashboards** !"
elif num_dashboards == 2:
    badge_html = '<span class="badge partial">⚡ 2 dashboards</span>'
    status_message = f"Il vous manque **1 dashboard** pour le pack complet"
elif num_dashboards == 1:
    badge_html = '<span class="badge partial">🚀 1 dashboard</span>'
    status_message = f"Débloquez **2 dashboards supplémentaires** pour booster vos ventes"
else:
    badge_html = '<span class="badge partial">❌ Aucun dashboard</span>'
    status_message = "Commencez par acheter votre premier dashboard"

st.markdown(f"""
<div class="user-info">
    ✅ <strong>Connecté</strong> : {user_info['email']}
    {badge_html}
    <br>
    💎 {status_message}
</div>
""", unsafe_allow_html=True)

# ========== NAVIGATION VERS LES DASHBOARDS ==========
st.markdown("## 📊 Vos Dashboards")

col1, col2, col3 = st.columns(3)

# Dashboard 1 : Finance Pro
with col1:
    has_finance = has_access_to_dashboard(customer_id, 'finance_pro')
    
    if has_finance:
        st.markdown("""
        <div class="dashboard-card finance">
            <h3>💰 Finance Pro</h3>
            <p>Analysez votre rentabilité produit par produit</p>
            <div class="feature-list">
                ✅ Calcul automatique des marges<br>
                ✅ Frais Etsy détaillés<br>
                ✅ Rapport PDF exportable<br>
                ✅ Recommandations IA
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        finance_url = f"/etsy_finance_pro?key={user_info['access_key']}"
        st.markdown(f'<a href="{finance_url}" target="_self" class="access-button finance">🚀 Accéder au Finance Pro</a>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="dashboard-card finance locked">
            <h3>💰 Finance Pro</h3>
            <p>Analysez votre rentabilité produit par produit</p>
            <div class="feature-list">
                ✅ Calcul automatique des marges<br>
                ✅ Frais Etsy détaillés<br>
                ✅ Rapport PDF exportable<br>
                ✅ Recommandations IA
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<a href="{PURCHASE_LINKS["finance_pro"]}" target="_blank" class="buy-button">🛒 Acheter Finance Pro - 29€</a>', unsafe_allow_html=True)

# Dashboard 2 : Customer Intelligence
with col2:
    has_customer = has_access_to_dashboard(customer_id, 'customer_intelligence')
    
    if has_customer:
        st.markdown("""
        <div class="dashboard-card customer">
            <h3>👥 Customer Intelligence</h3>
            <p>Comprenez vos clients et fidélisez-les</p>
            <div class="feature-list">
                ✅ Profil géographique<br>
                ✅ Analyse des avis clients<br>
                ✅ Taux de fidélisation<br>
                ✅ Clients à risque de churn
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        customer_url = f"/etsy_customer_intelligence?key={user_info['access_key']}"
        st.markdown(f'<a href="{customer_url}" target="_self" class="access-button customer">🚀 Accéder au Customer Intelligence</a>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="dashboard-card customer locked">
            <h3>👥 Customer Intelligence</h3>
            <p>Comprenez vos clients et fidélisez-les</p>
            <div class="feature-list">
                ✅ Profil géographique<br>
                ✅ Analyse des avis clients<br>
                ✅ Taux de fidélisation<br>
                ✅ Clients à risque de churn
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<a href="{PURCHASE_LINKS["customer_intelligence"]}" target="_blank" class="buy-button">🛒 Acheter Customer Intelligence - 29€</a>', unsafe_allow_html=True)

# Dashboard 3 : SEO Analyzer
with col3:
    has_seo = has_access_to_dashboard(customer_id, 'seo_analyzer')
    
    if has_seo:
        st.markdown("""
        <div class="dashboard-card seo">
            <h3>🔍 SEO Analyzer</h3>
            <p>Optimisez votre visibilité et explosez vos ventes</p>
            <div class="feature-list">
                ✅ Score SEO par listing<br>
                ✅ Analyse des titres<br>
                ✅ Efficacité des tags<br>
                ✅ Recommandations IA
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        seo_url = f"/etsy_seo_analyzer?key={user_info['access_key']}"
        st.markdown(f'<a href="{seo_url}" target="_self" class="access-button seo">🚀 Accéder au SEO Analyzer</a>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="dashboard-card seo locked">
            <h3>🔍 SEO Analyzer</h3>
            <p>Optimisez votre visibilité et explosez vos ventes</p>
            <div class="feature-list">
                ✅ Score SEO par listing<br>
                ✅ Analyse des titres<br>
                ✅ Efficacité des tags<br>
                ✅ Recommandations IA
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<a href="{PURCHASE_LINKS["seo_analyzer"]}" target="_blank" class="buy-button">🛒 Acheter SEO Analyzer - 29€</a>', unsafe_allow_html=True)

# ========== SUGGESTION BUNDLE SI INCOMPLET ==========
if num_dashboards < 3 and 'bundle' not in user_products:
    st.markdown("---")
    st.info("💡 **Astuce :** Économisez en achetant le Growth Bundle (67€) plutôt que les dashboards séparément !")
    st.markdown(f'<a href="{PURCHASE_LINKS["bundle"]}" target="_blank" class="buy-button">🎁 Acheter Growth Bundle - 67€ (au lieu de 87€)</a>', unsafe_allow_html=True)

# ========== COMPARAISON DES OPTIONS ==========
st.markdown("---")
st.markdown("## 💎 Options d'achat")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Dashboards individuels - 29€/pièce
    
    ✅ Achetez uniquement ce dont vous avez besoin
    ✅ Accès immédiat et illimité
    ✅ Mises à jour de sécurité incluses
    ✅ Support email standard
    
    💰 **Prix total si 3 dashboards : 87€**
    """)

with col2:
    st.markdown("""
    ### Growth Bundle - 67€ ⭐
    
    ✅ **Les 3 dashboards inclus**
    ✅ Accès immédiat et illimité
    ✅ **Mises à jour gratuites**
    ✅ **Support prioritaire**
    ✅ **Accès IA en avant-première**
    
    💰 **Économisez 20€** vs achat séparé
    """)

# ========== GUIDE DE DÉMARRAGE ==========
st.markdown("---")
st.markdown("## 🚀 Guide de Démarrage Rapide")

with st.expander("📥 1. Comment exporter vos données Etsy ?", expanded=False):
    st.markdown("""
    **Pour le Finance Pro et Customer Intelligence :**
    1. Allez sur **Etsy.com** → **Shop Manager**
    2. **Settings** → **Options** → **Download Data**
    3. Section **Orders** : Téléchargez **"Order Items"** (CSV)
    4. Section **Reviews** : Téléchargez vos avis (optionnel)
    
    **Pour le SEO Analyzer :**
    1. **Shop Manager** → **Settings** → **Download Data**
    2. Section **Listings** : Téléchargez tous vos listings (CSV)
    """)

with st.expander("📊 2. Quel dashboard utiliser en premier ?", expanded=False):
    st.markdown("""
    **Recommandation selon votre objectif :**
    
    🎯 **Vous voulez comprendre votre rentabilité ?**
    → Commencez par **Finance Pro**
    
    🎯 **Vous voulez augmenter vos ventes ?**
    → Utilisez **SEO Analyzer** pour optimiser vos listings
    
    🎯 **Vous voulez fidéliser vos clients ?**
    → Analysez avec **Customer Intelligence**
    
    💡 **Astuce :** Utilisez les 3 dashboards en synergie pour maximiser vos résultats !
    """)

with st.expander("❓ 3. Questions fréquentes", expanded=False):
    st.markdown("""
    **Q : Mes données sont-elles sécurisées ?**
    R : Oui ! Vos données restent sur votre ordinateur. Nous ne sauvegardons rien sans votre consentement explicite.
    
    **Q : Puis-je partager mon accès ?**
    R : Non, chaque licence est personnelle et liée à votre email.
    
    **Q : Les mises à jour sont-elles incluses ?**
    R : Oui pour le Growth Bundle. Les dashboards individuels reçoivent les mises à jour de sécurité uniquement.
    
    **Q : Puis-je avoir un remboursement ?**
    R : Oui, garantie satisfait ou remboursé 30 jours sans condition.
    
    **Q : Puis-je acheter les dashboards séparément puis avoir le bundle ?**
    R : Oui ! Vous pouvez acheter d'abord 1 ou 2 dashboards, puis compléter plus tard.
    """)

# ========== SUPPORT ==========
st.markdown("---")
st.markdown("## 💬 Besoin d'aide ?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📧 Email Support
    [support@architecte-ia.fr](mailto:support@architecte-ia.fr)
    
    Réponse sous 24h
    """)

with col2:
    st.markdown("""
    ### 📺 Tutoriels Vidéo
    [Voir les tutos](https://youtube.com/@architecteia)
    
    Guides pas à pas
    """)

with col3:
    st.markdown("""
    ### 📚 Documentation
    [Lire la doc](https://docs.architecte-ia.fr)
    
    Guides complets
    """)

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Etsy Analytics Pro</strong> - Version 2.0</p>
    <p>💎 Créé par <a href="https://architecte-ia.fr">Architecte IA</a></p>
    <p style='font-size: 0.9em;'>
        <a href="https://architecte-ia.fr/cgu">CGU</a> • 
        <a href="https://architecte-ia.fr/privacy">Confidentialité</a> • 
        <a href="https://architecte-ia.fr/contact">Contact</a>
    </p>
</div>
""", unsafe_allow_html=True)