"""
data_collection/collector.py

Module de collecte de données brutes (sans anonymisation).
OPTIMISÉ : Détection des doublons par hash pour éviter les copies inutiles.
"""

import streamlit as st
import hashlib
from datetime import datetime
import os
import json


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


def get_file_hash(file_content):
    """
    Calcule le hash SHA256 d'un fichier pour détecter les doublons.
    
    Args:
        file_content (bytes): Contenu du fichier
    
    Returns:
        str: Hash SHA256 du fichier
    """
    return hashlib.sha256(file_content).hexdigest()


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
        
        # MODE DÉVELOPPEMENT : Sauvegarder localement
        if not _is_production():
            save_files_locally(uploaded_files, user_id, template_name)
            return True
        
        # MODE PRODUCTION : Sauvegarder sur Supabase Storage
        else:
            save_files_to_supabase(uploaded_files, user_id, template_name)
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


def save_files_locally(uploaded_files, user_id, template_name):
    """
    Sauvegarde les fichiers localement (mode développement).
    OPTIMISÉ : Détecte les doublons par hash.
    
    Args:
        uploaded_files (list or dict): Fichiers uploadés
        user_id (str): Hash de l'email utilisateur
        template_name (str): Nom du template
    """
    # Créer le dossier de destination (SANS timestamp)
    data_dir = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'collected_data', 
        'raw_data',
        user_id, 
        template_name
    )
    os.makedirs(data_dir, exist_ok=True)
    
    # Charger l'historique des hashes
    hash_file = os.path.join(data_dir, '_file_hashes.json')
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            file_hashes = json.load(f)
    else:
        file_hashes = {}
    
    # Gérer différents formats d'input
    files_list = _normalize_files_input(uploaded_files)
    
    # Copier chaque fichier
    files_saved = 0
    files_skipped = 0
    
    for file in files_list:
        if file is not None:
            # IMPORTANT : Réinitialiser le curseur AVANT de lire
            file.seek(0)
            
            # Lire le contenu du fichier
            file_content = file.read()
            
            # Vérifier que le contenu n'est pas vide
            if len(file_content) == 0:
                print(f"⚠️ Fichier vide ignoré : {file.name}")
                file.seek(0)
                continue
            
            # Calculer le hash du fichier
            current_hash = get_file_hash(file_content)
            
            # Vérifier si le fichier existe déjà avec le même contenu
            if file.name in file_hashes and file_hashes[file.name] == current_hash:
                print(f"⏭️ Fichier déjà existant (hash identique) : {file.name}")
                files_skipped += 1
                file.seek(0)
                continue
            
            # Sauvegarder le fichier
            file_path = os.path.join(data_dir, file.name)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Mettre à jour l'historique des hashes
            file_hashes[file.name] = current_hash
            
            files_saved += 1
            print(f"✅ Fichier sauvegardé : {file.name}")
            
            # Réinitialiser le curseur pour utilisation ultérieure
            file.seek(0)
    
    # Sauvegarder l'historique des hashes
    with open(hash_file, 'w') as f:
        json.dump(file_hashes, f, indent=2)
    
    # Sauvegarder metadata avec timestamp
    metadata_path = os.path.join(data_dir, '_metadata.txt')
    with open(metadata_path, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n--- Upload {timestamp} ---\n")
        f.write(f"Nouveaux fichiers : {files_saved}\n")
        f.write(f"Fichiers ignorés (doublons) : {files_skipped}\n")
    
    # Confirmation discrète dans la console
    print(f"✅ {files_saved} fichier(s) collecté(s) | {files_skipped} doublon(s) ignoré(s)")


def save_files_to_supabase(uploaded_files, user_id, template_name):
    """
    Sauvegarde les fichiers sur Supabase Storage (mode production).
    OPTIMISÉ : Détecte les doublons par hash.
    
    Args:
        uploaded_files (list or dict): Fichiers uploadés
        user_id (str): Hash de l'email utilisateur
        template_name (str): Nom du template
    """
    try:
        # Import uniquement en production
        from supabase import create_client
        
        # Connexion à Supabase
        supabase = create_client(
            st.secrets["supabase"]["url"],
            st.secrets["supabase"]["key"]
        )
        
        # Chemin de base (SANS timestamp)
        base_path = f"raw_data/{user_id}/{template_name}/"
        
        # Télécharger l'historique des hashes depuis Supabase
        hash_file_path = base_path + "_file_hashes.json"
        try:
            hash_data = supabase.storage.from_('user-data').download(hash_file_path)
            file_hashes = json.loads(hash_data.decode('utf-8'))
            print("📥 Historique des hashes chargé")
        except:
            file_hashes = {}
            print("📝 Nouvel historique de hashes")
        
        # Gérer différents formats d'input
        files_list = _normalize_files_input(uploaded_files)
        
        # Upload chaque fichier
        files_saved = 0
        files_skipped = 0
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
                    file.seek(0)
                    continue
                
                # Calculer le hash du fichier
                current_hash = get_file_hash(file_content)
                
                # Vérifier si le fichier existe déjà avec le même contenu
                if file.name in file_hashes and file_hashes[file.name] == current_hash:
                    print(f"⏭️ Fichier déjà existant (hash identique) : {file.name}")
                    files_skipped += 1
                    file.seek(0)
                    continue
                
                # Chemin complet
                file_path = base_path + file.name
                
                try:
                    # Upload vers Supabase
                    response = supabase.storage.from_('user-data').upload(
                        file_path,
                        file_content,
                        file_options={
                            "content-type": file.type if hasattr(file, 'type') else "text/csv",
                            "upsert": "true"  # Remplace si existe
                        }
                    )
                    
                    # Mettre à jour l'historique des hashes
                    file_hashes[file.name] = current_hash
                    
                    files_saved += 1
                    print(f"✅ Fichier uploadé : {file.name}")
                    
                except Exception as upload_error:
                    error_msg = str(upload_error)
                    files_errors.append(f"{file.name}: {error_msg}")
                    print(f"❌ Erreur upload {file.name}: {error_msg}")
                
                # Réinitialiser le curseur
                file.seek(0)
        
        # Sauvegarder l'historique des hashes mis à jour
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
            print("📤 Historique des hashes sauvegardé")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde hashes : {e}")
        
        # Upload metadata avec timestamp
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata_content = f"\n--- Upload {timestamp} ---\nNouveaux fichiers : {files_saved}\nFichiers ignorés (doublons) : {files_skipped}\n".encode()
            
            # Récupérer l'ancien metadata pour append
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
        
        # Rapport final
        if files_saved > 0 or files_skipped > 0:
            print(f"✅ {files_saved} fichier(s) collecté(s) | {files_skipped} doublon(s) ignoré(s)")
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