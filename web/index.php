<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8">
<title>Arby-X Dashboard</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="http://code.jquery.com/jquery-3.3.1.min.js"></script>
<style>
 html, body{width:100%;height:100%;background:#111;color:#ddd;font-family:'Open Sans', sans-serif;margin:0 auto;padding:0;box-sizing: border-box;display:block;text-align:center;}
 #balances{width:100%;display:block;box-sizing: border-box;}
 h2{padding:.25em;margin:0;box-sizing: border-box;font-weight:100;}
 .balance{width:12.5%;display:inline-block;text-align:center;padding:.5em;box-sizing: border-box;margin:0;}
 #estimate{width:100%;display:block;text-align:center;padding:1em .5em .5em;box-sizing:border-box;margin:auto 0;}
 #estimate span{font-weight:900;}
 .theEstimate{width:50%;display:inline-block;text-align:center;padding:.5em;box-sizing:border-box;margin:0;}
 .red{color:#B00;}
 .green{color:#0B0;}
 p{display:inline-block;margin:0;padding:0;}
</style>
</head>
<body>
<div id="myDiv"></div>
<div id="balances"></div>
<div id="estimate"></div>
<script>
$( document ).ready(function() {
    var plot_data = new Array();

    //$.getJSON("balances?ts=2018-02-12 17:00", function(data){
    //$.getJSON("balances?ts=2018-02-16 19:00", function(data){
    $.getJSON("balances?ts=2018-02-14 13:30", function(data){
    $.each(data, function(key, value){
	    var x_data = new Array();
	    var y_data = new Array();
	    var first = .0;
	    $.each(value, function(b, v){
		if (first == .0){
		    first = parseFloat(v["balance"]);
		}
		y_data.push(parseFloat(v["balance"]) / first - 1);
		x_data.push(v["timestamp"]);
	    });
	    trace = {
		type: "scatter",
		mode: "lines",
		name: key,
		x: x_data,
		y: y_data
	    };
	    plot_data.push(trace);
	});
    
    var layout = {
    title: 'ARBY-X utveckling',
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
     var balances = {};
     //$.getJSON("balances?ts=2018-02-12 17:00", function(data){
     //$.getJSON("balances?ts=2018-02-16 19:00", function(data){
     $.getJSON("balances?ts=2018-02-14 13:30", function(data){
     $.each(data, function(key, value){
	     balances[key] = new Array(.0, .0);
	     $.each(value, function(b, v){
		 if(balances[key][0] == .0){
		     balances[key][0] = parseFloat(v["balance"]);
		 }
		 balances[key][1] = parseFloat(v["balance"]);
	     });
	 });
	 $.each(balances, function(k, val){
	     //alert(val[1]);
	     var html = "<div class='balance'><h2>" + k + "</h2>" + val[1] + "</div>";
	     $("#balances").append(html);
	 });
	 var origRates = {
"BTC":{"price_usd":9205.47, "price_btc":1.0},
"ETH":{"price_usd":892.75, "price_btc":.0969635},
"XRP":{"price_usd":1.08, "price_btc":.00011727},
"BCC":{"price_usd":1300.84, "price_btc":.141287},
"ADA":{"price_usd":.381806, "price_btc":.00004147},
"XLM":{"price_usd":.443037, "price_btc":.00004812},
"XVG":{"price_usd":.056473, "price_btc":.00000613},
"NEO":{"price_usd":116.66, "price_btc":.0126704}};

	 var estimates = new Array(.0, .0);
	 var estimates2 = new Array(.0, .0);
	 var estimates3 = new Array(.0, .0);
	 var estimates4 = new Array(.0, .0);
	 $.getJSON("https://api.coinmarketcap.com/v1/ticker/", function(d){
	     $.each(d, function(k, v){
		 if(v["symbol"] in balances || v["symbol"] == "BCH"){
		     if(v["symbol"] == "BCH"){
			 estimates2[0] += balances["BCC"][0] * parseFloat(v["price_usd"]);
			 estimates2[1] += balances["BCC"][1] * parseFloat(v["price_usd"]);
			 estimates[0] += balances["BCC"][0] * parseFloat(v["price_btc"]);
			 estimates[1] += balances["BCC"][1] * parseFloat(v["price_btc"]);
			 estimates3[0] += balances["BCC"][0] * origRates["BCC"]["price_btc"];
			 estimates3[1] += balances["BCC"][1] * parseFloat(v["price_btc"]);
			 estimates4[0] += balances["BCC"][0] * origRates["BCC"]["price_usd"];
			 estimates4[1] += balances["BCC"][1] * parseFloat(v["price_usd"]);
		     }else{
			 estimates2[0] += balances[v["symbol"]][0] * parseFloat(v["price_usd"]);
			 estimates2[1] += balances[v["symbol"]][1] * parseFloat(v["price_usd"]);
			 estimates[0] += balances[v["symbol"]][0] * parseFloat(v["price_btc"]);
			 estimates[1] += balances[v["symbol"]][1] * parseFloat(v["price_btc"]);
			 estimates3[0] += balances[v["symbol"]][0] * origRates[v["symbol"]]["price_btc"];
			 estimates3[1] += balances[v["symbol"]][1] * parseFloat(v["price_btc"]);
			 estimates4[0] += balances[v["symbol"]][0] * origRates[v["symbol"]]["price_usd"];
			 estimates4[1] += balances[v["symbol"]][1] * parseFloat(v["price_usd"]);
		     }
		 }
	     });
	     
	     var diff = (100 * (estimates[1]/estimates[0] - 1));
	     var p = "<p class='" + (diff < .0 ? "red" : "green") + "'> ";
	     var str = "<span>" + estimates[1].toPrecision(5) + " BTC </span>" + p + diff.toPrecision(3) + " %</p>";
	     
	     var diff2 = (100 * (estimates2[1]/estimates2[0] - 1));
	     var p2 = "<p class='" + (diff2 < .0 ? "red" : "green") + "'> ";
	     var str2 = "<span>$ " + estimates2[1].toPrecision(5) + " </span>" + p2 + diff2.toPrecision(3) + " %</p>";

	     var diff3 = (100 * (estimates3[1]/estimates3[0] - 1));
	     var p3 = "<p class='" + (diff3 < .0 ? "red" : "green") + "'> ";
	     var str3 = "<span>" + estimates3[0].toPrecision(5) + " BTC</span>" + p3 + diff3.toPrecision(3) + " %</p>";
	     
	     var diff4 = (100 * (estimates4[1]/estimates4[0] - 1));
	     var p4 = "<p class='" + (diff4 < .0 ? "red" : "green") + "'> ";
	     var str4 = "<span>$ " + estimates4[0].toPrecision(5) + " </span>" + p4 + diff4.toPrecision(3) + " %</p>";

	     $("#estimate").append("<div class='theEstimate' id='est1'><h2>Estimated value BTC</h2>" + str3 + "<br>" + str + "</div>");

	     $("#estimate").append("<div class='theEstimate' id='est2'><h2>Estimated value USD</h2>" + str4 + "<br>" + str2 + "</div>");

	 });
     });
 });
</script>
</body>
</html>
