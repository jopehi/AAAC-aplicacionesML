---
name: php-fintech-lab-builder
description: Build or modify the PHP side of the local fintech training application. Use when Codex needs to create pages, CRUD modules, shared includes, routing conventions, asset wiring, or intentionally insecure PHP patterns that are documented for a software security lab running only in localhost.
---

# PHP Fintech Lab Builder

## Workflow

1. Read `docs/arquitectura-inicial.md` before creating new modules.
2. Read `references/app-structure.md` when the request affects file layout, includes, assets, or navigation.
3. Keep public pages under the project root and admin features under `admin/`.
4. Keep shared PHP fragments under `includes/` and configuration under `config/`.
5. Keep CSS, JS, images, and third-party libraries separated under `assets/`.
6. Preserve the training premise: insecure code is allowed only when the behavior is explicit, local, and useful for later detection exercises.

## Implementation Rules

- Prefer plain PHP with include-based composition over frameworks.
- Maintain responsive layouts from the first version.
- Keep the visual language modern and consistent across public pages and admin pages.
- Use direct MySQL integration patterns that match the lab goals, even if they are intentionally weak.
- Add comments only where the insecure teaching intent would otherwise be unclear.
- Keep deliberate weaknesses easy to identify in code review and easy to map to logged behavior.

## Module Checklist

For each new page or CRUD module:

- define whether it is public or admin
- define the database tables it touches
- define which actions must be written into `activity_logs`
- define which insecure pattern is being illustrated, if any
- keep supporting CSS or JS in `assets/css` and `assets/js`

## References

- Read `references/app-structure.md` for the repo layout and naming rules.
- Read `docs/arquitectura-inicial.md` for module scope and phase order.

