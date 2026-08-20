# Grundsatz

Myliner erzeugt eine oder mehrere animierte Linien. Die Linien bewegen sich über die
Zeichenfläche und hinterlassen Spuren. Überschneidungen werden heller; auslaufende Spuren werden
wieder dunkler.

# Ausführungsformen

- Die Desktop-Anwendung lässt sich mit `poetry run myliner [options]` starten.
- Der Engine lässt sich als Klasse in andere Python-Projekte importieren.
- Die Animation steht als Web-Komponente für Webseiten zur Verfügung.
- Eine VS-Code-Extension zeigt die Animation in einer eigenen Explorer-View an.
- Das `README.md` dokumentiert Installation, Optionen und Bedienung aller Ausführungsformen.

# Desktop-Anwendung

## Auflösung

Im Fenstermodus ist die längere Seite höchstens 800 Pixel groß. Die kürzere Seite ergibt sich aus
dem Seitenverhältnis des Monitors. Optional steht ein Fullscreen-Modus in nativer Auflösung zur
Verfügung.

## Initialisierung

Jede Linie startet mit zwei zufälligen Punkten auf gegenüberliegenden Seiten der Zeichenfläche.
Die Standardwerte sind:

- Farbe: `#FF6600` beziehungsweise RGB `255, 102, 0`.
- Helligkeit: `0`. Dieser Wert entspricht der normalen Linienfarbe. Größere Werte hellen sie in
  Richtung Weiß auf. Beim Entfernen alter Frames darf der Wert nie unter `0` fallen.
- Dicke: `3` Pixel.
- History: `150` Frames pro Linie.
- Speed: `10` neue Frames pro Sekunde.
- Richtung eines Endpunkts: `15` bis `165` Grad zur jeweiligen Seite.
- Versatz eines Endpunkts pro Frame: `5` bis `20` Pixel.

## Zeichnen und Fading

Ein Frame verbindet die beiden aktuellen Endpunkte. Bereits belegte Pixel werden heller. Danach
bewegen sich beide Endpunkte um ihren Versatz weiter. Erreicht ein Punkt den Rand, werden Richtung
und Versatz neu gewählt, sodass er sich wieder in die Zeichenfläche bewegt.

Jede Linie verwaltet ihre eigene History. Frames außerhalb dieser History werden entfernt und
verringern Helligkeit und Abdeckung der betroffenen Pixel. Visuell dunkeln alte Spuren schrittweise
bis Schwarz ab.

Wird die Linienanzahl reduziert, wird jeweils die älteste Linie einschließlich ihrer vollständigen
History sofort entfernt. Es dürfen keine Restspuren dieser Linie sichtbar bleiben.

## Performance

Speed ist ein zentraler Qualitätsfaktor. Die Animation soll auch mit mehreren dicken Linien,
langer History und hoher Speed-Einstellung flüssig laufen. Pixel-, Helligkeits- und
Framebuffer-Verarbeitung sollen deshalb möglichst vektorisiert mit NumPy-Arrays erfolgen.

## Steuerung

- `q/a`: Linienanzahl um eins erhöhen oder die älteste Linie entfernen, Bereich 1 bis 20.
- `w/s`: Speed auf den nächsten oder vorherigen Fibonacci-Wert setzen, mindestens 1.
- `e/d`: Liniendicke um eins erhöhen oder verringern, mindestens 1.
- `h`: Hilfe ein- oder ausblenden; die Animation läuft weiter.
- `f`: Fullscreen ein- oder ausschalten.
- `Esc` oder Mausklick: Anwendung beenden.

Die Speed-Einstellung hat keine feste technische Obergrenze. Die verfügbare Rendering-Leistung ist
die einzige praktische Begrenzung. Das Hilfe-Overlay zeigt Paare als
`[Taste]/[Taste]: [Beschreibung]` und Umschalter als `[Taste]: [Beschreibung]` an.

# Browser-Demo

Die React-Demo bindet `<myliner-overlay>` als Overlay ein. Sie lässt sich per Link, Button oder
`Ctrl+Alt+P` starten. Das schwarze, gerahmte Overlay ist standardmäßig 50% des Viewports groß und
zentriert; Größe und Position sind konfigurierbar.

Die Taste `f` schaltet Browser und Komponente gemeinsam in den Fullscreen-Modus und wieder zurück.
Ein kleiner lokaler Webserver wird nur bei Bedarf mit `poetry run myliner-web` gestartet. Start,
Bedienung und Beenden sind im `README.md` dokumentiert.

# VS-Code-Extension

Die Extension stellt nach dem Muster von VS Code Pets eine kleine, einklappbare Webview direkt im
Explorer bereit. Sie registriert keinen eigenen Activity-Bar-Container, ersetzt oder benennt den
Explorer nicht um und öffnet keinen Editor-Tab. Die Linien erscheinen direkt in dieser View.

Die View verwendet die Web-Komponente für ein konsistentes Rendering. Sie ist rahmenlos und
transparent, sodass die aktuelle VS-Code-Seitenleistenfarbe sichtbar bleibt. Ein Klick beendet die
Animation nicht. Die Animation startet automatisch mit folgenden kompakten Einstellungen:

- zwei Linien;
- Speed `10`;
- Dicke `1` Pixel;
- Endpunktversatz `1` bis `10` Pixel.

Die Extension registriert keine Tastenkürzel. Im Titelmenü stehen genau vier Buttons bereit: Linie
entfernen, Linie hinzufügen, Speed reduzieren und Speed erhöhen. Diese Aktionen sowie
`Myliner: Show Panel` sind auch in der Command Palette verfügbar.

Es gibt keine Befehle für Start, Stop, Dicke, Hilfe oder Fullscreen. Die View zeigt kein
Hilfe-Overlay.

# Dokumentation

- Alle Komponenten, Klassen, Methoden und Funktionen erhalten kurze, technisch aussagekräftige
  Docstrings beziehungsweise JSDoc-Kommentare in Englisch.
- Komplexe Abläufe werden nur an geeigneten Stellen mit kurzen englischen Kommentaren erklärt.
- Das Kernmodul wird in einer eigenen, vom `README.md` verlinkten Markdown-Datei dokumentiert.
- Technische Zeichnungen liegen als editierbare diagrams.net-Dateien mit der Endung
  `.drawio.svg` unter `docs/`.
