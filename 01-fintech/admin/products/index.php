<?php
$asset_base = '../../assets';
$root_prefix = '../..';
require_once __DIR__ . '/../../includes/bootstrap.php';
require_login('admin');

$flash = get_flash();
$error = '';
$editingProduct = null;

if (isset($_GET['delete'])) {
    $deleteId = (int) $_GET['delete'];
    mysqli_query($conn, 'DELETE FROM products WHERE id = ' . $deleteId);
    log_activity($conn, current_user()['id'], current_user()['username'], 'delete', 'products', $deleteId, 'Producto eliminado desde panel');
    set_flash('success', 'Producto eliminado.');
    redirect(root_url('admin/products/index.php'));
}

if (isset($_GET['edit'])) {
    $editId = (int) $_GET['edit'];
    $editResult = mysqli_query($conn, 'SELECT * FROM products WHERE id = ' . $editId . ' LIMIT 1');
    $editingProduct = mysqli_fetch_assoc($editResult);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $productId = (int) (isset($_POST['product_id']) ? $_POST['product_id'] : 0);
    $name = trim(isset($_POST['name']) ? $_POST['name'] : '');
    $category = trim(isset($_POST['category']) ? $_POST['category'] : '');
    $description = trim(isset($_POST['description']) ? $_POST['description'] : '');
    $annualReturnHint = (float) (isset($_POST['annual_return_hint']) ? $_POST['annual_return_hint'] : 0);
    $status = trim(isset($_POST['status']) ? $_POST['status'] : 'active');

    if ($name === '' || $category === '') {
        $error = 'Nombre y categoria son obligatorios.';
    } else {
        if ($productId > 0) {
            $stmt = mysqli_prepare($conn, 'UPDATE products SET name = ?, category = ?, description = ?, annual_return_hint = ?, status = ? WHERE id = ?');
            mysqli_stmt_bind_param($stmt, 'sssdsi', $name, $category, $description, $annualReturnHint, $status, $productId);
            mysqli_stmt_execute($stmt);
            mysqli_stmt_close($stmt);
            log_activity($conn, current_user()['id'], current_user()['username'], 'update', 'products', $productId, 'Producto actualizado');
            set_flash('success', 'Producto actualizado.');
        } else {
            $stmt = mysqli_prepare($conn, 'INSERT INTO products (name, category, description, annual_return_hint, status) VALUES (?, ?, ?, ?, ?)');
            mysqli_stmt_bind_param($stmt, 'sssds', $name, $category, $description, $annualReturnHint, $status);
            mysqli_stmt_execute($stmt);
            $newId = mysqli_insert_id($conn);
            mysqli_stmt_close($stmt);
            log_activity($conn, current_user()['id'], current_user()['username'], 'create', 'products', $newId, 'Producto creado');
            set_flash('success', 'Producto creado.');
        }

        redirect(root_url('admin/products/index.php'));
    }
}

$products = mysqli_query($conn, 'SELECT * FROM products ORDER BY id DESC');

$page_title = 'Gestion de productos';
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
        <span class="section-kicker"><?php echo $editingProduct ? 'Editar' : 'Nuevo'; ?></span>
        <h2><?php echo $editingProduct ? 'Actualizar producto' : 'Registrar producto'; ?></h2>
        <form class="stack-form" method="post">
            <input type="hidden" name="product_id" value="<?php echo e($editingProduct ? $editingProduct['id'] : '0'); ?>">
            <label><span>Nombre</span><input type="text" name="name" value="<?php echo e($editingProduct ? $editingProduct['name'] : ''); ?>"></label>
            <label><span>Categoria</span><input type="text" name="category" value="<?php echo e($editingProduct ? $editingProduct['category'] : ''); ?>"></label>
            <label><span>Rentabilidad estimada</span><input type="number" min="0" step="0.01" name="annual_return_hint" value="<?php echo e($editingProduct ? $editingProduct['annual_return_hint'] : '0'); ?>"></label>
            <label><span>Descripcion</span><textarea name="description"><?php echo e($editingProduct ? $editingProduct['description'] : ''); ?></textarea></label>
            <label>
                <span>Estado</span>
                <select name="status">
                    <option value="active" <?php echo $editingProduct && $editingProduct['status'] === 'active' ? 'selected' : ''; ?>>Activo</option>
                    <option value="inactive" <?php echo $editingProduct && $editingProduct['status'] === 'inactive' ? 'selected' : ''; ?>>Inactivo</option>
                </select>
            </label>
            <button class="button" type="submit">Guardar producto</button>
        </form>
    </article>

    <article class="app-card">
        <span class="section-kicker">Listado</span>
        <h2>Productos registrados</h2>
        <div class="table-wrap">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>Categoria</th>
                        <th>Rentabilidad</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <?php while ($row = mysqli_fetch_assoc($products)): ?>
                        <tr>
                            <td><?php echo e($row['id']); ?></td>
                            <td><?php echo e($row['name']); ?></td>
                            <td><?php echo e($row['category']); ?></td>
                            <td><?php echo e($row['annual_return_hint']); ?>%</td>
                            <td class="actions-cell">
                                <a href="?edit=<?php echo e($row['id']); ?>">Editar</a>
                                <a href="?delete=<?php echo e($row['id']); ?>" onclick="return confirm('Eliminar producto?');">Eliminar</a>
                            </td>
                        </tr>
                    <?php endwhile; ?>
                </tbody>
            </table>
        </div>
    </article>
</section>

<?php include __DIR__ . '/../../includes/admin-footer.php'; ?>

