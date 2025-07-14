import csv
import pandas as pd
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import logging
import smtplib
from email.message import EmailMessage
import os
# CONFIG - CHANGE ONLY THESE VARIABLES FOR DEPLOYMENT
BASE_DIR = r"C:\Users\HUAWEI\Desktop\internship\PGLPI\GLPI_Auto"
INPUT_DIR = os.path.join(BASE_DIR, "raw")
OUTPUT_FILE = os.path.join(BASE_DIR, "processed", "cleaned_latest.csv")
LOG_FILE = os.path.join(BASE_DIR, "logs.txt")
PBI_PATH = r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"

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

def launch_powerbi():
    """Open existing dashboard or create new one"""
    dashboard_path = os.path.join(BASE_DIR, "dashboard", "GLPI_Dashboard.pbix")
    csv_path = os.path.join(BASE_DIR, "processed", "cleaned_latest.csv")
    
    try:
        if os.path.exists(dashboard_path):
            # Open existing dashboard
            subprocess.run(
                f'"{PBI_PATH}" "{dashboard_path}"',
                shell=True,
                check=True,
                timeout=30
            )
        else:
            # Create new dashboard on first run
            os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
            subprocess.run(
                f'"{PBI_PATH}" "{csv_path}"',
                shell=True,
                check=True,
                timeout=30
            )
            logging.info("Please save your dashboard as GLPI_Dashboard.pbix")
    except Exception as e:
        logging.error(f"Power BI Error: {str(e)}")
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
                df = read_csv_file(event.src_path)  # Use your existing function
                print("Colonnes détectées:", df.columns.tolist())  # Debug
                df_clean = clean_data(df)
                
              # Sauvegarde
                output_path = os.path.join(BASE_DIR, "processed", "cleaned_latest.csv")
               # Update the clean_data saving part:
                df_clean.to_csv(
                     OUTPUT_FILE,
                     index=False,
                     encoding='utf-8-sig',
                     sep=',',
                     quoting=csv.QUOTE_ALL,
                     date_format='%Y-%m-%d',
                     line_terminator='\r\n'
                )
                logging.info(f"Nouveau fichier nettoyé sauvegardé : {OUTPUT_FILE}")
                # After saving the CSV
                if not os.path.exists(output_path):
                 logging.error("File was not created!")
                elif os.path.getsize(output_path) == 0:
                 logging.error("File is empty!")
                else:
                # Manually set file type
                 os.rename(output_path, output_path)  # This refreshes file metadata
                 logging.info("CSV file verified")
                launch_powerbi()
            except Exception as e:
                error_msg = f"ERREUR sur {event.src_path} : {str(e)}"
                logging.error(error_msg)
                
           

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