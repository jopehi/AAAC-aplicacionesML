<?php

function e($value)
{
    return htmlspecialchars((string) $value, ENT_QUOTES, 'UTF-8');
}

function redirect($path)
{
    header('Location: ' . $path);
    exit;
}

function set_flash($type, $message)
{
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }

    $_SESSION['flash'] = [
        'type' => $type,
        'message' => $message,
    ];
}

function get_flash()
{
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }

    if (empty($_SESSION['flash'])) {
        return null;
    }

    $flash = $_SESSION['flash'];
    unset($_SESSION['flash']);

    return $flash;
}

function asset_url($path)
{
    global $asset_base;

    $base = isset($asset_base) ? rtrim($asset_base, '/') : 'assets';

    return $base . '/' . ltrim($path, '/');
}

function root_url($path = '')
{
    global $root_prefix;

    $prefix = isset($root_prefix) ? rtrim($root_prefix, '/') : '.';

    if ($path === '') {
        return $prefix;
    }

    return $prefix . '/' . ltrim($path, '/');
}

function money($amount)
{
    return '$' . number_format((float) $amount, 2);
}

function log_activity($conn, $userId, $username, $actionType, $entityType, $entityId, $details)
{
    $ipAddress = isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '127.0.0.1';
    $userAgent = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : 'CLI';

    $stmt = mysqli_prepare(
        $conn,
        'INSERT INTO activity_logs (user_id, username_snapshot, action_type, entity_type, entity_id, details, ip_address, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    );

    if (!$stmt) {
        return;
    }

    mysqli_stmt_bind_param(
        $stmt,
        'isssisss',
        $userId,
        $username,
        $actionType,
        $entityType,
        $entityId,
        $details,
        $ipAddress,
        $userAgent
    );
    mysqli_stmt_execute($stmt);
    mysqli_stmt_close($stmt);
}

