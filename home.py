import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Etsy Analytics Pro - Transforme tes données en décisions rentables",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'mailto:support@architecte-ia.fr',
        'About': "Etsy Analytics Pro - Découvre ta vraie rentabilité produit par produit"
    }
)

# ✅ Masquer le menu Streamlit
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# ✅ NOUVEAU : Redirection automatique si déjà connecté
if 'access_key' in st.session_state and st.session_state.get('access_key'):
    st.markdown(f"""
    <meta http-equiv="refresh" content="0;url=/dashboard?key={st.session_state['access_key']}">
    """, unsafe_allow_html=True)
    st.info("🔄 Redirection vers votre tableau de bord...")
    st.stop()

# Vérifier dans les query params aussi
params = st.query_params
if 'key' in params:
    access_key = params['key']
    st.markdown(f"""
    <meta http-equiv="refresh" content="0;url=/dashboard?key={access_key}">
    """, unsafe_allow_html=True)
    st.info("🔄 Redirection vers votre tableau de bord...")
    st.stop()

# Meta tags SEO
st.markdown("""
    <meta name="description" content="Découvre enfin ta vraie rentabilité produit par produit sur Etsy. 3 dashboards gratuits : Finance Pro, Customer Intelligence, SEO Analyzer.">
    <meta name="keywords" content="etsy rentabilité, etsy marges, etsy analytics, calcul frais etsy, optimisation boutique etsy">
    <meta property="og:title" content="Transforme tes données Etsy en décisions rentables">
    <meta property="og:description" content="Arrête de perdre de l'argent sans le savoir. Analyse tes marges réelles en 30 secondes.">
""", unsafe_allow_html=True)

# Styles CSS
st.markdown("""
    <style>
    /* Reset */
    .main > div {padding-top: 0rem; padding-bottom: 0rem;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        text-align: center;
        color: white;
        margin: -1rem -1rem 0 -1rem;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        opacity: 0.95;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    .hero-cta {
        display: inline-block;
        background: #F56400;
        color: white;
        padding: 1.2rem 3rem;
        border-radius: 50px;
        font-size: 1.3rem;
        font-weight: bold;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .hero-cta:hover {
        background: #ff7a1a;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .hero-features {
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin-top: 2rem;
        font-size: 1.1rem;
    }
    
    .hero-feature {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Dashboard Cards */
    .dashboard-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 2px solid transparent;
        height: 100%;
    }
    
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.15);
    }
    
    .dashboard-card.finance {border-color: #F56400;}
    .dashboard-card.customer {border-color: #667eea;}
    .dashboard-card.seo {border-color: #f5576c;}
    
    .dashboard-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .dashboard-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #262730;
    }
    
    .dashboard-description {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    
    .dashboard-features {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .dashboard-features li {
        padding: 0.5rem 0;
        color: #262730;
        font-size: 0.95rem;
    }
    
    .dashboard-features li:before {
        content: "✅ ";
        margin-right: 0.5rem;
    }
    
    .badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        margin-top: 1rem;
    }
    
    .badge.free {
        background: #28a745;
        color: white;
    }
    
    /* Pricing Section */
    .pricing-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 4rem 2rem;
        margin: 4rem -1rem 0 -1rem;
    }
    
    .pricing-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 3rem;
        color: #262730;
    }
    
    .pricing-card {
        background: white;
        border-radius: 15px;
        padding: 2.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .pricing-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.15);
    }
    
    .pricing-card.premium {
        border: 3px solid #F56400;
        position: relative;
    }
    
    .pricing-badge {
        position: absolute;
        top: -15px;
        left: 50%;
        transform: translateX(-50%);
        background: #F56400;
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .pricing-name {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #262730;
    }
    
    .pricing-price {
        font-size: 3rem;
        font-weight: 800;
        color: #F56400;
        margin-bottom: 0.5rem;
    }
    
    .pricing-period {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    .pricing-features {
        list-style: none;
        padding: 0;
        margin: 2rem 0;
        text-align: left;
    }
    
    .pricing-features li {
        padding: 0.7rem 0;
        color: #262730;
        font-size: 0.95rem;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .pricing-features li:last-child {
        border-bottom: none;
    }
    
    .pricing-features li:before {
        content: "✅ ";
        margin-right: 0.5rem;
    }
    
    .pricing-cta {
        display: block;
        width: 100%;
        padding: 1rem;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: bold;
        text-decoration: none;
        text-align: center;
        transition: all 0.3s ease;
        margin-top: 1.5rem;
    }
    
    .pricing-cta.primary {
        background: #F56400;
        color: white;
    }
    
    .pricing-cta.secondary {
        background: #667eea;
        color: white;
    }
    
    .pricing-cta:hover {
        opacity: 0.9;
        transform: scale(1.02);
    }
    
    /* Footer */
    .footer {
        background: #262730;
        color: white;
        padding: 3rem 2rem;
        margin: 4rem -1rem -1rem -1rem;
        text-align: center;
    }
    
    .footer a {
        color: #F56400;
        text-decoration: none;
    }
    
    .footer a:hover {
        text-decoration: underline;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {font-size: 2.5rem;}
        .hero-subtitle {font-size: 1.2rem;}
        .hero-features {flex-direction: column; gap: 1rem;}
    }
    </style>
""", unsafe_allow_html=True)


# ========== HERO SECTION ==========
st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Analyse ta boutique Etsy en 30 secondes</h1>
        <p class="hero-subtitle">3 dashboards gratuits pour comprendre tes marges, tes clients et ton SEO</p>
        <a href="/signup_page" class="hero-cta">Analyser gratuitement</a>
        <p style='margin-top: 1.5rem; font-size: 1rem; opacity: 0.9;'>
            Déjà client ? <a href="/dashboard" style='color: white; text-decoration: underline;'>Se connecter</a>
        </p>
    </div>
""", unsafe_allow_html=True)

# ========== 3 DASHBOARDS GRATUITS ==========
st.markdown("<h2 style='text-align: center; font-size: 2.5rem; margin: 4rem 0 3rem 0; color: #262730;'>3 Dashboards Gratuits</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="dashboard-card finance">
            <div class="dashboard-icon">💰</div>
            <h3 class="dashboard-title">Finance Pro</h3>
            <p class="dashboard-description">Calcule tes marges réelles produit par produit</p>
            <ul class="dashboard-features">
                <li>Calcul automatique des marges</li>
                <li>Tous les frais Etsy (6,5% + TVA + Offsite Ads)</li>
                <li>Produits rentables vs ruineux</li>
                <li>Visualisations interactives</li>
                <li>Recommandations IA (Premium)</li>
            </ul>
            <span class="badge free">Gratuit</span>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="dashboard-card customer">
            <div class="dashboard-icon">👥</div>
            <h3 class="dashboard-title">Customer Intelligence</h3>
            <p class="dashboard-description">Comprends tes clients et fidélise-les</p>
            <ul class="dashboard-features">
                <li>Profil géographique détaillé</li>
                <li>Analyse des avis clients</li>
                <li>Métriques de fidélisation (LTV)</li>
                <li>Clients à risque de churn</li>
                <li>Actions de réactivation (Premium)</li>
            </ul>
            <span class="badge free">Gratuit</span>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="dashboard-card seo">
            <div class="dashboard-icon">🔍</div>
            <h3 class="dashboard-title">SEO Analyzer</h3>
            <p class="dashboard-description">Optimise ta visibilité et explose tes ventes</p>
            <ul class="dashboard-features">
                <li>Score SEO par listing (0-100)</li>
                <li>Analyse des titres optimisés</li>
                <li>Efficacité des tags</li>
                <li>Impact des photos sur ventes</li>
                <li>Optimisations prioritaires (Premium)</li>
            </ul>
            <span class="badge free">Gratuit</span>
        </div>
    """, unsafe_allow_html=True)

# ========== PRICING ==========
st.markdown("""
    <div class="pricing-section">
        <h2 class="pricing-title">Choisis ta formule</h2>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="pricing-card">
            <h3 class="pricing-name">Gratuit</h3>
            <div class="pricing-price">0€</div>
            <ul class="pricing-features">
                <li>3 dashboards complets</li>
                <li>10 analyses par semaine</li>
                <li>Métriques de base détaillées</li>
                <li>Visualisations interactives</li>
                <li>Calcul automatique des marges</li>
            </ul>
            <a href="/signup_page" class="pricing-cta secondary">Commencer gratuitement</a>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="pricing-card premium">
            <div class="pricing-badge">Recommandé</div>
            <h3 class="pricing-name">Insights Premium</h3>
            <div class="pricing-price">9€</div>
            <div class="pricing-period">par mois</div>
            <ul class="pricing-features">
                <li><strong>Tout le gratuit +</strong></li>
                <li>Analyses illimitées (pas de quota)</li>
                <li>Recommandations IA</li>
                <li>Export PDF professionnel</li>
                <li>Benchmarks sectoriels</li>
                <li>Calculateurs d'impact ROI</li>
                <li>Alertes opportunités hebdo</li>
                <li>Support prioritaire < 24h</li>
            </ul>
            <a href="/signup_page" class="pricing-cta primary">Essayer Premium</a>
            <p style='margin-top: 1rem; font-size: 0.9rem; color: #666;'>
                Annulation à tout moment
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ========== COMMENT ÇA MARCHE ==========
st.markdown("<h2 style='text-align: center; font-size: 2.5rem; margin: 4rem 0 3rem 0; color: #262730;'>Comment ça marche ?</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>📥</div>
            <h3 style='font-size: 1.5rem; margin-bottom: 1rem;'>1. Exporte tes données</h3>
            <p style='color: #666;'>Télécharge ton CSV depuis Etsy<br>(2 minutes, ultra simple)</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>🤖</div>
            <h3 style='font-size: 1.5rem; margin-bottom: 1rem;'>2. L'IA analyse tout</h3>
            <p style='color: #666;'>Marges, clients, SEO...<br>Résultats en 30 secondes</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>📈</div>
            <h3 style='font-size: 1.5rem; margin-bottom: 1rem;'>3. Optimise et vends +</h3>
            <p style='color: #666;'>Actions concrètes pour<br>augmenter tes marges</p>
        </div>
    """, unsafe_allow_html=True)

# ========== FAQ ==========
st.markdown("<h2 style='text-align: center; font-size: 2.5rem; margin: 4rem 0 3rem 0; color: #262730;'>Questions fréquentes</h2>", unsafe_allow_html=True)

with st.expander("C'est compliqué à utiliser ?"):
    st.markdown("""
    **Non ! Si tu sais télécharger un fichier CSV depuis Etsy, tu sais utiliser l'outil.**
    
    Tout s'analyse automatiquement après. Aucune compétence technique requise.
    
    **Étapes :**
    1. Va sur Etsy > Boutique Manager > Paramètres > Télécharger les données
    2. Télécharge ton CSV "Order Items"
    3. Upload-le dans l'outil
    4. BAM ! Tous tes graphiques et analyses s'affichent
    """)

with st.expander("Mes données sont-elles sécurisées ?"):
    st.markdown("""
    **Oui, sécurité maximale !**
    
    - Données hébergées sur serveurs sécurisés (**Supabase** - certifié SOC2)
    - Données **chiffrées**
    - **JAMAIS** partagées avec des tiers
    - Seul toi as accès à ton compte (clé d'accès personnelle)
    - Nous ne revendons **aucune donnée**
    - Conformité **RGPD**
    """)

with st.expander("Pourquoi c'est gratuit ?"):
    st.markdown("""
    **Modèle freemium transparent :**
    
    En acceptant de partager tes données de ventes de manière **anonymisée** (hash de ton email), 
    tu nous aides à améliorer notre IA et on peut t'offrir l'accès gratuit.
    
    **Alternative :** Insights Premium (9€/mois) sans collecte de données requise.
    
    **Avantages version gratuite :**
    - Accès aux 3 dashboards
    - 10 analyses/semaine (suffisant pour 99% des vendeurs)
    - Toutes les métriques de base
    - Calcul automatique des marges
    """)

with st.expander("Pourquoi limiter à 10 analyses/semaine ?"):
    st.markdown("""
    **Pour éviter les abus et garantir une bonne expérience à tous.**
    
    10 analyses/semaine est largement suffisant pour :
    - Analyser tes ventes hebdomadaires
    - Tester différentes périodes
    - Optimiser progressivement
    
    **Besoin de plus ?** Insights Premium offre des analyses illimitées.
    """)

with st.expander("Ça calcule aussi les frais Offsite Ads, Etsy Ads, etc. ?"):
    st.markdown("""
    **Oui ! Finance Pro prend tout en compte :**
    
    - Frais de transaction (6,5%)
    - Mise en vente (0,20€)
    - Traitement paiement (4% + 0,30€)
    - TVA (20% sur tous les frais)
    - **Offsite Ads** (12% ou 15%)
    - **Etsy Ads** (budget configurable)
    - **Abonnement Plus** (si applicable)
    
    Tu peux même **uploader ton relevé mensuel Etsy** pour avoir les frais exacts au centime près !
    
    **C'est le calcul le plus précis du marché.**
    """)

with st.expander("Je peux annuler Premium quand je veux ?"):
    st.markdown("""
    **Oui, à tout moment.**
    
    - Aucun engagement
    - Annulation en 1 clic
    - Retour automatique au plan gratuit
    - Tes données restent accessibles
    """)

with st.expander("Combien de temps ça prend pour analyser ?"):
    st.markdown("""
    **Entre 10 et 30 secondes** selon la taille de ton fichier CSV.
    
    Même si tu as 10 000 ventes, l'analyse est quasi instantanée.
    
    Tu uploads ton fichier, et **BAM**, tous tes graphiques et recommandations s'affichent.
    """)

with st.expander("Garantie satisfait ou remboursé ?"):
    st.markdown("""
    **Version gratuite :** Aucun risque, c'est gratuit !
    
    **Insights Premium :** Si tu n'es pas satisfait dans les 7 premiers jours, 
    on te rembourse intégralement sans question.
    """)

# ========== CTA FINAL ==========
st.markdown("""
    <div style='background: linear-gradient(135deg, #F56400 0%, #ff8c42 100%); 
                padding: 4rem 2rem; margin: 4rem -1rem 0 -1rem; 
                text-align: center; color: white;'>
        <h2 style='font-size: 2.5rem; margin-bottom: 1rem;'>
            Arrête de perdre de l'argent sans le savoir
        </h2>
        <p style='font-size: 1.3rem; margin-bottom: 2rem; opacity: 0.95;'>
            Rejoins nos créateurs qui ont optimisé leurs marges
        </p>
        <a href="/signup_page" class="hero-cta" style='background: white; color: #F56400;'>
            Analyser ma boutique gratuitement
        </a>
        <p style='margin-top: 1.5rem; font-size: 1rem; opacity: 0.9;'>
            ✅ Analyse tes ventes en 30 secondes (pas 5 heures dans Excel)<br>
            ✅ Découvre tes produits rentables (et ceux qui te ruinent)<br>
            ✅ Optimise tes prix, ton SEO et ta stratégie client
        </p>
        <p style='margin-top: 1.5rem; font-size: 0.9rem; opacity: 0.8;'>
            Inscription en 30 secondes • Aucune carte bancaire requise
        </p>
    </div>
""", unsafe_allow_html=True)

# ========== FOOTER ==========
st.markdown("""
    <div class="footer">
        <p style='font-size: 1.2rem; margin-bottom: 2rem;'>
            <strong>Etsy Analytics Pro</strong> - Version 2.0 Freemium
        </p>
        <p style='margin-bottom: 1rem;'>
            Créé par <a href="https://architecte-ia.fr" target="_blank">Architecte IA</a>
        </p>
        <p style='margin-bottom: 1rem;'>
            <a href="https://www.youtube.com/@architecteIA" target="_blank">YouTube</a> • 
            <a href="mailto:support@architecte-ia.fr">Support Email</a> •
            <a href="/dashboard">Connexion</a>
        </p>
        <p style='font-size: 0.9rem; opacity: 0.8;'>
            <a href="https://architecte-ia.fr/cgu">CGU</a> • 
            <a href="https://architecte-ia.fr/privacy">Confidentialité</a> • 
            <a href="https://architecte-ia.fr/contact">Contact</a>
        </p>
        <p style='margin-top: 2rem; font-size: 0.85rem; opacity: 0.6;'>
            © 2025 Architecte IA - Tous droits réservés
        </p>
    </div>
""", unsafe_allow_html=True)