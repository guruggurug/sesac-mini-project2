# Stitch exports

`raw/` contains dated, immutable comparison snapshots and is never served by the application.
Production-ready Jinja templates live in `src/frontend/templates/` and must be migrated selectively rather than overwritten by a full Stitch export.

The CSS flow is:

```text
stitch-export/raw
-> src/frontend/templates
-> Tailwind content scan
-> src/frontend/static/css/index.css
```
