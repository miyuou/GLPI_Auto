import pandas as pd
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import smtplib
from email.message import EmailMessage
import os

# Configuration des chemins
BASE_DIR = r"C:\Users\HUAWEI\Desktop\internship\PGLPI\GLPI_Auto"
INPUT_DIR = os.path.join(BASE_DIR, "raw")
OUTPUT_FILE = os.path.join(BASE_DIR, "processed", "cleaned_latest.csv")
LOG_FILE = os.path.join(BASE_DIR, "logs.txt")

# Configuration du logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

def read_csv_file(filepath):
    """Lecture du CSV avec gestion des encodages"""
    encodings = ['utf-8', 'latin1', 'cp1252']
    for encoding in encodings:
        try:
            return pd.read_csv(filepath, sep=';', encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Aucun encodage valide pour {filepath}")

def send_alert(subject, body):
    """Envoi de notification par email"""
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = "glpi_auto@yourcompany.com"
    msg['To'] = "admin@yourcompany.com"
    
    try:
        with smtplib.SMTP('smtp.office365.com', 587, timeout=10) as server:
            server.starttls()
            server.login("your_email@company.com", "password")
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Erreur email : {str(e)}")
        with open(os.path.join(BASE_DIR, "email_fallback.txt"), "a", encoding='utf-8') as f:
            f.write(f"{subject}\n{body}\n\n")

def clean_data(df):
    """Version finale avec nettoyage complet et suppression des colonnes originales"""
    try:
        # 1. Vérification des colonnes requises
        required_cols = {'ID', 'Titre', 'Attribué à - Technicien', 'Demandeur - Demandeur'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Colonnes manquantes: {missing_cols}")

        # 2. Fonction de nettoyage des noms (optimale)
        def clean_name(name):
            if pd.isna(name):
                return None
            parts = []
            seen = set()
            for part in str(name).split():
                if part not in seen:
                    seen.add(part)
                    parts.append(part)
            return " ".join(parts)

        # 3. Nettoyage des techniciens
        df['Technicien'] = df['Attribué à - Technicien'].apply(
            lambda x: [clean_name(tech) for tech in str(x).split('\n') if tech.strip()]
            if pd.notna(x) else [])

        # 4. Nettoyage du demandeur
        df['Demandeur'] = df['Demandeur - Demandeur'].apply(clean_name)

        # 5. Explosion pour 1 ligne par technicien
        df = df.explode('Technicien').reset_index(drop=True)

        # 6. Suppression des colonnes originales
        df = df.drop(columns=['Attribué à - Technicien', 'Demandeur - Demandeur'], errors='ignore')

        # 7. Formatage des dates (toutes les colonnes contenant 'date' ou 'cré')
        date_cols = [col for col in df.columns if any(kw in col.lower() for kw in ['date', 'cré'])]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

        return df

    except Exception as e:
        logging.error(f"ERREUR nettoyage: {str(e)}", exc_info=True)
        raise
class GLPI_Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.csv'):
            try:
                logging.info(f"Nouveau fichier détecté : {event.src_path}")
                 # Suppression automatique de l'ancien fichier nettoyé
                if os.path.exists(OUTPUT_FILE):
                    os.remove(OUTPUT_FILE)
                    logging.info(f"Ancien fichier nettoyé supprimé : {OUTPUT_FILE}")
                
                # Lecture et nettoyage
                df = pd.read_csv_file(event.src_path)
                print("Colonnes détectées:", df.columns.tolist())  # Debug
                df_clean = clean_data(df)
                
              # Sauvegarde
                df_clean.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
                logging.info(f"Nouveau fichier nettoyé sauvegardé : {OUTPUT_FILE}")
                
            except Exception as e:
                error_msg = f"ERREUR sur {event.src_path} : {str(e)}"
                logging.error(error_msg)
                
            except Exception as e:
                error_msg = f"ERREUR sur {event.src_path} : {str(e)}"
                logging.error(error_msg)
                send_alert("GLPI - Erreur de traitement", error_msg)

if __name__ == "__main__":
    # Création des dossiers
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Traitement initial des fichiers existants
    event_handler = GLPI_Handler()
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.csv'):
            filepath = os.path.join(INPUT_DIR, filename)
            try:
                logging.info(f"Traitement initial du fichier : {filename}")
                df = read_csv_file(filepath)
                df_clean = clean_data(df)
                df_clean.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            except Exception as e:
                logging.error(f"Erreur traitement initial {filename} : {str(e)}")
    
    # Surveillance des nouveaux fichiers
    observer = Observer()
    observer.schedule(event_handler, path=INPUT_DIR, recursive=False)
    observer.start()
    logging.info("=== Service GLPI Auto démarré ===")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()