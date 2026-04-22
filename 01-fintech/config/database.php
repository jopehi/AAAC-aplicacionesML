<?php

$db_host = '127.0.0.1';
$db_port = '3306';
$db_name = 'fintech';
$db_user = 'root';
$db_pass = 'idmatx';

$conn = mysqli_connect($db_host, $db_user, $db_pass, $db_name, (int) $db_port);

if (!$conn) {
    die('Database connection failed: ' . mysqli_connect_error());
}

