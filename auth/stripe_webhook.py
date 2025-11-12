# auth/stripe_webhook.py
from flask import Flask, request
import stripe
from supabase import create_client
import secrets

app = Flask(__name__)
stripe.api_key = st.secrets["stripe"]["secret_key"]

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, st.secrets["stripe"]["webhook_secret"]
        )
    except ValueError:
        return 'Invalid payload', 400
    
    # Quand un paiement réussit
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_details']['email']
        
        # Génère clé d'accès unique
        access_key = secrets.token_urlsafe(16)
        
        # Sauvegarde dans Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('customers').insert({
            'email': customer_email,
            'access_key': access_key,
            'product': session['metadata']['product'],
            'purchased_at': datetime.now().isoformat()
        }).execute()
        
        # Envoie email avec lien d'accès
        send_access_email(
            customer_email, 
            f"https://etsy-analytics-pro.streamlit.app/?key={access_key}"
        )
    
    return 'Success', 200