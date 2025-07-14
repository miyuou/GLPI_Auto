@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
:: ================================================
:: FICHIER DE LANCEMENT POUR GLPI_AUTO
:: Cas d'usage ci-dessous
:: ================================================

REM -- Configuration des chemins --
set PYTHON_PATH="C:\Users\HUAWEI\Desktop\internship\PGLPI\GLPI_Auto\.venv\Scripts\python.exe"
set SCRIPT_PATH="C:\Users\HUAWEI\Desktop\internship\PGLPI\GLPI_Auto\scripts\glpi_watcher.py"
set LOG_FILE="C:\Users\HUAWEI\Desktop\internship\PGLPI\GLPI_Auto\logs.txt"
set PBI_PATH="C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
REM -- Vérification des fichiers --
if not exist %PYTHON_PATH% (
    echo Erreur: Python introuvable a l'emplacement %PYTHON_PATH%
    pause
    exit /b 1
)

if not exist %SCRIPT_PATH% (
    echo Erreur: Script glpi_watcher.py introuvable a l'emplacement %SCRIPT_PATH%
    pause
    exit /b 1
)

REM -- Menu interactif --
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo  GLPI AUTO-CLEANER - CAS D'USAGE
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo 1. Lancer le script en mode visible (debug)
echo 2. Installer le service Windows (admin)
echo 3. Désinstaller le service (admin)
echo 4. Voir les logs
echo 5. Quitter
echo.

choice /c 12345 /m "Choisissez une option"
if %errorlevel% equ 1 goto :debug
if %errorlevel% equ 2 goto :install
if %errorlevel% equ 3 goto :uninstall
if %errorlevel% equ 4 goto :logs
if %errorlevel% equ 5 exit

:debug
echo [DEBUG] Lancement visible - Ctrl+C pour arrêter
echo Verification du chemin Python: %PYTHON_PATH%
echo Verification du chemin Script: %SCRIPT_PATH%
%PYTHON_PATH% %SCRIPT_PATH% --pbi_path %PBI_PATH%
pause
exit

:install
echo [ADMIN] Installation du service...
call nssm install GLPI_AutoCleaner %PYTHON_PATH% %SCRIPT_PATH%
call nssm set GLPI_AutoCleaner AppDirectory "%~dp0"
call nssm start GLPI_AutoCleaner
echo Service installé et démarré!
pause
exit

:uninstall
echo [ADMIN] Désinstallation du service...
call nssm stop GLPI_AutoCleaner
call nssm remove GLPI_AutoCleaner confirm
echo Service désinstallé!
pause
exit

:logs
if not exist %LOG_FILE% (
    echo Fichier de logs introuvable a l'emplacement %LOG_FILE%
    pause
    exit /b 1
)
notepad %LOG_FILE%
exit