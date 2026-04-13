# Industry Mapper — Mapping Logic

## Overview

`industry_mapper.py` maps the raw Polish `industry` text from `job_offers` into two new columns:

- **`mapped_industry`** — English category name (e.g., `"IT & Digital Tech"`)
- **`kw_industry`** — comma-separated list of matched English keywords (e.g., `"programming, testing"`)

Source column `industry` contains comma-separated Polish (or English) industry tags scraped from pracuj.pl, e.g.:
```
IT - Administracja, IT - Rozwój oprogramowania, Programowanie
Praca fizyczna, Produkcja, Pracownicy produkcji
```

---

## Matching Algorithm

### Word Boundary Matching

Keywords are matched using **regex word boundaries**, not substring `in`:

```python
pattern = r'(?:^|[\s,/;()])' + re.escape(keyword) + r'(?:[\s,/;()]|$)'
```

This prevents false matches like `'pr'` in `"Praca fizyczna"` or `'it'` in `"Budownictwo"`.

### Priority System

Categories are evaluated in priority order (1 = highest). The **first category with any keyword match wins** — remaining categories are skipped.

### Exclude Keywords

Categories can optionally define `exclude_keywords` — a list of keywords that, if found in the industry text, cause the category to be **skipped** even if its own keywords match. This allows lower-priority categories to "win" in specific contexts.

Example: Technical Sales & B2B (priority 5) excludes `nieruchomości` — when the industry text contains both `Sprzedaż` and `Nieruchomości`, Technical Sales is skipped and the job falls through to Construction & Real Estate (priority 7).

### Keyword Structure

Each category uses a `dict {polish_keyword: english_translation}`:

```python
'keywords': {
    'programowanie': 'programming',
    'testowanie': 'testing',
    ...
}
```

This guarantees 1:1 pairing between PL and EN keywords (no list length mismatch possible).

---

## Categories

| Priority | Category | Keywords | Excludes | Examples (PL) |
|:--------:|----------|:--------:|:--------:|---------------|
| 1 | IT & Digital Tech | 34 | — | `it - administracja`, `programowanie`, `testowanie`, `ux/ui`, `helpdesk` |
| 2 | Medicine & Pharma | 13 | — | `medycyna`, `farmacja`, `apteka`, `lekarz`, `biotechnologia` |
| 3 | Finance & Banking | 20 | — | `finanse`, `księgowość`, `audyt`, `bankowość`, `ubezpieczenia` |
| 4 | Engineering & Design | 16 | — | `inżynieria`, `automatyka`, `projektowanie`, `elektronika`, `r&d` |
| 5 | Technical Sales & B2B | 9 | `nieruchomości` | `sprzedaż`, `usługi profesjonalne`, `b2b`, `energia`, `motoryzacja` |
| 6 | Skilled Trades | 14 | — | `elektryk`, `mechanik`, `monter`, `spawacz`, `utrzymanie ruchu` |
| 7 | Construction & Real Estate | 11 | — | `budownictwo`, `nieruchomości`, `infrastruktura`, `mieszkaniowe`, `facility management` |
| 8 | Logistics & Supply Chain | 13 | — | `transport`, `logistyka`, `spedycja`, `łańcuch dostaw`, `kierowca` |
| 9 | Legal & Compliance | 9 | — | `prawo`, `prawnik`, `compliance`, `bhp`, `zamówienia publiczne` |
| 10 | Marketing & Creative | 13 | — | `marketing`, `e-commerce`, `social media`, `reklama`, `seo` |
| 11 | HR & Recruitment | 10 | — | `human resources`, `rekrutacja`, `kadry`, `employer branding` |
| 12 | Education & Science | 9 | — | `edukacja`, `szkolenia`, `nauka`, `szkolnictwo`, `nauczyciel` |
| 13 | Retail & Front Office | 12 | — | `sprzedawca`, `kasjer`, `sieci handlowe`, `odzież`, `fmcg` |
| 14 | Customer Service & Admin | 7 | — | `obsługa klienta`, `call center`, `recepcja`, `administracja biurowa` |
| 15 | Hospitality & Gastronomy | 8 | — | `hotelarstwo`, `gastronomia`, `turystyka`, `katering` |
| 16 | General Labor | 14 | — | `praca fizyczna`, `produkcja`, `kurier`, `ochrona`, `sprzątanie` |

---

## Priority Implications

Because the first matching category wins:

- A job with `"IT - Administracja, Finanse / Bankowość"` maps to **IT & Digital Tech** (priority 1 > 3)
- A job with `"Sprzedaż, Praca fizyczna"` maps to **Technical Sales & B2B** (priority 5 > 16)
- A job with `"Budownictwo, Inżynieria, Projektowanie"` maps to **Engineering & Design** (priority 4 > 7)
- A job with `"Nieruchomości, Sprzedaż"` maps to **Construction & Real Estate** (priority 7) — Technical Sales (priority 5) is skipped via `exclude_keywords`

Jobs that match no keywords get `mapped_industry = NULL`.
