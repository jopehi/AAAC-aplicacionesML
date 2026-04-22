<?php
if (!isset($page_title)) {
    $page_title = 'Fintech Nova';
}
if (!isset($asset_base)) {
    $asset_base = 'assets';
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $page_title; ?></title>
    <meta name="description" content="Fintech ficticia para laboratorio de software con enfoque en arquitectura web, trazabilidad y analitica de comportamiento.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="<?php echo e(asset_url('css/main.css')); ?>">
</head>
<body>
