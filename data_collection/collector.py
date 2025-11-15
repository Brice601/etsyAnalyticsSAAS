import streamlit as st
import hashlib
from datetime import datetime
import pandas as pd

# En production, utiliser Supabase
# from supabase import create_client


def show_data_opt_in(user_email):
    """
    Affiche le pop-up de consentement au premier upload de données.
    
    Args:
        user_email (str): Email de l'utilisateur connecté
    """
    # Vérifier si le consentement a déjà été demandé
    if 'consent_asked' not in st.session_state:
        st.session_state.consent_asked = False
    
    # Si déjà demandé, ne rien afficher
    if st.session_state.consent_asked:
        return
    
    # Afficher le pop-up de consentement
    with st.expander("🤝 Aidez-nous à créer les prédictions IA", expanded=True):
        st.markdown("""
        ### Participez à la prochaine version avec IA prédictive !
        
        En acceptant, vous nous aidez à entraîner notre modèle de prédictions.
        Vous serez les premiers à en bénéficier gratuitement.
        
        #### Ce que nous collectons :
        - ✅ **Vos données de ventes** (anonymisées - aucun nom de client)
        - ✅ **Catégories de produits** (pour améliorer les recommandations)
        - ✅ **Évolutions mensuelles** (pour les prédictions de tendances)
        - ✅ **Métriques agrégées** (CA total, panier moyen, etc.)
        
        #### Ce que nous ne collectons JAMAIS :
        - ❌ **Noms de clients** ou informations personnelles
        - ❌ **Adresses** de livraison
        - ❌ **Emails** de vos clients
        - ❌ **Numéros de téléphone**
        - ❌ **Données bancaires**
        
        #### En échange, vous recevez :
        - 🎁 **Accès gratuit aux prédictions IA** (valeur 20€/mois)
        - 🎁 **Nouvelles fonctionnalités en avant-première**
        - 🎁 **Recommandations personnalisées améliorées**
        - 🎁 **Analyses de tendances du marché**
        
        ---
        
        #### 🔒 Sécurité et conformité :
        - Vos données sont **anonymisées** (hash de votre email)
        - Stockage sécurisé sur serveurs européens
        - Conformité **RGPD** totale
        - Vous pouvez **retirer votre consentement à tout moment**
        
        ---
        
        *Pour plus d'informations, consultez notre [Politique de confidentialité](https://architecte-ia.fr/privacy)*
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ J'accepte de participer", type="primary", use_container_width=True):
                st.session_state.data_consent = True
                st.session_state.consent_asked = True
                
                # Sauvegarder le consentement
                from auth.access_manager import save_consent
                save_consent(user_email, True)
                
                st.success("✅ Merci ! Vous contribuez à l'amélioration de l'outil.")
                st.info("🎁 Vous recevrez un email dès que les prédictions IA seront disponibles.")
                st.rerun()
        
        with col2:
            if st.button("❌ Non merci", use_container_width=True):
                st.session_state.data_consent = False
                st.session_state.consent_asked = True
                
                # Sauvegarder le refus
                from auth.access_manager import save_consent
                save_consent(user_email, False)
                
                st.info("Pas de problème ! Vous pourrez toujours changer d'avis dans les paramètres.")
                st.rerun()


def collect_data_if_consent(df, user_email, dashboard_type):
    """
    Collecte et anonymise les données si l'utilisateur a donné son consentement.
    
    Args:
        df (pd.DataFrame): DataFrame contenant les données à collecter
        user_email (str): Email de l'utilisateur
        dashboard_type (str): Type de dashboard ('finance_pro', 'customer_intelligence', 'seo_analyzer')
    """
    # Vérifier le consentement
    if not st.session_state.get('data_consent', False):
        return
    
    try:
        # Anonymiser l'email avec hash SHA-256
        user_id = hashlib.sha256(user_email.encode()).hexdigest()
        
        # Préparer les données selon le dashboard
        if dashboard_type == 'finance_pro':
            anonymized_data = anonymize_finance_data(df, user_id)
        
        elif dashboard_type == 'customer_intelligence':
            anonymized_data = anonymize_customer_data(df, user_id)
        
        elif dashboard_type == 'seo_analyzer':
            anonymized_data = anonymize_seo_data(df, user_id)
        
        else:
            st.warning(f"⚠️ Type de dashboard inconnu : {dashboard_type}")
            return
        
        # Sauvegarder (en production : Supabase)
        save_anonymized_data(anonymized_data)
        
    except Exception as e:
        st.warning(f"⚠️ Erreur lors de la collecte de données : {e}")


def anonymize_finance_data(df, user_id):
    """
    Anonymise les données du dashboard Finance Pro.
    
    Args:
        df (pd.DataFrame): DataFrame des ventes
        user_id (str): Hash de l'email utilisateur
    
    Returns:
        dict: Données anonymisées prêtes pour la sauvegarde
    """
    # Agréger les données - PAS DE DONNÉES BRUTES
    aggregated_data = {
        "user_id": user_id,
        "dashboard": "finance_pro",
        "collected_at": datetime.now().isoformat(),
        "metrics": {
            # Métriques financières globales
            "total_revenue": float(df['Price'].sum()) if 'Price' in df.columns else 0,
            "num_orders": int(len(df)),
            "avg_order_value": float(df['Price'].mean()) if 'Price' in df.columns else 0,
            
            # Top produits (anonymisés)
            "top_products_revenue": df.groupby('Product')['Price'].sum().nlargest(5).to_dict() if 'Product' in df.columns else {},
            
            # Évolution mensuelle (agrégée)
            "monthly_trend": {
                str(k): float(v) for k, v in df.groupby(
                    pd.to_datetime(df['Date']).dt.to_period('M')
                )['Price'].sum().items()
            } if 'Date' in df.columns else {},
            
            # Catégories (si disponibles)
            "category_distribution": df['Category'].value_counts().to_dict() if 'Category' in df.columns else {},
            
            # Statistiques de coûts (agrégées)
            "avg_cost": float(df['Cost'].mean()) if 'Cost' in df.columns else 0,
            "total_cost": float(df['Cost'].sum()) if 'Cost' in df.columns else 0,
            
            # Panier moyen par mois
            "monthly_avg_basket": {
                str(k): float(v) for k, v in df.groupby(
                    pd.to_datetime(df['Date']).dt.to_period('M')
                )['Price'].mean().items()
            } if 'Date' in df.columns else {}
        }
    }
    
    return aggregated_data


def anonymize_customer_data(df, user_id):
    """
    Anonymise les données du dashboard Customer Intelligence.
    
    Args:
        df (pd.DataFrame): DataFrame des commandes
        user_id (str): Hash de l'email utilisateur
    
    Returns:
        dict: Données anonymisées prêtes pour la sauvegarde
    """
    aggregated_data = {
        "user_id": user_id,
        "dashboard": "customer_intelligence",
        "collected_at": datetime.now().isoformat(),
        "metrics": {
            # Métriques clients globales
            "total_customers": int(df['Buyer'].nunique()) if 'Buyer' in df.columns else 0,
            "total_orders": int(len(df)),
            "avg_orders_per_customer": float(len(df) / df['Buyer'].nunique()) if 'Buyer' in df.columns and df['Buyer'].nunique() > 0 else 0,
            
            # Distribution géographique (pays uniquement, pas de villes)
            "country_distribution": df['Country'].value_counts().to_dict() if 'Country' in df.columns else {},
            
            # Évolution temporelle
            "orders_by_month": {
                str(k): int(v) for k, v in df.groupby(
                    pd.to_datetime(df['Date']).dt.to_period('M')
                ).size().items()
            } if 'Date' in df.columns else {},
            
            # Panier moyen par pays
            "avg_basket_by_country": df.groupby('Country')['Total'].mean().to_dict() if 'Country' in df.columns and 'Total' in df.columns else {},
            
            # Jour de la semaine (agrégé)
            "orders_by_weekday": df.groupby(
                pd.to_datetime(df['Date']).dt.day_name()
            ).size().to_dict() if 'Date' in df.columns else {}
        }
    }
    
    return aggregated_data


def anonymize_seo_data(df, user_id):
    """
    Anonymise les données du dashboard SEO Analyzer.
    
    Args:
        df (pd.DataFrame): DataFrame des listings
        user_id (str): Hash de l'email utilisateur
    
    Returns:
        dict: Données anonymisées prêtes pour la sauvegarde
    """
    aggregated_data = {
        "user_id": user_id,
        "dashboard": "seo_analyzer",
        "collected_at": datetime.now().isoformat(),
        "metrics": {
            # Métriques SEO globales
            "num_listings": int(len(df)),
            "avg_price": float(df['Price'].mean()) if 'Price' in df.columns else 0,
            "avg_title_length": float(df['Title'].str.len().mean()) if 'Title' in df.columns else 0,
            
            # Distribution des prix (par tranche)
            "price_ranges": {
                "0-20": int(len(df[df['Price'] < 20])) if 'Price' in df.columns else 0,
                "20-50": int(len(df[(df['Price'] >= 20) & (df['Price'] < 50)])) if 'Price' in df.columns else 0,
                "50-100": int(len(df[(df['Price'] >= 50) & (df['Price'] < 100)])) if 'Price' in df.columns else 0,
                "100+": int(len(df[df['Price'] >= 100])) if 'Price' in df.columns else 0
            },
            
            # Nombre moyen de photos
            "avg_num_images": float(df['Num_Images'].mean()) if 'Num_Images' in df.columns else 0,
            
            # Catégories (si disponibles)
            "category_distribution": df['Category'].value_counts().to_dict() if 'Category' in df.columns else {}
        }
    }
    
    return aggregated_data


def save_anonymized_data(data):
    """
    Sauvegarde les données anonymisées (mode dev : fichier local, prod : Supabase).
    
    Args:
        data (dict): Données anonymisées à sauvegarder
    """
    # MODE DÉVELOPPEMENT : Sauvegarder dans un fichier JSON local
    try:
        import json
        import os
        
        # Créer le dossier data_collection s'il n'existe pas
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'collected_data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Nom du fichier basé sur user_id et timestamp
        filename = f"{data['user_id']}_{data['dashboard']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(data_dir, filename)
        
        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        # Confirmation discrète (pas de st.success pour ne pas polluer l'UI)
        # st.write(f"✅ Données collectées (anonymisées) : {filename}")
    
    except Exception as e:
        st.warning(f"⚠️ Impossible de sauvegarder les données : {e}")
    
    # MODE PRODUCTION : Sauvegarder dans Supabase
    # try:
    #     supabase = create_client(
    #         st.secrets["supabase"]["url"],
    #         st.secrets["supabase"]["key"]
    #     )
    #     
    #     supabase.table('training_data').insert(data).execute()
    # 
    # except Exception as e:
    #     st.warning(f"⚠️ Erreur Supabase : {e}")


def show_consent_settings(user_email):
    """
    Permet à l'utilisateur de modifier son consentement dans les paramètres.
    
    Args:
        user_email (str): Email de l'utilisateur
    """
    from auth.access_manager import get_user_consent, save_consent
    
    current_consent = get_user_consent(user_email)
    
    st.markdown("### 🤝 Gestion du consentement de données")
    
    if current_consent:
        st.success("✅ Vous participez actuellement à l'amélioration de l'outil.")
        st.markdown("""
        **Merci de votre contribution !**
        
        Vous recevrez un accès gratuit aux prédictions IA dès leur sortie.
        """)
        
        if st.button("❌ Retirer mon consentement"):
            save_consent(user_email, False)
            st.session_state.data_consent = False
            st.success("✅ Consentement retiré. Nous ne collecterons plus vos données.")
            st.rerun()
    
    else:
        st.info("ℹ️ Vous ne participez pas actuellement à la collecte de données.")
        st.markdown("""
        **En acceptant, vous aidez à créer les prédictions IA et recevez :**
        - 🎁 Accès gratuit aux prédictions IA (20€/mois)
        - 🎁 Nouvelles fonctionnalités en avant-première
        - 🎁 Recommandations personnalisées améliorées
        """)
        
        if st.button("✅ Accepter de participer"):
            save_consent(user_email, True)
            st.session_state.data_consent = True
            st.success("✅ Merci ! Vous contribuez à l'amélioration de l'outil.")
            st.rerun()
