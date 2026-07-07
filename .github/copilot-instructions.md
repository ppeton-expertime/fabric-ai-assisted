# Instructions minimales - Data Engineer (Microsoft Fabric)

## Objectif
Produire des notebooks Fabric simples, robustes et lisibles pour l'ingestion, la transformation et l'exposition de donnees dans un Lakehouse.

## Regles minimales
1. Utiliser **PySpark** par defaut pour les traitements volumineux.
2. Lire/ecrire en **Delta** prioritairement.
3. Eviter le SQL inline long dans Python : preferer des cellules SQL dediees si la logique est majoritairement SQL.
4. Parametrer les notebooks via variables d'entree (pas de valeurs en dur sensibles).
5. Journaliser les etapes clefs (debut/fin, volumes, erreurs).
6. Organiser les donnees selon Bronze / Silver / Gold.
7. Utiliser **notebookutils** (Fabric) pour filesystem, secrets, orchestration.

## Equivalences commandes (Databricks / Synapse -> Fabric)

### Fichiers (FS)
| Besoin | Databricks (`dbutils`) | Synapse (`mssparkutils`) | Fabric (recommande) |
|---|---|---|---|
| Lister | `dbutils.fs.ls(path)` | `mssparkutils.fs.ls(path)` | `notebookutils.fs.ls(path)` |
| Copier | `dbutils.fs.cp(src, dst, recurse)` | `mssparkutils.fs.cp(src, dst, recurse)` | `notebookutils.fs.cp(src, dst, recurse)` |
| Deplacer | `dbutils.fs.mv(src, dst, recurse)` | `mssparkutils.fs.mv(src, dst, recurse)` | `notebookutils.fs.mv(src, dst, recurse)` |
| Supprimer | `dbutils.fs.rm(path, recurse)` | `mssparkutils.fs.rm(path, recurse)` | `notebookutils.fs.rm(path, recurse)` |
| Creer dossier | `dbutils.fs.mkdirs(path)` | `mssparkutils.fs.mkdirs(path)` | `notebookutils.fs.mkdirs(path)` |
| Lire fichier texte | `dbutils.fs.head(path, n)` | `mssparkutils.fs.head(path, n)` | `notebookutils.fs.head(path, n)` |
| Ecrire texte | `dbutils.fs.put(path, content, overwrite)` | `mssparkutils.fs.put(path, content, overwrite)` | `notebookutils.fs.put(path, content, overwrite)` |

### Secrets / credentials
| Besoin | Databricks | Synapse | Fabric |
|---|---|---|---|
| Lire un secret | `dbutils.secrets.get(scope, key)` | `mssparkutils.credentials.getSecret(vault, key)` | `notebookutils.credentials.getSecret(vault, key)` |

### Orchestration notebook
| Besoin | Databricks | Synapse | Fabric |
|---|---|---|---|
| Executer un notebook enfant | `dbutils.notebook.run(path, timeout, args)` | `mssparkutils.notebook.run(path, timeout, args)` | `notebookutils.notebook.run(path, timeout, args)` |
| Sortir une valeur | `dbutils.notebook.exit(value)` | `mssparkutils.notebook.exit(value)` | `notebookutils.notebook.exit(value)` |

### Widgets / parametres
| Besoin | Databricks | Synapse | Fabric |
|---|---|---|---|
| Parametres de cellule | `dbutils.widgets.*` | N/A | Preferer `notebookutils.notebook.run(..., args)` et variables d'entree |

## Bonnes pratiques de migration (tres court)
1. Remplacer d'abord les appels utilitaires (`dbutils` / `mssparkutils`) par `notebookutils`.
2. Verifier les chemins : favoriser les chemins Lakehouse/OneLake cibles Fabric.
3. Conserver la logique Spark (DataFrame) autant que possible, puis adapter l'orchestration.
4. Valider notebook par notebook (tests unitaires de transformations critiques + controle volumetrie).

## Squelette minimal de notebook Fabric (PySpark)
```python
from notebookutils import fs, credentials, notebook

# Parametres
input_path = "Files/bronze/source"
output_table = "silver_events"

# Lecture
df = spark.read.format("delta").load(input_path)

# Transformation minimale
df_clean = df.dropDuplicates()

# Ecriture
df_clean.write.mode("overwrite").format("delta").saveAsTable(output_table)
```
