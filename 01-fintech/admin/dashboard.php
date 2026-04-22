<?php
$asset_base = '../assets';
$root_prefix = '..';
require_once __DIR__ . '/../includes/bootstrap.php';
require_login('admin');

$flash = get_flash();

$stats = [
    'clients' => 0,
    'products' => 0,
    'accounts' => 0,
    'transactions' => 0,
    'users' => 0,
];

foreach ($stats as $table => $value) {
    $tableName = $table === 'accounts' ? 'client_products' : $table;
    if ($table === 'transactions') {
        $tableName = 'transactions';
    } elseif ($table === 'products') {
        $tableName = 'products';
    } elseif ($table === 'clients') {
        $tableName = 'clients';
    } elseif ($table === 'users') {
        $tableName = 'users';
    }

    $result = mysqli_query($conn, 'SELECT COUNT(*) AS total FROM ' . $tableName);
    $row = mysqli_fetch_assoc($result);
    $stats[$table] = (int) $row['total'];
}

$logs = mysqli_query(
    $conn,
    'SELECT username_snapshot, action_type, entity_type, details, created_at
     FROM activity_logs
     ORDER BY id DESC
     LIMIT 10'
);

$page_title = 'Resumen general';
include __DIR__ . '/../includes/admin-header.php';
include __DIR__ . '/../includes/admin-nav.php';
?>

<?php if ($flash): ?>
    <div class="flash flash-<?php echo e($flash['type']); ?>"><?php echo e($flash['message']); ?></div>
<?php endif; ?>

<section class="app-grid metrics-grid">
    <article class="app-card">
        <p class="metric-label">Clientes</p>
        <span class="metric-value"><?php echo e($stats['clients']); ?></span>
    </article>
    <article class="app-card">
        <p class="metric-label">Productos</p>
        <span class="metric-value"><?php echo e($stats['products']); ?></span>
    </article>
    <article class="app-card">
        <p class="metric-label">Cuentas</p>
        <span class="metric-value"><?php echo e($stats['accounts']); ?></span>
    </article>
    <article class="app-card">
        <p class="metric-label">Transacciones</p>
        <span class="metric-value"><?php echo e($stats['transactions']); ?></span>
    </article>
    <article class="app-card">
        <p class="metric-label">Usuarios</p>
        <span class="metric-value"><?php echo e($stats['users']); ?></span>
    </article>
</section>

<section class="app-grid two-columns">
    <article class="app-card">
        <span class="section-kicker">Atajos</span>
        <h2>Operaciones rapidas</h2>
        <div class="action-list">
            <a class="button-secondary block-button" href="<?php echo e(root_url('admin/clients/index.php')); ?>">Administrar clientes</a>
            <a class="button-secondary block-button" href="<?php echo e(root_url('admin/accounts/index.php')); ?>">Ver productos de clientes</a>
            <a class="button-secondary block-button" href="<?php echo e(root_url('admin/products/index.php')); ?>">Administrar productos</a>
            <a class="button-secondary block-button" href="<?php echo e(root_url('admin/users/index.php')); ?>">Administrar usuarios</a>
            <a class="button-secondary block-button" href="<?php echo e(root_url('admin/logs/index.php')); ?>">Revisar auditoria</a>
            <a class="button-secondary block-button" href="<?php echo e(root_url('dashboard.php')); ?>">Ver dashboard de cliente</a>
        </div>
    </article>

    <article class="app-card">
        <span class="section-kicker">Contexto</span>
        <h2>Base operativa</h2>
        <p class="muted-copy">El panel ya puede administrar clientes y productos, mientras el dashboard de cliente procesa movimientos basicos con saldos ficticios y deja evidencia en el log de actividad.</p>
    </article>
</section>

<section class="app-card">
    <div class="section-heading compact">
        <div>
            <span class="section-kicker">Actividad</span>
            <h2>Ultimos eventos</h2>
        </div>
    </div>

    <div class="table-wrap">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Usuario</th>
                    <th>Accion</th>
                    <th>Entidad</th>
                    <th>Detalle</th>
                </tr>
            </thead>
            <tbody>
                <?php while ($row = mysqli_fetch_assoc($logs)): ?>
                    <tr>
                        <td><?php echo e($row['created_at']); ?></td>
                        <td><?php echo e($row['username_snapshot']); ?></td>
                        <td><?php echo e($row['action_type']); ?></td>
                        <td><?php echo e($row['entity_type']); ?></td>
                        <td><?php echo e($row['details']); ?></td>
                    </tr>
                <?php endwhile; ?>
            </tbody>
        </table>
    </div>
</section>

<?php include __DIR__ . '/../includes/admin-footer.php'; ?>
