<?php
$asset_base = '../../assets';
$root_prefix = '../..';
require_once __DIR__ . '/../../includes/bootstrap.php';
require_login('admin');

$flash = get_flash();
$userFilter = trim(isset($_GET['username']) ? $_GET['username'] : '');
$actionFilter = trim(isset($_GET['action_type']) ? $_GET['action_type'] : '');
$entityFilter = trim(isset($_GET['entity_type']) ? $_GET['entity_type'] : '');
$detailFilter = trim(isset($_GET['details']) ? $_GET['details'] : '');

$sql = '
    SELECT id, user_id, username_snapshot, action_type, entity_type, entity_id, details, ip_address, user_agent, created_at
    FROM activity_logs
    WHERE 1=1
';

$params = [];
$types = '';

if ($userFilter !== '') {
    $sql .= ' AND username_snapshot = ?';
    $types .= 's';
    $params[] = $userFilter;
}

if ($actionFilter !== '') {
    $sql .= ' AND action_type = ?';
    $types .= 's';
    $params[] = $actionFilter;
}

if ($entityFilter !== '') {
    $sql .= ' AND entity_type = ?';
    $types .= 's';
    $params[] = $entityFilter;
}

if ($detailFilter !== '') {
    $sql .= ' AND details LIKE ?';
    $types .= 's';
    $params[] = '%' . $detailFilter . '%';
}

$sql .= ' ORDER BY id DESC LIMIT 200';

$stmt = mysqli_prepare($conn, $sql);

if ($types !== '') {
    mysqli_stmt_bind_param($stmt, $types, ...$params);
}

mysqli_stmt_execute($stmt);
$logs = mysqli_stmt_get_result($stmt);
mysqli_stmt_close($stmt);

$usernames = mysqli_query($conn, 'SELECT DISTINCT username_snapshot FROM activity_logs WHERE username_snapshot IS NOT NULL AND username_snapshot <> "" ORDER BY username_snapshot ASC');
$actions = mysqli_query($conn, 'SELECT DISTINCT action_type FROM activity_logs ORDER BY action_type ASC');
$entities = mysqli_query($conn, 'SELECT DISTINCT entity_type FROM activity_logs ORDER BY entity_type ASC');

$page_title = 'Auditoria y logs';
include __DIR__ . '/../../includes/admin-header.php';
include __DIR__ . '/../../includes/admin-nav.php';
?>

<?php if ($flash): ?>
    <div class="flash flash-<?php echo e($flash['type']); ?>"><?php echo e($flash['message']); ?></div>
<?php endif; ?>

<section class="app-card">
    <div class="section-heading compact">
        <div>
            <span class="section-kicker">Auditoria</span>
            <h2>Revision de eventos del sistema</h2>
        </div>
    </div>

    <form class="inline-filter" method="get">
        <label>
            <span>Usuario</span>
            <select name="username">
                <option value="">Todos</option>
                <?php while ($row = mysqli_fetch_assoc($usernames)): ?>
                    <option value="<?php echo e($row['username_snapshot']); ?>" <?php echo $userFilter === $row['username_snapshot'] ? 'selected' : ''; ?>>
                        <?php echo e($row['username_snapshot']); ?>
                    </option>
                <?php endwhile; ?>
            </select>
        </label>

        <label>
            <span>Accion</span>
            <select name="action_type">
                <option value="">Todas</option>
                <?php while ($row = mysqli_fetch_assoc($actions)): ?>
                    <option value="<?php echo e($row['action_type']); ?>" <?php echo $actionFilter === $row['action_type'] ? 'selected' : ''; ?>>
                        <?php echo e($row['action_type']); ?>
                    </option>
                <?php endwhile; ?>
            </select>
        </label>

        <label>
            <span>Entidad</span>
            <select name="entity_type">
                <option value="">Todas</option>
                <?php while ($row = mysqli_fetch_assoc($entities)): ?>
                    <option value="<?php echo e($row['entity_type']); ?>" <?php echo $entityFilter === $row['entity_type'] ? 'selected' : ''; ?>>
                        <?php echo e($row['entity_type']); ?>
                    </option>
                <?php endwhile; ?>
            </select>
        </label>

        <label>
            <span>Detalle contiene</span>
            <input type="text" name="details" value="<?php echo e($detailFilter); ?>" placeholder="Buscar en detalle">
        </label>

        <button class="button" type="submit">Filtrar</button>
        <a class="button-secondary small-button" href="<?php echo e(root_url('admin/logs/index.php')); ?>">Limpiar</a>
    </form>
</section>

<section class="app-card">
    <div class="table-wrap">
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Fecha</th>
                    <th>Usuario</th>
                    <th>Accion</th>
                    <th>Entidad</th>
                    <th>ID entidad</th>
                    <th>Detalle</th>
                    <th>IP</th>
                    <th>User Agent</th>
                </tr>
            </thead>
            <tbody>
                <?php while ($row = mysqli_fetch_assoc($logs)): ?>
                    <tr>
                        <td><?php echo e($row['id']); ?></td>
                        <td><?php echo e($row['created_at']); ?></td>
                        <td><?php echo e($row['username_snapshot']); ?></td>
                        <td><?php echo e($row['action_type']); ?></td>
                        <td><?php echo e($row['entity_type']); ?></td>
                        <td><?php echo e($row['entity_id']); ?></td>
                        <td><?php echo e($row['details']); ?></td>
                        <td><?php echo e($row['ip_address']); ?></td>
                        <td><?php echo e($row['user_agent']); ?></td>
                    </tr>
                <?php endwhile; ?>
            </tbody>
        </table>
    </div>
</section>

<?php include __DIR__ . '/../../includes/admin-footer.php'; ?>

