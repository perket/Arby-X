<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8">
<title>Arby-X Dashboard</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<style>
 html, body{width:100%;height:100%;background:#111;color:#ddd;font-family:'Open Sans', sans-serif;margin:0 auto;padding:0;box-sizing: border-box;display:block;text-align:center;}
 #balances{width:100%;display:block;box-sizing: border-box;}
 h2{padding:.25em;margin:0;box-sizing: border-box;font-weight:100;}
 .balance{width:12.5%;display:inline-block;text-align:center;padding:.5em;box-sizing: border-box;margin:0;}
 .red{color:#B00;}
 .green{color:#0B0;}
 p{display:inline-block;margin:0;padding:0;}
</style>
</head>
<body>
<div id="myDiv"></div>
<div id="balances"></div>
<script>
$(document).ready(function() {
    // Compute timestamp for 7 days ago
    var d = new Date();
    d.setDate(d.getDate() - 7);
    var ts = d.toISOString().slice(0, 19).replace("T", " ");

    var plot_data = [];

    $.getJSON("balances?ts=" + encodeURIComponent(ts), function(data){
        $.each(data, function(key, value){
            var x_data = [];
            var y_data = [];
            var first = 0;
            $.each(value, function(b, v){
                if (first == 0){
                    first = parseFloat(v["balance"]);
                }
                y_data.push(parseFloat(v["balance"]) / first - 1);
                x_data.push(v["timestamp"]);
            });
            var trace = {
                type: "scatter",
                mode: "lines",
                name: key,
                x: x_data,
                y: y_data
            };
            plot_data.push(trace);
        });

        var layout = {
            title: 'Arby-X Balance History',
            paper_bgcolor: '#111',
            plot_bgcolor: '#111',
            font: {color: '#ddd'},
            xaxis: {color: '#ddd', tickcolor: '#ddd', linecolor: '#ddd'},
            yaxis: {color: '#ddd', tickcolor: '#ddd', linecolor: '#ddd'}
        };

        Plotly.newPlot('myDiv', plot_data, layout);
    });
});
</script>
<script>
$(document).ready(function() {
    var d = new Date();
    d.setDate(d.getDate() - 7);
    var ts = d.toISOString().slice(0, 19).replace("T", " ");

    $.getJSON("balances?ts=" + encodeURIComponent(ts), function(data){
        var balances = {};
        $.each(data, function(key, value){
            balances[key] = [0, 0];
            $.each(value, function(b, v){
                if(balances[key][0] == 0){
                    balances[key][0] = parseFloat(v["balance"]);
                }
                balances[key][1] = parseFloat(v["balance"]);
            });
        });
        $.each(balances, function(k, val){
            var diff = val[0] > 0 ? (100 * (val[1]/val[0] - 1)).toFixed(2) : 0;
            var cls = diff >= 0 ? "green" : "red";
            var html = "<div class='balance'><h2>" + k + "</h2>" + val[1].toFixed(8) + " <p class='" + cls + "'>" + diff + "%</p></div>";
            $("#balances").append(html);
        });
    });
});
</script>
</body>
</html>
