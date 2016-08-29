TODO: translate readme...

# simple http server

Der Wert für den zu verwendenden Port kann über das Kommandozeilenargument
`--port` bzw. `-p` angegeben werden, also zum Beispiel wie folgt:

    >>> python3 server.py -p 3000
    listening on port 3000
    press CTRL-C to shut down the server
    [...]

Wird kein bestimmter Port angegeben, wird ein beliebiger freier Port genutzt.

Die auszuliefernden Daten sind im Unterordner `static` zu finden, die im Falle
von Fehler- oder Statusmeldungen auszuliefenden Daten befinden sich im
Unterordner `status`. Sollte man diese Pfade ändern wollen, so findet man die zu
ändernden Variablen in Zeile 24 und 25:

    DOCUMENT_ROOT_DIR = 'static'
    STATUS_DIR = 'status'

Bei einer Eingabe von `CTRL-C` wird der Server gestoppt. Dabei wartet der Server
noch auf den Abschluss von noch ausstehenden Anfragen. Besteht hierbei noch eine
Verbindung von einem Client zum Server, würde dieser somit noch bis zum
Beantworten dieser Anfrage warten, und erst danach herunterfahren. Möchte man
ein sofortiges Herunterfahren des Servers erzwingen, ist die erneute Eingabe von
`CTRL-C` nötig.
