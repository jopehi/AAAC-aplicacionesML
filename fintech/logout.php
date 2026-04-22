<?php
$asset_base = 'assets';
$root_prefix = '.';
require_once __DIR__ . '/includes/bootstrap.php';

$user = current_user();

if ($user) {
    log_activity($conn, $user['id'], $user['username'], 'logout', 'users', $user['id'], 'Cierre de sesion');
}

logout_user();
set_flash('success', 'Sesion finalizada.');
redirect(root_url('login.php'));

