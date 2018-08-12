<?php
$host = '127.0.0.1';
$db   = 'arby';
$user = 'root';
$pass = '123456';
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$opt = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];
$pdo = new PDO($dsn, $user, $pass, $opt);

if (isset($_GET['currency']) && isset($_GET['ts'])) {
    $currency = $_GET['currency'];
    $ts = $_GET['ts'];
    $stmt = $pdo->prepare('SELECT * FROM balances WHERE currency = :currency and ts > :ts order by ts asc;');
    $stmt->execute(["currency" => $currency, "ts" => $ts]);
}elseif(isset($_GET['ts'])){
  $ts = $_GET['ts'];
  $stmt = $pdo->prepare('SELECT * FROM balances WHERE ts > :ts order by ts asc;');
  $stmt->execute(["ts" => $ts]);
}elseif(isset($_GET['currency'])){
  $currency = $_GET['currency'];
  $stmt = $pdo->prepare('SELECT * FROM balances WHERE currency = :currency order by ts asc;');
  $stmt->execute(["currency" => $currency]);
}else{
    $stmt = $pdo->query('SELECT * FROM balances order by currency asc, ts asc;');
}

$res = array();

foreach ($stmt as $row){
    $curr = $row['currency'];
    $bal = $row['balance'];
    $ts = $row['ts'];
    if (!array_key_exists($curr, $res)) {
	$res[$curr] = array();
    }
    $r = array("balance" => $bal, "timestamp" => $ts);
    
    array_push($res[$curr], $r);
}
echo json_encode($res);

?>
