# app.py
import streamlit as st
import hashlib
from datetime import datetime, timedelta

# Clés d'accès stockées sur Supabase
VALID_KEYS = {
    "ABC123XYZ": {
        "email": "client@email.com",
        "expiry": None,  # Accès illimité
        "purchased_date": "2024-11-12"
    }
}

def check_access():
    """Vérifie la clé d'accès dans l'URL"""
    params = st.query_params
    access_key = params.get("key", None)
    
    if not access_key or access_key not in VALID_KEYS:
        st.error("❌ Accès non autorisé")
        st.markdown("""
        ### 🔒 Accès réservé aux clients
        
        Pour accéder à vos dashboards Etsy Analytics Pro :
        1. Vérifiez l'email reçu après votre achat
        2. Cliquez sur le lien d'accès unique
        
        Pas encore client ? 
        [Acheter maintenant - 47€](https://buy.stripe.com/votre-lien)
        """)
        st.stop()
    
    return VALID_KEYS[access_key]

# Vérification au lancement
user_info = check_access()
st.success(f"✅ Connecté - {user_info['email']}")