# Post-it per Ubuntu (GNOME)

App desktop per attaccare post-it sul desktop: note veloci e liste to-do
con checkbox. Scritta in **Python + GTK3**, salvata automaticamente su file
locale (JSON) in `~/.local/share/postit/notes.json`.

## Funzionalità

- **Più note** indipendenti, ognuna in una propria finestra.
- Ogni nota può essere **nota di testo** o **lista to-do** (checkbox).
- **Persistenza automatica**: ogni modifica viene salvata da sola (e al riavvio le note ricompaiono dove le hai lasciate).
- **Sul desktop**: di default le note restano nel "livello desktop", cioè le vedi solo quando il desktop è visibile (non in primo piano).
  Dal menu di ogni nota puoi attivare **"Sempre in primo piano"**, come fai con il terminale.
- **Grafica realistica**: carta con bordi irregolari, ombra e nastro adesivo, leggermente ruotata — come un post-it vero attaccato alla parete.
- Colore della carta personalizzabile (giallo, rosa, azzurro, verde, bianco).

## Installazione

```bash
cd ~/IA/Post-it
chmod +x install.sh
./install.sh
```

Lo script installa le dipendenze se mancano, crea la voce nel menu
applicazioni e abilita l'avvio automatico al login.

### Dipendenze (se vuoi installarle a mano)

```bash
sudo apt install python3-gi python3-gi-cairo python3-cairo \
    gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

> **Importante**: `python3-gi-cairo` è indispensabile (l'app usa `cairo.Context`
> per disegnare la carta). Se vedi l'errore
> `Couldn't find foreign struct converter for 'cairo.Context'`,
> significa che manca proprio questo pacchetto.

## Uso

| Azione | Come |
|---|---|
| Avviare | `python3 ~/IA/Post-it/main.py` (o dal menu applicazioni) |
| Nuova nota | Eseguire di nuovo `main.py`, oppure bottone **+** su una nota, oppure voce "Nuova nota" nel menu |
| Nascondere una nota | Crocetta **×** (resta salvata) |
| Eliminare | Menu (⋮) → **Elimina nota** |
| Cambiare tipo/colore/fissare | Menu (⋮) → Tipo di nota / Colore / Sempre in primo piano |
| Spostare la nota | Trascinare la barra in alto |
| Uscire | Menu (⋮) → Esci dall'app (o icona nella barra in alto, se disponibile) |

> **Nota sull'icona nella barra (tray)**: funziona se hai l'estensione
> *AppIndicator* di GNOME (attiva di default su Ubuntu).

> **Nota single-instance**: l'app è una sola istanza. Se è già aperta,
> rieseguire `main.py` non apre una seconda copia ma crea solo una nuova nota
> nell'istanza esistente. (Per forzare più istanze per test: `POSTIT_APP_ID=... python3 main.py`.)

## Comportamento sul desktop (Wayland vs Xorg)

L'app gestisce da sola la compatibilità col tuo ambiente:

- Su **Xorg** l'app gira direttamente sul backend X11: livello desktop e
  "sempre in primo piano" funzionano al 100%.
- Su **Wayland** (sessione GNOME di default) GTK3 gira come client nativo
  Wayland, dove *`set_keep_above` è un no-op*: per questo "sempre in primo
  piano" non funzionerebbe. L'app quindi **forza automaticamente il backend
  X11 (via XWayland)**, che il window manager di GNOME gestisce correttamente.

Il "livello desktop" è realizzato con una **finestra normale senza
decorazioni** (niente `_NET_WM_WINDOW_TYPE_DESKTOP` né `keep_below`):
su GNOME Shell quei meccanismi mettono la finestra *sotto* il desktop
(Nautilus, a tutto schermo) rendendola **insensibile al mouse**. Con una
finestra normale la nota riceve sempre click e digitazione, e quando apri
altre finestre queste la coprono (il comportamento "attaccata al desktop").
"Sempre in primo piano" usa `keep_above`.

Puoi forzare manualmente il backend con la variabile `POSTIT_BACKEND`
(es. `POSTIT_BACKEND=wayland python3 main.py`).

## Struttura

```
main.py              avvio
postit/app.py        applicazione (multi-note, tray, css)
postit/note_window.py finestra di una nota (testo/todo, menu)
postit/paper.py      disegno della carta (cairo)
postit/model.py      dati: Note e TodoItem
postit/storage.py    salvataggio JSON
install.sh           setup + autostart
```

## Prossimi passi (idee)

- Sincronizzazione su cloud o database
- Riordino dei task tramite drag & drop
- Data di scadenza / promemoria
