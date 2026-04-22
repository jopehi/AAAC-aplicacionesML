# App Structure

## Root layout

Use this structure as the default target:

```text
admin/
assets/css/
assets/js/
assets/img/
assets/vendor/
config/
docs/
includes/
skills/
sql/
```

## PHP conventions

- Public entry pages stay at the project root.
- Admin pages stay under `admin/` and can be grouped by entity.
- Shared fragments use `includes/header.php`, `includes/footer.php`, `includes/navbar.php`, and similar files.
- Database access starts in `config/database.php`.

## UI conventions

- Keep a single global stylesheet such as `assets/css/main.css` at the beginning.
- Add page-specific JS only when interaction requires it.
- Treat the public site and admin panel as one product family with two views.

## Lab conventions

- Do not hide insecure choices behind abstraction if the teaching goal is to inspect them later.
- Keep the code runnable in Laragon with PHP and MySQL on localhost.
- Favor readability over architecture purity in the first iterations.

