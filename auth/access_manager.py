import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# Configuration des dashboards par produit
DASHBOARD_ACCESS = {
    'starter': ['finance_pro'],
    'bundle': ['finance_pro', 'customer_intelligence', 'seo_analyzer']
}

# Noms lisibles des dashboards
DASHBOARD_NAMES = {
    'finance_pro': 'Finance Pro',
    'customer_intelligence': 'Customer Intelligence',
    'seo_analyzer': 'SEO Analyzer'
}


def get_supabase_client() -> Client:
    """Initialise et retourne le client Supabase"""
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )


def check_access():
    """
    Vérifie si l'utilisateur a un accès valide via la clé dans l'URL ou session_state.
    Retourne les informations utilisateur si valide, sinon arrête l'exécution.
    """
    # D'abord vérifier session_state (navigation interne)
    if 'access_key' in st.session_state and st.session_state['access_key']:
        access_key = st.session_state['access_key']
    else:
        # Sinon récupérer le paramètre 'key' de l'URL (accès initial)
        params = st.query_params
        access_key = params.get("key", None)
    
    # Si pas de clé, afficher message d'erreur et arrêter
    if not access_key:
        st.error("❌ Accès non autorisé - Clé manquante")
        st.markdown("""
        ### 🔒 Accès réservé aux clients
        
        Pour accéder à Etsy Analytics Pro, vous devez disposer d'une clé d'accès valide.
        
        **Vous êtes client ?**
        - Vérifiez l'email reçu après votre achat
        - Cliquez sur le lien d'accès unique fourni
        
        **Pas encore client ?**
        - [Acheter le Starter Pack - 29€](https://buy.stripe.com/starter)
        - [Acheter le Growth Bundle - 67€](https://buy.stripe.com/bundle) ⭐ Recommandé
        
        ---
        
        ✅ Accès immédiat après paiement  
        ✅ 30 jours satisfait ou remboursé  
        ✅ Support email inclus
        """)
        st.stop()
    
    # Connexion Supabase
    try:
        supabase = get_supabase_client()
        
        # Requête pour vérifier la clé
        response = supabase.table('customers').select('*').eq('access_key', access_key).execute()
        
        # Si pas de résultat
        if not response.data or len(response.data) == 0:
            st.error("❌ Clé d'accès invalide")
            st.markdown("""
            ### 🔒 Clé d'accès non reconnue
            
            La clé d'accès fournie n'est pas valide ou a expiré.
            
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
        
        # Mettre à jour la dernière connexion
        supabase.table('customers').update({
            'last_login': datetime.now().isoformat()
        }).eq('access_key', access_key).execute()
        
        # Sauvegarder dans session_state
        st.session_state['access_key'] = access_key
        st.session_state['user_info'] = user_info
        
        return user_info
        
    except Exception as e:
        st.error(f"❌ Erreur de connexion : {e}")
        st.stop()


def save_consent(email, consent_value):
    """Sauvegarde le consentement de l'utilisateur dans Supabase"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table('customers').update({
            'data_consent': consent_value
        }).eq('email', email).execute()
        
        return True
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde du consentement : {e}")
        return False


def has_access_to_dashboard(access_key, dashboard_id):
    """
    Vérifie si un utilisateur a accès à un dashboard spécifique.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('customers').select('product').eq('access_key', access_key).execute()
        
        if not response.data:
            return False
        
        user_product = response.data[0].get('product', 'starter')
        allowed_dashboards = DASHBOARD_ACCESS.get(user_product, [])
        
        return dashboard_id in allowed_dashboards
        
    except Exception as e:
        st.warning(f"⚠️ Erreur vérification accès : {e}")
        return False


def get_user_dashboards(access_key):
    """Retourne la liste des dashboards accessibles pour un utilisateur."""
    try:
        supabase = get_supabase_client()
        response = supabase.table('customers').select('product').eq('access_key', access_key).execute()
        
        if not response.data:
            return []
        
        user_product = response.data[0].get('product', 'starter')
        return DASHBOARD_ACCESS.get(user_product, [])
        
    except Exception as e:
        st.warning(f"⚠️ Erreur récupération dashboards : {e}")
        return []


def show_upgrade_message(dashboard_id, current_product):
    """Affiche un message d'upgrade si l'utilisateur n'a pas accès au dashboard."""
    dashboard_name = DASHBOARD_NAMES.get(dashboard_id, dashboard_id)
    
    st.error(f"❌ Accès refusé au dashboard : {dashboard_name}")
    
    if current_product == 'starter':
        st.markdown(f"""
        ### 🔒 Dashboard réservé au Growth Bundle
        
        Le dashboard **{dashboard_name}** est disponible uniquement avec le **Growth Bundle**.
        
        **Vous avez actuellement : Starter Pack**
        
        #### 🎁 Passez au Growth Bundle pour débloquer :
        
        ✅ **Customer Intelligence** - Comprenez vos clients  
        ✅ **SEO Analyzer** - Optimisez votre visibilité  
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


def display_user_badge(user_info):
    """Affiche un badge avec les informations utilisateur dans la sidebar."""
    product_name = "Starter Pack" if user_info['product'] == 'starter' else "Growth Bundle"
    product_emoji = "🥉" if user_info['product'] == 'starter' else "🏆"
    
    st.sidebar.markdown(f"""
    ---
    ### {product_emoji} Votre Abonnement
    
    **Email :** {user_info['email']}  
    **Pack :** {product_name}
    
    ---
    """)
    
    # Afficher les dashboards accessibles
    accessible_dashboards = get_user_dashboards(user_info['access_key'])
    
    st.sidebar.markdown("**Vos dashboards :**")
    for dashboard_id in accessible_dashboards:
        dashboard_name = DASHBOARD_NAMES.get(dashboard_id, dashboard_id)
        st.sidebar.markdown(f"✅ {dashboard_name}")
    
    # Bouton upgrade si Starter
    if user_info['product'] == 'starter':
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Débloquez tous les dashboards !**")
        if st.sidebar.button("⬆️ Upgrader vers Bundle", type="primary"):
            st.sidebar.info("🔥 Passez au Growth Bundle pour 38€ !")
            st.sidebar.markdown("[Upgrader maintenant](https://buy.stripe.com/upgrade)")


def get_user_consent(email):
    """Récupère le statut de consentement d'un utilisateur."""
    try:
        supabase = get_supabase_client()
        response = supabase.table('customers').select('data_consent').eq('email', email).execute()
        
        if response.data:
            return response.data[0].get('data_consent', False)
        
        return False
        
    except Exception as e:
        st.warning(f"⚠️ Erreur récupération consentement : {e}")
        return False