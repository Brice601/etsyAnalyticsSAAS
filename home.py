import streamlit as st
import json
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from auth.access_manager import check_access, has_access_to_dashboard
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
        cursor: pointer;
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
        cursor: not-allowed;
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
    .badge.starter {
        background-color: #ffc107;
        color: #000;
    }
    .badge.bundle {
        background-color: #28a745;
        color: #fff;
    }
    .badge.locked {
        background-color: #6c757d;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# ========== VÉRIFICATION D'ACCÈS ==========
user_info = check_access()

# ========== EN-TÊTE ==========
st.markdown('<p class="main-header">🏠 Etsy Analytics Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Transformez vos données Etsy en décisions rentables</p>', unsafe_allow_html=True)

# ========== INFOS UTILISATEUR ==========
product_name = "Starter Pack" if user_info['product'] == 'starter' else "Growth Bundle"
product_class = "starter" if user_info['product'] == 'starter' else "bundle"

st.markdown(f"""
<div class="user-info">
    ✅ <strong>Connecté</strong> : {user_info['email']}
    <span class="badge {product_class}">{product_name}</span>
</div>
""", unsafe_allow_html=True)

# ========== NAVIGATION VERS LES DASHBOARDS ==========
st.markdown("## 📊 Vos Dashboards")

# Dashboard 1 : Finance Pro
col1, col2, col3 = st.columns(3)

with col1:
    has_finance_access = has_access_to_dashboard(user_info['access_key'], 'finance_pro')
    
    if has_finance_access:
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
        
        # Utiliser switch_page qui gère mieux les paramètres
        if st.button("🚀 Accéder au Finance Pro", key="btn_finance", type="primary", use_container_width=True):
            # Sauvegarder la clé en session_state avant de naviguer
            st.session_state['access_key'] = user_info['access_key']
            st.switch_page("pages/etsy_finance_pro.py")
    else:
        st.markdown("""
        <div class="dashboard-card finance locked">
            <h3>💰 Finance Pro</h3>
            <p>Analysez votre rentabilité produit par produit</p>
            <span class="badge locked">🔒 Disponible dans tous les packs</span>
        </div>
        """, unsafe_allow_html=True)

with col2:
    has_customer_access = has_access_to_dashboard(user_info['access_key'], 'customer_intelligence')
    
    if has_customer_access:
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
        
        if st.button("🚀 Accéder au Customer Intelligence", key="btn_customer", type="primary", use_container_width=True):
            st.session_state['access_key'] = user_info['access_key']
            st.switch_page("pages/etsy_customer_intelligence.py")
    else:
        st.markdown("""
        <div class="dashboard-card customer locked">
            <h3>👥 Customer Intelligence</h3>
            <p>Comprenez vos clients et fidélisez-les</p>
            <span class="badge locked">🔒 Growth Bundle uniquement</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⬆️ Upgrader vers Growth Bundle", key="upgrade_customer"):
            st.info("🎁 Passez au Growth Bundle pour débloquer ce dashboard !")
            st.markdown("[🔥 Upgrader maintenant](https://buy.stripe.com/bundle)")

with col3:
    has_seo_access = has_access_to_dashboard(user_info['access_key'], 'seo_analyzer')
    
    if has_seo_access:
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
        
        if st.button("🚀 Accéder au SEO Analyzer", key="btn_seo", type="primary", use_container_width=True):
            st.session_state['access_key'] = user_info['access_key']
            st.switch_page("pages/etsy_seo_analyzer.py")
    else:
        st.markdown("""
        <div class="dashboard-card seo locked">
            <h3>🔍 SEO Analyzer</h3>
            <p>Optimisez votre visibilité et explosez vos ventes</p>
            <span class="badge locked">🔒 Growth Bundle uniquement</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⬆️ Upgrader vers Growth Bundle", key="upgrade_seo"):
            st.info("🎁 Passez au Growth Bundle pour débloquer ce dashboard !")
            st.markdown("[🔥 Upgrader maintenant](https://buy.stripe.com/bundle)")

# ========== COMPARAISON DES PACKS ==========
st.markdown("---")
st.markdown("## 💎 Comparaison des Packs")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Starter Pack - 29€
    
    ✅ **Finance Pro Dashboard**
    - Analyse complète de rentabilité
    - Frais Etsy détaillés
    - Rapport PDF exportable
    - Recommandations IA
    
    ✅ **Guide PDF complet**
    ✅ **Support email**
    
    ❌ Customer Intelligence
    ❌ SEO Analyzer
    ❌ Accès IA en avant-première
    ❌ Support prioritaire
    """)

with col2:
    st.markdown("""
    ### Growth Bundle - 67€ ⭐
    
    ✅ **Tous les dashboards (3)**
    - Finance Pro
    - Customer Intelligence  
    - SEO Analyzer
    
    ✅ **Accès IA en avant-première**
    ✅ **Support prioritaire**
    ✅ **Mises à jour gratuites**
    ✅ **Nouvelles fonctionnalités en exclusivité**
    
    💰 **Économisez 30€** vs achat séparé
    """)

if user_info['product'] == 'starter':
    st.info("💡 **Vous avez le Starter Pack.** Passez au Growth Bundle pour débloquer tous les dashboards !")
    st.markdown("[🔥 Upgrader maintenant - 38€ seulement](https://buy.stripe.com/upgrade)")

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
    R : Oui pour le Growth Bundle. Le Starter Pack reçoit les mises à jour de sécurité uniquement.
    
    **Q : Puis-je avoir un remboursement ?**
    R : Oui, garantie satisfait ou remboursé 30 jours sans condition.
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
