<?php
$asset_base = '../../assets';
$root_prefix = '../..';
require_once __DIR__ . '/../../includes/bootstrap.php';
require_login('admin');

$clientFilter = isset($_GET['client_id']) ? (int) $_GET['client_id'] : 0;
$flash = get_flash();
$error = '';
$editingAccount = null;
$currentAdmin = current_user();

if (isset($_GET['toggle']) && isset($_GET['status'])) {
    $accountId = (int) $_GET['toggle'];
    $newStatus = $_GET['status'] === 'inactive' ? 'inactive' : 'active';

    $stmt = mysqli_prepare(
        $conn,
        'SELECT cp.id, cp.client_id, cp.product_id, cp.account_number, c.company, p.name AS product_name
         FROM client_products cp
         INNER JOIN clients c ON c.id = cp.client_id
         INNER JOIN products p ON p.id = cp.product_id
         WHERE cp.id = ? LIMIT 1'
    );
    mysqli_stmt_bind_param($stmt, 'i', $accountId);
    mysqli_stmt_execute($stmt);
    $accountResult = mysqli_stmt_get_result($stmt);
    $accountRow = mysqli_fetch_assoc($accountResult);
    mysqli_stmt_close($stmt);

    if ($accountRow) {
        $stmt = mysqli_prepare($conn, 'UPDATE client_products SET status = ? WHERE id = ?');
        mysqli_stmt_bind_param($stmt, 'si', $newStatus, $accountId);
        mysqli_stmt_execute($stmt);
        mysqli_stmt_close($stmt);

        log_activity(
            $conn,
            $currentAdmin['id'],
            $currentAdmin['username'],
            $newStatus === 'active' ? 'open_product' : 'close_product',
            'client_products',
            $accountId,
            $accountRow['company'] . ' / ' . $accountRow['product_name'] . ' / ' . $accountRow['account_number']
        );

        set_flash('success', $newStatus === 'active' ? 'Producto reabierto.' : 'Producto cerrado.');
    }

    $redirectUrl = 'admin/accounts/index.php';
    if ($clientFilter > 0) {
        $redirectUrl .= '?client_id=' . $clientFilter;
    }
    redirect(root_url($redirectUrl));
}

if (isset($_GET['edit'])) {
    $editId = (int) $_GET['edit'];
    $stmt = mysqli_prepare(
        $conn,
        'SELECT cp.*, c.company, p.name AS product_name
         FROM client_products cp
         INNER JOIN clients c ON c.id = cp.client_id
         INNER JOIN products p ON p.id = cp.product_id
         WHERE cp.id = ? LIMIT 1'
    );
    mysqli_stmt_bind_param($stmt, 'i', $editId);
    mysqli_stmt_execute($stmt);
    $editResult = mysqli_stmt_get_result($stmt);
    $editingAccount = mysqli_fetch_assoc($editResult);
    mysqli_stmt_close($stmt);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = isset($_POST['action']) ? $_POST['action'] : '';

    if ($action === 'save_account') {
        $accountId = (int) (isset($_POST['account_id']) ? $_POST['account_id'] : 0);
        $clientId = (int) (isset($_POST['client_id']) ? $_POST['client_id'] : 0);
        $productId = (int) (isset($_POST['product_id']) ? $_POST['product_id'] : 0);
        $accountNumber = trim(isset($_POST['account_number']) ? $_POST['account_number'] : '');
        $balance = (float) (isset($_POST['balance']) ? $_POST['balance'] : 0);
        $status = isset($_POST['status']) && $_POST['status'] === 'inactive' ? 'inactive' : 'active';

        if ($clientId <= 0 || $productId <= 0 || $accountNumber === '') {
            $error = 'Cliente, producto y numero de cuenta son obligatorios.';
        } elseif ($balance < 0) {
            $error = 'El saldo inicial no puede ser negativo.';
        } else {
            $stmt = mysqli_prepare($conn, 'SELECT id FROM client_products WHERE account_number = ? AND id <> ? LIMIT 1');
            mysqli_stmt_bind_param($stmt, 'si', $accountNumber, $accountId);
            mysqli_stmt_execute($stmt);
            $duplicateNumberResult = mysqli_stmt_get_result($stmt);
            $duplicateNumber = mysqli_fetch_assoc($duplicateNumberResult);
            mysqli_stmt_close($stmt);

            if ($duplicateNumber) {
                $error = 'Ese numero de cuenta ya existe.';
            } else {
                $stmt = mysqli_prepare(
                    $conn,
                    'SELECT id FROM client_products WHERE client_id = ? AND product_id = ? AND id <> ? LIMIT 1'
                );
                mysqli_stmt_bind_param($stmt, 'iii', $clientId, $productId, $accountId);
                mysqli_stmt_execute($stmt);
                $duplicateProductResult = mysqli_stmt_get_result($stmt);
                $duplicateProduct = mysqli_fetch_assoc($duplicateProductResult);
                mysqli_stmt_close($stmt);

                if ($duplicateProduct) {
                    $error = 'Ese cliente ya tiene ese producto asignado.';
                }
            }
        }

        if ($error === '') {
            if ($accountId > 0) {
                $stmt = mysqli_prepare(
                    $conn,
                    'UPDATE client_products SET client_id = ?, product_id = ?, account_number = ?, balance = ?, status = ? WHERE id = ?'
                );
                mysqli_stmt_bind_param($stmt, 'iisdsi', $clientId, $productId, $accountNumber, $balance, $status, $accountId);
                mysqli_stmt_execute($stmt);
                mysqli_stmt_close($stmt);

                log_activity($conn, $currentAdmin['id'], $currentAdmin['username'], 'update', 'client_products', $accountId, 'Producto de cliente actualizado');
                set_flash('success', 'Producto de cliente actualizado.');
            } else {
                $stmt = mysqli_prepare(
                    $conn,
                    'INSERT INTO client_products (client_id, product_id, account_number, balance, status) VALUES (?, ?, ?, ?, ?)'
                );
                mysqli_stmt_bind_param($stmt, 'iisds', $clientId, $productId, $accountNumber, $balance, $status);
                mysqli_stmt_execute($stmt);
                $newId = mysqli_insert_id($conn);
                mysqli_stmt_close($stmt);

                log_activity($conn, $currentAdmin['id'], $currentAdmin['username'], 'create', 'client_products', $newId, 'Producto abierto para cliente');
                set_flash('success', 'Producto asignado al cliente.');
            }

            $redirectUrl = 'admin/accounts/index.php';
            if ($clientId > 0) {
                $redirectUrl .= '?client_id=' . $clientId;
            }
            redirect(root_url($redirectUrl));
        }
    }
}

$sql = '
    SELECT cp.id, cp.account_number, cp.balance, cp.status, c.id AS client_id,
           c.full_name AS client_name, c.company,
           p.id AS product_id, p.name AS product_name, p.category
    FROM client_products cp
    INNER JOIN clients c ON c.id = cp.client_id
    INNER JOIN products p ON p.id = cp.product_id
';

if ($clientFilter > 0) {
    $sql .= ' WHERE c.id = ?';
}

$sql .= ' ORDER BY c.company ASC, cp.id DESC';

if ($clientFilter > 0) {
    $stmt = mysqli_prepare($conn, $sql);
    mysqli_stmt_bind_param($stmt, 'i', $clientFilter);
    mysqli_stmt_execute($stmt);
    $accounts = mysqli_stmt_get_result($stmt);
    mysqli_stmt_close($stmt);
} else {
    $accounts = mysqli_query($conn, $sql);
}

$clients = mysqli_query($conn, "SELECT id, company, full_name FROM clients WHERE status = 'active' ORDER BY company ASC");
$products = mysqli_query($conn, "SELECT id, name, category FROM products WHERE status = 'active' ORDER BY name ASC");

$page_title = 'Productos de clientes';
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
        <span class="section-kicker"><?php echo $editingAccount ? 'Editar' : 'Apertura'; ?></span>
        <h2><?php echo $editingAccount ? 'Actualizar producto del cliente' : 'Abrir producto para cliente'; ?></h2>
        <p class="muted-copy">Control basico de datos: no se permite duplicar el mismo producto para el mismo cliente ni repetir numeros de cuenta.</p>

        <form class="stack-form" method="post">
            <input type="hidden" name="action" value="save_account">
            <input type="hidden" name="account_id" value="<?php echo e($editingAccount ? $editingAccount['id'] : '0'); ?>">

            <label>
                <span>Cliente</span>
                <select name="client_id">
                    <option value="">Selecciona un cliente</option>
                    <?php while ($client = mysqli_fetch_assoc($clients)): ?>
                        <option value="<?php echo e($client['id']); ?>" <?php echo ($editingAccount && (int) $editingAccount['client_id'] === (int) $client['id']) || (!$editingAccount && $clientFilter === (int) $client['id']) ? 'selected' : ''; ?>>
                            <?php echo e($client['company'] . ' - ' . $client['full_name']); ?>
                        </option>
                    <?php endwhile; ?>
                </select>
            </label>

            <label>
                <span>Producto</span>
                <select name="product_id">
                    <option value="">Selecciona un producto</option>
                    <?php while ($product = mysqli_fetch_assoc($products)): ?>
                        <option value="<?php echo e($product['id']); ?>" <?php echo $editingAccount && (int) $editingAccount['product_id'] === (int) $product['id'] ? 'selected' : ''; ?>>
                            <?php echo e($product['name'] . ' - ' . $product['category']); ?>
                        </option>
                    <?php endwhile; ?>
                </select>
            </label>

            <label>
                <span>Numero de cuenta</span>
                <input type="text" name="account_number" value="<?php echo e($editingAccount ? $editingAccount['account_number'] : ''); ?>" placeholder="Ej: AC-550011">
            </label>

            <label>
                <span>Saldo inicial</span>
                <input type="number" name="balance" min="0" step="0.01" value="<?php echo e($editingAccount ? $editingAccount['balance'] : '0.00'); ?>">
            </label>

            <label>
                <span>Estado</span>
                <select name="status">
                    <option value="active" <?php echo (!$editingAccount || $editingAccount['status'] === 'active') ? 'selected' : ''; ?>>Activo</option>
                    <option value="inactive" <?php echo $editingAccount && $editingAccount['status'] === 'inactive' ? 'selected' : ''; ?>>Inactivo</option>
                </select>
            </label>

            <button class="button" type="submit"><?php echo $editingAccount ? 'Actualizar producto' : 'Abrir producto'; ?></button>
        </form>
    </article>

    <article class="app-card">
        <div class="section-heading compact">
            <div>
                <span class="section-kicker">Consulta</span>
                <h2>Portafolio de productos por cliente</h2>
            </div>
        </div>

        <form class="inline-filter" method="get">
            <label>
                <span>Cliente</span>
                <select name="client_id">
                    <option value="0">Todos los clientes</option>
                    <?php
                    $filterClients = mysqli_query($conn, "SELECT id, company, full_name FROM clients WHERE status = 'active' ORDER BY company ASC");
                    while ($client = mysqli_fetch_assoc($filterClients)):
                    ?>
                        <option value="<?php echo e($client['id']); ?>" <?php echo $clientFilter === (int) $client['id'] ? 'selected' : ''; ?>>
                            <?php echo e($client['company'] . ' - ' . $client['full_name']); ?>
                        </option>
                    <?php endwhile; ?>
                </select>
            </label>
            <button class="button" type="submit">Filtrar</button>
            <a class="button-secondary small-button" href="<?php echo e(root_url('admin/accounts/index.php')); ?>">Limpiar</a>
        </form>
    </article>
</section>

<section class="app-card">
    <div class="table-wrap">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Cliente</th>
                    <th>Empresa</th>
                    <th>Cuenta</th>
                    <th>Producto</th>
                    <th>Categoria</th>
                    <th>Saldo</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                <?php while ($row = mysqli_fetch_assoc($accounts)): ?>
                    <tr>
                        <td><?php echo e($row['client_name']); ?></td>
                        <td><?php echo e($row['company']); ?></td>
                        <td><?php echo e($row['account_number']); ?></td>
                        <td><?php echo e($row['product_name']); ?></td>
                        <td><?php echo e($row['category']); ?></td>
                        <td><?php echo e(money($row['balance'])); ?></td>
                        <td><?php echo e($row['status']); ?></td>
                        <td class="actions-cell">
                            <a href="<?php echo e(root_url('admin/accounts/index.php?edit=' . $row['id'] . ($clientFilter > 0 ? '&client_id=' . $clientFilter : ''))); ?>">Editar</a>
                            <?php if ($row['status'] === 'active'): ?>
                                <a href="<?php echo e(root_url('admin/accounts/index.php?toggle=' . $row['id'] . '&status=inactive' . ($clientFilter > 0 ? '&client_id=' . $clientFilter : ''))); ?>" onclick="return confirm('Cerrar producto para este cliente?');">Cerrar</a>
                            <?php else: ?>
                                <a href="<?php echo e(root_url('admin/accounts/index.php?toggle=' . $row['id'] . '&status=active' . ($clientFilter > 0 ? '&client_id=' . $clientFilter : ''))); ?>">Reabrir</a>
                            <?php endif; ?>
                        </td>
                    </tr>
                <?php endwhile; ?>
            </tbody>
        </table>
    </div>
</section>

<?php include __DIR__ . '/../../includes/admin-footer.php'; ?>

