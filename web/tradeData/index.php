<?php
//select * from order_details inner join orders on order_details.id=orders.id;
$host = 'HOST';
$db   = 'DATABASE';
$user = 'USER';
$pass = 'PASSWORD';
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$opt = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
        ];
$pdo = new PDO($dsn, $user, $pass, $opt);
$stmt = $pdo->query('select * from order_details inner join orders on order_details.id=orders.id;');

$res = Array();
while ($row = $stmt->fetch()){
  $id = $row['id'];
  $v = $row['volume'];
  $r = $row['rate'];
  $oid = $row['origId'];
  $e = $row['exchange'];
  $ts = $row['ts'];
  $m = $row['market'];
  $s = $row['side'];
  if (!array_key_exists($id, $res)) {
    $res[$id] = array("timestamp" => $ts, "market" => $m, "orderDetails" => Array());
  }
  $r = Array("exchange" => $e, "rate" => $r, "volume" => $v, "exchangeId" => $oid, "side" => $s);
  array_push($res[$id]["orderDetails"], $r);
}
echo json_encode($res);
?>