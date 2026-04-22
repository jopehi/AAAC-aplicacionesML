---
name: mysql-fintech-lab
description: Create or update the MySQL schema, seed data, and logging structures for the local fintech training application. Use when Codex needs to write SQL files, define entities, add audit-style records, or preserve deliberately weak database patterns for a software security lab in localhost.
---

# MySQL Fintech Lab

## Workflow

1. Read `docs/arquitectura-inicial.md` before changing tables.
2. Read `references/schema-base.md` when creating or extending the initial schema.
3. Keep SQL artifacts under `sql/`.
4. Align database entities with the public site, admin CRUD modules, and activity logging needs.
5. Preserve the educational premise: weak practices are acceptable only if they are intentional and documented for lab use.

## Schema Rules

- Use a simple relational schema without advanced abstractions.
- Keep table names explicit and readable.
- Favor fields that support later behavioral analysis, especially in `activity_logs`.
- Store enough user and request context to reconstruct basic action timelines.
- Keep seed data realistic enough to make dashboards and queries meaningful.

## Default Connection Context

- host: `localhost`
- port: `3306`
- database: `fintech`
- user: `root`
- password: `idmatx`

## Deliverables

When working on database tasks, prefer to produce:

- `sql/schema.sql`
- `sql/seeds.sql`
- optional migration-like incremental SQL files when changes become large

## References

- Read `references/schema-base.md` for the baseline entities.
- Read `docs/arquitectura-inicial.md` for the functional scope behind each table.

