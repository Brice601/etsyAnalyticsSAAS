# utils/email_sender.py
import resend  # ou SendGrid, Mailgun

def send_access_email(customer_email, access_link):
    resend.api_key = st.secrets["resend"]["api_key"]
    
    html_content = f"""
    <h2>🎉 Bienvenue dans Etsy Analytics Pro !</h2>
    
    <p>Merci pour votre achat. Voici votre accès personnel :</p>
    
    <a href="{access_link}" 
       style="background: #0066FF; color: white; padding: 15px 30px; 
              text-decoration: none; border-radius: 5px; display: inline-block;">
        🚀 Accéder à mes dashboards
    </a>
    
    <p><strong>Ce lien est personnel et ne doit pas être partagé.</strong></p>
    
    <h3>🎓 Pour bien démarrer :</h3>
    <ol>
        <li>Exportez vos ventes Etsy (CSV)</li>
        <li>Uploadez le fichier sur votre dashboard</li>
        <li>Découvrez vos insights en temps réel !</li>
    </ol>
    
    <p>📺 <a href="https://youtube.com/...">Voir le tutoriel vidéo</a></p>
    
    <p>Besoin d'aide ? Répondez à cet email.</p>
    
    <p>L'équipe Architecte IA</p>
    """
    
    resend.Emails.send({
        "from": "support@architecte-ia.fr",
        "to": customer_email,
        "subject": "🎉 Votre accès Etsy Analytics Pro",
        "html": html_content
    })