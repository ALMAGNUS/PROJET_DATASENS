# Hadoop / winutils — Windows + PySpark

Sur Windows, PySpark s’appuie sur des utilitaires Hadoop (`winutils.exe`) pour les accès fichiers. Sans eux, vous voyez des **WARN** du type :

- `Did not find winutils.exe`
- `HADOOP_HOME and hadoop.home.dir are unset`

Ce n’est pas toujours bloquant en `local[*]`, mais ça peut provoquer des erreurs à l’écriture Parquet.

## Automatique (DataSens)

Le code fixe **`HADOOP_HOME`** sur le dossier `hadoop/` à la racine du projet **si la variable n’est pas déjà définie**.

### Installer winutils en une commande (recommandé)

À la racine du dépôt :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/download_winutils.ps1
```

Ou double-clic / CMD : `scripts\download_winutils.bat`

Le script télécharge **`winutils.exe`** (branche Hadoop **3.3.5**, compatible Spark **3.5.x**) depuis [cdarlint/winutils](https://github.com/cdarlint/winutils) dans **`hadoop/bin/`**.  
Réinstallation : ajouter **`-Force`** au script PowerShell.

## Téléchargement manuel

1. Version compatible **Spark 3.5.x** ≈ **Hadoop 3.3.4–3.3.5**.
2. Télécharger `winutils.exe` depuis [cdarlint/winutils](https://github.com/cdarlint/winutils) — dossier `hadoop-3.3.x/bin/`.
3. Copier **`winutils.exe`** dans **`hadoop/bin/`**.

Structure attendue :

```
PROJET_DATASENS/
  hadoop/
    bin/
      winutils.exe
    README.md
```

## Optionnel : variable d’environnement

Si vous préférez un autre emplacement :

```powershell
$env:HADOOP_HOME = "C:\chemin\vers\hadoop"
# winutils doit être dans %HADOOP_HOME%\bin\
```

Référence : [Hadoop on Windows (wiki)](https://wiki.apache.org/hadoop/WindowsProblems).

### Messages encore visibles au démarrage

- **`Unable to load native-hadoop library`** : normal sur Windows — Hadoop n’embarque pas de binaire natif pour cette plateforme ; Spark utilise les classes Java. Pas d’impact en `local[*]` pour la lecture Parquet.
- **`spark.local.dir will be overridden`** : avertissement générique ; en mode `local[*]` sans YARN/Mesos, tu peux l’ignorer.

`get_spark_session()` réduit déjà ces bruits (options JVM + `setLogLevel("ERROR")`). S’il en reste, c’est souvent avant la prise en compte du niveau de log.
