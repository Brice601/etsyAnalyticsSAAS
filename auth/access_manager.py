import streamlit as st
from datetime import datetime, timedelta

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
    # 'finance_pro': 'https://buy.stripe.com/5kQ28t5TreeMdbi9Qp7IY03',
    # 'customer_intelligence': 'https://buy.stripe.com/9B600l3Lj3A82wEfaJ7IY02',
    # 'seo_analyzer': 'https://buy.stripe.com/5kQ6oJ4Pn4Ec0owfaJ7IY01',
    # 'bundle': 'https://buy.stripe.com/8x2bJ33Ljb2Ac7e2nX7IY00',
    'insights': 'https://buy.stripe.com/8x2cN781zdaI3AI5A97IY06'  # TODO: Remplacer par le vrai lien Stripe
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
        ### 🔒 Accès réservé aux utilisateurs inscrits
        
        Pour accéder à Etsy Analytics Pro, vous devez créer un compte gratuit.
        
        [🚀 Créer mon compte gratuit](/signup_page)
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
            st.markdown("[🚀 Créer mon compte gratuit](/signup_page)")
            st.stop()
        
        user_info = response.data[0]
        user_info['access_key'] = access_key
        
        # Vérifier le consentement data (obligatoire)
        if not user_info.get('data_consent', False):
            st.error("❌ Consentement de données obligatoire")
            st.markdown("""
            Votre compte n'a pas donné son consentement pour la collecte de données.
            
            Pour utiliser Etsy Analytics Pro gratuitement, vous devez accepter 
            la collecte anonymisée de vos données.
            
            [📝 Modifier mes préférences](/signup_page)
            """)
            st.stop()
        
        # Update last_login
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
    """
    NOUVEAU MODÈLE FREEMIUM:
    Tous les utilisateurs ont accès aux 3 dashboards gratuitement
    (tant qu'ils ont donné leur consentement data)
    """
    return True  # Accès gratuit pour tous !


def has_insights_subscription(customer_id):
    """
    Vérifie si l'utilisateur a l'abonnement Insights 9€/mois
    
    Args:
        customer_id: UUID du client dans Supabase
    
    Returns:
        bool: True si l'utilisateur a l'abonnement Insights actif
    """
    user_products = get_user_products(customer_id)
    return 'insights' in user_products


def get_user_dashboards(customer_id):
    """
    NOUVEAU MODÈLE FREEMIUM:
    Retourne toujours les 3 dashboards (accès gratuit)
    """
    return list(DASHBOARD_NAMES.keys())


def show_upgrade_message(dashboard_id, customer_id):
    """
    OBSOLÈTE dans le modèle freemium
    Garder pour rétrocompatibilité mais ne devrait jamais être appelé
    """
    st.info("✅ Vous avez accès à tous les dashboards gratuitement !")


def show_insights_upgrade_cta():
    """
    Affiche le CTA d'upgrade vers Insights de manière uniforme
    """
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; text-align: center; color: white;
                margin: 20px 0;'>
        <h3 style='margin-top: 0;'>💎 Débloquez toutes les recommandations</h3>
        <p style='font-size: 1.2rem; margin: 15px 0;'>
            Insights Premium - <strong>9€/mois</strong>
        </p>
        <ul style='text-align: left; max-width: 600px; margin: 20px auto; font-size: 1.05rem;'>
            <li>✅ Analyses illimitées (plus de limite 10/semaine)</li>
            <li>✅ Recommandations IA complètes</li>
            <li>✅ Export PDF sans limite</li>
            <li>✅ Benchmarks vs secteur en temps réel</li>
            <li>✅ Calculateurs d'impact précis</li>
            <li>✅ Roadmaps d'actions priorisées</li>
            <li>✅ Alertes opportunités hebdomadaires</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <a href="{PURCHASE_LINKS['insights']}" target="_blank" 
       style="display: block; background: #28a745; color: white; 
              padding: 15px; border-radius: 10px; text-align: center; 
              font-weight: bold; font-size: 1.2rem; text-decoration: none; 
              margin-top: 20px;">
        🚀 Upgrade → Insights 9€/mois
    </a>
    """, unsafe_allow_html=True)


def show_locked_recommendation(title, priority="🟡 MOYENNE"):
    """
    Affiche une recommandation lockée de manière uniforme
    
    Args:
        title (str): Titre de la recommandation
        priority (str): Niveau de priorité (🔴 HAUTE, 🟡 MOYENNE, 🟢 INFO)
    """
    with st.expander(f"🔒 {priority} - {title}"):
        st.markdown("""
        <div style='filter: blur(5px); pointer-events: none; user-select: none;'>
            <p><strong>Cette recommandation premium inclut :</strong></p>
            <ul>
                <li>Analyse comparative détaillée vs benchmarks secteur</li>
                <li>Roadmap d'actions priorisées par impact</li>
                <li>Calculateur d'impact financier précis</li>
                <li>Quick wins actionnables immédiatement</li>
            </ul>
            <p>Cette analyse vous aide à optimiser vos performances en identifiant 
            les leviers d'amélioration les plus rentables pour votre situation spécifique.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🔐 Débloquez avec Insights 9€/mois")


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


def check_usage_limit(customer_id):
    """
    Vérifie si l'utilisateur gratuit n'a pas dépassé sa limite (10 analyses/semaine)
    Les utilisateurs Insights Premium ont un accès illimité
    
    Args:
        customer_id (UUID): ID du client
    
    Returns:
        dict: {
            'allowed': bool,
            'usage_count': int,
            'limit': int,
            'reset_date': datetime,
            'days_until_reset': int
        }
    """
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return {'allowed': True, 'usage_count': 0, 'limit': 10}
        
        # Récupérer les infos utilisateur
        response = supabase.table('customers') \
            .select('usage_count, usage_reset_date') \
            .eq('id', customer_id) \
            .execute()
        
        if not response.data:
            return {'allowed': False, 'usage_count': 0, 'limit': 10}
        
        user_data = response.data[0]
        
        # Si utilisateur a Insights → accès illimité
        if has_insights_subscription(customer_id):
            return {
                'allowed': True,
                'usage_count': user_data.get('usage_count', 0),
                'limit': 999999,  # Illimité
                'is_premium': True
            }
        
        # Vérifier si besoin de reset (7 jours écoulés)
        reset_date = datetime.fromisoformat(user_data['usage_reset_date'])
        days_since_reset = (datetime.now() - reset_date).days
        
        if days_since_reset >= 7:
            # Reset le compteur
            supabase.table('customers').update({
                'usage_count': 0,
                'usage_reset_date': datetime.now().isoformat()
            }).eq('id', customer_id).execute()
            
            return {
                'allowed': True,
                'usage_count': 0,
                'limit': 10,
                'reset_date': datetime.now(),
                'days_until_reset': 7,
                'is_premium': False
            }
        
        # Vérifier la limite (10 analyses/semaine pour gratuit)
        usage_count = user_data.get('usage_count', 0)
        limit = 10
        
        return {
            'allowed': usage_count < limit,
            'usage_count': usage_count,
            'limit': limit,
            'reset_date': reset_date,
            'days_until_reset': 7 - days_since_reset,
            'is_premium': False
        }
        
    except Exception as e:
        if DEBUG_MODE:
            st.warning(f"⚠️ Erreur check_usage_limit : {e}")
        # En cas d'erreur, autoriser l'accès
        return {'allowed': True, 'usage_count': 0, 'limit': 10}


def increment_usage(customer_id):
    """
    Incrémente le compteur d'utilisation de l'utilisateur
    À appeler après chaque analyse réussie
    
    Args:
        customer_id (UUID): ID du client
    
    Returns:
        bool: True si succès, False sinon
    """
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            return False
        
        # Ne pas incrémenter pour les utilisateurs Insights
        if has_insights_subscription(customer_id):
            return True
        
        # Incrémenter via la fonction SQL
        response = supabase.rpc('increment_usage', {'user_id': customer_id}).execute()
        
        return True
        
    except Exception as e:
        if DEBUG_MODE:
            st.warning(f"⚠️ Erreur increment_usage : {e}")
        return False


def show_usage_limit_message(usage_info):
    """
    Affiche un message quand la limite d'usage est atteinte
    
    Args:
        usage_info (dict): Info retournée par check_usage_limit()
    """
    st.error(f"""
    ❌ **Limite d'analyses atteinte ({usage_info['usage_count']}/{usage_info['limit']})**
    
    Vous avez utilisé toutes vos analyses gratuites pour cette semaine.
    """)
    
    st.info(f"""
    🔄 **Réinitialisation dans {usage_info['days_until_reset']} jour(s)**
    
    Votre quota sera réinitialisé le {usage_info['reset_date'].strftime('%d/%m/%Y')}.
    """)
    
    st.markdown("---")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; text-align: center; color: white;'>
        <h3 style='margin-top: 0;'>💎 Passez à Insights Premium</h3>
        <p style='font-size: 1.2rem; margin: 15px 0;'>
            <strong>9€/mois</strong> seulement
        </p>
        <ul style='text-align: left; max-width: 600px; margin: 20px auto; font-size: 1.05rem;'>
            <li>✅ <strong>Analyses illimitées</strong></li>
            <li>✅ <strong>Recommandations IA complètes</strong></li>
            <li>✅ <strong>Export PDF sans limite</strong></li>
            <li>✅ <strong>Support prioritaire</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <a href="{PURCHASE_LINKS['insights']}" target="_blank" 
       style="display: block; background: #28a745; color: white; 
              padding: 15px; border-radius: 10px; text-align: center; 
              font-weight: bold; font-size: 1.2rem; text-decoration: none; 
              margin-top: 20px;">
        🚀 Upgrade → Insights 9€/mois
    </a>
    """, unsafe_allow_html=True)

def should_increment_usage(customer_id):
    """
    Vérifie si on doit incrémenter le compteur
    Retourne True si > 30 min depuis dernière analyse
    """
    supabase = get_supabase_client()
    
    response = supabase.table('customers') \
        .select('last_analysis_timestamp') \
        .eq('id', customer_id) \
        .execute()
    
    if not response.data:
        return True
    
    last_timestamp = response.data[0].get('last_analysis_timestamp')
    
    # Si jamais analysé, on incrémente
    if not last_timestamp:
        return True
    
    # Vérifier si > 30 min
    last_dt = datetime.fromisoformat(last_timestamp)
    time_diff = datetime.now() - last_dt
    
    return time_diff > timedelta(minutes=30)


def increment_usage_with_timestamp(customer_id):
    """
    Incrémente ET met à jour le timestamp
    """
    supabase = get_supabase_client()
    
    # Ne pas incrémenter pour Premium
    if has_insights_subscription(customer_id):
        # Juste update timestamp
        supabase.table('customers').update({
            'last_analysis_timestamp': datetime.now().isoformat()
        }).eq('id', customer_id).execute()
        return True
    
    # Récupérer l'usage actuel
    response = supabase.table('customers').select('usage_count').eq('id', customer_id).execute()
    
    if not response.data:
        return False
    
    current_usage = response.data[0].get('usage_count', 0)
    
    # Incrémenter usage + timestamp
    supabase.table('customers').update({
        'usage_count': current_usage + 1,
        'last_analysis_timestamp': datetime.now().isoformat()
    }).eq('id', customer_id).execute()
    
    return True