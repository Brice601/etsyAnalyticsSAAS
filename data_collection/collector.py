"""
data_collection/collector.py - VERSION FINALE

Gestion de la collecte de données avec opt-in obligatoire
"""

import streamlit as st
import hashlib
from datetime import datetime
import os
import json


def show_data_opt_in(user_email):
    """
    Affiche le pop-up de consentement au premier upload.
    Le consentement est déjà vérifié dans check_access(), donc ici on informe juste l'utilisateur.
    
    Args:
        user_email (str): Email de l'utilisateur
    """
    # Dans le nouveau modèle, le consentement est obligatoire dès l'inscription
    # Donc ce pop-up n'est plus nécessaire
    # On garde la fonction pour compatibilité mais elle ne fait rien
    pass


def get_file_hash(file_content):
    """Calcule le hash SHA256 d'un fichier pour détecter les doublons."""
    return hashlib.sha256(file_content).hexdigest()


def collect_raw_data(uploaded_files, user_email, template_name):
    """
    Collecte les fichiers bruts si l'utilisateur a donné son consentement.
    
    Args:
        uploaded_files: Peut être un dict, une liste, ou un seul fichier
        user_email: Email de l'utilisateur
        template_name: Nom du dashboard (finance_pro, customer_intelligence, seo_analyzer)
    
    Returns:
        bool: True si collecte réussie, False sinon
    """
    try:
        # Vérifier le consentement (déjà vérifié mais double check)
        from auth.access_manager import get_supabase_client
        
        supabase = get_supabase_client()
        if supabase:
            response = supabase.table('customers').select('data_consent').eq('email', user_email).execute()
            if not response.data or not response.data[0].get('data_consent'):
                return False
        
        # Hash de l'email pour anonymisation
        user_id = hashlib.sha256(user_email.encode()).hexdigest()
        
        # Déterminer le mode (production ou local)
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
    
    # Charger les hashes existants
    hash_file = os.path.join(data_dir, '_file_hashes.json')
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            file_hashes = json.load(f)
    else:
        file_hashes = {}
    
    # Normaliser les fichiers en liste
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
            
            # Vérifier si déjà uploadé
            if file.name in file_hashes and file_hashes[file.name] == current_hash:
                files_skipped += 1
                file.seek(0)
                continue
            
            # Sauvegarder le fichier
            file_path = os.path.join(data_dir, file.name)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            file_hashes[file.name] = current_hash
            files_saved += 1
            file.seek(0)
    
    # Sauvegarder les hashes
    with open(hash_file, 'w') as f:
        json.dump(file_hashes, f, indent=2)
    
    # Sauvegarder metadata
    metadata_path = os.path.join(data_dir, '_metadata.txt')
    with open(metadata_path, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n--- Upload {timestamp} ---\n")
        f.write(f"Nouveaux fichiers : {files_saved}\n")
        f.write(f"Fichiers ignorés (doublons) : {files_skipped}\n")
    
    if files_saved > 0:
        st.success(f"✅ {files_saved} fichier(s) collecté(s) avec succès (local)")
    
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
        
        # Charger les hashes existants
        try:
            hash_data = supabase.storage.from_('user-data').download(hash_file_path)
            file_hashes = json.loads(hash_data.decode('utf-8'))
        except:
            file_hashes = {}
        
        # Normaliser les fichiers en liste
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
                
                # Vérifier si déjà uploadé
                if file.name in file_hashes and file_hashes[file.name] == current_hash:
                    files_skipped += 1
                    file.seek(0)
                    continue
                
                # Upload vers Supabase
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
        
        # Sauvegarder les hashes mis à jour
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
        
        # Sauvegarder metadata
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
        
        # if files_saved > 0:
        #     st.success(f"✅ {files_saved} fichier(s) collecté(s) avec succès")
        # elif files_skipped > 0:
        #     st.info(f"ℹ️ {files_skipped} fichier(s) déjà collecté(s) (doublons ignorés)")
        
        return files_saved > 0 or files_skipped > 0
    
    except ImportError:
        st.error("❌ Module supabase non installé.")
        return False
    except Exception as e:
        st.warning(f"⚠️ Erreur Supabase : {e}")
        return False


def _normalize_files_input(uploaded_files):
    """
    Normalise l'input des fichiers en une liste.
    Gère les cas : dict, list, ou single file.
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
    OBSOLÈTE dans le nouveau modèle freemium.
    Le consentement est obligatoire à l'inscription.
    Garder pour compatibilité.
    """
    st.info("ℹ️ Le consentement de données est obligatoire pour utiliser la version gratuite.")
    st.markdown("""
    Votre consentement a été donné lors de l'inscription.
    
    Si vous souhaitez retirer votre consentement, contactez-nous à support@architecte-ia.fr
    
    **Alternative :** Passez à Insights Premium (9€/mois) qui ne requiert pas de collecte de données.
    """)