# Bosnia and Herzegovina — legislation as Markdown (LawCodex)

State-level legislation of **Bosnia and Herzegovina** (Bosna i Hercegovina / Босна и Херцеговина)
as plain Markdown, in the three official languages: Bosnian (`bs/`), Croatian (`hr/`) and
Serbian (`sr/`, Cyrillic).

Part of [LawCodex](https://github.com/LawCodex): one repository per jurisdiction.

## Sources

1. **Parliamentary Assembly of BiH** — https://www.parlament.ba ("Zakoni"): for each law the
   Assembly publishes a record (dates of adoption in both Houses, *Službeni glasnik BiH* number)
   and the text as PDF in bs/hr/sr:
   - *Prečišćeni tekstovi zakona* — consolidated texts prepared by the Assembly's secretariat.
     They are expressly **unofficial** ("Neslužbeni prečišćeni tekst … služi za internu
     upotrebu"); the date of consolidation is in the title.
   - *Usvojeni zakoni* / *Ranije usvojeni zakoni* — laws as adopted (original texts; many are
     amending laws). Only records that carry a text file are included: most older records
     ("Ranije usvojeni zakoni", 162 of 170) have no text attached.
2. **Constitutional Court of BiH** — https://www.ustavnisud.ba: the Constitution of BiH
   (Annex 4 to the Dayton Peace Agreement) in bs/hr/sr.

The official gazette publisher (JP NIO Službeni list BiH, https://www.sluzbenilist.ba) sells
access to its texts (subscription); it was not used.

## What is covered

| Directory (per language) | Content | bs | hr | sr |
|---|---|---|---|---|
| `ustav/` | Constitution of BiH | 1 | 1 | 1 |
| `preciscen-tekst/` (hr: `prociscen-tekst/`) | Unofficial consolidated texts by the Parliamentary Assembly (latest version of each) | 135 | 135 | 135 |
| `zakoni/<year>/` | Laws as adopted (original text), year of the *Službeni glasnik BiH* | 96 | 95 | 96 |

Consolidated files are named after the law (`zakon-o-prekrsajima.md`); adopted laws as
`<year>-<gazette no.>-<slug>.md` (e.g. `2015-75-15-zakon-o-izmjeni-zakona-o-placama-….md`).
Front matter: `title`, `identifier` (*Službeni glasnik BiH* number), `date` (adoption by the
second House), `status`, `text_version` (`unofficial_consolidated` / `original_as_adopted`),
`source`, `retrieved`. Consolidated texts get `status: in_force` (they are maintained by the
Assembly for laws in force); adopted laws get `status: unknown`.

The PDF text was extracted with `pdftotext`; article labels (Član/Članak/Члан) are `####`
headings, all-caps chapter lines `###`. Footnotes and formatting conventions of the
consolidated texts (bold/italic/underline marking each amendment) are lost in plain text.

## What is NOT covered

- Most state laws adopted before ~2014 whose text is not attached on parlament.ba; there is
  no free official full-text database of BiH state legislation.
- Entity legislation (Federation of BiH, Republika Srpska) and Brčko District.
- Secondary legislation; English translations (parlament.ba has none for these records).

## Licence

Legislative texts and official acts are excluded from copyright protection under the BiH
Law on Copyright and Related Rights. Texts reproduced as published by the institutions named above.

## Regenerating

```
python scripts/ba_fetch.py  ../_raw/ba
python scripts/ba_convert.py ../_raw/ba .
```

Needs `pdftotext` (poppler) and `scripts/requirements.txt`. Retrieved 2026-10-12.
