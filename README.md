# Triangular Arbitrage
Triangular arbitrage is the act of exploiting an arbitrage opportunity resulting from a pricing discrepancy among three different currencies.

At the moment this project is just a study and actually is partially profitable.

## Setup
- Install [Node.js](https://nodejs.org/en/)
- Install [Flask](https://flask.palletsprojects.com/en/2.0.x/)
- Generate API keys in Binance and put them in `sendOrders > config.py`
- Change starting crypto and starting amount in `sendOrders > app.py` (r. 56-58)
- Go to the current folder and run both projects:

Run the scanner:
```bash
cd scannerNode
npm install
node app.js
```

Run the orders sender:
```bash
cd sendOrders
python app.py
```

## Limitations and future improvements
One of the main issue about Triangular Arbitrage is execution speed. Connection between Node.js and Flask should be avoided to increase speed. 
Asset's price changes faster than the update timing of scanner, so there are conversion problems between assets. Just if the real price remains same as which calculated, script is able to complete every orders and is also profitable. 


Another problem is about stepSize. Different decimal approximations make difficult calculate the same price in three different assets which probably don't share same approximation. A proximated solution is to avoid orders which can't confirm profitable conditions.


An important improvement could be consider not just one crypto as starting asset, but consider every asset. To achieve this goal is necessary take two more steps: the first one is convert a starting crypto to connect with the three main steps. The last one is take back the starting crypto

## Credits
Scanner component is based on [BinanceTriangularArbitrage_v2](https://github.com/karthik947/BinanceTriangularArbitrage_v2) 
Copyright (c) 2019 [Karthik D](https://github.com/karthik947)
