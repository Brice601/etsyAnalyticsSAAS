"""
data_collection/collector.py

Module de collecte de données brutes (sans anonymisation).
Les données sont copiées telles quelles localement ou vers Supabase Storage.
L'anonymisation se fera lors de l'utilisation ultérieure des données.
"""

import streamlit as st
import hashlib
from datetime import datetime
import os


def show_data_opt_in(user_email):
    """
    Affiche le pop-up de consentement au premier upload.
    
    Args:
        user_email (str): Email de l'utilisateur
    """
    # Vérifier si le consentement a déjà été demandé
    if 'consent_asked' not in st.session_state:
        st.session_state.consent_asked = False
    
    # Si déjà demandé, ne rien afficher
    if st.session_state.consent_asked:
        return
    
    # Afficher le pop-up
    with st.expander("🤝 Aidez-nous à créer les prédictions IA", expanded=True):
        st.markdown("""
        ### Participez à la prochaine version avec IA !
        
        En acceptant, vous nous aidez à entraîner notre modèle de prédictions pour améliorer l'outil.
        
        **Ce que nous collectons :**
        - ✅ Vos données de ventes (anonymisées lors de l'utilisation)
        - ✅ Catégories de produits
        - ✅ Évolutions mensuelles
        
        **Ce que nous ne collectons JAMAIS :**
        - ❌ Noms de clients
        - ❌ Adresses email des clients
        - ❌ Informations personnelles identifiables
        
        **En échange :**
        - 🎁 Accès gratuit aux prédictions IA (valeur 20€/mois)
        - 🎁 Nouvelles fonctionnalités en avant-première
        - 🎁 Recommandations personnalisées améliorées
        
        ---
        *Les données ne sont ni revendues, ni partagées avec des tiers.*  
        *Elles sont traitées uniquement par notre algorithme pour améliorer l'outil.*  
        *Vous pouvez retirer votre consentement à tout moment dans les paramètres.*
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ J'accepte", use_container_width=True, type="primary"):
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


def collect_raw_data(uploaded_files, user_email, template_name):
    """
    Collecte les fichiers bruts (sans anonymisation) si l'utilisateur a donné son consentement.
    
    Args:
        uploaded_files (list or dict): Liste ou dictionnaire des fichiers uploadés
        user_email (str): Email de l'utilisateur
        template_name (str): Nom du template ('finance_pro', 'customer_intelligence', 'seo_analyzer')
    
    Returns:
        bool: True si la collecte a réussi, False sinon
    """
    # Vérifier le consentement
    if not st.session_state.get('data_consent', False):
        return False
    
    try:
        # Hash de l'email pour anonymiser l'utilisateur
        user_id = hashlib.sha256(user_email.encode()).hexdigest()
        
        # Timestamp pour version des fichiers
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # MODE DÉVELOPPEMENT : Sauvegarder localement
        if not _is_production():
            save_files_locally(uploaded_files, user_id, template_name, timestamp)
            return True
        
        # MODE PRODUCTION : Sauvegarder sur Supabase Storage
        else:
            save_files_to_supabase(uploaded_files, user_id, template_name, timestamp)
            return True
    
    except Exception as e:
        st.warning(f"⚠️ Erreur lors de la collecte de données : {e}")
        return False


def _is_production():
    """
    Détecte si on est en production ou en local.
    
    Returns:
        bool: True si en production (Streamlit Cloud), False sinon
    """
    # En production, on aura les secrets Supabase
    try:
        return 'supabase' in st.secrets and st.secrets['supabase'].get('url')
    except:
        return False


def save_files_locally(uploaded_files, user_id, template_name, timestamp):
    """
    Sauvegarde les fichiers localement (mode développement).
    OPTIMISÉ : Écrase les anciens fichiers pour éviter les doublons.
    
    Args:
        uploaded_files (list or dict): Fichiers uploadés
        user_id (str): Hash de l'email utilisateur
        template_name (str): Nom du template
        timestamp (str): Timestamp de la collecte (utilisé uniquement pour metadata)
    """
    # Créer le dossier de destination (SANS timestamp dans le chemin)
    data_dir = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'collected_data', 
        'raw_data',
        user_id, 
        template_name
        # Pas de timestamp ici pour éviter la multiplication des dossiers
    )
    os.makedirs(data_dir, exist_ok=True)
    
    # Gérer différents formats d'input
    files_list = _normalize_files_input(uploaded_files)
    
    # Copier chaque fichier
    files_saved = 0
    for file in files_list:
        if file is not None:
            # IMPORTANT : Réinitialiser le curseur AVANT de lire
            file.seek(0)
            
            # Lire le contenu du fichier
            file_content = file.read()
            
            # Vérifier que le contenu n'est pas vide
            if len(file_content) == 0:
                print(f"⚠️ Fichier vide ignoré : {file.name}")
                continue
            
            # Sauvegarder (écrase l'ancien si existe)
            file_path = os.path.join(data_dir, file.name)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            files_saved += 1
            
            # Réinitialiser le curseur pour utilisation ultérieure
            file.seek(0)
    
    # Sauvegarder un fichier metadata avec le timestamp
    metadata_path = os.path.join(data_dir, '_metadata.txt')
    with open(metadata_path, 'w') as f:
        f.write(f"Last upload: {timestamp}\n")
        f.write(f"Files count: {files_saved}\n")
    
    # Confirmation discrète dans la console (pas dans l'UI)
    print(f"✅ {files_saved} fichier(s) collecté(s) (écrasés si existants) : {data_dir}")


def save_files_to_supabase(uploaded_files, user_id, template_name, timestamp):
    """
    Sauvegarde les fichiers sur Supabase Storage (mode production).
    OPTIMISÉ : Utilise upsert pour écraser les anciens fichiers.
    
    Args:
        uploaded_files (list or dict): Fichiers uploadés
        user_id (str): Hash de l'email utilisateur
        template_name (str): Nom du template
        timestamp (str): Timestamp de la collecte
    """
    try:
        # Import uniquement en production
        from supabase import create_client
        
        # Connexion à Supabase
        supabase = create_client(
            st.secrets["supabase"]["url"],
            st.secrets["supabase"]["key"]
        )
        
        # Chemin de base (SANS timestamp pour éviter les doublons)
        base_path = f"raw_data/{user_id}/{template_name}/"
        
        # Gérer différents formats d'input
        files_list = _normalize_files_input(uploaded_files)
        
        # Upload chaque fichier
        files_saved = 0
        files_errors = []
        
        for file in files_list:
            if file is not None:
                # IMPORTANT : Réinitialiser le curseur AVANT de lire
                file.seek(0)
                
                # Lire le contenu
                file_content = file.read()
                
                # Vérifier que le contenu n'est pas vide
                if len(file_content) == 0:
                    print(f"⚠️ Fichier vide ignoré : {file.name}")
                    continue
                
                # Chemin complet
                file_path = base_path + file.name
                
                try:
                    # 🔥 UTILISER UPSERT pour écraser si existe déjà
                    response = supabase.storage.from_('user-data').upload(
                        file_path,
                        file_content,
                        file_options={
                            "content-type": file.type if hasattr(file, 'type') else "text/csv",
                            "upsert": "true"  # CRITIQUE : Remplace si existe
                        }
                    )
                    
                    files_saved += 1
                    print(f"✅ Fichier uploadé : {file_path}")
                    
                except Exception as upload_error:
                    # Log détaillé de l'erreur
                    error_msg = str(upload_error)
                    files_errors.append(f"{file.name}: {error_msg}")
                    print(f"❌ Erreur upload {file.name}: {error_msg}")
                
                # Réinitialiser le curseur
                file.seek(0)
        
        # Upload metadata avec timestamp
        try:
            metadata_content = f"Last upload: {timestamp}\nFiles count: {files_saved}\n".encode()
            supabase.storage.from_('user-data').upload(
                base_path + "_metadata.txt",
                metadata_content,
                file_options={
                    "content-type": "text/plain",
                    "upsert": "true"
                }
            )
        except:
            pass  # Non bloquant si metadata échoue
        
        # Rapport final
        if files_saved > 0:
            print(f"✅ {files_saved} fichier(s) collecté(s) sur Supabase (écrasés si existants)")
            return True
        else:
            if files_errors:
                st.warning(f"⚠️ Erreurs upload : {', '.join(files_errors)}")
            print("⚠️ Aucun fichier n'a pu être uploadé")
            return False
    
    except ImportError:
        st.error("❌ Module supabase non installé. Impossible de collecter les données en production.")
        return False
    except Exception as e:
        st.warning(f"⚠️ Erreur Supabase : {e}")
        print(f"❌ Erreur générale : {e}")
        return False


def _normalize_files_input(uploaded_files):
    """
    Normalise l'input des fichiers en une liste.
    
    Args:
        uploaded_files: dict, list, ou fichier unique
    
    Returns:
        list: Liste de fichiers
    """
    if uploaded_files is None:
        return []
    
    if isinstance(uploaded_files, dict):
        return [f for f in uploaded_files.values() if f is not None]
    
    elif isinstance(uploaded_files, list):
        return [f for f in uploaded_files if f is not None]
    
    else:
        return [uploaded_files]


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