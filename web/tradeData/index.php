<?php
require_once __DIR__ . '/../config.php';

$stmt = $pdo->query('select * from order_details inner join orders on order_details.id=orders.id;');

$res = array();
while ($row = $stmt->fetch()) {
    $id = $row['id'];
    if (!array_key_exists($id, $res)) {
        $res[$id] = array("timestamp" => $row['ts'], "market" => $row['market'], "orderDetails" => array());
    }
    array_push($res[$id]["orderDetails"], array(
        "exchange" => $row['exchange'],
        "rate" => $row['rate'],
        "volume" => $row['volume'],
        "exchangeId" => $row['origId'],
        "side" => $row['side']
    ));
}
echo json_encode($res);
?>
