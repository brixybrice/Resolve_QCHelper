# Resolve_QCHelper

Plugin DaVinci Resolve (Workflow Integration) pour la prise de notes QC pendant une
relecture de timeline. Il ajoute une fenêtre flottante « Reviewers Notes » permettant
d'annoter rapidement le clip sous le playhead avec un timecode source précis.

## Fonctionnalités

- Détection automatique du **timecode source** (pas le TC timeline) du clip sous le
  playhead, même si le clip a été trimé/décalé sur la timeline.
- 9 boutons rapides, personnalisables (libellé + contenu de la note).
- Raccourcis clavier : **Ctrl+Option** (touches physiques) + une touche de la rangée
  **Q W E R T Y U I O** déclenche directement le bouton correspondant (Q=1, W=2, E=3,
  R=4, T=5, Y=6, U=7, I=8, O=9), sans avoir à cliquer.
- **Ctrl+W** (sans Option) ferme la fenêtre du plugin.
- Un champ de texte libre pour les notes qui ne rentrent pas dans un bouton prédéfini
  (validation avec `Enter` ou le bouton `Save`).
- Les notes sont ajoutées (jamais écrasées) dans le champ de métadonnée
  `Reviewers Notes` du clip dans le Media Pool, chacune préfixée par le timecode source
  au moment de l'ajout.
- Une seule instance de la fenêtre à la fois : relancer le plugin la ramène au premier
  plan au lieu d'en ouvrir une seconde.

## Installation

1. Copier `QCHelper.py` **et** le dossier `QCHelper_settings/` (avec son
   `buttons_config.json`) dans :

   ```
   /Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins
   ```

2. Redémarrer DaVinci Resolve si l'appli était déjà ouverte.
3. Lancer le plugin depuis le menu **Workspace > Workflow Integrations** (ou équivalent
   selon la version de Resolve).

> Le script dépend de l'API Fusion/`bmd` injectée par Resolve : il ne peut pas être
> exécuté en dehors de l'application (`python QCHelper.py` ne fonctionnera pas).

## Utilisation

1. Ouvrir un projet avec une timeline active dans Resolve.
2. Lancer le plugin : la fenêtre « Reviewers Notes » apparaît, toujours au premier plan.
3. Déplacer le playhead sur le clip à commenter.
4. Soit :
   - cliquer sur un des 9 boutons (ou appuyer sur `Ctrl+Option+Q/W/E/R/T/Y/U/I/O`),
   - saisir un texte libre dans le champ prévu puis valider avec `Enter` ou `Save`.
5. La note est enregistrée dans les métadonnées du clip, préfixée par son timecode
   source (ex : `01:00:12:04 --> Perche`).
6. `Escape` ou `Ctrl+W` ferme la fenêtre.

## Configuration des boutons

Les 9 boutons se configurent via `QCHelper_settings/buttons_config.json` :

```json
{
    "1": {"btn": "Boom", "content": "Perche"},
    "2": {"btn": "Blur", "content": "Léger flou"},
    "3": {"btn": "Bad Slate", "content": "Mauvais Clap"}
}
```

- `btn` : le texte affiché sur le bouton.
- `content` : le texte inséré dans la note lors du clic (ou du raccourci clavier).

Il suffit d'éditer ce fichier et de relancer le plugin pour appliquer les changements —
aucune modification du code Python n'est nécessaire. Si le fichier est absent ou
invalide, le plugin fonctionne quand même en repli, avec les numéros bruts (1 à 9)
comme libellé et contenu.

## Limitations connues

- Le raccourci utilise volontairement **Ctrl+Option** (touches physiques) plutôt que
  **Cmd**, car `Cmd+Shift+Q` et `Cmd+Option+Shift+Q` sont des raccourcis système macOS
  réservés (déconnexion, immédiate avec Option) qui interceptent la frappe avant même
  qu'elle n'atteigne Resolve — ça a été découvert en testant la version précédente.
- Des messages de debug (`[QCHelper][debug] ...`) s'affichent dans la console Python de
  Resolve à chaque frappe dans la fenêtre — utile pour vérifier la structure réelle de
  `Modifiers` si un raccourci ne se déclenche pas. Voir `CLAUDE.md` pour le détail.

## Développement

Voir `CLAUDE.md` pour le détail de l'architecture (calcul du TC source, stockage des
métadonnées, structure de l'UI Fusion).
