# Note di versione / Changelog

Tutte le modifiche rilevanti a **Postitino** sono documentate in questo file.

---

## [1.0.0] - 2026-10-01

### 🚀 Nuove funzionalità (Features)

- **Liste To-Do interattive**:
  - Caselle di spunta (checkbox) con testo barrato per i task completati.
  - Riordino dei task tramite Drag & Drop con maniglia dedicata (`⋮⋮`).
  - Riordino da tastiera rapido tramite scorciatoie `Alt+Su` e `Alt+Giù`.
  - Pulsante e voce di menu per la pulizia immediata di tutti i task completati.
- **Zoom dinamico del testo**:
  - Modifica della dimensione del font per singola nota.
  - Scorciatoie da tastiera: `Ctrl++` (ingrandisci), `Ctrl+-` (rimpicciolisci), `Ctrl+0` (reimposta a 13pt).
  - Zoom rapido con mouse tramite `Ctrl` + rotellina del mouse sopra la nota.
  - Sottomenu dedicato "Dimensione testo" nel menu opzioni.
- **Integrazione Tray Icon (Ayatana / AppIndicator)**:
  - Icona nella barra superiore di sistema di GNOME/Ubuntu.
  - Voci rapide "Nuova nota", "Mostra tutte le note" e "Nascondi tutte le note".
  - Elenco dinamico delle note aperte con spunta di visibilità (`✓`) per aprire/nascondere singole note al volo.
- **Persistenza & Memoria posizioni**:
  - Salvataggio automatico debounced (~400ms) su `~/.local/share/postit/notes.json`.
  - Salvataggio automatico del file di backup di sicurezza (`notes.json.bak`) con fallback in caso di crash.
  - Piena persistenza delle coordinate dello schermo: nascondere una nota (`×` o `Ctrl+W`) e riaprirla la posiziona esattamente dove si trovava prima.
- **Opzione Nota dritta (0°)**:
  - Possibilità di azzerare la rotazione casuale e raddrizzare la nota direttamente dal menu.
- **Copia negli appunti (`Ctrl+Shift+C`)**:
  - Copia dell'intero contenuto della nota; per le liste to-do genera automaticamente testo formattato in Markdown (`- [ ]`, `- [x]`).
- **Conferma eliminazione nota**:
  - Dialog di conferma su eliminazione dal menu o tramite scorciatoia `Ctrl+Shift+D`.
- **Finestra Informazioni nativa (`Gtk.AboutDialog`)**:
  - Finestra About conforme agli standard GNOME/GTK con logo vettoriale, versione, descrizione delle funzionalità, link GitHub e crediti.
- **Scorciatoie globali per nota**:
  - `Ctrl+N`: Nuova nota
  - `Ctrl+W`: Nascondi nota
  - `Ctrl+Shift+C`: Copia negli appunti
  - `Ctrl+Shift+D`: Elimina nota con conferma

### 🛠️ Architettura e Compatibilità

- **Backend Wayland / X11**: forzatura automatica su XWayland (`GDK_BACKEND=x11`) per garantire il funzionamento di "Sempre in primo piano" e l'interazione mouse su desktop GNOME/Mutter.
- **Finestra frameless con resize preciso**: maniglie di ridimensionamento sui 4 bordi e sui 4 angoli con priorità geometrica corretta.
- **Anti-stallo drag**: timeout di sicurezza di 6 secondi per evitare il blocco del puntatore su XWayland/multi-monitor in caso di eventi release persi.
- **Localizzazione UI (i18n)**: supporto bilingue (Inglese predefinito, Italiano integrato) rilevato automaticamente da locale di sistema o sovrascrivibile con `POSTIT_LANG`.
- **Attribuzione IA**: trasparenza sullo sviluppo in pair programming con DeepSeek Flash.
