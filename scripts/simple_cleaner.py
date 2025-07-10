import pandas as pd
import os

print("=== DÉMARRAGE ===")

# Charge le fichier le plus récent du dossier raw
fichier = max(
    [os.path.join("..\\raw", f) for f in os.listdir("..\\raw") if f.endswith(".csv")], 
    key=os.path.getmtime
)
df = pd.read_csv(f"..\\raw\\{fichier}", sep=';', encoding='latin1')

# Nettoyage minimal
df['Technicien'] = df['Attribué à - Technicien'].str.replace(r'(\w+)( \1)+', r'\1', regex=True)
df['Demandeur'] = df['Demandeur - Demandeur'].str.replace(r'(\w+)( \1)+', r'\1', regex=True)

# Sauvegarde
df.to_csv("..\\processed\\cleaned.csv", index=False, encoding='utf-8-sig')
print("=== TERMINÉ ===")
print(f"Fichier nettoyé : ..\\processed\\cleaned.csv")
input("Appuyez sur Entrée pour quitter...")