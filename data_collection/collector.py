# data_collection/collector.py
import streamlit as st
from supabase import create_client

def show_data_opt_in():
    """Affiche le pop-up de consentement au premier upload"""
    
    if 'consent_asked' not in st.session_state:
        st.session_state.consent_asked = False
    
    if not st.session_state.consent_asked:
        with st.expander("🤝 Aidez-nous à créer les prédictions IA", expanded=True):
            st.markdown("""
            ### Participez à la prochaine version avec IA !
            
            En acceptant, vous nous aidez à entraîner notre modèle de prédictions.
            
            **Ce que nous collectons :**
            - ✅ Vos données de ventes (anonymisées)
            - ✅ Catégories de produits
            - ✅ Évolutions mensuelles
            
            **Ce que nous ne collectons JAMAIS :**
            - ❌ Noms de clients
            - ❌ Adresses
            - ❌ Informations personnelles
            
            **En échange :**
            - 🎁 Accès gratuit aux prédictions IA (valeur 20€/mois)
            - 🎁 Nouvelles fonctionnalités en avant-première
            
            ---
            *Vous pouvez retirer votre consentement à tout moment.*
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ J'accepte", type="primary", width='stretch'):
                    st.session_state.data_consent = True
                    st.session_state.consent_asked = True
                    save_consent(user_info['email'], True)
                    st.rerun()
            
            with col2:
                if st.button("❌ Non merci", width='stretch'):
                    st.session_state.data_consent = False
                    st.session_state.consent_asked = True
                    save_consent(user_info['email'], False)
                    st.rerun()

def collect_data_if_consent(df_sales, user_email):
    """Sauvegarde les données uniquement si consentement"""
    
    if st.session_state.get('data_consent', False):
        # Anonymisation
        anonymized_data = {
            "user_id": hashlib.sha256(user_email.encode()).hexdigest(),
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_revenue": float(df_sales['Item Total'].sum()),
                "num_orders": len(df_sales),
                "avg_order_value": float(df_sales['Item Total'].mean()),
                "top_products": df_sales['Item Name'].value_counts().head(5).to_dict(),
                "monthly_trend": df_sales.groupby(
                    pd.to_datetime(df_sales['Sale Date']).dt.to_period('M')
                )['Item Total'].sum().to_dict()
            }
        }
        
        # Sauvegarde sur Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('training_data').insert(anonymized_data).execute()
        
        # NE PAS sauvegarder les CSVs bruts, juste les métriques agrégées