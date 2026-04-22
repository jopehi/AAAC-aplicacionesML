<?php
$asset_base = 'assets';
$root_prefix = '.';
require_once __DIR__ . '/includes/bootstrap.php';

if (is_logged_in()) {
    if (current_user()['role'] === 'admin') {
        redirect(root_url('admin/dashboard.php'));
    }

    redirect(root_url('dashboard.php'));
}

$flash = get_flash();
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim(isset($_POST['username']) ? $_POST['username'] : '');
    $password = isset($_POST['password']) ? $_POST['password'] : '';

    if ($username === '' || $password === '') {
        $error = 'Completa usuario y clave.';
    } else {
        $stmt = mysqli_prepare($conn, 'SELECT id, client_id, full_name, username, email, password, role, status FROM users WHERE username = ? LIMIT 1');
        mysqli_stmt_bind_param($stmt, 's', $username);
        mysqli_stmt_execute($stmt);
        $result = mysqli_stmt_get_result($stmt);
        $user = mysqli_fetch_assoc($result);
        mysqli_stmt_close($stmt);

        if (!$user || $user['status'] !== 'active' || !password_verify($password, $user['password'])) {
            $error = 'Credenciales invalidas.';
            log_activity($conn, null, $username, 'login_failed', 'users', 0, 'Intento de acceso fallido');
        } else {
            login_user($user);
            log_activity($conn, (int) $user['id'], $user['username'], 'login', 'users', (int) $user['id'], 'Ingreso al sistema');

            if ($user['role'] === 'admin') {
                redirect(root_url('admin/dashboard.php'));
            }

            redirect(root_url('dashboard.php'));
        }
    }
}

$page_title = 'Acceso | Fintech Nova';
include __DIR__ . '/includes/header.php';
?>
<main class="auth-page">
    <section class="auth-shell container">
        <article class="auth-panel">
            <span class="section-kicker">Acceso</span>
            <h1>Ingresa al entorno de trabajo</h1>
            <p>Usa una cuenta de cliente o de administracion para entrar al dashboard correspondiente.</p>

            <?php if ($flash): ?>
                <div class="flash flash-<?php echo e($flash['type']); ?>"><?php echo e($flash['message']); ?></div>
            <?php endif; ?>

            <?php if ($error !== ''): ?>
                <div class="flash flash-error"><?php echo e($error); ?></div>
            <?php endif; ?>

            <form class="auth-form" method="post">
                <label>
                    <span>Usuario</span>
                    <input type="text" name="username" placeholder="admin o cliente">
                </label>
                <label>
                    <span>Clave</span>
                    <input type="password" name="password" placeholder="Ingresa tu clave">
                </label>
                <button class="button" type="submit">Entrar</button>
            </form>

            <div class="auth-links">
                <a class="button-secondary" href="<?php echo e(root_url('index.php')); ?>">Volver al inicio</a>
            </div>
        </article>
    </section>
</main>
<?php include __DIR__ . '/includes/footer.php'; ?>
