import streamlit as st
import json
import os
from datetime import datetime

# Chemin vers le fichier mock_customers.json
MOCK_CUSTOMERS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_customers.json')

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


def load_customers():
    """Charge les clients depuis mock_customers.json (ou Supabase en production)"""
    try:
        # En mode développement : utiliser mock_customers.json
        if os.path.exists(MOCK_CUSTOMERS_PATH):
            with open(MOCK_CUSTOMERS_PATH, 'r', encoding='utf-8') as f:
                customers = json.load(f)
                return customers
        else:
            st.error(f"❌ Fichier {MOCK_CUSTOMERS_PATH} introuvable")
            return {}
    
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des clients : {e}")
        return {}


def save_consent(email, consent_value):
    """Sauvegarde le consentement de l'utilisateur"""
    try:
        customers = load_customers()
        
        # Trouver le client par email
        for key, customer in customers.items():
            if customer.get('email') == email:
                customer['consent'] = consent_value
                
                # Sauvegarder dans le fichier
                with open(MOCK_CUSTOMERS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(customers, f, indent=2, ensure_ascii=False)
                
                return True
        
        return False
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde du consentement : {e}")
        return False


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
    
    # Charger les clients
    customers = load_customers()
    
    # Vérifier si la clé existe
    if access_key not in customers:
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
    user_info = customers[access_key]
    user_info['access_key'] = access_key
    
    # Sauvegarder dans session_state pour les navigations suivantes
    st.session_state['access_key'] = access_key
    
    # Ajouter dans session_state pour accès global
    if 'user_info' not in st.session_state:
        st.session_state.user_info = user_info
    
    return user_info


def has_access_to_dashboard(access_key, dashboard_id):
    """
    Vérifie si un utilisateur a accès à un dashboard spécifique.
    
    Args:
        access_key (str): Clé d'accès de l'utilisateur
        dashboard_id (str): Identifiant du dashboard ('finance_pro', 'customer_intelligence', 'seo_analyzer')
    
    Returns:
        bool: True si l'utilisateur a accès, False sinon
    """
    customers = load_customers()
    
    if access_key not in customers:
        return False
    
    user_product = customers[access_key].get('product', 'starter')
    allowed_dashboards = DASHBOARD_ACCESS.get(user_product, [])
    
    return dashboard_id in allowed_dashboards


def show_upgrade_message(dashboard_id, current_product):
    """
    Affiche un message d'upgrade si l'utilisateur n'a pas accès au dashboard.
    
    Args:
        dashboard_id (str): ID du dashboard demandé
        current_product (str): Produit actuel de l'utilisateur ('starter' ou 'bundle')
    """
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
    else:
        st.markdown(f"""
        ### ❌ Erreur d'accès
        
        Vous devriez avoir accès au dashboard **{dashboard_name}** avec votre abonnement actuel.
        
        **Si le problème persiste :**
        - Vérifiez votre connexion internet
        - Essayez de rafraîchir la page
        - Contactez le support : support@architecte-ia.fr
        """)
    
    st.stop()


def get_user_dashboards(access_key):
    """
    Retourne la liste des dashboards accessibles pour un utilisateur.
    
    Args:
        access_key (str): Clé d'accès de l'utilisateur
    
    Returns:
        list: Liste des IDs de dashboards accessibles
    """
    customers = load_customers()
    
    if access_key not in customers:
        return []
    
    user_product = customers[access_key].get('product', 'starter')
    return DASHBOARD_ACCESS.get(user_product, [])


def display_user_badge(user_info):
    """
    Affiche un badge avec les informations utilisateur.
    
    Args:
        user_info (dict): Dictionnaire contenant les infos utilisateur
    """
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


# ========== FONCTIONS POUR LA GESTION DES DONNÉES ==========

def get_user_consent(email):
    """
    Récupère le statut de consentement d'un utilisateur.
    
    Args:
        email (str): Email de l'utilisateur
    
    Returns:
        bool: True si l'utilisateur a consenti, False sinon
    """
    customers = load_customers()
    
    for customer in customers.values():
        if customer.get('email') == email:
            return customer.get('consent', False)
    
    return False


def update_last_login(email):
    """
    Met à jour la date de dernière connexion d'un utilisateur.
    
    Args:
        email (str): Email de l'utilisateur
    """
    try:
        customers = load_customers()
        
        for customer in customers.values():
            if customer.get('email') == email:
                customer['last_login'] = datetime.now().isoformat()
                
                with open(MOCK_CUSTOMERS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(customers, f, indent=2, ensure_ascii=False)
                
                return True
        
        return False
    
    except Exception as e:
        st.warning(f"⚠️ Impossible de mettre à jour last_login : {e}")
        return False


# ========== MODE PRODUCTION : SUPABASE ==========
# Ces fonctions seront utilisées en production avec Supabase

def check_access_supabase():
    """
    Version production utilisant Supabase au lieu de mock_customers.json
    """
    # TODO: Implémenter la connexion Supabase
    # from supabase import create_client
    # 
    # supabase = create_client(
    #     st.secrets["supabase"]["url"],
    #     st.secrets["supabase"]["key"]
    # )
    # 
    # params = st.query_params
    # access_key = params.get("key", None)
    # 
    # if not access_key:
    #     st.error("Accès non autorisé")
    #     st.stop()
    # 
    # response = supabase.table('customers').select('*').eq('access_key', access_key).execute()
    # 
    # if not response.data:
    #     st.error("Clé invalide")
    #     st.stop()
    # 
    # return response.data[0]
    
    pass


def save_consent_supabase(email, consent_value):
    """
    Version production pour sauvegarder le consentement dans Supabase
    """
    # TODO: Implémenter avec Supabase
    # supabase.table('customers').update({'data_consent': consent_value}).eq('email', email).execute()
    
    pass
