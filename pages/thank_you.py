import streamlit as st
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Merci ! - Etsy Analytics Pro",
    page_icon="🎉",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Masquer navigation Streamlit
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    
    .success-header {
        font-size: 4rem;
        text-align: center;
        margin: 2rem 0 1rem 0;
    }
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: #28a745;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 2rem 0;
    }
    .next-steps {
        background-color: #e7f3ff;
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        margin: 2rem 0;
    }
    .feature-highlight {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ========== HEADER DE SUCCÈS ==========
st.markdown('<div class="success-header">🎉</div>', unsafe_allow_html=True)
st.markdown('<p class="main-title">Paiement réussi !</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Bienvenue dans Insights Premium</p>', unsafe_allow_html=True)

# ========== MESSAGE PRINCIPAL ==========
st.markdown("""
<div class="info-box">
    <h2 style='margin-top: 0; text-align: center;'>✅ Votre abonnement est activé</h2>
    <p style='font-size: 1.2rem; text-align: center; margin: 20px 0;'>
        Vous avez maintenant accès à <strong>toutes les fonctionnalités premium</strong> d'Etsy Analytics Pro !
    </p>
</div>
""", unsafe_allow_html=True)

# ========== PROCHAINES ÉTAPES ==========
st.markdown("""
<div class="next-steps">
    <h3>📧 Que se passe-t-il maintenant ?</h3>
    <ol style='font-size: 1.1rem; line-height: 2;'>
        <li><strong>Email de confirmation envoyé</strong> : Vérifiez votre boîte mail (et les spams)</li>
        <li><strong>Votre compte est activé</strong> : Vous pouvez vous connecter immédiatement</li>
        <li><strong>Accès illimité débloqué</strong> : Plus de limite d'analyses</li>
        <li><strong>Recommandations IA disponibles</strong> : Dans les 3 dashboards</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# ========== BOUTON DE CONNEXION ==========
st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div style='text-align: center;'>
        <h3 style='margin-bottom: 1.5rem;'>🚀 Commencez dès maintenant</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔑 Me connecter à mon compte", type="primary", use_container_width=True):
        st.markdown("""
        <meta http-equiv="refresh" content="0;url=/dashboard">
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <p style='text-align: center; margin-top: 1rem; color: #666; font-size: 0.95rem;'>
        Utilisez l'email que vous avez fourni lors du paiement
    </p>
    """, unsafe_allow_html=True)

# ========== CE QUI EST DÉBLOQUÉ ==========
st.markdown("---")
st.markdown("## 💎 Voici ce qui est maintenant débloqué pour vous")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-highlight">
        <h4>🤖 Recommandations IA complètes</h4>
        <p>Analyses personnalisées dans Finance Pro, Customer Intelligence et SEO Analyzer</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-highlight">
        <h4>📊 Benchmarks sectoriels</h4>
        <p>Comparez vos performances vs la concurrence en temps réel</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-highlight">
        <h4>💰 Calculateurs d'impact</h4>
        <p>Estimations précises de gains potentiels pour chaque optimisation</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-highlight">
        <h4>♾️ Analyses illimitées</h4>
        <p>Plus de limite de 10 analyses par semaine</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-highlight">
        <h4>📄 Export PDF sans limite</h4>
        <p>Téléchargez tous vos rapports au format professionnel</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-highlight">
        <h4>⚡ Support prioritaire</h4>
        <p>Réponse garantie sous 24h par email</p>
    </div>
    """, unsafe_allow_html=True)

# ========== TUTORIEL RAPIDE ==========
st.markdown("---")
st.markdown("## 🎯 Par où commencer ?")

with st.expander("📥 1. Exportez vos données Etsy (2 minutes)", expanded=True):
    st.markdown("""
    **Pour utiliser les dashboards :**
    
    1. Allez sur **Etsy.com** → **Shop Manager**
    2. **Settings** → **Options** → **Download Data**
    3. Téléchargez :
       - **Order Items** (pour Finance Pro et Customer Intelligence)
       - **Listings** (pour SEO Analyzer)
    
    📺 [Voir le tutoriel vidéo](https://youtube.com/@architecteia)
    """)

with st.expander("💰 2. Analysez votre rentabilité (Finance Pro)"):
    st.markdown("""
    **Découvrez vos vraies marges :**
    
    ✅ Uploadez votre fichier "Order Items"  
    ✅ Configurez vos coûts (matières premières, shipping)  
    ✅ L'outil calcule automatiquement vos marges réelles  
    ✅ **NOUVEAU** : Accédez aux recommandations IA pour optimiser vos prix  
    
    👉 [Ouvrir Finance Pro](/etsy_finance_pro)
    """)

with st.expander("👥 3. Comprenez vos clients (Customer Intelligence)"):
    st.markdown("""
    **Fidélisez et réactivez vos clients :**
    
    ✅ Profil géographique détaillé  
    ✅ Analyse des avis (sentiment, patterns)  
    ✅ Clients VIP vs à risque de churn  
    ✅ **NOUVEAU** : Recommandations personnalisées de réactivation  
    
    👉 [Ouvrir Customer Intelligence](/etsy_customer_intelligence)
    """)

with st.expander("🔍 4. Optimisez votre SEO (SEO Analyzer)"):
    st.markdown("""
    **Explosez votre visibilité Etsy :**
    
    ✅ Score SEO 0-100 pour chaque listing  
    ✅ Analyse des titres, tags, descriptions  
    ✅ Impact des photos sur les conversions  
    ✅ **NOUVEAU** : Roadmap d'optimisations priorisées par impact  
    
    👉 [Ouvrir SEO Analyzer](/etsy_seo_analyzer)
    """)

# ========== BESOIN D'AIDE ==========
st.markdown("---")
st.markdown("## 💬 Besoin d'aide ?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📧 Email Support
    [support@architecte-ia.fr](mailto:support@architecte-ia.fr)
    
    Réponse < 24h  
    (prioritaire)
    """)

with col2:
    st.markdown("""
    ### 📺 Tutoriels
    [YouTube @architecteia](https://youtube.com/@architecteia)
    
    Guides vidéo  
    pas à pas
    """)

with col3:
    st.markdown("""
    ### 📚 Documentation
    [docs.architecte-ia.fr](https://docs.architecte-ia.fr)
    
    FAQ complète  
    et guides
    """)

# ========== RÉCAPITULATIF ABONNEMENT ==========
st.markdown("---")
st.markdown("## 📋 Récapitulatif de votre abonnement")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    **Plan souscrit :** Insights Premium 💎  
    **Montant :** 9€/mois  
    **Prochain paiement :** Automatique dans 1 mois  
    **Facturation :** Par email après chaque paiement  
    
    **Annulation :** À tout moment depuis votre compte  
    **Garantie :** Satisfait ou remboursé sous 7 jours  
    """)

with col2:
    st.info("""
    **💡 Astuce**
    
    Ajoutez notre email  
    à vos contacts pour  
    ne pas manquer nos  
    conseils premium !
    """)

# ========== FAQ RAPIDE ==========
st.markdown("---")
st.markdown("## ❓ Questions fréquentes")

with st.expander("📧 Je n'ai pas reçu l'email de confirmation ?"):
    st.markdown("""
    **Vérifiez ces 3 endroits :**
    
    1. ✅ Votre boîte de réception principale
    2. ✅ Le dossier **Spam / Courrier indésirable**
    3. ✅ Le dossier **Promotions** (Gmail)
    
    **Toujours rien ?**
    
    Contactez-nous à support@architecte-ia.fr avec votre email de paiement.
    Nous réactivons manuellement votre compte sous 24h.
    """)

with st.expander("🔑 Comment me connecter ?"):
    st.markdown("""
    **Connexion simple :**
    
    1. Cliquez sur le bouton bleu "Me connecter" en haut de cette page
    2. Entrez l'email utilisé lors du paiement
    3. C'est tout ! Pas de mot de passe nécessaire
    
    Votre clé d'accès unique a été générée automatiquement.
    """)

with st.expander("📊 Mes analyses sont-elles vraiment illimitées ?"):
    st.markdown("""
    **Oui, 100% illimité !**
    
    ✅ Autant d'analyses que vous voulez  
    ✅ Aucune restriction de fréquence  
    ✅ Accès aux 3 dashboards sans limite  
    ✅ Export PDF illimité  
    
    Fini la limite de 10 analyses/semaine de la version gratuite.
    """)

with st.expander("💰 Comment annuler mon abonnement ?"):
    st.markdown("""
    **Annulation en 2 clics :**
    
    1. Connectez-vous à votre compte
    2. Allez dans **Paramètres** → **Abonnement**
    3. Cliquez sur **Annuler l'abonnement**
    
    **Ou par email :**
    
    Envoyez-nous un simple email à support@architecte-ia.fr  
    Nous annulons sous 24h.
    
    **Important :** Vous gardez l'accès jusqu'à la fin de votre période payée.
    """)

with st.expander("🔄 Garantie satisfait ou remboursé ?"):
    st.markdown("""
    **Oui, 7 jours garantis !**
    
    Si vous n'êtes pas satisfait dans les **7 premiers jours**,  
    contactez-nous et nous vous remboursons **intégralement**.
    
    Aucune question posée.
    
    📧 support@architecte-ia.fr
    """)

# ========== CTA FINAL ==========
st.markdown("---")

st.markdown("""
<div style='background: linear-gradient(135deg, #F56400 0%, #ff8c42 100%); 
            padding: 3rem 2rem; border-radius: 15px; 
            text-align: center; color: white; margin: 2rem 0;'>
    <h2 style='margin-top: 0;'>🎉 Prêt à optimiser votre boutique Etsy ?</h2>
    <p style='font-size: 1.2rem; margin: 20px 0;'>
        Vos dashboards premium vous attendent
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🚀 Accéder à mon tableau de bord", type="primary", use_container_width=True):
        st.markdown("""
        <meta http-equiv="refresh" content="0;url=/dashboard">
        """, unsafe_allow_html=True)

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Etsy Analytics Pro</strong> - Version 2.0 Premium</p>
    <p>💎 Créé par <a href="https://architecte-ia.fr">Architecte IA</a></p>
    <p style='font-size: 0.9em;'>
        <a href="https://architecte-ia.fr/cgu">CGU</a> • 
        <a href="https://architecte-ia.fr/privacy">Confidentialité</a> • 
        <a href="mailto:support@architecte-ia.fr">Support</a>
    </p>
    <p style='margin-top: 1.5rem; font-size: 0.85rem; opacity: 0.7;'>
        © 2025 Architecte IA - Tous droits réservés
    </p>
</div>
""", unsafe_allow_html=True)