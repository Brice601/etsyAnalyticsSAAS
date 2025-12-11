import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration de la page
st.set_page_config(
    page_title="Etsy Analytics Pro - Connexion",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Masquer navigation Streamlit
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    
    /* Styles pour la page de connexion */
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
    }
    .login-title {
        font-size: 3rem;
        font-weight: bold;
        color: #F56400;
        text-align: center;
        margin-bottom: 1rem;
    }
    .login-subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

# ========== VÉRIFICATION CONNEXION ==========
params = st.query_params

# Si pas de clé dans l'URL ET pas dans session_state → Afficher formulaire de connexion
if 'key' not in params and 'access_key' not in st.session_state:
    
    st.markdown('<p class="login-title">🔐 Connexion</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Accédez à votre tableau de bord Etsy Analytics Pro</p>', unsafe_allow_html=True)
    
    # Formulaire de connexion
    with st.form("login_form"):
        email = st.text_input(
            "📧 Votre email",
            placeholder="votre.email@example.com",
            help="Entrez l'email utilisé lors de votre inscription"
        )
        
        submitted = st.form_submit_button("🚀 Me connecter", type="primary", use_container_width=True)
        
        if submitted:
            if not email or not email.strip():
                st.error("❌ Veuillez entrer votre email")
            else:
                try:
                    from auth.access_manager import get_supabase_client
                    
                    supabase = get_supabase_client()
                    
                    if supabase:
                        with st.spinner("🔄 Connexion en cours..."):
                            response = supabase.table('customers').select('*').eq('email', email.lower().strip()).execute()
                            
                            if response.data and len(response.data) > 0:
                                customer = response.data[0]
                                
                                # Vérifier consentement
                                if not customer.get('data_consent', False):
                                    st.error("""
                                    ❌ **Accès refusé**
                                    
                                    Votre compte n'a pas donné son consentement de données.
                                    
                                    Contactez-nous à support@architecte-ia.fr pour réactiver votre compte.
                                    """)
                                else:
                                    # Connexion réussie
                                    st.session_state['access_key'] = customer['access_key']
                                    st.session_state['user_info'] = customer
                                    
                                    st.success("✅ Connexion réussie ! Chargement du tableau de bord...")
                                    
                                    st.markdown(f"""
                                    <meta http-equiv="refresh" content="1;url=/dashboard?key={customer['access_key']}">
                                    """, unsafe_allow_html=True)
                                    
                                    st.stop()
                            else:
                                st.error("❌ Aucun compte trouvé avec cet email")
                                st.info("💡 Vous n'avez pas encore de compte ? Créez-en un ci-dessous")
                    else:
                        st.error("❌ Erreur de connexion à la base de données")
                        
                except Exception as e:
                    st.error(f"❌ Erreur de connexion : {e}")
    
    st.markdown("---")
    
    # Lien vers inscription
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <p style='font-size: 1.1rem; margin-bottom: 1rem; color: #666;'>
                Pas encore de compte ?
            </p>
            <a href="/signup_page" target="_self" 
               style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 15px 40px; border-radius: 10px; text-align: center; 
                      font-weight: bold; text-decoration: none; font-size: 1.1rem;
                      box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;">
                📝 Créer un compte gratuit
            </a>
            <p style='margin-top: 1rem; font-size: 0.9rem; color: #999;'>
                ✨ 3 dashboards gratuits • Inscription en 30 secondes
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Retour à la landing
    st.markdown("""
        <div style='text-align: center; margin-top: 3rem;'>
            <a href="/" target="_self" style="color: #666; text-decoration: none; font-size: 0.95rem;">
                ← Retour à l'accueil
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# Si clé dans URL, la mettre dans session_state
if 'key' in params:
    st.session_state['access_key'] = params['key']

# ========== À PARTIR D'ICI : CODE DASHBOARD NORMAL ==========

# Configuration pour le dashboard (après connexion réussie)
st.set_page_config(
    page_title="Etsy Analytics Pro - Hub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Masquer navigation dans le dashboard aussi
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    
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
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 2rem;
    }
    .usage-info {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    .premium-info {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
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
    .badge.free {
        background-color: #007bff;
        color: #fff;
    }
    .badge.premium {
        background-color: #28a745;
        color: #fff;
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
    .access-button:hover {
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

try:
    from auth.access_manager import (
        check_access, 
        has_insights_subscription,
        check_usage_limit,
        PURCHASE_LINKS
    )
except ImportError as e:
    st.error(f"❌ Erreur d'import : {e}")
    st.stop()

# ========== VÉRIFICATION D'ACCÈS ==========
user_info = check_access()

# Récupérer customer_id
customer_id = user_info.get('id')
user_email = user_info.get('email', 'Utilisateur')
shop_name = user_info.get('shop_name', 'Boutique Etsy')

# Vérifier abonnement Insights
has_insights = has_insights_subscription(customer_id)

# Vérifier usage
usage_info = check_usage_limit(customer_id)

# ========== EN-TÊTE ==========
st.markdown('<p class="main-header">🏠 Etsy Analytics Pro</p>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle">Bienvenue, <strong>{shop_name}</strong> !</p>', unsafe_allow_html=True)

# ========== INFOS UTILISATEUR ==========
if has_insights:
    badge_html = '<span class="badge premium">💎 Insights Premium</span>'
    status_message = "Vous avez un accès **illimité** à toutes les fonctionnalités !"
else:
    badge_html = '<span class="badge free">🆓 Version Gratuite</span>'
    usage_count = usage_info.get('usage_count', 0)
    limit = usage_info.get('limit', 10)
    days_until_reset = usage_info.get('days_until_reset', 7)
    status_message = f"**{usage_count}/{limit} analyses** utilisées cette semaine (reset dans {days_until_reset} jours)"

st.markdown(f"""
<div class="user-info">
    ✅ <strong>Connecté</strong> : {user_email}
    {badge_html}
    <br>
    📊 {status_message}
</div>
""", unsafe_allow_html=True)

# Afficher barre de progression pour utilisateurs gratuits
if not has_insights:
    usage_pct = min(usage_info.get('usage_count', 0) / usage_info.get('limit', 10), 1.0)
    
    if usage_pct >= 0.8:
        st.warning(f"⚠️ Attention : {usage_info.get('usage_count')}/{usage_info.get('limit')} analyses utilisées")
    
    st.progress(usage_pct)
    
    if usage_pct >= 1.0:
        st.markdown(f"""
        <div class="usage-info">
            ❌ <strong>Limite atteinte !</strong> Vous avez utilisé vos {usage_info.get('limit')} analyses gratuites.<br>
            🔄 Réinitialisation dans {usage_info.get('days_until_reset')} jour(s)<br>
            💎 Ou passez à <a href="{PURCHASE_LINKS['insights']}" target="_blank">Insights Premium (9€/mois)</a> pour des analyses illimitées
        </div>
        """, unsafe_allow_html=True)

# ========== NAVIGATION VERS LES DASHBOARDS ==========
st.markdown("---")
st.markdown("## 📊 Vos Dashboards (Accès Gratuit)")

st.info("✅ Vous avez accès aux **3 dashboards** gratuitement en échange de votre consentement data")

col1, col2, col3 = st.columns(3)

# Dashboard 1 : Finance Pro
with col1:
    st.markdown("""
    <div class="dashboard-card finance">
        <h3>💰 Finance Pro</h3>
        <p>Analysez votre rentabilité produit par produit</p>
        <div class="feature-list">
            ✅ Calcul automatique des marges<br>
            ✅ Frais Etsy détaillés<br>
            ✅ Visualisations interactives<br>
            🔒 Recommandations IA (Premium)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    finance_url = f"/etsy_finance_pro?key={user_info['access_key']}"
    st.markdown(f'<a href="{finance_url}" target="_self" class="access-button finance">🚀 Ouvrir Finance Pro</a>', unsafe_allow_html=True)

# Dashboard 2 : Customer Intelligence
with col2:
    st.markdown("""
    <div class="dashboard-card customer">
        <h3>👥 Customer Intelligence</h3>
        <p>Comprenez vos clients et fidélisez-les</p>
        <div class="feature-list">
            ✅ Profil géographique<br>
            ✅ Analyse des avis clients<br>
            ✅ Métriques de fidélisation<br>
            🔒 Actions de réactivation (Premium)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    customer_url = f"/etsy_customer_intelligence?key={user_info['access_key']}"
    st.markdown(f'<a href="{customer_url}" target="_self" class="access-button customer">🚀 Ouvrir Customer Intelligence</a>', unsafe_allow_html=True)

# Dashboard 3 : SEO Analyzer
with col3:
    st.markdown("""
    <div class="dashboard-card seo">
        <h3>🔍 SEO Analyzer</h3>
        <p>Optimisez votre visibilité et explosez vos ventes</p>
        <div class="feature-list">
            ✅ Score SEO par listing<br>
            ✅ Analyse des titres<br>
            ✅ Efficacité des tags<br>
            🔒 Optimisations prioritaires (Premium)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    seo_url = f"/etsy_seo_analyzer?key={user_info['access_key']}"
    st.markdown(f'<a href="{seo_url}" target="_self" class="access-button seo">🚀 Ouvrir SEO Analyzer</a>', unsafe_allow_html=True)

# ========== UPGRADE INSIGHTS SI GRATUIT ==========
if not has_insights:
    st.markdown("---")
    st.markdown("## 💎 Passez à Insights Premium")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Débloquez toutes les fonctionnalités premium
        
        **Pour seulement 9€/mois, obtenez :**
        
        ✅ **Analyses illimitées** (plus de limite 10/semaine)  
        ✅ **Recommandations IA complètes** dans les 3 dashboards  
        ✅ **Export PDF illimité** de tous vos rapports  
        ✅ **Benchmarks sectoriels** en temps réel  
        ✅ **Calculateurs d'impact** précis (CA, marges)  
        ✅ **Alertes opportunités** hebdomadaires  
        ✅ **Support prioritaire** (réponse < 24h)  
        
        """)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; text-align: center; color: white;
                    margin-top: 2rem;'>
            <h2 style='margin: 0;'>9€/mois</h2>
            <p style='margin: 10px 0; opacity: 0.9;'>Annulation à tout moment</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <a href="{PURCHASE_LINKS['insights']}" target="_blank" 
           style="display: block; background: #28a745; color: white; 
                  padding: 15px; border-radius: 10px; text-align: center; 
                  font-weight: bold; font-size: 1.1rem; text-decoration: none; 
                  margin-top: 20px;">
            🚀 Upgrade maintenant
        </a>
        """, unsafe_allow_html=True)

else:
    st.markdown("---")
    st.markdown("""
    <div class="premium-info">
        💎 <strong>Merci d'être un membre Premium !</strong><br>
        Vous avez accès à toutes les fonctionnalités sans limite.
    </div>
    """, unsafe_allow_html=True)

# ========== GUIDE DE DÉMARRAGE ==========
st.markdown("---")
st.markdown("## 🚀 Guide de Démarrage Rapide")

col1, col2 = st.columns(2)

with col1:
    with st.expander("📥 1. Comment exporter vos données Etsy ?", expanded=False):
        st.markdown("""
        **Pour Finance Pro et Customer Intelligence :**
        1. Allez sur **Etsy.com** → **Shop Manager**
        2. **Settings** → **Options** → **Download Data**
        3. Section **Orders** : Téléchargez **"Order Items"** (CSV)
        4. Section **Reviews** : Téléchargez vos avis (optionnel)
        
        **Pour SEO Analyzer :**
        1. **Shop Manager** → **Settings** → **Download Data**
        2. Section **Listings** : Téléchargez tous vos listings (CSV)
        """)
    
    with st.expander("🎯 2. Quel dashboard utiliser en premier ?", expanded=False):
        st.markdown("""
        **Recommandation selon votre objectif :**
        
        💰 **Vous voulez comprendre votre rentabilité ?**
        → Commencez par **Finance Pro**
        
        🔍 **Vous voulez augmenter vos ventes ?**
        → Utilisez **SEO Analyzer** pour optimiser vos listings
        
        👥 **Vous voulez fidéliser vos clients ?**
        → Analysez avec **Customer Intelligence**
        
        💡 **Astuce :** Utilisez les 3 dashboards en synergie pour maximiser vos résultats !
        """)

with col2:
    with st.expander("💎 3. Pourquoi passer à Insights Premium ?", expanded=False):
        st.markdown("""
        **Version Gratuite** vous donne accès aux dashboards de base, mais **Insights Premium** débloque :
        
        🤖 **Recommandations IA personnalisées** dans chaque dashboard  
        📊 **Analyses comparatives** vs benchmarks secteur  
        💰 **Calculateurs d'impact** précis (estimation gains)  
        📈 **Roadmaps d'actions** priorisées par ROI  
        ⚡ **Alertes opportunités** automatiques  
        📄 **Export PDF** de tous vos rapports  
        🔄 **Analyses illimitées** (pas de quota)  
        
        **Prix :** 9€/mois seulement (annulation à tout moment)
        """)
    
    with st.expander("❓ 4. Questions fréquentes", expanded=False):
        st.markdown("""
        **Q : Mes données sont-elles sécurisées ?**
        R : Oui ! Vos données sont anonymisées et stockées sur des serveurs sécurisés (Supabase).
        
        **Q : Pourquoi 10 analyses/semaine en gratuit ?**
        R : Pour éviter les abus. C'est largement suffisant pour analyser vos ventes hebdomadaires.
        
        **Q : Puis-je annuler Insights Premium ?**
        R : Oui, annulation à tout moment. Aucun engagement.
        
        **Q : Que se passe-t-il si je retire mon consentement data ?**
        R : Vous perdrez l'accès à la version gratuite. Alternative : passer à Premium (9€/mois).
        
        **Q : Les mises à jour sont-elles incluses ?**
        R : Oui, toutes les mises à jour sont incluses pour tous les utilisateurs.
        """)

# ========== STATISTIQUES D'UTILISATION ==========
st.markdown("---")
st.markdown("## 📈 Votre Activité")

col1, col2, col3, col4 = st.columns(4)

with col1:
    signup_date = user_info.get('signup_date')
    if signup_date:
        signup_dt = datetime.fromisoformat(signup_date)
        days_since = (datetime.now() - signup_dt).days
        st.metric("Membre depuis", f"{days_since} jours")
    else:
        st.metric("Membre depuis", "Nouveau")

with col2:
    st.metric("Analyses ce mois", usage_info.get('usage_count', 0))

with col3:
    last_login = user_info.get('last_login')
    if last_login:
        last_dt = datetime.fromisoformat(last_login)
        st.metric("Dernière connexion", last_dt.strftime('%d/%m/%Y'))
    else:
        st.metric("Dernière connexion", "Aujourd'hui")

with col4:
    if has_insights:
        st.metric("Statut", "Premium 💎")
    else:
        st.metric("Statut", "Gratuit 🆓")

# ========== PARAMÈTRES ==========
st.markdown("---")
st.markdown("## ⚙️ Paramètres du Compte")

with st.expander("🔧 Gérer mes préférences"):
    st.markdown(f"""
    **Email :** {user_email}  
    **Boutique Etsy :** {shop_name}  
    **Consentement data :** ✅ Actif (obligatoire pour version gratuite)  
    **Access Key :** `{user_info['access_key'][:20]}...` (gardez-la secrète)
    """)
    
    st.markdown("---")
    
    st.warning("""
    ⚠️ **Attention :** Le retrait du consentement data entraîne la perte d'accès à la version gratuite.
    
    Si vous souhaitez retirer votre consentement, contactez-nous à support@architecte-ia.fr
    """)

# ========== SUPPORT ==========
st.markdown("---")
st.markdown("## 💬 Besoin d'aide ?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📧 Email Support
    [support@architecte-ia.fr](mailto:support@architecte-ia.fr)
    
    Réponse sous 24-48h
    """)

with col2:
    st.markdown("""
    ### 📺 Tutoriels Vidéo
    [Voir les tutos YouTube](https://youtube.com/@architecteia)
    
    Guides pas à pas
    """)

with col3:
    st.markdown("""
    ### 📚 Documentation
    [Lire la doc complète](https://docs.architecte-ia.fr)
    
    FAQ et guides
    """)

# ========== DÉCONNEXION ==========
st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 2])

with col2:
    if st.button("🚪 Se déconnecter", use_container_width=True):
        # Vider la session
        st.session_state.clear()
        
        st.success("✅ Déconnexion réussie !")
        
        st.markdown("""
        <meta http-equiv="refresh" content="1;url=/dashboard">
        """, unsafe_allow_html=True)
        
        st.stop()

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Etsy Analytics Pro</strong> - Version 2.0 Freemium</p>
    <p>💎 Créé par <a href="https://architecte-ia.fr">Architecte IA</a></p>
    <p style='font-size: 0.9em;'>
        <a href="https://architecte-ia.fr/cgu">CGU</a> • 
        <a href="https://architecte-ia.fr/privacy">Confidentialité</a> • 
        <a href="https://architecte-ia.fr/contact">Contact</a>
    </p>
</div>
""", unsafe_allow_html=True)