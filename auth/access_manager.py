import streamlit as st
from datetime import datetime

# 🔥 MODE DEBUG : Affiche les étapes de connexion
DEBUG_MODE = False  # Mettre à True pour diagnostic

# Configuration des dashboards par produit
DASHBOARD_ACCESS = {
    'finance': ['finance_pro'],
    'customer': ['customer_intelligence'],
    'seo': ['seo_analyzer']
}

# Noms lisibles des dashboards
DASHBOARD_NAMES = {
    'finance_pro': 'Finance Pro',
    'customer_intelligence': 'Customer Intelligence',
    'seo_analyzer': 'SEO Analyzer'
}

# Liens d'achat Stripe par dashboard
PURCHASE_LINKS = {
    'finance_pro': 'https://buy.stripe.com/5kQ28t5TreeMdbi9Qp7IY03',
    'customer_intelligence': 'https://buy.stripe.com/9B600l3Lj3A82wEfaJ7IY02',
    'seo_analyzer': 'https://buy.stripe.com/5kQ6oJ4Pn4Ec0owfaJ7IY01',
    'bundle': 'https://buy.stripe.com/8x2bJ33Ljb2Ac7e2nX7IY00'
}


def debug_log(message):
    """Affiche un message de debug si DEBUG_MODE est activé"""
    if DEBUG_MODE:
        st.sidebar.info(f"🛠 DEBUG: {message}")


def get_supabase_client():
    """Initialise et retourne le client Supabase"""
    debug_log("Tentative de connexion à Supabase...")
    
    try:
        if "supabase" not in st.secrets:
            st.error("❌ Secrets Supabase non configurés dans Streamlit Cloud")
            st.info("Allez dans Settings > Secrets et ajoutez :\n```toml\n[supabase]\nurl = \"...\"\nkey = \"...\"\n```")
            debug_log("Secrets Supabase manquants")
            return None
        
        debug_log("Secrets Supabase trouvés")
        
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        masked_key = key[:20] + "..." if len(key) > 20 else "***"
        debug_log(f"URL: {url}")
        debug_log(f"Key: {masked_key}")
        
        try:
            from supabase import create_client
            debug_log("Module supabase importé avec succès")
        except ImportError as e:
            st.error("❌ Module 'supabase' non trouvé")
            st.info("Vérifiez que 'supabase>=2.7.0' est dans requirements.txt")
            debug_log(f"Erreur import supabase: {e}")
            return None
        
        debug_log("Création du client Supabase...")
        client = create_client(url, key)
        debug_log("✅ Client Supabase créé avec succès")
        
        return client
        
    except Exception as e:
        st.error(f"❌ Erreur initialisation Supabase")
        st.code(str(e))
        debug_log(f"Erreur générale: {e}")
        return None


def check_access():
    """
    Vérifie si l'utilisateur a un accès valide via la clé dans l'URL ou session_state.
    Retourne les informations utilisateur si valide, sinon arrête l'exécution.
    """
    debug_log("=== DÉBUT CHECK_ACCESS ===")
    
    # D'abord vérifier session_state (navigation interne)
    if 'access_key' in st.session_state and st.session_state['access_key']:
        access_key = st.session_state['access_key']
        debug_log(f"Clé trouvée dans session_state: {access_key}")
    else:
        # Sinon récupérer le paramètre 'key' de l'URL (accès initial)
        params = st.query_params
        access_key = params.get("key", None)
        debug_log(f"Clé trouvée dans URL: {access_key}")
    
    # Si pas de clé, afficher message d'erreur et arrêter
    if not access_key:
        debug_log("Aucune clé d'accès fournie")
        st.error("❌ Accès non autorisé - Clé manquante")
        st.markdown("""
        ### 🔒 Accès réservé aux clients
        
        Pour accéder à Etsy Analytics Pro, vous devez disposer d'une clé d'accès valide.
        
        **Vous êtes client ?**
        - Vérifiez l'email reçu après votre achat
        - Cliquez sur le lien d'accès unique fourni
        
        **Pas encore client ?**
        - [Finance Pro - 29€](https://buy.stripe.com/5kQ28t5TreeMdbi9Qp7IY03)
        - [Customer Intelligence - 29€](https://buy.stripe.com/9B600l3Lj3A82wEfaJ7IY02)
        - [SEO Analyzer - 29€](https://buy.stripe.com/5kQ6oJ4Pn4Ec0owfaJ7IY01)
        - [Growth Bundle - 67€](https://buy.stripe.com/8x2bJ33Ljb2Ac7e2nX7IY00) ⭐ Pack complet
        
        ---
        
        **🧪 MODE TEST :**
        Ajoutez `?key=VOTRE_CLE` à l'URL
        """)
        st.stop()
    
    # Connexion Supabase
    debug_log("Tentative de connexion à Supabase...")
    supabase = get_supabase_client()
    
    if supabase is None:
        st.error("❌ Impossible de se connecter à la base de données")
        debug_log("Échec connexion Supabase")
        st.stop()
    
    debug_log("Connexion Supabase OK")
    
    try:
        # Requête pour vérifier la clé
        debug_log(f"Recherche de la clé '{access_key}' dans la table customers...")
        
        response = supabase.table('customers') \
            .select('*') \
            .eq('access_key', access_key) \
            .execute()
        
        debug_log(f"Réponse brute: {response}")
        
        if not hasattr(response, 'data') or not response.data or len(response.data) == 0:
            debug_log("Clé d'accès non trouvée dans la base")
            st.error("❌ Clé d'accès invalide")
            st.markdown(f"""
            ### 🔒 Clé d'accès non reconnue
            
            La clé `{access_key}` n'est pas valide ou a expiré.
            
            **Solutions :**
            - Vérifiez que vous avez copié le lien complet depuis votre email
            - Contactez le support si le problème persiste : support@architecte-ia.fr
            
            **Acheter un accès :**
            - [Finance Pro - 29€](https://buy.stripe.com/5kQ28t5TreeMdbi9Qp7IY03)
            - [Customer Intelligence - 29€](https://buy.stripe.com/9B600l3Lj3A82wEfaJ7IY02)
            - [SEO Analyzer - 29€](https://buy.stripe.com/5kQ6oJ4Pn4Ec0owfaJ7IY01)
            - [Growth Bundle - 67€](https://buy.stripe.com/8x2bJ33Ljb2Ac7e2nX7IY00)
            """)
            st.stop()
        
        # Récupérer les infos client
        user_info = response.data[0]
        user_info['access_key'] = access_key
        
        debug_log(f"✅ Utilisateur trouvé: {user_info.get('email')}")
        
        # Mettre à jour la dernière connexion
        debug_log("Mise à jour last_login...")
        try:
            update_response = supabase.table('customers') \
                .update({'last_login': datetime.now().isoformat()}) \
                .eq('access_key', access_key) \
                .execute()
            debug_log("✅ last_login mis à jour")
        except Exception as update_error:
            debug_log(f"⚠️ Erreur mise à jour last_login: {update_error}")
        
        # Sauvegarder dans session_state
        st.session_state['access_key'] = access_key
        st.session_state['user_info'] = user_info
        
        debug_log("=== CHECK_ACCESS TERMINÉ AVEC SUCCÈS ===")
        
        return user_info
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la vérification d'accès")
        st.code(str(e))
        debug_log(f"❌ Erreur dans check_access: {e}")
        
        if DEBUG_MODE:
            import traceback
            st.code(traceback.format_exc())
        
        st.info("💡 Si le problème persiste, contactez le support : support@architecte-ia.fr")
        st.stop()


def get_user_products(customer_id):
    """
    Retourne la liste des produits achetés par l'utilisateur.
    Retourne ['finance', 'customer', 'seo'] ou combinaisons
    """
    debug_log(f"Récupération produits pour customer_id: {customer_id}")
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return []
        
        response = supabase.table('customer_products') \
            .select('product_id') \
            .eq('customer_id', customer_id) \
            .execute()
        
        if not response.data:
            debug_log("Aucun produit trouvé")
            return []
        
        products = [p['product_id'] for p in response.data]
        debug_log(f"Produits trouvés: {products}")
        
        return products
        
    except Exception as e:
        st.warning(f"⚠️ Erreur récupération produits : {e}")
        debug_log(f"Erreur get_user_products: {e}")
        return []


def has_access_to_dashboard(customer_id, dashboard_id):
    """
    Vérifie si un utilisateur a accès à un dashboard spécifique.
    dashboard_id: 'finance_pro', 'customer_intelligence', 'seo_analyzer'
    """
    debug_log(f"Vérification accès au dashboard '{dashboard_id}' pour customer_id {customer_id}")
    
    user_products = get_user_products(customer_id)
    
    # Vérifier si l'utilisateur a le bundle (= accès à tout)
    if 'bundle' in user_products:
        debug_log("Utilisateur a le bundle → accès complet")
        return True
    
    # Vérifier chaque produit individuel
    for product_id, dashboards in DASHBOARD_ACCESS.items():
        if product_id in user_products and dashboard_id in dashboards:
            debug_log(f"Accès accordé via produit '{product_id}'")
            return True
    
    debug_log("Aucun accès trouvé")
    return False


def get_user_dashboards(customer_id):
    """
    Retourne la liste des dashboards accessibles pour un utilisateur.
    Retourne ['finance_pro', 'customer_intelligence', 'seo_analyzer'] ou combinaisons
    """
    debug_log(f"Récupération dashboards pour customer_id {customer_id}")
    
    user_products = get_user_products(customer_id)
    
    # Si l'utilisateur a le bundle, il a accès à tout
    if 'bundle' in user_products:
        all_dashboards = list(DASHBOARD_NAMES.keys())
        debug_log(f"Bundle détecté → tous les dashboards: {all_dashboards}")
        return all_dashboards
    
    # Sinon, récupérer les dashboards des produits individuels
    dashboards = []
    for product_id in user_products:
        if product_id in DASHBOARD_ACCESS:
            dashboards.extend(DASHBOARD_ACCESS[product_id])
    
    dashboards = list(set(dashboards))  # Éliminer les doublons
    debug_log(f"Dashboards accessibles: {dashboards}")
    
    return dashboards


def show_upgrade_message(dashboard_id, customer_id):
    """
    Affiche un message d'achat pour débloquer un dashboard.
    """
    dashboard_name = DASHBOARD_NAMES.get(dashboard_id, dashboard_id)
    user_products = get_user_products(customer_id)
    
    st.error(f"❌ Accès refusé au dashboard : {dashboard_name}")
    
    # Compter combien de dashboards l'utilisateur possède
    num_owned = len(user_products)
    
    if num_owned == 0:
        # Utilisateur sans produits (ne devrait pas arriver)
        st.markdown(f"""
        ### 🔒 Dashboard non disponible
        
        Vous n'avez pas encore de dashboard actif.
        
        [🛒 Acheter {dashboard_name} - 29€]({PURCHASE_LINKS.get(dashboard_id, '#')})
        
        ou
        
        [🎁 Growth Bundle - 67€]({PURCHASE_LINKS['bundle']}) (3 dashboards)
        """)
    
    elif num_owned == 1:
        # Utilisateur avec 1 dashboard
        st.markdown(f"""
        ### 🔒 Dashboard réservé
        
        Le dashboard **{dashboard_name}** n'est pas inclus dans votre pack actuel.
        
        #### Options :
        
        1️⃣ **Acheter ce dashboard** → [29€]({PURCHASE_LINKS.get(dashboard_id, '#')})
        
        2️⃣ **Growth Bundle complet** → [67€]({PURCHASE_LINKS['bundle']}) (3 dashboards - Meilleure offre !)
        """)
    
    elif num_owned == 2:
        # Utilisateur avec 2 dashboards
        st.markdown(f"""
        ### 🔒 Il ne vous manque plus qu'un dashboard !
        
        Vous avez déjà **2 dashboards**. Complétez votre collection !
        
        [🛒 Acheter {dashboard_name} - 29€]({PURCHASE_LINKS.get(dashboard_id, '#')})
        
        💡 **Vous aurez alors les 3 dashboards pour 87€ total**
        """)
    
    st.stop()


def save_consent(email, consent_value):
    """Sauvegarde le consentement de l'utilisateur"""
    debug_log(f"Sauvegarde consentement pour {email}: {consent_value}")
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            debug_log("Impossible de sauvegarder le consentement (pas de connexion)")
            return False
        
        response = supabase.table('customers') \
            .update({'data_consent': consent_value}) \
            .eq('email', email) \
            .execute()
        
        debug_log("Consentement sauvegardé avec succès")
        return True
    
    except Exception as e:
        st.warning(f"⚠️ Erreur lors de la sauvegarde du consentement : {e}")
        debug_log(f"Erreur sauvegarde consentement: {e}")
        return False


def get_user_consent(email):
    """
    Récupère le statut de consentement d'un utilisateur.
    Retourne None si jamais demandé, True/False sinon
    """
    debug_log(f"Récupération consentement pour {email}")
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return None
        
        response = supabase.table('customers') \
            .select('data_consent') \
            .eq('email', email) \
            .execute()
        
        if response.data:
            consent = response.data[0].get('data_consent')
            debug_log(f"Consentement: {consent}")
            return consent
        
        debug_log("Utilisateur non trouvé")
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Erreur récupération consentement : {e}")
        debug_log(f"Erreur get_user_consent: {e}")
        return None