<?php
require_once __DIR__ . '/../config.php';

if (isset($_GET['currency']) && isset($_GET['ts'])) {
    $stmt = $pdo->prepare('SELECT * FROM balances WHERE currency = :currency and ts > :ts order by ts asc;');
    $stmt->execute(["currency" => $_GET['currency'], "ts" => $_GET['ts']]);
} elseif (isset($_GET['ts'])) {
    $stmt = $pdo->prepare('SELECT * FROM balances WHERE ts > :ts order by ts asc;');
    $stmt->execute(["ts" => $_GET['ts']]);
} elseif (isset($_GET['currency'])) {
    $stmt = $pdo->prepare('SELECT * FROM balances WHERE currency = :currency order by ts asc;');
    $stmt->execute(["currency" => $_GET['currency']]);
} else {
    $stmt = $pdo->query('SELECT * FROM balances order by currency asc, ts asc;');
}

$res = array();

foreach ($stmt as $row) {
    $curr = $row['currency'];
    if (!array_key_exists($curr, $res)) {
        $res[$curr] = array();
    }
    array_push($res[$curr], array("balance" => $row['balance'], "timestamp" => $row['ts']));
}
echo json_encode($res);
?>
