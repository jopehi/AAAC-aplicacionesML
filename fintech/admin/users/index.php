<?php
$asset_base = '../../assets';
$root_prefix = '../..';
require_once __DIR__ . '/../../includes/bootstrap.php';
require_login('admin');

$flash = get_flash();
$error = '';
$editingUser = null;
$currentAdmin = current_user();
$prefillClient = null;
$prefillUsername = '';

if (isset($_GET['client_id']) && !isset($_GET['edit'])) {
    $prefillClientId = (int) $_GET['client_id'];
    $stmt = mysqli_prepare($conn, 'SELECT id, full_name, email, company FROM clients WHERE id = ? LIMIT 1');
    mysqli_stmt_bind_param($stmt, 'i', $prefillClientId);
    mysqli_stmt_execute($stmt);
    $prefillResult = mysqli_stmt_get_result($stmt);
    $prefillClient = mysqli_fetch_assoc($prefillResult);
    mysqli_stmt_close($stmt);

    if ($prefillClient) {
        $prefillUsername = strtolower(preg_replace('/[^a-z0-9]+/', '', strstr($prefillClient['email'], '@', true) ?: $prefillClient['full_name']));
    }
}

if (isset($_GET['delete'])) {
    $deleteId = (int) $_GET['delete'];

    if ($deleteId === (int) $currentAdmin['id']) {
        set_flash('error', 'No puedes eliminar tu propio usuario.');
        redirect(root_url('admin/users/index.php'));
    }

    $stmt = mysqli_prepare($conn, 'DELETE FROM users WHERE id = ?');
    mysqli_stmt_bind_param($stmt, 'i', $deleteId);
    mysqli_stmt_execute($stmt);
    mysqli_stmt_close($stmt);

    log_activity($conn, $currentAdmin['id'], $currentAdmin['username'], 'delete', 'users', $deleteId, 'Usuario eliminado desde panel');
    set_flash('success', 'Usuario eliminado.');
    redirect(root_url('admin/users/index.php'));
}

if (isset($_GET['edit'])) {
    $editId = (int) $_GET['edit'];
    $stmt = mysqli_prepare($conn, 'SELECT * FROM users WHERE id = ? LIMIT 1');
    mysqli_stmt_bind_param($stmt, 'i', $editId);
    mysqli_stmt_execute($stmt);
    $result = mysqli_stmt_get_result($stmt);
    $editingUser = mysqli_fetch_assoc($result);
    mysqli_stmt_close($stmt);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $userId = (int) (isset($_POST['user_id']) ? $_POST['user_id'] : 0);
    $clientIdRaw = isset($_POST['client_id']) ? trim($_POST['client_id']) : '';
    $fullName = trim(isset($_POST['full_name']) ? $_POST['full_name'] : '');
    $username = trim(isset($_POST['username']) ? $_POST['username'] : '');
    $email = trim(isset($_POST['email']) ? $_POST['email'] : '');
    $password = isset($_POST['password']) ? $_POST['password'] : '';
    $role = trim(isset($_POST['role']) ? $_POST['role'] : 'client');
    $status = trim(isset($_POST['status']) ? $_POST['status'] : 'active');
    $clientId = $clientIdRaw === '' ? null : (int) $clientIdRaw;

    if ($fullName === '' || $username === '' || $email === '') {
        $error = 'Nombre, usuario y correo son obligatorios.';
    } elseif (!in_array($role, ['admin', 'client'], true)) {
        $error = 'Rol no valido.';
    } elseif ($userId === 0 && $password === '') {
        $error = 'La clave es obligatoria al crear el usuario.';
    } elseif ($role === 'client' && (!$clientId || $clientId <= 0)) {
        $error = 'Debes asignar un cliente al usuario cliente.';
    } else {
        $stmt = mysqli_prepare($conn, 'SELECT id FROM users WHERE username = ? AND id <> ? LIMIT 1');
        mysqli_stmt_bind_param($stmt, 'si', $username, $userId);
        mysqli_stmt_execute($stmt);
        $duplicateResult = mysqli_stmt_get_result($stmt);
        $duplicateUser = mysqli_fetch_assoc($duplicateResult);
        mysqli_stmt_close($stmt);

        if ($duplicateUser) {
            $error = 'Ese nombre de usuario ya existe.';
        } else {
            $finalClientId = $role === 'admin' ? null : $clientId;

            if ($error === '' && $role === 'client' && $finalClientId) {
                $stmt = mysqli_prepare($conn, 'SELECT id FROM users WHERE client_id = ? AND role = ? AND id <> ? LIMIT 1');
                $clientRole = 'client';
                mysqli_stmt_bind_param($stmt, 'isi', $finalClientId, $clientRole, $userId);
                mysqli_stmt_execute($stmt);
                $assignedResult = mysqli_stmt_get_result($stmt);
                $assignedUser = mysqli_fetch_assoc($assignedResult);
                mysqli_stmt_close($stmt);

                if ($assignedUser) {
                    $error = 'Ese cliente ya tiene un acceso creado. Edita el existente.';
                }
            }

            if ($error === '' && $userId > 0) {
                if ($password !== '') {
                    $passwordHash = password_hash($password, PASSWORD_DEFAULT);
                    $stmt = mysqli_prepare(
                        $conn,
                        'UPDATE users SET client_id = ?, full_name = ?, username = ?, email = ?, password = ?, role = ?, status = ? WHERE id = ?'
                    );
                    mysqli_stmt_bind_param($stmt, 'issssssi', $finalClientId, $fullName, $username, $email, $passwordHash, $role, $status, $userId);
                } else {
                    $stmt = mysqli_prepare(
                        $conn,
                        'UPDATE users SET client_id = ?, full_name = ?, username = ?, email = ?, role = ?, status = ? WHERE id = ?'
                    );
                    mysqli_stmt_bind_param($stmt, 'isssssi', $finalClientId, $fullName, $username, $email, $role, $status, $userId);
                }

                mysqli_stmt_execute($stmt);
                mysqli_stmt_close($stmt);

                log_activity($conn, $currentAdmin['id'], $currentAdmin['username'], 'update', 'users', $userId, 'Usuario actualizado');
                set_flash('success', 'Usuario actualizado.');
            } elseif ($error === '') {
                $passwordHash = password_hash($password, PASSWORD_DEFAULT);
                $stmt = mysqli_prepare(
                    $conn,
                    'INSERT INTO users (client_id, full_name, username, email, password, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)'
                );
                mysqli_stmt_bind_param($stmt, 'issssss', $finalClientId, $fullName, $username, $email, $passwordHash, $role, $status);
                mysqli_stmt_execute($stmt);
                $newId = mysqli_insert_id($conn);
                mysqli_stmt_close($stmt);

                log_activity($conn, $currentAdmin['id'], $currentAdmin['username'], 'create', 'users', $newId, 'Usuario creado');
                set_flash('success', 'Usuario creado.');
            }

            redirect(root_url('admin/users/index.php'));
        }
    }
}

$clients = mysqli_query($conn, 'SELECT id, company, full_name FROM clients ORDER BY company ASC');
$users = mysqli_query(
    $conn,
    'SELECT u.*, c.company
     FROM users u
     LEFT JOIN clients c ON c.id = u.client_id
     ORDER BY u.id DESC'
);

$page_title = 'Gestion de usuarios';
include __DIR__ . '/../../includes/admin-header.php';
include __DIR__ . '/../../includes/admin-nav.php';
?>

<?php if ($flash): ?>
    <div class="flash flash-<?php echo e($flash['type']); ?>"><?php echo e($flash['message']); ?></div>
<?php endif; ?>

<?php if ($error !== ''): ?>
    <div class="flash flash-error"><?php echo e($error); ?></div>
<?php endif; ?>

<section class="app-grid two-columns">
    <article class="app-card">
        <span class="section-kicker"><?php echo $editingUser ? 'Editar' : 'Nuevo'; ?></span>
        <h2><?php echo $editingUser ? 'Actualizar usuario' : 'Crear usuario'; ?></h2>
        <?php if ($prefillClient && !$editingUser): ?>
            <div class="flash flash-success">Vas a crear acceso para <?php echo e($prefillClient['company']); ?>. Define usuario y clave para habilitar su ingreso.</div>
        <?php endif; ?>
        <form class="stack-form" method="post">
            <input type="hidden" name="user_id" value="<?php echo e($editingUser ? $editingUser['id'] : '0'); ?>">
            <label><span>Nombre completo</span><input type="text" name="full_name" value="<?php echo e($editingUser ? $editingUser['full_name'] : ($prefillClient ? $prefillClient['full_name'] : '')); ?>"></label>
            <label><span>Usuario</span><input type="text" name="username" value="<?php echo e($editingUser ? $editingUser['username'] : $prefillUsername); ?>"></label>
            <label><span>Correo</span><input type="email" name="email" value="<?php echo e($editingUser ? $editingUser['email'] : ($prefillClient ? $prefillClient['email'] : '')); ?>"></label>
            <label><span>Clave <?php echo $editingUser ? '(deja vacio para conservarla)' : ''; ?></span><input type="password" name="password"></label>
            <label>
                <span>Rol</span>
                <select name="role">
                    <option value="client" <?php echo (!$editingUser || $editingUser['role'] === 'client') ? 'selected' : ''; ?>>Cliente</option>
                    <option value="admin" <?php echo $editingUser && $editingUser['role'] === 'admin' ? 'selected' : ''; ?>>Admin</option>
                </select>
            </label>
            <label>
                <span>Cliente asociado</span>
                <select name="client_id">
                    <option value="">Sin cliente</option>
                    <?php while ($client = mysqli_fetch_assoc($clients)): ?>
                        <option value="<?php echo e($client['id']); ?>" <?php echo ($editingUser && (int) $editingUser['client_id'] === (int) $client['id']) || (!$editingUser && $prefillClient && (int) $prefillClient['id'] === (int) $client['id']) ? 'selected' : ''; ?>>
                            <?php echo e($client['company'] . ' - ' . $client['full_name']); ?>
                        </option>
                    <?php endwhile; ?>
                </select>
            </label>
            <label>
                <span>Estado</span>
                <select name="status">
                    <option value="active" <?php echo $editingUser && $editingUser['status'] === 'active' ? 'selected' : ''; ?>>Activo</option>
                    <option value="inactive" <?php echo $editingUser && $editingUser['status'] === 'inactive' ? 'selected' : ''; ?>>Inactivo</option>
                </select>
            </label>
            <button class="button" type="submit">Guardar usuario</button>
        </form>
    </article>

    <article class="app-card">
        <span class="section-kicker">Listado</span>
        <h2>Usuarios creados</h2>
        <p class="muted-copy">Los usuarios con rol <strong>client</strong> deben quedar asociados a un cliente para que al iniciar sesion vean sus productos y puedan transaccionar.</p>
        <div class="table-wrap">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Usuario</th>
                        <th>Nombre</th>
                        <th>Rol</th>
                        <th>Cliente</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <?php while ($row = mysqli_fetch_assoc($users)): ?>
                        <tr>
                            <td><?php echo e($row['id']); ?></td>
                            <td><?php echo e($row['username']); ?></td>
                            <td><?php echo e($row['full_name']); ?></td>
                            <td><?php echo e($row['role']); ?></td>
                            <td><?php echo e($row['company'] ? $row['company'] : 'N/A'); ?></td>
                            <td><?php echo e($row['status']); ?></td>
                            <td class="actions-cell">
                                <a href="?edit=<?php echo e($row['id']); ?>">Editar</a>
                                <a href="?delete=<?php echo e($row['id']); ?>" onclick="return confirm('Eliminar usuario?');">Eliminar</a>
                            </td>
                        </tr>
                    <?php endwhile; ?>
                </tbody>
            </table>
        </div>
    </article>
</section>

<?php include __DIR__ . '/../../includes/admin-footer.php'; ?>
