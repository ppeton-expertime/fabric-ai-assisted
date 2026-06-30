# fabric-ai-assisted

Développement **assisté** de pipelines Microsoft Fabric **depuis VS Code** : notebook édité localement, exécuté sur le **compute Spark distant Fabric**, données en **Lakehouse**, génération de code via **GitHub Copilot**, versioning **GitHub**.

> Ce README formalise **le processus de travail** (hors CI/CD).
> Le détail complet — y compris le **CI/CD (Deployment Pipelines)** — est dans [`Mode_operatoire_Fabric_VSCode_Copilot_GitHub.md`](./Mode_operatoire_Fabric_VSCode_Copilot_GitHub.md).

---

## Sommaire

- [Prérequis](#prérequis)
- [Le processus en bref](#le-processus-en-bref)
- [Étapes détaillées](#étapes-détaillées)
- [Orchestration : pipeline planifié](#orchestration--pipeline-planifié)
- [Conventions de code](#conventions-de-code)
- [⚠️ Limites & contraintes connues](#️-limites--contraintes-connues)
- [Reprise de session (check-list)](#reprise-de-session-check-list)
- [Bonnes pratiques](#bonnes-pratiques)
- [Structure du repo](#structure-du-repo)

---

## Prérequis

| Élément | Détail |
|---|---|
| **VS Code** | + extension **Fabric Data Engineering** (ex-Synapse) |
| **GitHub Copilot** | extension + **Copilot Chat** (agent `FabricNotebook`) |
| **Git for Windows** | `git --version` pour vérifier |
| **Accès Fabric** | au moins **Contributor** sur le workspace + une **capacité** active (F2 min.) |
| **Lakehouses** | **schema-enabled** (par défaut depuis fin 2025) |

**Connexions à (re)faire après expiration de session :**
- Fabric : `Ctrl+Shift+P` → **`Fabric Data Engineering: Sign In`**
- GitHub : icône **Comptes** (bas-gauche VS Code) → **Sign in with GitHub**

---

## Le processus en bref

```mermaid
flowchart TD
    UI["Portail Fabric (UI)"] -->|"créer le notebook"| N["Notebook (.ipynb)"]
    A["VS Code + extension Fabric"] -->|"édition + Copilot"| N
    N -->|"kernel : Microsoft Fabric Runtime"| C["Compute Spark distant (Fabric)"]
    C --> T["Tables Delta (OneLake)"]
    N -->|"commit / push"| GH["Repo GitHub — develop"]
    GH <-->|"Git integration"| WS["Workspace Fabric"]
    PPL["Data pipeline (planifié)"] -->|"activité Notebook"| N
```

> Le notebook est **créé dans le portail** puis **édité dans VS Code**, et **s'exécute sur le Spark distant Fabric** (kernel *Microsoft Fabric Runtime*). Les **données** vivent dans OneLake (Lakehouse), le **code** est versionné dans GitHub. Un **pipeline planifié** orchestre l'exécution automatique.

---

## Étapes détaillées

### 1. Préparer l'espace de travail local (une fois)

```powershell
cd C:\Users\<user>\repos
git clone https://github.com/<org>/fabric-ai-assisted.git
cd fabric-ai-assisted
git checkout develop
git pull
```

> ⚠️ Ne pas cloner dans un dossier **OneDrive** (conflits avec `.git`).

Dans la vue **Fabric Data Engineering** : **Set Local Work Folder** → le clone, puis **Select Workspace**.

### 2. Créer le notebook **depuis le portail** (recommandé), puis le récupérer dans VS Code

> ✅ **Bonne pratique** : créer le notebook **dans l'UI Fabric** (plus robuste que la création depuis VS Code, qui peut poser des soucis de matérialisation/VFS).

**Dans le portail :**
1. Workspace → **New item** → **Notebook** → le **renommer** (ex. `nb_<domaine>`).
2. Panneau **Lakehouses** → **Add** → ajouter les Lakehouses cibles et **épingler le défaut**. ⚠️ Ces attachements sont **enregistrés dans la définition** du notebook (indispensable pour l'exécution par pipeline planifié).
3. (Optionnel) coder/coller les premières cellules, **Save**.

**Dans VS Code :**
4. Vue **Fabric Data Engineering** → **Refresh** (↻) → le notebook apparaît sous **Notebooks**.
5. **Download** (⬇️) l'item pour le matérialiser en local, puis l'ouvrir en **vue notebook** (kernel **Microsoft Fabric Runtime**). En cas de `.py` brut : clic droit → **Open in Synapse VS Code**.

### 3. Se connecter aux données (Lakehouse)

1. **Upload du fichier source** : se fait **dans le portail** (Lakehouse → **Files** → **Upload**).
2. **Lakehouse par défaut** : panneau **Lakehouses** → **Add** → épingler par défaut (active les chemins relatifs `Files/…` et les noms de table courts).
3. **Attacher les Lakehouses cibles** (Bronze/Silver/Gold) au notebook pour l'écriture cross-Lakehouse.

### 4. Générer le code avec Copilot

- `Ctrl+Alt+I` → Copilot Chat → agent **FabricNotebook** (mode **Local**).
- Outils MCP Fabric (`get_fabric_doc`, `query_code_examples`) = lecture seule → **Allow in this Session** (au cas par cas).
- Utiliser un **prompt cadré** (voir mode opératoire, Annexe A) puis **Keep** les cellules.
- **Règle d'or — « l'IA propose, l'équipe valide »** : relire le code généré, surtout les écritures cross-Lakehouse (voir [Conventions](#conventions-de-code)).

### 5. Exécuter sur le compute distant

- **Connect** → **Microsoft Fabric Runtime** → **New standard session** (ou *high concurrency* à plusieurs).
- Lancer les cellules. *Cold start* possible sur petite capacité (voir [Limites](#️-limites--contraintes-connues)).

### 6. Publier sur GitHub & synchroniser

Avant tout commit : **Clear All Outputs** + **`Ctrl+S`**.

**Voie recommandée — Git integration Fabric** (repo lisible) :
Portail → workspace → **Source control** → *Add account* (PAT, Contents: R/W) → cocher les items → **Commit** sur `develop`.

**Voie VS Code (Git CLI)** — nécessite de **matérialiser le notebook sur disque** d'abord (Download Item Definition, ou *Save As* vers le repo en `.ipynb` avec un chemin **local `C:\…`**) :

```powershell
git add <chemin-du-notebook>
git commit -m "feat(<domaine>): <description>"
git push
```

> `develop` = branche de travail · `main` = branche stable (promotion par **Pull Request revue**).

---

## Orchestration : pipeline planifié

> Objectif : exécuter le notebook **automatiquement**, sur planning, **sans VS Code** (le notebook tourne côté Fabric). Le pipeline se crée **dans le portail** (l'authoring + le scheduling sont une expérience portail) et se versionne ensuite via **Git integration**.

### Créer le pipeline

1. Workspace → **New item** → **Data pipeline** → le nommer (ex. `ppl_run_<domaine>`).
2. Canvas → panneau **Activities** → ajouter une activité **Notebook**.
3. Sélectionner l'activité → onglet **Settings** → champ **Notebook** = le notebook cible.
4. (Optionnel) onglet **General** → renommer l'activité (ex. `Run <domaine>`).
5. Onglet **Home** → **Save**, puis **Run** pour tester (onglet **Output** → statut **Succeeded**).

### Planifier (ex. tous les lundis à 11h)

6. Onglet **Home** → **Schedule** → toggle **On**.
7. **Frequency** = **Week** → cocher **Monday** → **Time** = **11:00**.
8. **Time zone** = **(UTC+01:00) … Paris** (gère automatiquement été/hiver). **Apply**.
9. (Recommandé) renseigner **Failure notifications** (email d'équipe) pour être alerté en cas d'échec d'un run planifié.

### À savoir

- **Prérequis** : le notebook doit avoir ses **Lakehouses attachés + défaut épinglé** enregistrés dans sa définition (sinon le run planifié échoue).
- **Identité d'exécution** : un run planifié s'exécute **sous l'identité de la personne qui crée/met à jour la planification** → s'assurer qu'elle garde les accès. *(En PROD : privilégier une identité de service / Workspace Identity.)*
- **Suivi** : menu **Monitor** → historique et runs à venir.
- **Versionner** le pipeline comme le notebook (Source control → Commit sur `develop`).

---

## Conventions de code

- **Lakehouse = couche** (Bronze / Silver / Gold) · **Schéma = domaine** (ex. `CITY`).
- **Idempotence** : `CREATE SCHEMA IF NOT EXISTS` + `CREATE OR REPLACE TABLE`.
- **Ingestion fichier en PySpark**, **transformations Silver/Gold en Spark SQL** (`%%sql`).
- **Écriture cross-Lakehouse en SQL pur** via **nommage 4 parties** `workspace.lakehouse.schema.table`, **Lakehouses attachés** — pas besoin d'ABFSS :

```python
%%sql
CREATE SCHEMA IF NOT EXISTS ws_assisted_dev.lkh_slv_demo.CITY;

CREATE OR REPLACE TABLE ws_assisted_dev.lkh_slv_demo.CITY.city_safety AS
SELECT ... FROM CITY.city_safety;
```

> Exemple complet (Bronze→Silver→Gold) : voir [`fabric/nb_city_safety.ipynb`](./fabric/nb_city_safety.ipynb). Résultats de réf. : **Bronze 7350 → Silver 7350 → Gold 2028**.

---

## ⚠️ Limites & contraintes connues

> À lire **avant** de démarrer.

| Limite / contrainte | Impact | Contournement |
|---|---|---|
| **Items non créables / non déplaçables dans les dossiers de workspace depuis VS Code** | Un notebook ne peut pas être rangé dans un sous-dossier via l'arbre VS Code | Organiser **dans le portail** (Move to / New folder) puis **Refresh** dans VS Code |
| **`saveAsTable` vers un Lakehouse non-défaut échoue** | Erreur `Couldn't find a catalog to handle the identifier` | **4-part naming en Spark SQL** (`CREATE OR REPLACE TABLE ws.lakehouse.schema.table …`) avec Lakehouses **attachés** |
| **`Ctrl+S` en mode VFS sauvegarde vers Fabric, pas vers Git** | Le code peut ne pas être dans le clone local | Mode **Local + Download**, **Save As** local, ou **Git integration** portail |
| **Sessions / tokens qui expirent** | Appels API (ex. download notebook) en `401` après longue session | **Sign In** à nouveau ; en dépannage **Developer: Reload Window** ; purge du cache VFS si besoin |
| **Items téléchargés sous un dossier GUID (via extension)** | Repo moins lisible | Privilégier la **Git integration Fabric** (dossier `fabric/`, noms lisibles) |
| **Casse du nom de schéma (OneLake sensible à la casse)** | `CITY` ≠ `city` → doublons de schémas possibles | Fixer **une convention de casse** et s'y tenir |
| **Lakehouse par défaut doit être schema-enabled** | Sinon les schémas ne sont pas accessibles | Garder un Lakehouse **schema-enabled** épinglé (ou aucun) |
| **Démarrage Spark sur petite capacité (F2)** | *Cold start* de quelques minutes, quotas de sessions concurrentes | Anticiper le délai ; **high concurrency** à plusieurs ; coordonner les exécutions ; monter la capacité si besoin |
| **Upload de fichier vers `Files/` indisponible depuis VS Code** | — | Faire l'upload **dans le portail** |
| **Pas de planning mensuel natif** | Fréquences pipeline = minute / heure / jour / **semaine** uniquement | Pour du mensuel : planning hebdo + activité **If** (test du jour), ou déclenchement via API |
| **Pipeline non éditable visuellement dans VS Code** | L'authoring du canvas + le scheduling se font au **portail** | Créer/planifier au portail ; **versionner** ensuite via Git integration |

---

## Reprise de session (check-list)

> La session Spark et les variables en mémoire sont perdues entre deux jours ; les **données** Delta et les fichiers, eux, **persistent**.

1. **Sign In** Fabric.
2. `git checkout develop && git pull`.
3. Ouvrir le notebook → kernel **Microsoft Fabric Runtime** → **nouvelle session**.
4. **Ré-attacher** les Lakehouses + épingler le défaut.
5. Cellule de contrôle :
   ```python
   import notebookutils
   display(notebookutils.fs.ls("Files/CITY"))   # fichier source présent ?
   spark.sql("SHOW SCHEMAS").show()              # schéma attendu présent ?
   spark.sql("SHOW TABLES IN CITY").show()       # tables déjà écrites ?
   ```

---

## Bonnes pratiques

- 🔒 **Committer en fin de chaque session** (sinon risque de notebook vide le lendemain).
- 🤝 **« L'IA propose, l'équipe valide »** : relire le code Copilot.
- 🧱 **Lakehouse = couche, schéma = domaine**.
- ♻️ **Idempotence** (`IF NOT EXISTS` / `CREATE OR REPLACE`).
- 🧭 **Pas de valeurs en dur** : chemins relatifs / paramètres externalisés.
- 🧹 **Clear All Outputs** avant commit.
- 🌿 **`develop`** pour travailler, **`main`** pour le stable (PR revue).

---

## Structure du repo

```
fabric-ai-assisted/
├── fabric/
│   ├── nb_city_safety.ipynb         # notebook médaillon (Bronze→Silver→Gold)
│   ├── nb_city_safety_ui.ipynb      # notebook créé depuis l'UI (variante recommandée)
│   └── ppl_load_city_safety/        # data pipeline planifié (activité Notebook)
├── .gitignore                       # ignore le cache de l'extension Fabric (.vfscache, .stubs, dossier GUID…)
├── README.md                        # ce fichier — le processus
└── Mode_operatoire_Fabric_VSCode_Copilot_GitHub.md   # manuel détaillé + CI/CD
```

**Branches** : `develop` (travail) · `main` (stable, promotion par PR).

---

*Pour le détail pas-à-pas, les schémas d'architecture, le prompt Copilot type et le CI/CD (Deployment Pipelines DEV→UAT→PROD), voir le [mode opératoire complet](./Mode_operatoire_Fabric_VSCode_Copilot_GitHub.md).*
