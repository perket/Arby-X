# Arby-X

Arby-X is a fully automated system for trading with cryptocurrencies. Arby-X is constantly looking for arbitrage between Binance and Bittrex, and when a large enough arbitrage is found a trade is initialized. The program is split into different threads managing different tasks, one each for reading the orderbooks from both exchanges, one that compares them and two threads that execute trades, one each for the exchanges. 