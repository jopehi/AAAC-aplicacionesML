<?php
$asset_base = '../../assets';
$root_prefix = '../..';
require_once __DIR__ . '/../../includes/bootstrap.php';
require_login('admin');

$flash = get_flash();
$error = '';
$editingClient = null;

if (isset($_GET['delete'])) {
    $deleteId = $_GET['delete'];
    $query = 'DELETE FROM clients WHERE id = ' . $deleteId;
    mysqli_query($conn, $query);
    log_activity($conn, current_user()['id'], current_user()['username'], 'delete', 'clients', $deleteId, 'Cliente eliminado desde panel');
    set_flash('success', 'Cliente eliminado.');
    redirect(root_url('admin/clients/index.php'));
}

if (isset($_GET['edit'])) {
    $editId = (int) $_GET['edit'];
    $editResult = mysqli_query($conn, 'SELECT * FROM clients WHERE id = ' . $editId . ' LIMIT 1');
    $editingClient = mysqli_fetch_assoc($editResult);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $clientId = (int) (isset($_POST['client_id']) ? $_POST['client_id'] : 0);
    $fullName = trim(isset($_POST['full_name']) ? $_POST['full_name'] : '');
    $email = trim(isset($_POST['email']) ? $_POST['email'] : '');
    $company = trim(isset($_POST['company']) ? $_POST['company'] : '');
    $phone = trim(isset($_POST['phone']) ? $_POST['phone'] : '');
    $country = trim(isset($_POST['country']) ? $_POST['country'] : '');
    $status = trim(isset($_POST['status']) ? $_POST['status'] : 'active');

    if ($fullName === '' || $email === '' || $company === '') {
        $error = 'Nombre, correo y empresa son obligatorios.';
    } else {
        if ($clientId > 0) {
            $stmt = mysqli_prepare($conn, 'UPDATE clients SET full_name = ?, email = ?, company = ?, phone = ?, country = ?, status = ? WHERE id = ?');
            mysqli_stmt_bind_param($stmt, 'ssssssi', $fullName, $email, $company, $phone, $country, $status, $clientId);
            mysqli_stmt_execute($stmt);
            mysqli_stmt_close($stmt);
            log_activity($conn, current_user()['id'], current_user()['username'], 'update', 'clients', $clientId, 'Cliente actualizado');
            set_flash('success', 'Cliente actualizado.');
        } else {
            $stmt = mysqli_prepare($conn, 'INSERT INTO clients (full_name, email, company, phone, country, status) VALUES (?, ?, ?, ?, ?, ?)');
            mysqli_stmt_bind_param($stmt, 'ssssss', $fullName, $email, $company, $phone, $country, $status);
            mysqli_stmt_execute($stmt);
            $newId = mysqli_insert_id($conn);
            mysqli_stmt_close($stmt);
            log_activity($conn, current_user()['id'], current_user()['username'], 'create', 'clients', $newId, 'Cliente creado');
            set_flash('success', 'Cliente creado.');
        }

        redirect(root_url('admin/clients/index.php'));
    }
}

$clients = mysqli_query(
    $conn,
    'SELECT c.*, COUNT(u.id) AS total_users, MAX(u.id) AS access_user_id
     FROM clients c
     LEFT JOIN users u ON u.client_id = c.id
     GROUP BY c.id
     ORDER BY c.id DESC'
);

$page_title = 'Gestion de clientes';
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
        <span class="section-kicker"><?php echo $editingClient ? 'Editar' : 'Nuevo'; ?></span>
        <h2><?php echo $editingClient ? 'Actualizar cliente' : 'Registrar cliente'; ?></h2>
        <form class="stack-form" method="post">
            <input type="hidden" name="client_id" value="<?php echo e($editingClient ? $editingClient['id'] : '0'); ?>">
            <label><span>Nombre</span><input type="text" name="full_name" value="<?php echo e($editingClient ? $editingClient['full_name'] : ''); ?>"></label>
            <label><span>Correo</span><input type="email" name="email" value="<?php echo e($editingClient ? $editingClient['email'] : ''); ?>"></label>
            <label><span>Empresa</span><input type="text" name="company" value="<?php echo e($editingClient ? $editingClient['company'] : ''); ?>"></label>
            <label><span>Telefono</span><input type="text" name="phone" value="<?php echo e($editingClient ? $editingClient['phone'] : ''); ?>"></label>
            <label><span>Pais</span><input type="text" name="country" value="<?php echo e($editingClient ? $editingClient['country'] : ''); ?>"></label>
            <label>
                <span>Estado</span>
                <select name="status">
                    <option value="active" <?php echo $editingClient && $editingClient['status'] === 'active' ? 'selected' : ''; ?>>Activo</option>
                    <option value="inactive" <?php echo $editingClient && $editingClient['status'] === 'inactive' ? 'selected' : ''; ?>>Inactivo</option>
                </select>
            </label>
            <button class="button" type="submit">Guardar cliente</button>
        </form>
    </article>

    <article class="app-card">
        <span class="section-kicker">Listado</span>
        <h2>Clientes registrados</h2>
        <p class="muted-copy">Para habilitar acceso, crea primero el cliente y luego usa la accion <strong>Crear acceso</strong> para asignarle usuario y clave.</p>
        <div class="table-wrap">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>Empresa</th>
                        <th>Acceso</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <?php while ($row = mysqli_fetch_assoc($clients)): ?>
                        <tr>
                            <td><?php echo e($row['id']); ?></td>
                            <td><?php echo e($row['full_name']); ?></td>
                            <td><?php echo e($row['company']); ?></td>
                            <td><?php echo (int) $row['total_users'] > 0 ? 'Habilitado' : 'Pendiente'; ?></td>
                            <td><?php echo e($row['status']); ?></td>
                            <td class="actions-cell">
                                <a href="?edit=<?php echo e($row['id']); ?>">Editar</a>
                                <a href="<?php echo e(root_url('admin/accounts/index.php?client_id=' . $row['id'])); ?>">Ver productos</a>
                                <?php if ((int) $row['total_users'] > 0): ?>
                                    <a href="<?php echo e(root_url('admin/users/index.php?edit=' . $row['access_user_id'])); ?>">Ver acceso</a>
                                <?php else: ?>
                                    <a href="<?php echo e(root_url('admin/users/index.php?client_id=' . $row['id'])); ?>">Crear acceso</a>
                                <?php endif; ?>
                                <a href="?delete=<?php echo e($row['id']); ?>" onclick="return confirm('Eliminar cliente?');">Eliminar</a>
                            </td>
                        </tr>
                    <?php endwhile; ?>
                </tbody>
            </table>
        </div>
    </article>
</section>

<?php include __DIR__ . '/../../includes/admin-footer.php'; ?>
