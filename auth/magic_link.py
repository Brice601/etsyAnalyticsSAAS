# auth/magic_link.py
import streamlit_authenticator as stauth
from supabase import create_client

def send_magic_link(email):
    """Envoie un lien de connexion par email"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Vérifie si email a acheté
    response = supabase.table('customers').select('*').eq('email', email).execute()
    
    if response.data:
        # Génère token temporaire
        token = generate_token(email)
        send_email(email, f"https://app.com/?token={token}")
        return True
    return False