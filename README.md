# 🎙 Whispr Local

**Dictée vocale IA, 100% locale et gratuite.**

Whispr Local te permet de dicter du texte à la voix dans n'importe quelle application — navigateur, éditeur de code, messagerie, terminal — sans qu'aucune donnée ne quitte ta machine.

Inspiré de Wispr Flow, mais open source, gratuit, et souverain.

---

## Pourquoi Whispr Local ?

| | Wispr Flow | Whispr Local |
|---|---|---|
| Coût | Abonnement payant | **Gratuit** |
| Données audio | Serveurs tiers | **Ta machine uniquement** |
| Fonctionne hors ligne | Non | **Oui** |
| Personnalisable | Limité | **Totalement** |

---

## Fonctionnalités

- 🎙 **Dictée en un raccourci** — appuie une fois pour démarrer, une fois pour arrêter
- 💉 **Injection automatique** — le texte transcrit est collé directement là où se trouve ton curseur
- 🗂 **Historique des transcriptions** — fenêtre dédiée avec les dernières dictées, éditables et copiables
- 🔴 **Indicateur visuel flottant** — un pill discret en bas d'écran confirme que l'enregistrement est en cours
- 🖥 **Interface graphique** — fenêtre principale avec statut en temps réel
- 📌 **Icône dans la barre des tâches** — ferme la fenêtre sans quitter l'outil ; le raccourci reste actif
- 🔒 **100% local** — aucune connexion après le premier téléchargement du modèle

---

## Prérequis

| Élément | Version minimale |
|---|---|
| Windows | 10 ou 11 |
| Python | 3.10+ |
| Microphone | N'importe quel micro intégré ou externe |
| Connexion internet | Uniquement lors du **premier lancement** (téléchargement du modèle IA, ~465 Mo) |

> **Ressources consommées :** ~500 Mo de RAM pendant la transcription, quelques secondes de CPU. Aucun GPU requis.

---

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/bouhlelyacine-hue/whispr-local.git
cd whispr-local
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

> **Premier lancement :** le modèle Whisper (`small`, ~465 Mo) sera téléchargé automatiquement depuis HuggingFace. Il est ensuite mis en cache sur ta machine — les lancements suivants sont instantanés.

### 4. Lancer l'outil

```bash
python main.py
```

> 💡 Si le raccourci clavier ne fonctionne pas, relance le terminal **en tant qu'administrateur**.

---

## Utilisation

### Via le bouton de l'interface

1. Lance `python main.py`
2. Attends que le statut passe à **"● Prêt"**
3. Clique sur **"🎙 Démarrer"**
4. Parle dans ton micro
5. Clique sur **"⏹ Arrêter"**
6. Le texte apparaît dans l'historique et est automatiquement injecté au curseur

### Via le raccourci clavier (recommandé)

| Action | Raccourci |
|---|---|
| Démarrer l'enregistrement | `Ctrl + Alt + Espace` |
| Arrêter et transcrire | `Ctrl + Alt + Espace` |

Le texte est injecté directement dans l'application active (Claude, navigateur, Word, etc.).

### Système tray

- **Fermer la fenêtre** → l'outil continue de tourner en arrière-plan, le raccourci reste actif
- **Double-clic sur l'icône** → rouvre la fenêtre
- **Clic droit → Quitter** → arrête l'outil complètement

### Historique des transcriptions

Par défaut, **aucune donnée n'est conservée sur le disque**. L'historique est uniquement affiché en mémoire le temps de la session.

Pour activer la persistance, clique sur le bouton **"💾 Inactif"** dans l'interface — il passe en **"💾 Actif"**. Tu peux le désactiver à tout moment.

Quand la sauvegarde est active, les transcriptions sont stockées dans un fichier `history.enc` **chiffré (AES-128 via Fernet)**. La clé de chiffrement est dérivée automatiquement depuis l'identité de ta machine (`COMPUTERNAME` + `USERNAME`) via PBKDF2 (200 000 itérations) — **aucune clé n'est stockée sur le disque**.

Chaque entrée de l'historique contient :
- L'heure de la transcription
- Le texte éditable (tu peux le corriger avant de l'utiliser)
- Un bouton **Copier** pour le mettre dans le presse-papiers
- Un bouton **Injecter** pour l'envoyer dans l'application active

---

## Configuration

Ouvre le fichier `config.py` pour personnaliser l'outil :

```python
HOTKEY = "ctrl+alt+space"    # Raccourci clavier
LANGUAGE = "fr"               # Langue de transcription (fr, en, es, de, ...)
MODEL_SIZE = "small"          # Modèle Whisper : tiny | base | small | medium | large
SAMPLE_RATE = 16000           # Fréquence d'échantillonnage (ne pas modifier)
MAX_RECORDING_SECONDS = 120   # Durée maximale d'un enregistrement (en secondes)
```

### Choisir le bon modèle

| Modèle | Taille | Qualité | Vitesse |
|---|---|---|---|
| `tiny` | ~75 Mo | Basique | Très rapide |
| `base` | ~145 Mo | Correcte | Rapide |
| `small` | ~465 Mo | **Recommandé** | Rapide |
| `medium` | ~1,5 Go | Très bonne | Moyenne |
| `large` | ~3 Go | Excellente | Lente |

> Pour un usage quotidien en français, `small` est le meilleur compromis.

---

## Structure du projet

```
whispr-local/
├── main.py          # Point d'entrée — lance l'application
├── gui.py           # Interface graphique principale
├── overlay.py       # Indicateur visuel flottant (pill de statut)
├── recorder.py      # Capture audio depuis le microphone
├── transcriber.py   # Transcription via Whisper local
├── injector.py      # Injection du texte dans l'application active
├── history.py       # Persistance chiffrée de l'historique (AES-128)
├── config.py        # Configuration (raccourci, langue, modèle)
└── requirements.txt # Dépendances Python
```

---

## Stack technique

| Bibliothèque | Rôle |
|---|---|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Transcription vocale IA (OpenAI Whisper, optimisé CPU) |
| [sounddevice](https://python-sounddevice.readthedocs.io) | Capture audio depuis le microphone |
| [keyboard](https://github.com/boppreh/keyboard) | Raccourci clavier global système |
| [pyperclip](https://github.com/asweigart/pyperclip) | Gestion du presse-papiers |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | Interface graphique moderne |
| [pystray](https://github.com/moses-palmer/pystray) | Icône dans la barre des tâches |
| [Pillow](https://python-pillow.org) | Génération de l'icône tray |
| [cryptography](https://cryptography.io) | Chiffrement AES-128 de l'historique (Fernet) |

---

## Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| Le raccourci ne fonctionne pas | Droits insuffisants | Relancer le terminal en tant qu'administrateur |
| "Erreur de chargement" au démarrage | Pas de connexion internet (premier lancement) | Vérifier la connexion et relancer |
| Micro non détecté | Pas de micro par défaut défini | Vérifier les paramètres audio Windows |
| Le texte est injecté au mauvais endroit | Le focus a changé pendant la transcription | Cliquer dans le champ cible avant de dicter |
| La transcription est lente | Modèle trop grand pour la machine | Passer à `small` ou `base` dans `config.py` |

---

## Licence

Ce projet utilise exclusivement des composants open source.
Le modèle Whisper est publié par OpenAI sous licence [MIT](https://github.com/openai/whisper/blob/main/LICENSE).
