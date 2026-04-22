USE fintech;

INSERT INTO clients (id, full_name, email, company, phone, country, status) VALUES
(1, 'Laura Mendoza', 'laura@axionretail.com', 'Axion Retail Pay', '+57 300 111 2233', 'Colombia', 'active'),
(2, 'Daniel Rojas', 'daniel@nexocapital.com', 'Banco Nexo Capital', '+52 55 1234 5678', 'Mexico', 'active')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

INSERT INTO users (id, client_id, full_name, username, email, password, role, status) VALUES
(1, NULL, 'Administrador Nova', 'admin', 'admin@fintechnova.local', '$2y$10$Diat4K9wxfmhmLfJ0V74K.w23yjcGLWIqkgt8IAWZvzDzqKmmocUq', 'admin', 'active'),
(2, 1, 'Laura Mendoza', 'cliente', 'laura@axionretail.com', '$2y$10$.WXITVVsdoXlCZggquJ7mekRdn8ZafWmuppiXVx3PevwldRrASlpq', 'client', 'active')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

INSERT INTO products (id, name, category, description, annual_return_hint, status) VALUES
(1, 'Nova Treasury Hub', 'Treasury', 'Panel de tesoreria y liquidez corporativa.', 6.50, 'active'),
(2, 'Yield Bridge', 'Investment', 'Producto de inversion digital para excedentes.', 9.80, 'active'),
(3, 'Signal Score API', 'Analytics', 'Motor de observacion y scoring transaccional.', 0.00, 'active')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO client_products (id, client_id, product_id, account_number, balance, status) VALUES
(1, 1, 1, 'AC-100200', 158000.00, 'active'),
(2, 1, 2, 'INV-883410', 42500.00, 'active'),
(3, 2, 3, 'AN-440021', 12000.00, 'active')
ON DUPLICATE KEY UPDATE balance = VALUES(balance);

INSERT INTO transactions (id, client_product_id, transaction_type, amount, description, created_by) VALUES
(1, 1, 'deposit', 25000.00, 'Capital inicial de tesoreria', 1),
(2, 2, 'deposit', 18000.00, 'Asignacion a estrategia de crecimiento', 1),
(3, 1, 'withdraw', 3500.00, 'Pago operativo de prueba', 2)
ON DUPLICATE KEY UPDATE description = VALUES(description);

