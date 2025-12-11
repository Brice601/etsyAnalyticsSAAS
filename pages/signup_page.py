import streamlit as st
import re
import hashlib
from datetime import datetime
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration de la page
st.set_page_config(
    page_title="Inscription - Etsy Analytics Pro",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Styles CSS personnalisés
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #F56400;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .benefit-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .consent-box {
        background-color: #e7f3ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin: 2rem 0;
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
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
    </style>
""", unsafe_allow_html=True)

def get_supabase_client():
    """Initialise le client Supabase"""
    try:
        if "supabase" not in st.secrets:
            return None
        
        from supabase import create_client
        
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        return create_client(url, key)
        
    except Exception as e:
        st.error(f"❌ Erreur connexion Supabase: {e}")
        return None


def validate_email(email):
    """Valide le format de l'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def check_email_exists(email):
    """Vérifie si l'email existe déjà"""
    supabase = get_supabase_client()
    
    if supabase is None:
        return False
    
    try:
        response = supabase.table('customers').select('id').eq('email', email).execute()
        return len(response.data) > 0
    except:
        return False


def generate_access_key():
    """Génère une clé d'accès unique"""
    import uuid
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()


def create_customer(email, shop_name):
    """Crée un nouveau customer dans Supabase"""
    supabase = get_supabase_client()
    
    if supabase is None:
        return None, "Erreur de connexion à la base de données"
    
    try:
        # Générer access_key
        access_key = generate_access_key()
        
        # Créer le customer
        customer_data = {
            'email': email.lower().strip(),
            'shop_name': shop_name.strip(),
            'access_key': access_key,
            'data_consent': True,  # Obligatoire
            'consent_updated_at': datetime.now().isoformat(),
            'signup_date': datetime.now().isoformat(),
            'usage_count': 0,
            'usage_reset_date': datetime.now().isoformat(),
            'is_email_verified': False
        }
        
        response = supabase.table('customers').insert(customer_data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0], None
        else:
            return None, "Erreur lors de la création du compte"
        
    except Exception as e:
        return None, f"Erreur: {str(e)}"


# ========== HEADER ==========
st.markdown('<p class="main-header">🚀 Bienvenue sur Etsy Analytics Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Créez votre compte gratuit en 30 secondes</p>', unsafe_allow_html=True)

# ========== BÉNÉFICES ==========
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="benefit-box">
        <h3 style='margin-top: 0;'>💰 Finance Pro</h3>
        <p>Calculez vos marges réelles produit par produit</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="benefit-box">
        <h3 style='margin-top: 0;'>👥 Customer Intelligence</h3>
        <p>Comprenez vos clients et fidélisez-les</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="benefit-box">
        <h3 style='margin-top: 0;'>🔍 SEO Analyzer</h3>
        <p>Optimisez votre visibilité Etsy</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== FORMULAIRE D'INSCRIPTION ==========
st.markdown("## 📝 Créer votre compte gratuit")

with st.form("signup_form"):
    
    # Email
    email = st.text_input(
        "📧 Email pro*",
        placeholder="votre.email@example.com",
        help="Nous utiliserons cet email pour vous contacter et vous envoyer vos analyses"
    )
    
    # Nom de la boutique
    shop_name = st.text_input(
        "🏪 Nom de votre boutique Etsy *",
        placeholder="MaBoutiqueEtsy",
        help="Le nom exact de votre boutique sur Etsy (nous pourrons vérifier son activité)"
    )
    
    st.markdown("---")
    
    # Consentement data - OBLIGATOIRE
    st.markdown("""
    <div class="consent-box">
        <h3>🤝 Consentement de collecte de données (OBLIGATOIRE)</h3>
        <p>
        Pour utiliser Etsy Analytics Pro <strong>gratuitement</strong>, nous avons besoin de collecter 
        vos données de ventes de manière anonymisée pour améliorer notre IA.
        </p>
        <p><strong>Ce que nous collectons :</strong></p>
        <ul>
            <li>✅ Vos données de ventes Etsy (anonymisées par hash)</li>
            <li>✅ Métriques de performance (CA, marges, etc.)</li>
            <li>✅ Catégories de produits</li>
        </ul>
        <p><strong>Ce que nous ne collectons JAMAIS :</strong></p>
        <ul>
            <li>❌ Noms de vos clients</li>
            <li>❌ Adresses emails de vos clients</li>
            <li>❌ Informations personnelles identifiables</li>
        </ul>
        <p><strong>En échange :</strong></p>
        <ul>
            <li>🎁 Accès gratuit aux 3 dashboards</li>
            <li>🎁 10 analyses par semaine</li>
            <li>🎁 Accès anticipé aux nouvelles fonctionnalités IA</li>
        </ul>
        <p style='font-size: 0.9em; color: #666;'>
        <em>Les données sont traitées uniquement par notre algorithme IA. 
        Elles ne sont ni revendues, ni partagées avec des tiers.</em>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    consent = st.checkbox(
        "✅ J'accepte que mes données soient collectées de manière anonyme pour améliorer l'outil",
        value=False
    )
    
    st.markdown("---")
    
    # Bouton d'inscription
    submitted = st.form_submit_button("🚀 Créer mon compte gratuit", type="primary", use_container_width=True)
    
    if submitted:
        # Validation
        errors = []
        
        if not email or not email.strip():
            errors.append("❌ L'email est obligatoire")
        elif not validate_email(email):
            errors.append("❌ Format d'email invalide")
        elif check_email_exists(email):
            errors.append("❌ Cet email est déjà utilisé")
        
        if not shop_name or not shop_name.strip():
            errors.append("❌ Le nom de la boutique est obligatoire")
        elif len(shop_name.strip()) < 3:
            errors.append("❌ Le nom de la boutique doit faire au moins 3 caractères")
        
        if not consent:
            errors.append("❌ Vous devez accepter la collecte de données pour utiliser l'outil gratuitement")
        
        # Afficher les erreurs
        if errors:
            for error in errors:
                st.markdown(f"""
                <div class="error-box">
                    {error}
                </div>
                """, unsafe_allow_html=True)
            
            if not consent:
                st.markdown("""
                <div class="warning-box">
                    <strong>⚠️ Consentement obligatoire</strong><br>
                    Sans consentement, nous ne pouvons pas vous offrir l'accès gratuit.<br>
                    Si vous ne souhaitez pas partager vos données, d'autres outils payants existent.
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Créer le compte
            with st.spinner("🔄 Création de votre compte..."):
                customer, error = create_customer(email, shop_name)
                
                if error:
                    st.markdown(f"""
                    <div class="error-box">
                        ❌ <strong>Erreur :</strong> {error}
                    </div>
                    """, unsafe_allow_html=True)
                
                elif customer:
                    # Succès !
                    st.markdown("""
                    <div class="success-box">
                        ✅ <strong>Compte créé avec succès !</strong><br>
                        Vous allez être redirigé vers votre tableau de bord...
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Sauvegarder dans session state
                    st.session_state['access_key'] = customer['access_key']
                    st.session_state['user_info'] = customer
                    st.session_state['just_signed_up'] = True
                    
                    # Redirection vers dashboard
                    st.success("🎉 Bienvenue ! Redirection en cours...")
                    st.markdown(f"""
                    <script>
                        setTimeout(function() {{
                            window.location.href = "/dashboard?key={customer['access_key']}";
                        }}, 2000);
                    </script>
                    """, unsafe_allow_html=True)
                    
                    # Bouton manuel si JS ne fonctionne pas
                    st.markdown(f"""
                    <a href="/dashboard?key={customer['access_key']}" target="_self" 
                       style="display: block; background: #28a745; color: white; 
                              padding: 15px; border-radius: 10px; text-align: center; 
                              font-weight: bold; font-size: 1.2rem; text-decoration: none; 
                              margin-top: 20px;">
                        ➡️ Accéder à mon tableau de bord
                    </a>
                    """, unsafe_allow_html=True)

# ========== ALTERNATIVE ==========
st.markdown("---")
st.markdown("### 🔐 Vous avez déjà un compte ?")

col1, col2 = st.columns([3, 1])

with col1:
    login_email = st.text_input(
        "Entrez votre email pro",
        placeholder="votre.email@example.com",
        key="login_email"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔑 Se connecter", use_container_width=True):
        if login_email and validate_email(login_email):
            supabase = get_supabase_client()
            
            if supabase:
                try:
                    response = supabase.table('customers').select('*').eq('email', login_email.lower().strip()).execute()
                    
                    if response.data and len(response.data) > 0:
                        customer = response.data[0]
                        
                        # Vérifier consentement
                        if not customer.get('data_consent', False):
                            st.error("""
                            ❌ Votre compte n'a pas donné son consentement de données.
                            
                            Pour réactiver votre compte, vous devez accepter la collecte de données.
                            """)
                        else:
                            st.session_state['access_key'] = customer['access_key']
                            st.session_state['user_info'] = customer
                            
                            st.success("✅ Connexion réussie ! Redirection...")
                            
                            st.markdown(f"""
                            <script>
                                setTimeout(function() {{
                                    window.location.href = "/dashboard?key={customer['access_key']}";
                                }}, 1500);
                            </script>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <a href="/dashboard?key={customer['access_key']}" target="_self" 
                               style="display: block; background: #007bff; color: white; 
                                      padding: 15px; border-radius: 10px; text-align: center; 
                                      font-weight: bold; text-decoration: none; margin-top: 20px;">
                                ➡️ Accéder à mon tableau de bord
                            </a>
                            """, unsafe_allow_html=True)
                    else:
                        st.error("❌ Aucun compte trouvé avec cet email")
                        st.info("💡 Créez un compte ci-dessus si vous êtes nouveau")
                
                except Exception as e:
                    st.error(f"❌ Erreur de connexion : {e}")
        else:
            st.error("❌ Email invalide")

# ========== FAQ ==========
st.markdown("---")
st.markdown("## ❓ Questions fréquentes")

with st.expander("🔒 Mes données sont-elles sécurisées ?"):
    st.markdown("""
    **Oui, absolument.**
    
    - Vos données sont **anonymisées** (hash de votre email)
    - Nous ne stockons **aucune information client** (noms, emails de vos clients)
    - Les fichiers sont stockés sur des serveurs **sécurisés** (Supabase)
    - Nous ne **revendons jamais** vos données
    - Conformité **RGPD**
    """)

with st.expander("📊 Que faites-vous exactement avec mes données ?"):
    st.markdown("""
    Nous utilisons vos données **uniquement** pour :
    
    1. **Entraîner notre IA** pour générer de meilleures recommandations
    2. **Créer des benchmarks sectoriels** (comparaisons anonymisées)
    3. **Améliorer l'outil** (nouvelles fonctionnalités)
    
    **Ce que nous ne faisons JAMAIS :**
    - Revendre vos données
    - Partager avec des tiers
    - Contacter vos clients
    - Utiliser vos données à des fins marketing externes
    """)

with st.expander("💰 Pourquoi c'est gratuit ?"):
    st.markdown("""
    **Modèle freemium :**
    
    - **Gratuit** : Accès aux 3 dashboards + 10 analyses/semaine
    - **Insights Premium (9€/mois)** : Analyses illimitées + Recommandations IA + Export PDF
    
    En acceptant de partager vos données anonymisées, vous nous aidez à améliorer l'outil 
    et nous pouvons vous offrir l'accès gratuit en échange.
    """)

with st.expander("🔄 Puis-je retirer mon consentement ?"):
    st.markdown("""
    **Non, pas pour le moment.**
    
    Le consentement est obligatoire pour utiliser la version gratuite. 
    
    Si vous retirez votre consentement, vous perdrez l'accès à l'outil.
    
    **Alternative :** Passez à Insights Premium (9€/mois) qui ne nécessite pas de collecte de données 
    (nous pouvons supprimer cette exigence car vous payez pour le service).
    """)

with st.expander("⏱️ Pourquoi limiter à 10 analyses/semaine ?"):
    st.markdown("""
    **Pour éviter les abus** et garantir une bonne expérience à tous.
    
    10 analyses/semaine est largement suffisant pour :
    - Analyser vos ventes une fois par semaine
    - Tester différentes périodes
    - Optimiser vos listings progressivement
    
    Si vous avez besoin de plus, **Insights Premium (9€/mois)** offre des analyses illimitées.
    """)

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