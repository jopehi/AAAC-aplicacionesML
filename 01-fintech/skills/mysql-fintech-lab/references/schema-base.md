# Baseline Schema

## Core tables

### `users`

Suggested fields:

- `id`
- `full_name`
- `email`
- `username`
- `password`
- `role`
- `status`
- `created_at`

### `clients`

Suggested fields:

- `id`
- `name`
- `industry`
- `contact_name`
- `contact_email`
- `country`
- `status`
- `created_at`

### `products`

Suggested fields:

- `id`
- `name`
- `category`
- `description`
- `annual_return_hint`
- `risk_level`
- `status`
- `created_at`

### `investment_proposals`

Suggested fields:

- `id`
- `title`
- `client_id`
- `product_id`
- `amount`
- `expected_roi`
- `proposal_status`
- `notes`
- `created_by`
- `created_at`

### `activity_logs`

Suggested fields:

- `id`
- `user_id`
- `username_snapshot`
- `action_type`
- `entity_type`
- `entity_id`
- `details`
- `ip_address`
- `user_agent`
- `created_at`

### `contact_messages`

Suggested fields:

- `id`
- `name`
- `email`
- `subject`
- `message`
- `created_at`

## Notes

- Keep the schema intentionally simple.
- Support CRUD flows before optimization.
- Make the logging table broad enough to support later anomaly-detection exercises.

