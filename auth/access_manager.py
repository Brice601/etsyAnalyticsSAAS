import streamlit as st
from datetime import datetime

# 🔥 MODE DEBUG : Affiche les étapes de connexion
DEBUG_MODE = False  # ACTIVÉ pour diagnostic

# Configuration des dashboards par produit
DASHBOARD_ACCESS = {
    'starter': ['finance_pro'],
    'bundle': ['finance_pro', 'customer_intelligence', 'seo_analyzer'],
    'finance': ['finance_pro'],
    'marketing': ['customer_intelligence'],
    'operations': ['seo_analyzer']
}

# Noms lisibles des dashboards
DASHBOARD_NAMES = {
    'finance_pro': 'Finance Pro',
    'customer_intelligence': 'Customer Intelligence',
    'seo_analyzer': 'SEO Analyzer'
}


def debug_log(message):
    """Affiche un message de debug si DEBUG_MODE est activé"""
    if DEBUG_MODE:
        st.sidebar.info(f"🛠 DEBUG: {message}")


def get_supabase_client():
    """Initialise et retourne le client Supabase"""
    debug_log("Tentative de connexion à Supabase...")
    
    try:
        # Vérifier que les secrets existent
        if "supabase" not in st.secrets:
            st.error("❌ Secrets Supabase non configurés dans Streamlit Cloud")
            st.info("Allez dans Settings > Secrets et ajoutez :\n```toml\n[supabase]\nurl = \"...\"\nkey = \"...\"\n```")
            debug_log("Secrets Supabase manquants")
            return None
        
        debug_log("Secrets Supabase trouvés")
        
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        # Masquer la clé pour la sécurité
        masked_key = key[:20] + "..." if len(key) > 20 else "***"
        debug_log(f"URL: {url}")
        debug_log(f"Key: {masked_key}")
        
        # Import Supabase
        try:
            from supabase import create_client
            debug_log("Module supabase importé avec succès")
        except ImportError as e:
            st.error("❌ Module 'supabase' non trouvé")
            st.info("Vérifiez que 'supabase>=2.7.0' est dans requirements.txt")
            debug_log(f"Erreur import supabase: {e}")
            return None
        
        # Créer le client
        debug_log("Création du client Supabase...")
        client = create_client(url, key)
        debug_log("✅ Client Supabase créé avec succès")
        
        # PAS DE TEST DE CONNEXION ICI
        # Le test sera fait lors de la première vraie requête
        
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
        - [Acheter le dashboard Finance - 29€](https://buy.stripe.com/starter)
        - [Acheter le Growth Bundle - 67€](https://buy.stripe.com/bundle) ⭐ Recommandé
        
        ---
        
        **🧪 MODE TEST :**
        Ajoutez `?key=VOTRE_CLE` à l'URL
        
        Exemple : `https://votre-app.streamlit.app/?key=test123`
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
        
        # 🔥 CORRECTION : Utiliser .execute() sans .data d'abord
        response = supabase.table('customers') \
            .select('*') \
            .eq('access_key', access_key) \
            .execute()
        
        debug_log(f"Réponse brute: {response}")
        
        # Vérifier si response.data existe et contient des données
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
            - [Starter Pack - 29€](https://buy.stripe.com/starter)
            - [Growth Bundle - 67€](https://buy.stripe.com/bundle)
            """)
            st.stop()
        
        # Récupérer les infos client
        user_info = response.data[0]
        user_info['access_key'] = access_key
        
        debug_log(f"✅ Utilisateur trouvé: {user_info.get('email')} - Produit: {user_info.get('product')}")
        
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
            # Ne pas bloquer si la mise à jour échoue
        
        # Sauvegarder dans session_state
        st.session_state['access_key'] = access_key
        st.session_state['user_info'] = user_info
        
        debug_log("=== CHECK_ACCESS TERMINÉ AVEC SUCCÈS ===")
        
        return user_info
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la vérification d'accès")
        st.code(str(e))
        debug_log(f"❌ Erreur dans check_access: {e}")
        
        # Afficher plus d'infos en mode debug
        if DEBUG_MODE:
            import traceback
            st.code(traceback.format_exc())
        
        st.info("💡 Si le problème persiste, contactez le support : support@architecte-ia.fr")
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


def has_access_to_dashboard(access_key, dashboard_id):
    """
    Vérifie si un utilisateur a accès à un dashboard spécifique.
    """
    debug_log(f"Vérification accès au dashboard '{dashboard_id}' pour clé {access_key}")
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            debug_log("Pas de connexion Supabase")
            return False
        
        response = supabase.table('customers') \
            .select('product') \
            .eq('access_key', access_key) \
            .execute()
        
        if not response.data:
            debug_log("Utilisateur non trouvé")
            return False
        
        user_product = response.data[0].get('product', 'starter')
        allowed_dashboards = DASHBOARD_ACCESS.get(user_product, [])
        
        has_access = dashboard_id in allowed_dashboards
        debug_log(f"Produit: {user_product} - Accès au dashboard: {has_access}")
        
        return has_access
        
    except Exception as e:
        st.warning(f"⚠️ Erreur vérification accès : {e}")
        debug_log(f"Erreur has_access_to_dashboard: {e}")
        return False


def get_user_dashboards(access_key):
    """Retourne la liste des dashboards accessibles pour un utilisateur."""
    debug_log(f"Récupération dashboards pour clé {access_key}")
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return []
        
        response = supabase.table('customers') \
            .select('product') \
            .eq('access_key', access_key) \
            .execute()
        
        if not response.data:
            return []
        
        user_product = response.data[0].get('product', 'starter')
        dashboards = DASHBOARD_ACCESS.get(user_product, [])
        
        debug_log(f"Produit: {user_product} - Dashboards: {dashboards}")
        
        return dashboards
        
    except Exception as e:
        st.warning(f"⚠️ Erreur récupération dashboards : {e}")
        debug_log(f"Erreur get_user_dashboards: {e}")
        return []


def show_upgrade_message(dashboard_id, current_product):
    """Affiche un message d'upgrade si l'utilisateur n'a pas accès au dashboard."""
    dashboard_name = DASHBOARD_NAMES.get(dashboard_id, dashboard_id)
    
    st.error(f"❌ Accès refusé au dashboard : {dashboard_name}")
    
    if current_product in ['starter', 'finance', 'marketing', 'operations']:
        st.markdown(f"""
        ### 🔒 Dashboard réservé au Growth Bundle
        
        Le dashboard **{dashboard_name}** est disponible uniquement avec le **Growth Bundle**.
        
        **Vous avez actuellement : {current_product.title()}**
        
        #### 🎁 Passez au Growth Bundle pour débloquer :
        
        ✅ **Tous les dashboards (3)**
        ✅ **Accès IA en avant-première**  
        ✅ **Support prioritaire**  
        ✅ **Mises à jour gratuites**
        
        ---
        
        💰 **Prix upgrade : 38€ seulement**  
        (au lieu de 67€ - vous économisez 29€)
        
        [🔥 Upgrader maintenant](https://buy.stripe.com/upgrade)
        
        ---
        
        **Questions ?** Contactez-nous : support@architecte-ia.fr
        """)
    
    st.stop()


def get_user_consent(email):
    """
    Récupère le statut de consentement d'un utilisateur.
    ✅ CORRIGÉ : Retourne None si jamais demandé, True/False sinon
    """
    debug_log(f"Récupération consentement pour {email}")
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return None  # ✅ Retourner None au lieu de False
        
        response = supabase.table('customers') \
            .select('data_consent') \
            .eq('email', email) \
            .execute()
        
        if response.data:
            # ✅ IMPORTANT : Distinguer "pas de consentement" de "jamais demandé"
            consent = response.data[0].get('data_consent')
            
            # Si consent est None, l'utilisateur n'a jamais été sollicité
            # Si consent est False, l'utilisateur a refusé
            # Si consent est True, l'utilisateur a accepté
            
            debug_log(f"Consentement: {consent}")
            return consent  # Peut être None, True ou False
        
        debug_log("Utilisateur non trouvé")
        return None  # ✅ Retourner None au lieu de False
        
    except Exception as e:
        st.warning(f"⚠️ Erreur récupération consentement : {e}")
        debug_log(f"Erreur get_user_consent: {e}")
        return None  # ✅ Retourner None au lieu de False