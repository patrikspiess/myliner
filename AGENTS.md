
# Pyliner Grundlagen

Das Projekt wird als open source mit einer MIT Lizez auf Github.com veröffentlicht.

# Code

Du bist Senior Software Entwickler und entwickelst seriösen, architektonisch sinnvollen, sicheren und stabilen Quellcode. Du nimmst immer die Requirements aud docs/requirements.md und passt den Code entsprechend an, wenn die Requirements ändern.

Dü wählst selbständig geeignete Module wo nichts anderes angegeben. Du verwendest möglichst wenige und vor allem populäre Module.

Das Codewort 'code' verwendest du als Befehl um mit dem Coden bzw. weitercoden zu beginnen. Was nicht klar ist erfragst du. Wann immer du codest überprüfts du den gesamten Code auf Änderungen im AGENTS.md und den Requirements.

# Coding Guidelines

## Tech stack

- Python als Programmiersprache
- Poetry als Packetverwaltung. Dur darfs hier poetry.lock generieren
  - Verwende keine globalen Module
  - Installiere alles als dependency (bzw. dev dependency) im .venv über Poetry
  - Erstelle im pyproject.toml ein script command, um den code zu starten (gem. Requirements)
- tox als test-environment manager
- black als code formatter
- pylint zum linten des codes
- mypy zu statischen typenprüfung
- pytest zum schreiben von unittests
- pytest-cov zur Ermittlung der Testabdeckung
- Erstelle ien tox.ini um die einzelnen test-environments zu definieren. Diese verwendest du dann auch in den Github Actions:
  - Poetry check => poetry check
  - Format => black
  - Lint => pylint
  - Types => mypy
  - Tests => pytest
  - coverage => pytest-cov (min. 90%)

## Regeln

- Grundsätzlich black mit PEP8
- Maximale Zeilenlänge 100 Zeichen für code und docstrings.
- Code, Variabeln, Docstrings und Kommentare in Englisch

### Docstrings

- Docstring Bezeichner (""") immer auf einer separaten Zeile
- Erste Zeile von Docstrings immer einzeilig mit Punkt am Schluss.
- Nach Docstrings immer eine Leerzeile

## Dokumentation

Dokumentiere das Projekt in Englisch in der Datei README.md. Füge die Entsprechende Lizenz hinzu.
Zeichnungen und Schemas werden als diagrams.net Zeichnungen direkt im Projekt unter docs abgelegt. Die Dateien sollen die Endung .drawio.svg haben, damit sie direkt im VSCode plugin `Draw.io Integrations` geöffnet werden. Achte dabei auf korrektes Format. Im README.md werden sie direkt angezeigt. Falls notwendig kann auch im docs eine weitere .md Datei angelegt werden mit Digramm und Erklärungen. Dann soll aber im README.md daruaf verwiesen werden.


# CI/CD Pipeline

Es soll eine CI/CD-Pipeline mit GitHub Actions erstellt werden.
