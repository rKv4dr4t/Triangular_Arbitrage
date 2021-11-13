from flask import Flask, render_template, request, flash, redirect, session
from flask_session import Session
import config
from binance.client import Client
from binance.enums import *
from flask_socketio import SocketIO
import math
from datetime import datetime
import requests

import websocket, json

app = Flask(__name__)
app.secret_key = b'jdrtfjd53453543jyrtjstjsrjstjhtsrhs'
client = Client(config.API_KEY, config.API_SECRET)
socketio = SocketIO(app)



# Shutdown server 
@app.route("/shutdown", methods=['GET'])
def shutdown():
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func is None:
        raise RuntimeError('Not running werkzeug')
    shutdown_func()
    #return requests.get('http://127.0.0.1:80').content
    return "Shutting down..."



# Receive json from scanner
@app.route('/postjson', methods = ['POST', 'GET'])
def postJsonHandler():
    # Every minute update list of stepSize 
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    last = current_time[-2:]

    # Create text file with stepSize of assets. First delete content then print them
    if last  == "00": 
        exchangeInfo = client.get_exchange_info()
        totalSymbols = exchangeInfo["symbols"]
        txt_file = open("stepSize.txt", "r+")
        txt_file.truncate(0)
        for symbol in totalSymbols:
            s0 = symbol
            st = symbol["symbol"]
            sz = symbol["filters"][2]["stepSize"]
            tt = st + ": " + sz
            txt_file.write(tt + "\n")
        txt_file.close()

    #############################
    #############################
    #############################
    # Quantity to trade
    amount = 20
    # Starting crypto
    start_sym = "USDT" 
    # Binance fee
    fee = 0.075
    #############################
    #############################
    #############################

    # Take json request
    content = request.get_json()
    content1 = str(content)

    # If text is void doesn't print result
    if content1 == "{\'params\': {\'storeIds\': []}}":
        print("No opportunities found")
    else:

        # Take value from json
        content2Value = content1.split("value")[1]
        startValue = '\': '
        endValue = ', \'tp'
        content3Value = content2Value[content2Value.find(startValue)+len(startValue):content2Value.rfind(endValue)]

        # Take tpath from json  
        content2Tpath = content1.split("tpath")[1]
        startTpath = ': \''
        endTpath = '\'}'
        content3Tpath = content2Tpath[content2Tpath.find(startTpath)+len(startTpath):content2Tpath.rfind(endTpath)]

        # Create total path
        contentPath = content3Tpath + "---" + content3Value

        # Definition of sides   
        contentSplit = content3Tpath.split("--")
        if "BUY" in contentSplit[0]:
            first_side = "BUY"
        if "SELL" in contentSplit[0]:
            first_side = "SELL"

        if "BUY" in contentSplit[1]:
            second_side = "BUY"
        if "SELL" in contentSplit[1]:
            second_side = "SELL"

        if "BUY" in contentSplit[2]:
            third_side = "BUY"
        if "SELL" in contentSplit[2]:
            third_side = "SELL"

        # Definition of mono symbols
        first_mono_symbol = contentSplit[0].split("...")[0]
        second_mono_symbol = contentSplit[1].split("...")[0]
        third_mono_symbol = contentSplit[2].split("...")[0]

        # Definition of symbols
        first_symbol = contentSplit[0].split("...")[1].split("-")[0]
        second_symbol = contentSplit[1].split("...")[1].split("-")[0]
        third_symbol = contentSplit[2].split("...")[1].split("-")[0]

        # Definition of raw_qty
        first_raw_qty = contentSplit[0].split("...")[1].split("-")[2]
        second_raw_qty = contentSplit[1].split("...")[1].split("-")[2]
        third_raw_qty = contentSplit[2].split("...")[1].split("-")[2]

        # Function to calculate stepSize in number
        def stepSizer(sy):
            with open("stepSize.txt") as f:
                for num, line in enumerate(f, 1):
                    if sy in line:
                        lineDect = line
                        lineDetected = lineDect.replace("\n", "")
                        stepSize_raw = lineDetected.partition(": ")[2]

                        stepSize_raw_position = stepSize_raw.find("1")
                        stepSize_pre_raw = stepSize_raw.partition(".")[2]
                        stepSize_pre_raw_raw = stepSize_pre_raw.partition("1")[0]
                        if stepSize_raw_position == 0:
                            noDec = True
                            return 0 
                        else:
                            noDec = False
                            return stepSize_pre_raw_raw.count("0") + 1
        
        # Truncate decimals without rounded them
        def truncate(f, n):
            return math.floor(f * 10 ** n) / 10 ** n

        # Definition of qty
        first_pre_qty = ""
        second_pre_qty = ""
        third_pre_qty = ""
        third_pass_qty = ""
        third_pass_pass_qty = ""

        # Remove "-" and "e" from initials quantity to avoiding errors
        if "-" in str(first_raw_qty):
            first_raw_qty = first_raw_qty.replace("-", "")
            first_raw_qty = float(first_raw_qty)
        if "e" in str(first_raw_qty):
            first_raw_qty = first_raw_qty.replace("e", "")
            first_raw_qty = float(first_raw_qty)

        if "-" in str(second_raw_qty):
            second_raw_qty = second_raw_qty.replace("-", "")
            second_raw_qty = float(second_raw_qty)
        if "e" in str(second_raw_qty):
            second_raw_qty = second_raw_qty.replace("e", "")
            second_raw_qty = float(second_raw_qty)

        if "-" in str(third_raw_qty):
            third_raw_qty = third_raw_qty.replace("-", "")
            third_raw_qty = float(third_raw_qty)
        if "e" in str(third_raw_qty):
            third_raw_qty = third_raw_qty.replace("e", "")
            third_raw_qty = float(third_raw_qty)

        ####################################################################################
        ####################################################################################

        # Combinations of orders and determination of quantities

        if first_side == "SELL" and second_side == "BUY" and third_side == "SELL":
            first_pre_qty = amount  
            first_qty = truncate(first_pre_qty, stepSizer(first_symbol))

            second_pre_qty = ((1 / float(second_raw_qty)) * (float(first_raw_qty) * amount)) 
            second_qty = truncate(second_pre_qty, stepSizer(second_symbol))

            third_pre_qty = ((1 / float(second_raw_qty)) * truncate((float(first_raw_qty) * amount), stepSizer(first_symbol)))  
            third_qty = truncate(second_qty, stepSizer(third_symbol))
            third_pass_qty = float(third_raw_qty) * third_pre_qty 

            # 

            st_to_nd_final = float(first_raw_qty) * first_qty 
            nd_from_st_final = float(second_raw_qty) * second_qty 

            nd_to_rd_final = second_qty 
            rd_from_nd_final = third_qty 

            st_to_rd_final = first_qty 
            rd_from_st_final = float(third_raw_qty) * third_qty


        ####################################################################################

        if first_side == "SELL" and second_side == "BUY" and third_side == "BUY":
            first_pre_qty = amount  
            first_qty = truncate(first_pre_qty, stepSizer(first_symbol))

            second_pre_qty = ((1 / float(second_raw_qty)) * (float(first_raw_qty) * amount)) 
            second_qty = truncate(second_pre_qty, stepSizer(second_symbol))

            third_pre_qty = (1 / float(third_raw_qty)) * float(second_pre_qty) 
            third_qty = truncate(third_pre_qty, stepSizer(third_symbol))
            third_pass_qty = third_pre_qty

            # 

            st_to_nd_final = float(first_raw_qty) * first_qty 
            nd_from_st_final = second_qty 

            nd_to_rd_final = float(second_raw_qty) * second_qty 
            rd_from_nd_final = float(third_raw_qty) * third_qty 

            st_to_rd_final = first_qty 
            rd_from_st_final = third_qty

        ####################################################################################

        if first_side == "BUY" and second_side == "BUY" and third_side == "SELL": 
            first_pre_qty = ((1 / float(first_raw_qty)) * amount) 
            first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

            second_pre_qty = ((1 / float(second_raw_qty)) * (1 / float(first_raw_qty) * amount)) 
            second_qty = truncate(float(second_pre_qty), stepSizer(second_symbol))

            third_pre_qty = second_pre_qty 
            third_qty = truncate(float(second_qty), stepSizer(third_symbol))
            third_pass_qty = float(third_raw_qty) * third_pre_qty

            # 

            st_to_nd_final = first_qty 
            nd_from_st_final = float(second_raw_qty) * second_qty 

            nd_to_rd_final = second_qty 
            rd_from_nd_final = third_qty 

            st_to_rd_final = float(first_raw_qty) * first_qty
            rd_from_st_final = float(third_raw_qty) * third_qty

        ####################################################################################

        if first_side == "BUY" and second_side == "SELL" and third_side == "BUY": 
            first_pre_qty = ((1 / float(first_raw_qty)) * amount) 
            first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

            second_pre_qty = first_pre_qty    
            second_qty = truncate(float(first_qty), stepSizer(second_symbol))

            third_pre_qty = ((1 / float(third_raw_qty)) * (float(second_raw_qty) * truncate(first_qty, stepSizer(first_symbol)))) 
            third_qty = truncate(float(third_pre_qty), stepSizer(third_symbol))
            third_pass_qty = third_pre_qty

            # 

            st_to_nd_final = first_qty 
            nd_from_st_final = second_qty 

            nd_to_rd_final = float(second_raw_qty) * second_qty  
            rd_from_nd_final = float(third_raw_qty) * third_qty  

            st_to_rd_final = float(first_raw_qty) * first_qty 
            rd_from_st_final = third_qty

        ####################################################################################

        if first_side == "SELL" and second_side == "SELL" and third_side == "BUY":
            first_pre_qty = amount 
            first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

            second_pre_qty = (float(first_raw_qty) * amount) 
            second_qty = truncate(float(second_pre_qty), stepSizer(second_symbol))
    
            third_pre_qty = ((1 / float(third_raw_qty)) * (float(second_raw_qty) * second_pre_qty)) 
            third_qty = truncate(float(third_pre_qty), stepSizer(third_symbol))
            third_pass_qty = third_pre_qty

            # 

            st_to_nd_final = float(first_raw_qty) * first_qty 
            nd_from_st_final = second_qty 

            nd_to_rd_final = float(second_raw_qty) * second_qty  
            rd_from_nd_final = float(third_raw_qty) * third_qty  

            st_to_rd_final = first_qty 
            rd_from_st_final = third_qty

        ####################################################################################

        if first_side == "BUY" and second_side == "SELL" and third_side == "SELL":
            first_pre_qty = ((1 / float(first_raw_qty)) * amount) 
            first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

            second_pre_qty = first_pre_qty 
            second_qty = truncate(float(first_qty), stepSizer(second_symbol))

            third_pre_qty = float(second_raw_qty) * float(second_pre_qty)
            third_qty = truncate(float(third_pre_qty), stepSizer(third_symbol))
            third_pass_qty = float(third_raw_qty) * third_pre_qty

            # 

            st_to_nd_final = first_qty 
            nd_from_st_final = second_qty 

            nd_to_rd_final = float(second_raw_qty) * second_qty  
            rd_from_nd_final = third_qty  

            st_to_rd_final = float(first_raw_qty) * first_qty 
            rd_from_st_final = float(third_raw_qty) * third_qty

        ####################################################################################
        ####################################################################################

        # Check pairing quantities between orders

        # if third_mono_symbol == start_sym:
        #     print("true")
        # else:
        #     print("false")

        # if st_to_nd_final <= nd_from_st_final:
        #     print("true - " + str(st_to_nd_final) + " - " + str(nd_from_st_final))
        # else:
        #     print("false - " + str(st_to_nd_final) + " - " + str(nd_from_st_final))
        
        # if nd_to_rd_final <= rd_from_nd_final:
        #     print("true - " + str(nd_to_rd_final) + " - " + str(rd_from_nd_final))
        # else:
        #     print("false - " + str(nd_to_rd_final) + " - " + str(rd_from_nd_final))
        
        # if st_to_rd_final <= rd_from_st_final:
        #     print("true - " + str(st_to_rd_final) + " - " + str(rd_from_st_final))
        # else:
        #     print("false - " + str(st_to_rd_final) + " - " + str(rd_from_st_final))

        ####################################################################################

        # Send orders

        if third_mono_symbol == start_sym: 
            if st_to_nd_final <= nd_from_st_final and nd_to_rd_final <= rd_from_nd_final and st_to_rd_final <= (rd_from_st_final - ((rd_from_st_final * fee) / 100)):
        
                try:
                    client.create_order(symbol=first_symbol, side=first_side,type=ORDER_TYPE_MARKET,quantity=first_qty)
                    
                    try:
                        client.create_order(symbol=second_symbol, side=second_side,type=ORDER_TYPE_MARKET,quantity=second_qty )
                        
                        try:
                            client.create_order(symbol=third_symbol, side=third_side,type=ORDER_TYPE_MARKET,quantity=third_qty)

                            print("\n" + str(first_symbol) + ": " + str(first_qty) + " - " + str(second_symbol) + ": " + str(second_qty) + " - " + str(third_symbol) + ": " + str(third_qty))
                            
                            print("ORDERS DONE" + "\n")
                            #print("1 a 2: " + str(st_to_nd_final) + " - " + str(nd_from_st_final) + " -- 2 a 3: " + str(nd_to_rd_final) + " - " + str(rd_from_nd_final) + " -- 3 a 1: " + str(st_to_rd_final) + " - " + str(rd_from_st_final))

                            # Shutdown server
                            return redirect('/shutdown')
                        
                        except Exception as erro:
                            flash(erro.message, "erro")
                            print("\n" + str(first_symbol) + ": " + str(first_qty) + " - " + str(second_symbol) + ": " + str(second_qty) + " - " + str(third_symbol) + ": " + str(third_qty))
                            print("ERROR 3: " + erro.message + "\n") 
                            #print("1 a 2: " + str(st_to_nd_final) + " - " + str(nd_from_st_final) + " -- 2 a 3: " + str(nd_to_rd_final) + " - " + str(rd_from_nd_final) + " -- 3 a 1: " + str(st_to_rd_final) + " - " + str(rd_from_st_final))

                            # Shutdown server
                            return redirect('/shutdown')   

                    except Exception as err:
                        flash(err.message, "err")
                        print("\n" +  str(first_symbol) + ": " + str(first_qty) + " - " + str(second_symbol) + ": " + str(second_qty) + " - " + str(third_symbol) + ": " + str(third_qty))
                        print("ERROR 2: " + err.message + "\n")
                        #print("1 a 2: " + str(st_to_nd_final) + " - " + str(nd_from_st_final) + " -- 2 a 3: " + str(nd_to_rd_final) + " - " + str(rd_from_nd_final) + " -- 3 a 1: " + str(st_to_rd_final) + " - " + str(rd_from_st_final))

                        # Shutdown server
                        return redirect('/shutdown')

                except Exception as er:
                    flash(er.message, "er")
                    print("\n" + str(first_symbol) + ": " + str(first_qty) + " - " + str(second_symbol) + ": " + str(second_qty) + " - " + str(third_symbol) + ": " + str(third_qty))
                    print("ERROR 1: " + er.message + "\n")
                    #print("1 a 2: " + str(st_to_nd_final) + " - " + str(nd_from_st_final) + " -- 2 a 3: " + str(nd_to_rd_final) + " - " + str(rd_from_nd_final) + " -- 3 a 1: " + str(st_to_rd_final) + " - " + str(rd_from_st_final))
                    
                    # Shutdown server
                    return redirect('/shutdown')

        ####################################################################################

    return 'JSON posted'

if __name__ == '__main__':
  app.run(debug=True)

