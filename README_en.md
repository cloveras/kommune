# kommune

A Python script for downloading and archiving public post lists from Norwegian municipalities.

Currently supported:

- Vågan: https://vagan.kommune.no/politikk-og-organisasjon/innsyn/postliste/  
- Vestvågøy: https://www.vestvagoy.kommune.no/organisasjon/innsyn-i-post-og-saker/  
- Flakstad: https://flakstad.kommune.no/postliste/  
- Moskenes: https://moskenes.kommune.no/innsyn/postliste/

These municipal “post lists” are daily registers of official correspondence (letters, applications, decisions, etc.).  
Because the web search requires selecting **a single date** before you can view results, it’s impractical for larger searches.

This script downloads all content locally so you can search, browse, and archive everything offline — without dealing with per-day limitations.  
Additional functionality may be added later.

---

## About the websites

The starting pages look like this:  
https://vagan.kommune.no/politikk-og-organisasjon/innsyn/postliste/

Each post list page corresponds to **one day**, with a date parameter like:  
`fradato=2025-01-10`  
Example:  
https://vagan.kommune.no/innsyn.aspx?response=journalpost_postliste&MId1=731&scripturi=/innsyn.aspx&skin=infolink&fradato=2025-01-10T00:00:00

Each case (journal entry) has its own URL, such as:  
https://vagan.kommune.no/innsyn.aspx?response=journalpost_detaljer&journalpostid=2021113411&scripturi=/innsyn.aspx&skin=infolink&Mid1=731&

Cases are presented like this:  
![Example case](kommune.png)

---

## Usage

It’s recommended to use a Python virtual environment (especially on macOS):

```bash
python -m venv venv
source venv/bin/activate
```

Install required packages:

```bash
pip install -r requirements.txt
```

Run the script with the desired municipality, start date, and end date:

```bash
python download.py vagan 2024-01-01 2024-12-31
python download.py vestvagoy 2025-01-01 2025-01-15
```

---

## Data structure

For each case, the script creates its own directory with all downloaded files, for example:

```
$ ls -1 "archive-vagan/2025/01/10/2021113419 25_75 - Gbn 58_28 - Utskifting av oppdrettskar - Kleppstadveien 7 Polarsmolt AS"
Byggesak med saksnummer 25_75.pdf
Polarsmolt Fiskekar ø12.4m rev6.pdf
details.txt
```

The `details.txt` file contains metadata and text extracted from the page, such as:

```
$ cat "archive-vagan/2025/01/10/2021113419 25_75 - Gbn 58_28 - Utskifting av oppdrettskar - Kleppstadveien 7 Polarsmolt AS/details.txt"
Document ID: 25/757 - Building case no. 25/75
Archive ID: 25/75 - Gbn 58/28 - Replacement of fish tanks - Kleppstadveien 7 Polarsmolt AS
Journal date: 10.01.2025
Letter date: 10.01.2025
Responsible officer: Ayman Sawaha

Sender(s):
Marius N Lindgaard

Byggesak med saksnummer 25_75.pdf
Polarsmolt Fiskekar ø12.4m rev6.pdf
```

---

## Logging output

```bash
$ python ./download.py -f vagan 2025-01-10 2025-01-10
2025-01-10
  2021113333: 22/682 - Error in enforcement request
  2021113335: 24/1742 - Ownership unit - Rental of municipal housing
  2021113419: 25/75 - Gbn 58/28 - Replacement of fish tanks - Kleppstadveien 7 Polarsmolt AS
    - Byggesak med saksnummer 25_75.pdf
    - Polarsmolt Fiskekar ø12.4m rev6.pdf
  2021113448: 25/95 - Gbn 10/27 and 10/101 - self-declaration of exemption from concession
    - Egenerklæring.pdf
  2021113411: 22/3478 - Gbn 18/146 - Dried fish factory - Kløfterholmveien 10, Svolvær Saga Fisk AS
    - Completion of construction work.pdf
    - Permit for fire protection measures.pdf
```

The first number (`2021113333` etc.) is the `journalpostid` parameter extracted from each case URL.

---

## Notes

- The script waits **0–5 seconds** between each date to avoid hammering the municipal servers.  
- If a case directory already exists, it’s skipped by default.  
  Use the `-f` (force) flag to re-download:  
  ```bash
  python download.py -f vagan 2024-01-01 2024-12-31
  ```
- Output is stored under `archive-{municipality}/YYYY/MM/DD/...`.
