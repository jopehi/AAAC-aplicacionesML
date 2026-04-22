<?php

if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}

function current_user()
{
    return isset($_SESSION['user']) ? $_SESSION['user'] : null;
}

function is_logged_in()
{
    return current_user() !== null;
}

function login_user($user)
{
    $_SESSION['user'] = [
        'id' => (int) $user['id'],
        'client_id' => isset($user['client_id']) ? (int) $user['client_id'] : null,
        'full_name' => $user['full_name'],
        'username' => $user['username'],
        'role' => $user['role'],
    ];
}

function logout_user()
{
    unset($_SESSION['user']);
}

function require_login($role = null)
{
    $user = current_user();

    if (!$user) {
        set_flash('error', 'Debes iniciar sesion para continuar.');
        redirect(root_url('login.php'));
    }

    if ($role && $user['role'] !== $role) {
        set_flash('error', 'No tienes permiso para acceder a esta seccion.');

        if ($user['role'] === 'admin') {
            redirect(root_url('admin/dashboard.php'));
        }

        redirect(root_url('dashboard.php'));
    }
}

