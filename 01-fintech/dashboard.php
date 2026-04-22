<?php
$asset_base = 'assets';
$root_prefix = '.';
require_once __DIR__ . '/includes/bootstrap.php';
require_login('client');

$user = current_user();
$flash = get_flash();
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'new_transaction') {
    $accountId = (int) (isset($_POST['client_product_id']) ? $_POST['client_product_id'] : 0);
    $transactionType = isset($_POST['transaction_type']) ? $_POST['transaction_type'] : '';
    $amount = (float) (isset($_POST['amount']) ? $_POST['amount'] : 0);
    $description = trim(isset($_POST['description']) ? $_POST['description'] : '');

    if ($accountId <= 0 || $amount <= 0 || !in_array($transactionType, ['deposit', 'withdraw'], true)) {
        $error = 'Completa correctamente los datos de la transaccion.';
    } else {
        $stmt = mysqli_prepare(
            $conn,
            'SELECT cp.id, cp.balance, cp.account_number, cp.status, p.name AS product_name
             FROM client_products cp
             INNER JOIN products p ON p.id = cp.product_id
             WHERE cp.id = ? AND cp.client_id = ? LIMIT 1'
        );
        mysqli_stmt_bind_param($stmt, 'ii', $accountId, $user['client_id']);
        mysqli_stmt_execute($stmt);
        $result = mysqli_stmt_get_result($stmt);
        $account = mysqli_fetch_assoc($result);
        mysqli_stmt_close($stmt);

        if (!$account) {
            $error = 'La cuenta seleccionada no existe.';
        } elseif ($account['status'] !== 'active') {
            $error = 'No puedes transaccionar sobre una cuenta inactiva.';
        } else {
            $newBalance = (float) $account['balance'];

            if ($transactionType === 'withdraw') {
                $newBalance -= $amount;
                if ($newBalance < 0) {
                    $error = 'Saldo insuficiente para retirar.';
                }
            } else {
                $newBalance += $amount;
            }

            if ($error === '') {
                mysqli_begin_transaction($conn);

                try {
                    $updateStmt = mysqli_prepare($conn, 'UPDATE client_products SET balance = ? WHERE id = ?');
                    mysqli_stmt_bind_param($updateStmt, 'di', $newBalance, $accountId);
                    mysqli_stmt_execute($updateStmt);
                    mysqli_stmt_close($updateStmt);

                    $insertStmt = mysqli_prepare(
                        $conn,
                        'INSERT INTO transactions (client_product_id, transaction_type, amount, description, created_by) VALUES (?, ?, ?, ?, ?)'
                    );
                    mysqli_stmt_bind_param($insertStmt, 'isdsi', $accountId, $transactionType, $amount, $description, $user['id']);
                    mysqli_stmt_execute($insertStmt);
                    $transactionId = mysqli_insert_id($conn);
                    mysqli_stmt_close($insertStmt);

                    mysqli_commit($conn);

                    log_activity(
                        $conn,
                        $user['id'],
                        $user['username'],
                        'transaction_' . $transactionType,
                        'transactions',
                        $transactionId,
                        $account['product_name'] . ' / ' . $account['account_number'] . ' / ' . $description
                    );

                    set_flash('success', 'Transaccion registrada correctamente.');
                    redirect(root_url('dashboard.php'));
                } catch (Throwable $exception) {
                    mysqli_rollback($conn);
                    $error = 'No fue posible procesar la transaccion.';
                }
            }
        }
    }
}

$summaryStmt = mysqli_prepare(
    $conn,
    'SELECT cp.id, cp.account_number, cp.balance, cp.status, p.name AS product_name, p.category
     FROM client_products cp
     INNER JOIN products p ON p.id = cp.product_id
     WHERE cp.client_id = ?
     ORDER BY cp.id DESC'
);
mysqli_stmt_bind_param($summaryStmt, 'i', $user['client_id']);
mysqli_stmt_execute($summaryStmt);
$accountsResult = mysqli_stmt_get_result($summaryStmt);
$accounts = [];
$activeAccounts = [];
$totalBalance = 0;
while ($row = mysqli_fetch_assoc($accountsResult)) {
    $accounts[] = $row;
    $totalBalance += (float) $row['balance'];
    if ($row['status'] === 'active') {
        $activeAccounts[] = $row;
    }
}
mysqli_stmt_close($summaryStmt);

$transactionsStmt = mysqli_prepare(
    $conn,
    'SELECT t.created_at, t.transaction_type, t.amount, t.description, cp.account_number, p.name AS product_name
     FROM transactions t
     INNER JOIN client_products cp ON cp.id = t.client_product_id
     INNER JOIN products p ON p.id = cp.product_id
     WHERE cp.client_id = ?
     ORDER BY t.id DESC
     LIMIT 10'
);
mysqli_stmt_bind_param($transactionsStmt, 'i', $user['client_id']);
mysqli_stmt_execute($transactionsStmt);
$transactions = mysqli_stmt_get_result($transactionsStmt);
mysqli_stmt_close($transactionsStmt);

$page_title = 'Dashboard de cliente';
include __DIR__ . '/includes/admin-header.php';
?>
<div class="app-shell client-shell">
    <aside class="app-sidebar">
        <a class="brand app-brand" href="<?php echo e(root_url('dashboard.php')); ?>">
            <span class="brand-mark">FN</span>
            <span class="brand-copy">
                <strong>Fintech Nova</strong>
                <small>Client dashboard</small>
            </span>
        </a>
        <nav class="app-menu">
            <a href="<?php echo e(root_url('dashboard.php')); ?>">Resumen</a>
            <a href="<?php echo e(root_url('index.php')); ?>">Sitio publico</a>
        </nav>
    </aside>

    <div class="app-main">
        <header class="app-topbar">
            <div>
                <p class="app-kicker">Portal de cliente</p>
                <h1>Hola, <?php echo e($user['full_name']); ?></h1>
            </div>
            <div class="app-userbox">
                <span><?php echo e($user['username']); ?></span>
                <a class="button-secondary small-button" href="<?php echo e(root_url('logout.php')); ?>">Salir</a>
            </div>
        </header>

        <?php if ($flash): ?>
            <div class="flash flash-<?php echo e($flash['type']); ?>"><?php echo e($flash['message']); ?></div>
        <?php endif; ?>

        <?php if ($error !== ''): ?>
            <div class="flash flash-error"><?php echo e($error); ?></div>
        <?php endif; ?>

        <section class="app-grid metrics-grid">
            <article class="app-card">
                <p class="metric-label">Productos activos</p>
                <span class="metric-value"><?php echo isset($activeAccounts) ? count($activeAccounts) : 0; ?></span>
            </article>
            <article class="app-card">
                <p class="metric-label">Saldo total</p>
                <span class="metric-value"><?php echo e(money($totalBalance)); ?></span>
            </article>
        </section>

        <section class="app-grid two-columns">
            <article class="app-card">
                <div class="section-heading compact">
                    <div>
                        <span class="section-kicker">Productos</span>
                        <h2>Saldos por cuenta</h2>
                    </div>
                </div>

                <div class="table-wrap">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Cuenta</th>
                                <th>Producto</th>
                                <th>Categoria</th>
                                <th>Saldo</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($accounts as $account): ?>
                                <tr>
                                    <td><?php echo e($account['account_number']); ?></td>
                                    <td><?php echo e($account['product_name']); ?></td>
                                    <td><?php echo e($account['category']); ?></td>
                                    <td><?php echo e(money($account['balance'])); ?></td>
                                    <td><?php echo e($account['status']); ?></td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            </article>

            <article class="app-card">
                <div class="section-heading compact">
                    <div>
                        <span class="section-kicker">Transacciones</span>
                        <h2>Registrar movimiento</h2>
                    </div>
                </div>

                <form class="stack-form" method="post">
                    <input type="hidden" name="action" value="new_transaction">
                    <label>
                        <span>Cuenta</span>
                        <select name="client_product_id">
                            <option value="">Selecciona una cuenta</option>
                            <?php foreach ($accounts as $account): ?>
                                <?php if ($account['status'] !== 'active') { continue; } ?>
                                <option value="<?php echo e($account['id']); ?>">
                                    <?php echo e($account['account_number'] . ' - ' . $account['product_name']); ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </label>
                    <label>
                        <span>Tipo</span>
                        <select name="transaction_type">
                            <option value="deposit">Deposito</option>
                            <option value="withdraw">Retiro</option>
                        </select>
                    </label>
                    <label>
                        <span>Monto</span>
                        <input type="number" name="amount" min="1" step="0.01" placeholder="0.00">
                    </label>
                    <label>
                        <span>Descripcion</span>
                        <input type="text" name="description" placeholder="Detalle de la operacion">
                    </label>
                    <button class="button" type="submit">Guardar transaccion</button>
                </form>
            </article>
        </section>

        <section class="app-card">
            <div class="section-heading compact">
                <div>
                    <span class="section-kicker">Historial</span>
                    <h2>Ultimos movimientos</h2>
                </div>
            </div>

            <div class="table-wrap">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Cuenta</th>
                            <th>Producto</th>
                            <th>Tipo</th>
                            <th>Monto</th>
                            <th>Descripcion</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php while ($row = mysqli_fetch_assoc($transactions)): ?>
                            <tr>
                                <td><?php echo e($row['created_at']); ?></td>
                                <td><?php echo e($row['account_number']); ?></td>
                                <td><?php echo e($row['product_name']); ?></td>
                                <td><?php echo e($row['transaction_type']); ?></td>
                                <td><?php echo e(money($row['amount'])); ?></td>
                                <td><?php echo e($row['description']); ?></td>
                            </tr>
                        <?php endwhile; ?>
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</div>
</body>
</html>
