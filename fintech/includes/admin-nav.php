<?php $authUser = current_user(); ?>
<div class="app-shell">
    <aside class="app-sidebar">
        <a class="brand app-brand" href="<?php echo e(root_url('admin/dashboard.php')); ?>">
            <span class="brand-mark">FN</span>
            <span class="brand-copy">
                <strong>Fintech Nova</strong>
                <small>Admin panel</small>
            </span>
        </a>

        <nav class="app-menu">
            <a href="<?php echo e(root_url('admin/dashboard.php')); ?>">Resumen</a>
            <a href="<?php echo e(root_url('admin/clients/index.php')); ?>">Clientes</a>
            <a href="<?php echo e(root_url('admin/accounts/index.php')); ?>">Productos cliente</a>
            <a href="<?php echo e(root_url('admin/products/index.php')); ?>">Productos</a>
            <a href="<?php echo e(root_url('admin/users/index.php')); ?>">Usuarios</a>
            <a href="<?php echo e(root_url('admin/logs/index.php')); ?>">Auditoria</a>
        </nav>
    </aside>

    <div class="app-main">
        <header class="app-topbar">
            <div>
                <p class="app-kicker">Panel administrativo</p>
                <h1><?php echo e($page_title); ?></h1>
            </div>
            <div class="app-userbox">
                <span><?php echo e($authUser['full_name']); ?></span>
                <a class="button-secondary small-button" href="<?php echo e(root_url('logout.php')); ?>">Salir</a>
            </div>
        </header>
