import requests
import pandas as pd
from glpi_watcher import clean_data  # Réutilise la même fonction

def fetch_from_api():
    response = requests.get(
        "https://votre-glpi/apirest.php/ticket",
        headers={"Session-Token": "VOTRE_CLE_API"}
    )
    df = pd.DataFrame(response.json()['data'])
    return clean_data(df)  # Nettoyage identique !

if __name__ == "__main__":
    df = fetch_from_api()
    df.to_csv("C:/GLPI_Auto/processed/cleaned_latest.csv", index=False)