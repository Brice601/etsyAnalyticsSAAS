import streamlit as st
from datetime import datetime

DEBUG_MODE = False

DASHBOARD_ACCESS = {
    'finance': ['finance_pro'],
    'customer': ['customer_intelligence'],
    'seo': ['seo_analyzer']
}

DASHBOARD_NAMES = {
    'finance_pro': 'Finance Pro',
    'customer_intelligence': 'Customer Intelligence',
    'seo_analyzer': 'SEO Analyzer'
}

PURCHASE_LINKS = {
    'finance_pro': 'https://buy.stripe.com/5kQ28t5TreeMdbi9Qp7IY03',
    'customer_intelligence': 'https://buy.stripe.com/9B600l3Lj3A82wEfaJ7IY02',
    'seo_analyzer': 'https://buy.stripe.com/5kQ6oJ4Pn4Ec0owfaJ7IY01',
    'bundle': 'https://buy.stripe.com/8x2bJ33Ljb2Ac7e2nX7IY00'
}


def get_supabase_client():
    try:
        if "supabase" not in st.secrets:
            st.error("❌ Secrets Supabase non configurés")
            return None
        
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        from supabase import create_client
        client = create_client(url, key)
        
        return client
        
    except Exception as e:
        st.error(f"❌ Erreur initialisation Supabase: {e}")
        return None


def check_access():
    if 'access_key' in st.session_state and st.session_state['access_key']:
        access_key = st.session_state['access_key']
    else:
        params = st.query_params
        access_key = params.get("key", None)
    
    if not access_key:
        st.error("❌ Accès non autorisé - Clé manquante")
        st.markdown("""
        ### 🔒 Accès réservé aux clients
        
        Pour accéder à Etsy Analytics Pro, vous devez disposer d'une clé d'accès valide.
        """)
        st.stop()
    
    supabase = get_supabase_client()
    
    if supabase is None:
        st.error("❌ Impossible de se connecter à la base de données")
        st.stop()
    
    try:
        response = supabase.table('customers') \
            .select('*') \
            .eq('access_key', access_key) \
            .execute()
        
        if not hasattr(response, 'data') or not response.data or len(response.data) == 0:
            st.error("❌ Clé d'accès invalide")
            st.stop()
        
        user_info = response.data[0]
        user_info['access_key'] = access_key
        
        try:
            supabase.table('customers') \
                .update({'last_login': datetime.now().isoformat()}) \
                .eq('access_key', access_key) \
                .execute()
        except:
            pass
        
        st.session_state['access_key'] = access_key
        st.session_state['user_info'] = user_info
        
        return user_info
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la vérification d'accès: {e}")
        st.stop()


def get_user_products(customer_id):
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return []
        
        response = supabase.table('customer_products') \
            .select('product_id') \
            .eq('customer_id', customer_id) \
            .execute()
        
        if not response.data:
            return []
        
        products = [p['product_id'] for p in response.data]
        return products
        
    except Exception as e:
        st.warning(f"⚠️ Erreur récupération produits : {e}")
        return []


def has_access_to_dashboard(customer_id, dashboard_id):
    user_products = get_user_products(customer_id)
    
    if 'bundle' in user_products:
        return True
    
    for product_id, dashboards in DASHBOARD_ACCESS.items():
        if product_id in user_products and dashboard_id in dashboards:
            return True
    
    return False


def get_user_dashboards(customer_id):
    user_products = get_user_products(customer_id)
    
    if 'bundle' in user_products:
        return list(DASHBOARD_NAMES.keys())
    
    dashboards = []
    for product_id in user_products:
        if product_id in DASHBOARD_ACCESS:
            dashboards.extend(DASHBOARD_ACCESS[product_id])
    
    return list(set(dashboards))


def show_upgrade_message(dashboard_id, customer_id):
    dashboard_name = DASHBOARD_NAMES.get(dashboard_id, dashboard_id)
    user_products = get_user_products(customer_id)
    
    st.error(f"❌ Accès refusé au dashboard : {dashboard_name}")
    
    num_owned = len(user_products)
    
    if num_owned == 0:
        st.markdown(f"""
        ### 🔒 Dashboard non disponible
        
        Vous n'avez pas encore de dashboard actif.
        
        [🛒 Acheter {dashboard_name} - 29€]({PURCHASE_LINKS.get(dashboard_id, '#')})
        
        ou
        
        [🎁 Growth Bundle - 67€]({PURCHASE_LINKS['bundle']}) (3 dashboards)
        """)
    elif num_owned == 1:
        st.markdown(f"""
        ### 🔒 Dashboard réservé
        
        Le dashboard **{dashboard_name}** n'est pas inclus dans votre pack actuel.
        
        [🛒 Acheter ce dashboard - 29€]({PURCHASE_LINKS.get(dashboard_id, '#')})
        """)
    elif num_owned == 2:
        st.markdown(f"""
        ### 🔒 Il ne vous manque plus qu'un dashboard !
        
        [🛒 Acheter {dashboard_name} - 29€]({PURCHASE_LINKS.get(dashboard_id, '#')})
        """)
    
    st.stop()


def save_consent(email, consent_value):
    """
    Sauvegarde le consentement avec timestamp
    """
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return False
        
        response = supabase.table('customers') \
            .update({
                'data_consent': consent_value,
                'consent_updated_at': datetime.now().isoformat()
            }) \
            .eq('email', email) \
            .execute()
        
        return True
    
    except Exception as e:
        st.warning(f"⚠️ Erreur sauvegarde consentement : {e}")
        return False


def get_user_consent(email):
    """
    Récupère UNIQUEMENT le statut de consentement
    """
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return None
        
        response = supabase.table('customers') \
            .select('data_consent') \
            .eq('email', email) \
            .execute()
        
        if response.data:
            return response.data[0].get('data_consent')
        
        return None
        
    except Exception as e:
        return None


def get_user_consent_with_timestamp(email):
    """
    Récupère le consentement ET le timestamp
    Permet de distinguer false par défaut vs false explicite
    
    Returns:
        dict ou None: {'data_consent': bool, 'consent_updated_at': datetime}
    """
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return None
        
        response = supabase.table('customers') \
            .select('data_consent, consent_updated_at') \
            .eq('email', email) \
            .execute()
        
        if response.data:
            return response.data[0]
        
        return None
        
    except Exception as e:
        return None