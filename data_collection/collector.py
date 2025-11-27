"""
data_collection/collector.py - VERSION FINALE

CORRECTION : Gérer le cas où data_consent = false par défaut à la création
"""

import streamlit as st
import hashlib
from datetime import datetime
import os
import json


def show_data_opt_in(user_email):
    """
    Affiche le pop-up de consentement au premier upload.
    ✅ CORRIGÉ : Distingue false par défaut vs false explicite
    
    Args:
        user_email (str): Email de l'utilisateur
    """
    from auth.access_manager import get_user_consent_with_timestamp
    
    # Récupérer le consentement ET la date de dernière modification
    consent_data = get_user_consent_with_timestamp(user_email)
    
    if consent_data is not None:
        db_consent = consent_data.get('data_consent')
        consent_updated_at = consent_data.get('consent_updated_at')
        
        # Si consent_updated_at existe, l'utilisateur a VRAIMENT répondu
        if consent_updated_at is not None:
            st.session_state.consent_asked = True
            st.session_state.data_consent = db_consent
            return
    
    # Initialiser les variables de session
    if 'consent_asked' not in st.session_state:
        st.session_state.consent_asked = False
    
    if 'data_consent' not in st.session_state:
        st.session_state.data_consent = False
    
    # Si déjà demandé dans cette session, ne rien afficher
    if st.session_state.consent_asked:
        return
    
    # Afficher le pop-up
    with st.expander("🤝 Aidez-nous à créer les prédictions IA", expanded=True):
        st.markdown("""
        ### Participez à la prochaine version avec IA !
        
        En acceptant, vous nous aidez à entraîner notre modèle de prédictions pour améliorer l'outil.
        
        **Ce que nous collectons :**
        - ✅ Vos données de ventes (anonymisées)
        - ✅ Catégories de produits
        - ✅ Évolutions mensuelles
        
        **Ce que nous ne collectons JAMAIS :**
        - ❌ Noms de clients
        - ❌ Adresses email des clients
        - ❌ Informations personnelles identifiables
        
        **En échange :**
        - 🎁 Accès gratuit pendant 3 mois aux prédictions IA (valeur 20€/mois)
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
                
                from auth.access_manager import save_consent
                save_consent(user_email, True)
                
                st.success("✅ Merci ! Vous contribuez à l'amélioration de l'outil.")
                st.info("🎁 Vous recevrez un email dès que les prédictions IA seront disponibles.")
                st.rerun()
        
        with col2:
            if st.button("❌ Non merci", use_container_width=True):
                st.session_state.data_consent = False
                st.session_state.consent_asked = True
                
                from auth.access_manager import save_consent
                save_consent(user_email, False)
                
                st.info("Pas de problème ! Vous pourrez toujours changer d'avis dans les paramètres.")
                st.rerun()


def get_file_hash(file_content):
    """Calcule le hash SHA256 d'un fichier pour détecter les doublons."""
    return hashlib.sha256(file_content).hexdigest()


def collect_raw_data(uploaded_files, user_email, template_name):
    """Collecte les fichiers bruts si l'utilisateur a donné son consentement."""
    
    if not st.session_state.get('data_consent', False):
        return False
    
    try:
        user_id = hashlib.sha256(user_email.encode()).hexdigest()
        
        if not _is_production():
            return save_files_locally(uploaded_files, user_id, template_name)
        else:
            return save_files_to_supabase(uploaded_files, user_id, template_name)
    
    except Exception as e:
        st.warning(f"⚠️ Erreur lors de la collecte de données : {e}")
        return False


def _is_production():
    """Détecte si on est en production ou en local."""
    try:
        return 'supabase' in st.secrets and st.secrets['supabase'].get('url')
    except:
        return False


def save_files_locally(uploaded_files, user_id, template_name):
    """Sauvegarde les fichiers localement (mode développement)."""
    data_dir = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'collected_data', 
        'raw_data',
        user_id, 
        template_name
    )
    os.makedirs(data_dir, exist_ok=True)
    
    hash_file = os.path.join(data_dir, '_file_hashes.json')
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            file_hashes = json.load(f)
    else:
        file_hashes = {}
    
    files_list = _normalize_files_input(uploaded_files)
    files_saved = 0
    files_skipped = 0
    
    for file in files_list:
        if file is not None:
            file.seek(0)
            file_content = file.read()
            
            if len(file_content) == 0:
                file.seek(0)
                continue
            
            current_hash = get_file_hash(file_content)
            
            if file.name in file_hashes and file_hashes[file.name] == current_hash:
                files_skipped += 1
                file.seek(0)
                continue
            
            file_path = os.path.join(data_dir, file.name)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            file_hashes[file.name] = current_hash
            files_saved += 1
            file.seek(0)
    
    with open(hash_file, 'w') as f:
        json.dump(file_hashes, f, indent=2)
    
    metadata_path = os.path.join(data_dir, '_metadata.txt')
    with open(metadata_path, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n--- Upload {timestamp} ---\n")
        f.write(f"Nouveaux fichiers : {files_saved}\n")
        f.write(f"Fichiers ignorés (doublons) : {files_skipped}\n")
    
    return True


def save_files_to_supabase(uploaded_files, user_id, template_name):
    """Sauvegarde les fichiers sur Supabase Storage (mode production)."""
    try:
        from supabase import create_client
        
        supabase = create_client(
            st.secrets["supabase"]["url"],
            st.secrets["supabase"]["service_role_key"]
        )
        
        base_path = f"raw_data/{user_id}/{template_name}/"
        hash_file_path = base_path + "_file_hashes.json"
        
        try:
            hash_data = supabase.storage.from_('user-data').download(hash_file_path)
            file_hashes = json.loads(hash_data.decode('utf-8'))
        except:
            file_hashes = {}
        
        files_list = _normalize_files_input(uploaded_files)
        files_saved = 0
        files_skipped = 0
        
        for file in files_list:
            if file is not None:
                file.seek(0)
                file_content = file.read()
                
                if len(file_content) == 0:
                    file.seek(0)
                    continue
                
                current_hash = get_file_hash(file_content)
                
                if file.name in file_hashes and file_hashes[file.name] == current_hash:
                    files_skipped += 1
                    file.seek(0)
                    continue
                
                file_path = base_path + file.name
                
                try:
                    supabase.storage.from_('user-data').upload(
                        file_path,
                        file_content,
                        file_options={
                            "content-type": file.type if hasattr(file, 'type') else "text/csv",
                            "upsert": "true"
                        }
                    )
                    
                    file_hashes[file.name] = current_hash
                    files_saved += 1
                except Exception as e:
                    print(f"❌ Erreur upload {file.name}: {e}")
                
                file.seek(0)
        
        try:
            hash_content = json.dumps(file_hashes, indent=2).encode('utf-8')
            supabase.storage.from_('user-data').upload(
                hash_file_path,
                hash_content,
                file_options={
                    "content-type": "application/json",
                    "upsert": "true"
                }
            )
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde hashes : {e}")
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata_content = f"\n--- Upload {timestamp} ---\nNouveaux fichiers : {files_saved}\nFichiers ignorés (doublons) : {files_skipped}\n".encode()
            
            try:
                old_metadata = supabase.storage.from_('user-data').download(base_path + "_metadata.txt")
                metadata_content = old_metadata + metadata_content
            except:
                pass
            
            supabase.storage.from_('user-data').upload(
                base_path + "_metadata.txt",
                metadata_content,
                file_options={
                    "content-type": "text/plain",
                    "upsert": "true"
                }
            )
        except Exception as e:
            print(f"⚠️ Erreur metadata : {e}")
        
        return files_saved > 0 or files_skipped > 0
    
    except ImportError:
        st.error("❌ Module supabase non installé.")
        return False
    except Exception as e:
        st.warning(f"⚠️ Erreur Supabase : {e}")
        return False


def _normalize_files_input(uploaded_files):
    """Normalise l'input des fichiers en une liste."""
    if uploaded_files is None:
        return []
    
    if isinstance(uploaded_files, dict):
        return [f for f in uploaded_files.values() if f is not None]
    elif isinstance(uploaded_files, list):
        return [f for f in uploaded_files if f is not None]
    else:
        return [uploaded_files]


def show_consent_settings(user_email):
    """Permet à l'utilisateur de modifier son consentement dans les paramètres."""
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