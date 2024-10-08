//+--------------------------------------------------------------+
//|     DWX_server_MT5.mq4
//|     @author: Darwinex Labs (www.darwinex.com)
//|
//|     Copyright (c) 2017-2021, Darwinex. All rights reserved.
//|
//|     Licensed under the BSD 3-Clause License, you may not use this file except
//|     in compliance with the License.
//|
//|     You may obtain a copy of the License at:
//|     https://opensource.org/licenses/BSD-3-Clause
//+--------------------------------------------------------------+
#property copyright "Copyright 2017-2021, Darwinex Labs."
#property link "https://www.darwinex.com/"
#property version "1.0"
#property strict

/*

- IMPORTANT: check if ORDER_TIME_GTC will still use expiration date. or do we need ORDER_TIME_SPECIFIED?

mql:
- do we need start/endIdentifier? if we use json, it should automatically give an error if not complete.

python:
- dont save  TimeGMT() in every file. we can just use time modified in python.
- maxTryOpenSeconds  (in python): if the file exists for 10 seconds (cant create a new one), return an error. maybe use multiple files for commands?

*/

#include <Trade\Trade.mqh>
#include <socket-library-mt4-mt5.mqh>
#include <formats\Json.mqh>

//--- object for performing trade operations
CTrade trade;

// Server socket
ServerSocket *glbServerSocket;

// Array of current clients
ClientSocket *glbClients[];

// Watch for need to create timer;
bool glbCreatedTimer = false;

input string t0 = "--- General Parameters ---";
// if the timer is too small, we might have problems accessing the files from python (mql will write to file every update time).
input int MILLISECOND_TIMER = 25;

input int numLastMessages = 50;
input string t1 = "If true, it will open charts for bar data symbols, ";
input string t2 = "which reduces the delay on a new bar.";
input bool openChartsForBarData = true;
input bool openChartsForHistoricData = true;
input string t3 = "--- Trading Parameters ---";
input int MaximumOrders = 20;
input double MaximumLotSize = 10;
input int SlippagePoints = 3;
input int lotSizeDigits = 5;
input bool asyncTradeMode = false;
// Set host and Port
input string HOST = "0.0.0.0";
input ushort PORT = 5000;

int maxCommandFiles = 50;
int maxNumberOfCharts = 100;

long lastMessageMillis = 0;
long lastUpdateMillis = GetTickCount(), lastUpdateOrdersMillis = GetTickCount();

string startIdentifier = "<:";
string endIdentifier = ":>";
string delimiter = "|";
string folderName = "DWX";
string filePathOrders = folderName + "/DWX_Orders.txt";
string filePathMessages = folderName + "/DWX_Messages.txt";
string filePathMarketData = folderName + "/DWX_Market_Data.txt";
string filePathBarData = folderName + "/DWX_Bar_Data.txt";
string filePathHistoricData = folderName + "/DWX_Historic_Data.txt";
string filePathSymbolsData = folderName + "/DWX_Symbols_Data.txt";
string filePathHistoricTrades = folderName + "/DWX_Historic_Trades.txt";
string filePathCommandsPrefix = folderName + "/DWX_Commands_";

string lastOrderText = "", lastMarketDataText = "", lastMessageText = "";

// struct SymbolSubscription
// {
//    ClientSocket pClient;
//    string MarketDataSymbols[];
// };

// SymbolSubscription symbolSubscriptions[];
// int symbolSubscriptionCount = 0;

// Timer interval in milliseconds
int timerInterval = 1; // * 1000;

struct MESSAGE
{
   long millis;
   string message;
};

MESSAGE lastMessages[];

string MarketDataSymbols[];

int commandIDindex = 0;
int commandIDs[];

/**
 * Class definition for an specific instrument: the tuple (symbol,timeframe)
 */
class Instrument
{
public:
   //--------------------------------------------------------------
   /** Instrument constructor */
   Instrument()
   {
      _symbol = "";
      _name = "";
      _timeframe = PERIOD_CURRENT;
      _lastPubTime = 0;
   }

   //--------------------------------------------------------------
   /** Getters */
   string symbol() { return _symbol; }
   ENUM_TIMEFRAMES timeframe() { return _timeframe; }
   string name() { return _name; }
   datetime getLastPublishTimestamp() { return _lastPubTime; }
   /** Setters */
   void setLastPublishTimestamp(datetime tmstmp) { _lastPubTime = tmstmp; }

   //--------------------------------------------------------------
   /** Setup instrument with symbol and timeframe descriptions
    *  @param argSymbol Symbol
    *  @param argTimeframe Timeframe
    */
   void setup(string argSymbol, string argTimeframe)
   {
      _symbol = argSymbol;
      _timeframe = StringToTimeFrame(argTimeframe);
      _name = _symbol + "_" + argTimeframe;
      _lastPubTime = 0;
      SymbolSelect(_symbol, true);
      if (openChartsForBarData)
      {
         OpenChartIfNotOpen(_symbol, _timeframe);
         Sleep(200); // sleep to allow time to open the chart and update the data.
      }
   }

   //--------------------------------------------------------------
   /** Get last N MqlRates from this instrument (symbol-timeframe)
    *  @param rates Receives last 'count' rates
    *  @param count Number of requested rates
    *  @return Number of returned rates
    */
   int GetRates(MqlRates &rates[], int count)
   {
      // ensures that symbol is setup
      if (StringLen(_symbol) > 0)
      {
         return CopyRates(_symbol, _timeframe, 1, count, rates);
      }
      return 0;
   }

protected:
   string _name;               //!< Instrument descriptive name
   string _symbol;             //!< Symbol
   ENUM_TIMEFRAMES _timeframe; //!< Timeframe
   datetime _lastPubTime;      //!< Timestamp of the last published OHLC rate. Default = 0 (1 Jan 1970)
};

// Array of instruments whose rates will be published if Publish_MarketRates = True. It is initialized at OnInit() and
// can be updated through TRACK_RATES request from client peers.
Instrument BarDataInstruments[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{

   if (!EventSetMillisecondTimer(MILLISECOND_TIMER))
   {
      Print("EventSetMillisecondTimer() returned an error: ", ErrorDescription(GetLastError()));
      return INIT_FAILED;
   }

   // set up server socket
   // Create the server socket
   glbServerSocket = new ServerSocket(PORT, false);
   if (glbServerSocket.Created())
   {
      Print("Server socket created");

      // Note: this can fail if MT4/5 starts up
      // with the EA already attached to a chart. Therefore,
      // we repeat in OnTick()
      glbCreatedTimer = EventSetMillisecondTimer(timerInterval);
   }
   else
   {
      Print("Server socket FAILED - is the port already in use?");
      return INIT_FAILED;
   }

   ResetFolder();
   ResetCommandIDs(NULL);
   ArrayResize(lastMessages, numLastMessages);

   trade.SetAsyncMode(asyncTradeMode);
   trade.SetDeviationInPoints(SlippagePoints); // (int)(slippagePips*_pipInPoints)
   trade.SetTypeFilling(ORDER_FILLING_RETURN); // will fill the complete order, there are also FOK and IOC modes: ORDER_FILLING_FOK, ORDER_FILLING_IOC.
   trade.LogLevel(LOG_LEVEL_ERRORS);           // else it will print a lot on tester.
   // trade.SetExpertMagicNumber(magicNumber);

   // Download symbols data

   return INIT_SUCCEEDED;
}
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{

   EventKillTimer();

   // free server socket and any clients
   glbCreatedTimer = false;

   // Delete all clients currently connected
   for (int i = 0; i < ArraySize(glbClients); i++)
   {
      delete glbClients[i];
   }

   // Free the server socket
   delete glbServerSocket;
   Print("Server socket terminated");

   ResetFolder();
}

//+------------------------------------------------------------------+
//| Expert timer function                                            |
//+------------------------------------------------------------------+
void OnTimer()
{

   // update prices regularly in case there was no tick within X milliseconds (for non-chart symbols).
   if (GetTickCount() >= lastUpdateMillis + MILLISECOND_TIMER)
      OnTick();

   // accept new connections, and handle incoming data from clients
   string recvMsg = "No data received";
   // Keep accepting any pending connections until Accept() returns NULL
   ClientSocket *pNewClient = NULL;

   do
   {
      pNewClient = glbServerSocket.Accept();
      if (pNewClient != NULL)
      {
         int sz = ArraySize(glbClients);
         ArrayResize(glbClients, sz + 1);
         glbClients[sz] = pNewClient;

         Print("Connection received!");
         // pNewClient.Send("Connected to the MT5 Server!\r\n");
      }

   } while (pNewClient != NULL);

   // Read incoming data from all current clients, watching for
   // any which now appear to be dead
   int ctClients = ArraySize(glbClients);
   for (int i = ctClients - 1; i >= 0; i--)
   {
      ClientSocket *pClient = glbClients[i];
      // pClient.Send("Welcome to MT5 Socket Server\r\n");

      // Keep reading CRLF-terminated lines of input from the client
      // until we run out of data
      string strCommand;
      do
      {
         strCommand = pClient.Receive();

         if (StringLen(strCommand) != 0)
         {
            Print(strCommand);

            // Free the server socket
            if (strCommand == "q")
            {
               delete glbServerSocket;
               Print("Server socket terminated");
               return;
            }

            ParseCommands(strCommand, pClient);
         }
      } while (strCommand != "");

      if (!pClient.IsSocketConnected())
      {
         // Client is dead. Remove from array
         delete pClient;
         for (int j = i + 1; j < ctClients; j++)
         {
            glbClients[j - 1] = glbClients[j];
         }
         ctClients--;
         ArrayResize(glbClients, ctClients);
      }
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   /*
      Use this OnTick() function to send market data to subscribed client.
   */
   lastUpdateMillis = GetTickCount();

   CheckOpenOrders();
   CheckMarketData();
   CheckBarData();

   // Use OnTick() to watch for failure to create the timer in OnInit()
   if (!glbCreatedTimer)
      glbCreatedTimer = EventSetMillisecondTimer(timerInterval);
}

void ParseCommands(string text, ClientSocket *pClient)
{
   // make sure that the file content is complete.
   int length = StringLen(text);
   if (length == 0)
   {
      SendError("Command not found: ", text, pClient, false);
      return;
   }

   if (StringSubstr(text, 0, 2) != startIdentifier)
   {
      SendError("WRONG_FORMAT_START_IDENTIFIER", "Start identifier not found for command: " + text, pClient, false);
      return;
   }

   if (StringSubstr(text, length - 2, 2) != endIdentifier)
   {
      SendError("WRONG_FORMAT_END_IDENTIFIER", "End identifier not found for command: " + text, pClient, false);
      return;
   }
   text = StringSubstr(text, 2, length - 4);

   ushort uSep = StringGetCharacter(delimiter, 0);
   string data[];
   int splits = StringSplit(text, uSep, data);

   if (splits != 3)
   {
      SendError("WRONG_FORMAT_COMMAND", "Wrong format for command: " + text, pClient, false);
      return;
   }

   int commandID = (int)data[0];
   string command = data[1];
   string content = data[2];

   // dont check commandID for the reset command because else it could get blocked if only the python/java/dotnet side restarts, but not the mql side.
   if (command != "RESET_COMMAND_IDS" && CommandIDfound(commandID))
   {
      string message = StringFormat("Not executing command because ID already exists. commandID: %d, command: %s, content: %s ", commandID, command, content);
      Print(message);
      SendError("COMMAND_NOT_EXECUTED", message, pClient, true);
      // return;
   }
   commandIDs[commandIDindex] = commandID;
   commandIDindex = (commandIDindex + 1) % ArraySize(commandIDs);

   if (command == "OPEN_ORDER")
   {
      OpenOrder(content, pClient);
   }
   else if (command == "CLOSE_ORDER")
   {
      CloseOrder(content, pClient);
   }
   else if (command == "CLOSE_ALL_ORDERS")
   {
      CloseAllOrders(pClient);
   }
   else if (command == "CLOSE_ORDERS_BY_SYMBOL")
   {
      CloseOrdersBySymbol(content, pClient);
   }
   else if (command == "CLOSE_ORDERS_BY_MAGIC")
   {
      CloseOrdersByMagic(content, pClient);
   }
   else if (command == "MODIFY_ORDER")
   {
      ModifyOrder(content, pClient);
   }
   else if (command == "SUBSCRIBE_SYMBOLS")
   {
      SubscribeSymbols(content, pClient);
   }
   else if (command == "SUBSCRIBE_SYMBOLS_BAR_DATA")
   {
      SubscribeSymbolsBarData(content, pClient);
   }
   else if (command == "GET_HISTORIC_TRADES")
   {
      GetHistoricTrades(content, pClient, false);
   }
   else if (command == "GET_HISTORIC_DATA")
   {
      GetHistoricData(content, pClient);
   }
   else if (command == "GET_ACTIVE_SYMBOLS")
   {
      GetActiveSymbols(content, pClient, false);
   }
   else if (command == "ACCOUNT_INFO")
   {
      GetAccountInfo(pClient, false);
   }
   else if (command == "RESET_COMMAND_IDS")
   {
      Print("Resetting stored command IDs.");
      ResetCommandIDs(pClient);
   }
}

void OpenOrder(string orderStr, ClientSocket *pClient)
{

   string sep = ",";
   ushort uSep = StringGetCharacter(sep, 0);
   string data[];
   int splits = StringSplit(orderStr, uSep, data);

   if (ArraySize(data) != 9)
   {
      SendError("OPEN_ORDER_WRONG_FORMAT", "Wrong format for OPEN_ORDER command: " + orderStr, pClient, false);
      return;
   }

   int numOrders = NumOrders();
   if (numOrders >= MaximumOrders)
   {
      SendError("OPEN_ORDER_MAXIMUM_NUMBER", StringFormat("Number of orders (%d) larger than or equal to MaximumOrders (%d).", numOrders, MaximumOrders), pClient, false);
      return;
   }

   string symbol = data[0];
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   int orderType = StringToOrderType(data[1]);
   double lots = NormalizeDouble(StringToDouble(data[2]), lotSizeDigits);
   double price = NormalizeDouble(StringToDouble(data[3]), digits);
   double stopLoss = NormalizeDouble(StringToDouble(data[4]), digits);
   double takeProfit = NormalizeDouble(StringToDouble(data[5]), digits);
   int magic = (int)StringToInteger(data[6]);
   string comment = data[7];
   datetime expiration = (datetime)StringToInteger(data[8]);

   if (price == 0 && orderType == POSITION_TYPE_BUY)
      price = ask(symbol);
   if (price == 0 && orderType == POSITION_TYPE_SELL)
      price = bid(symbol);

   if (orderType == -1)
   {
      SendError("OPEN_ORDER_TYPE", StringFormat("Order type could not be parsed: %f (%f)", orderType, data[1]), pClient, false);
      return;
   }

   if (lots < SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN) || lots > SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX))
   {
      SendError("OPEN_ORDER_LOTSIZE_OUT_OF_RANGE", StringFormat("Lot size out of range (min: %f, max: %f): %f", SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN), SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX), lots), pClient, false);
      return;
   }

   if (lots > MaximumLotSize)
   {
      SendError("OPEN_ORDER_LOTSIZE_TOO_LARGE", StringFormat("Lot size (%.2f) larger than MaximumLotSize (%.2f).", lots, MaximumLotSize), pClient, false);
      return;
   }

   if (price == 0)
   {
      SendError("OPEN_ORDER_PRICE_ZERO", "Price is zero: " + orderStr, pClient, false);
      return;
   }

   trade.SetExpertMagicNumber(magic);

   bool res = false;
   if (orderType == ORDER_TYPE_BUY)
      res = trade.Buy(lots, symbol, price, stopLoss, takeProfit, comment);
   if (orderType == ORDER_TYPE_SELL)
      res = trade.Sell(lots, symbol, price, stopLoss, takeProfit, comment);
   if (orderType == ORDER_TYPE_BUY_LIMIT)
      res = trade.BuyLimit(lots, price, symbol, stopLoss, takeProfit, ORDER_TIME_GTC, expiration, comment);
   if (orderType == ORDER_TYPE_SELL_LIMIT)
      res = trade.SellLimit(lots, price, symbol, stopLoss, takeProfit, ORDER_TIME_GTC, expiration, comment);
   if (orderType == ORDER_TYPE_BUY_STOP)
      res = trade.BuyStop(lots, price, symbol, stopLoss, takeProfit, ORDER_TIME_GTC, expiration, comment);
   if (orderType == ORDER_TYPE_SELL_STOP)
      res = trade.SellStop(lots, price, symbol, stopLoss, takeProfit, ORDER_TIME_GTC, expiration, comment);

   if (res)
   {
      SendInfo("Successfully sent order: " + symbol + ", " + OrderTypeToString(orderType) + ", " + DoubleToString(lots, lotSizeDigits) + ", " + DoubleToString(price, digits), pClient, false);
   }
   else
   {
      SendError("OPEN_ORDER", "Could not open order: " + ErrorDescription(GetLastError()), pClient, false);
   }
}

void ModifyOrder(string orderStr, ClientSocket *pClient)
{
   string sep = ",";
   ushort uSep = StringGetCharacter(sep, 0);
   string data[];
   int splits = StringSplit(orderStr, uSep, data);

   if (ArraySize(data) != 5)
   {
      SendError("MODIFY_ORDER_WRONG_FORMAT", "Wrong format for MODIFY_ORDER command: " + orderStr, pClient, false);
      return;
   }

   ulong ticket = StringToInteger(data[0]);

   bool isPosition = true;
   if (!PositionSelectByTicket(ticket))
   {
      isPosition = false;
      if (!OrderSelect(ticket))
      {
         SendError("MODIFY_ORDER_SELECT_TICKET", "Could not select order with ticket: " + IntegerToString(ticket), pClient, false);
         return;
      }
   }

   string symbol = "";
   int orderType = -1;
   if (isPosition)
   {
      symbol = PositionGetString(POSITION_SYMBOL);
      orderType = (int)PositionGetInteger(POSITION_TYPE);
   }
   else
   {
      symbol = OrderGetString(ORDER_SYMBOL);
      orderType = (int)OrderGetInteger(ORDER_TYPE);
   }
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   double price = NormalizeDouble(StringToDouble(data[1]), digits);
   double stopLoss = NormalizeDouble(StringToDouble(data[2]), digits);
   double takeProfit = NormalizeDouble(StringToDouble(data[3]), digits);
   datetime expiration = (datetime)StringToInteger(data[4]);

   if (!isPosition && price == 0)
   {
      price = OrderGetDouble(ORDER_PRICE_OPEN);
   }

   bool res = false;
   if (isPosition)
      res = trade.PositionModify(ticket, stopLoss, takeProfit);
   else
      res = trade.OrderModify(ticket, price, stopLoss, takeProfit, ORDER_TIME_GTC, expiration);
   if (res)
   {
      string message = StringFormat("Successfully modified order %d: %s, %s, %.5f, %.5f, %.5f", ticket, symbol, OrderTypeToString(orderType), price, stopLoss, takeProfit);
      SendInfo(message, pClient, false);
   }
   else
   {
      SendError("MODIFY_ORDER", StringFormat("Error in modifying order %d: %s", ticket, ErrorDescription(GetLastError())), pClient, false);
   }
}

void CloseOrder(string orderStr, ClientSocket *pClient)
{
   string sep = ",";
   ushort uSep = StringGetCharacter(sep, 0);
   string data[];
   int splits = StringSplit(orderStr, uSep, data);

   if (ArraySize(data) != 2)
   {
      SendError("CLOSE_ORDER_WRONG_FORMAT", "Wrong format for CLOSE_ORDER command: " + orderStr, pClient, false);
      return;
   }
   ulong ticket = StringToInteger(data[0]);
   double lots = NormalizeDouble(StringToDouble(data[1]), lotSizeDigits);

   bool isPosition = true;
   if (!PositionSelectByTicket(ticket))
   {
      isPosition = false;
      if (!OrderSelect(ticket))
      {
         SendError("CLOSE_ORDER_SELECT_TICKET", "Could not select order with ticket: " + IntegerToString(ticket), pClient, false);
         return;
      }
   }

   bool res = false;
   if (isPosition)
   {
      if (lots == 0)
         lots = PositionGetDouble(POSITION_VOLUME);

      if (lots < PositionGetDouble(POSITION_VOLUME))
         res = trade.PositionClosePartial(ticket, lots);
      else
         res = trade.PositionClose(ticket);
   }
   else
   {
      res = trade.OrderDelete(ticket);
   }

   if (res)
   {
      string symbol = "";
      if (isPosition)
         symbol = PositionGetString(POSITION_SYMBOL);
      else
         symbol = OrderGetString(ORDER_SYMBOL);

      string message = "Successfully closed order: " + IntegerToString(ticket) + ", " + symbol + ", " + DoubleToString(lots, lotSizeDigits);
      SendInfo(message, pClient, false);
   }
   else
   {
      SendError("CLOSE_ORDER_TICKET", "Could not close position " + IntegerToString(ticket) + ": " + ErrorDescription(GetLastError()), pClient, false);
   }
}

void CloseAllOrders(ClientSocket *pClient)
{

   int closed = 0, errors = 0;

   for (int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if (!PositionSelectByTicket(ticket))
         continue;
      if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
      {
         bool res = trade.PositionClose(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
      else if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
      {
         bool res = trade.PositionClose(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
   }
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if (!OrderSelect(ticket))
         continue;
      if (OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_STOP)
      {
         bool res = trade.OrderDelete(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
   }

   if (closed == 0 && errors == 0)
      SendInfo("No orders to close.", pClient, false);
   else if (errors > 0)
      SendError("CLOSE_ORDER_ALL", "Error during closing of " + IntegerToString(errors) + " orders.", pClient, false);
   else
      SendInfo("Successfully closed " + IntegerToString(closed) + " orders.", pClient, false);
}

void CloseOrdersBySymbol(string symbol, ClientSocket *pClient)
{

   int closed = 0, errors = 0;

   for (int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if (!PositionSelectByTicket(ticket) || PositionGetString(POSITION_SYMBOL) != symbol)
         continue;
      if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
      {
         bool res = trade.PositionClose(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
      else if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
      {
         bool res = trade.PositionClose(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
   }
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if (!OrderSelect(ticket) || OrderGetString(ORDER_SYMBOL) != symbol)
         continue;
      if (OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_STOP)
      {
         bool res = trade.OrderDelete(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
   }

   if (closed == 0 && errors == 0)
      SendInfo("No orders to close with symbol " + symbol + ".", pClient, false);
   else if (errors > 0)
      SendError("CLOSE_ORDER_SYMBOL", "Error during closing of " + IntegerToString(errors) + " orders with symbol " + symbol + ".", pClient, false);
   else
      SendInfo("Successfully closed " + IntegerToString(closed) + " orders with symbol " + symbol + ".", pClient, false);
}

void CloseOrdersByMagic(string magicStr, ClientSocket *pClient)
{

   int magic = (int)StringToInteger(magicStr);

   int closed = 0, errors = 0;

   for (int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if (!PositionSelectByTicket(ticket) || PositionGetInteger(POSITION_MAGIC) != magic)
         continue;
      if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
      {
         bool res = trade.PositionClose(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
      else if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
      {
         bool res = trade.PositionClose(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
   }
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if (!OrderSelect(ticket) || OrderGetInteger(ORDER_MAGIC) != magic)
         continue;
      if (OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_STOP)
      {
         bool res = trade.OrderDelete(ticket);
         if (res)
            closed++;
         else
            errors++;
      }
   }

   if (closed == 0 && errors == 0)
      SendInfo("No orders to close with magic " + IntegerToString(magic) + ".", pClient, false);
   else if (errors > 0)
      SendError("CLOSE_ORDER_MAGIC", "Error during closing of " + IntegerToString(errors) + " orders with magic " + IntegerToString(magic) + ".", pClient, false);
   else
      SendInfo("Successfully closed " + IntegerToString(closed) + " orders with magic " + IntegerToString(magic) + ".", pClient, false);
}

int NumOrders()
{

   int n = 0;

   for (int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if (!PositionSelectByTicket(ticket))
         continue;
      if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY || PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
      {
         n++;
      }
   }
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if (!OrderSelect(ticket))
         continue;
      if (OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_STOP)
      {
         n++;
      }
   }
   return n;
}

void SubscribeSymbols(string symbolsStr, ClientSocket *pClient)
{

   string sep = ",";
   ushort uSep = StringGetCharacter(sep, 0);
   string data[];
   int splits = StringSplit(symbolsStr, uSep, data);

   if (ArraySize(data) == 0)
   {
      ArrayResize(MarketDataSymbols, 0);
      SendInfo("Unsubscribed from all tick data because of empty symbol list.", pClient, false);
      return;
   }

   string successSymbols = "", errorSymbols = "";
   for (int i = 0; i < ArraySize(data); i++)
   {
      if (SymbolSelect(data[i], true))
      {
         ArrayResize(MarketDataSymbols, i + 1);
         MarketDataSymbols[i] = data[i];
         successSymbols += data[i] + ", ";
      }
      else
      {
         errorSymbols += data[i] + ", ";
      }
   }

   if (StringLen(errorSymbols) > 0)
   {
      SendError("SUBSCRIBE_SYMBOL", "Could not subscribe to symbols: " + StringSubstr(errorSymbols, 0, StringLen(errorSymbols) - 2), pClient, false);
   }
   if (StringLen(successSymbols) > 0)
   {
      SendInfo("Successfully subscribed to: " + StringSubstr(successSymbols, 0, StringLen(successSymbols) - 2), pClient, false);
   }
}

void SubscribeSymbolsBarData(string dataStr, ClientSocket *pClient)
{

   string sep = ",";
   ushort uSep = StringGetCharacter(sep, 0);
   string data[];
   int splits = StringSplit(dataStr, uSep, data);

   if (ArraySize(data) == 0)
   {
      ArrayResize(BarDataInstruments, 0);
      SendInfo("Unsubscribed from all bar data because of empty symbol list.", pClient, false);
      return;
   }

   if (ArraySize(data) < 2 || ArraySize(data) % 2 != 0)
   {
      SendError("BAR_DATA_WRONG_FORMAT", "Wrong format to subscribe to bar data: " + dataStr, pClient, false);
      return;
   }

   // Format: SYMBOL_1,TIMEFRAME_1,SYMBOL_2,TIMEFRAME_2,...,SYMBOL_N,TIMEFRAME_N
   string errorSymbols = "";

   int numInstruments = ArraySize(data) / 2;

   for (int s = 0; s < numInstruments; s++)
   {

      if (SymbolSelect(data[2 * s], true))
      {

         ArrayResize(BarDataInstruments, s + 1);

         BarDataInstruments[s].setup(data[2 * s], data[(2 * s) + 1]);
      }
      else
      {
         errorSymbols += "'" + data[2 * s] + "', ";
      }
   }

   if (StringLen(errorSymbols) > 0)
      errorSymbols = "[" + StringSubstr(errorSymbols, 0, StringLen(errorSymbols) - 2) + "]";

   if (StringLen(errorSymbols) == 0)
   {
      SendInfo("Successfully subscribed to bar data: " + dataStr, pClient, false);

      CheckBarData();
   }
   else
   {
      SendError("SUBSCRIBE_BAR_DATA", "Could not subscribe to bar data for: " + errorSymbols, pClient, false);
   }
}

//+------------------------------------------------------------------+
//| Return the symbol index in the Market Watch symbol list          |
//+------------------------------------------------------------------+
int SymbolIndex(const string symbol)
{
   int total = SymbolsTotal(false);
   for (int i = 0; i < total; i++)
   {
      string name = SymbolName(i, false);
      if (name == symbol)
         return i;
   }
   return (WRONG_VALUE);
}

void GetAccountInfo(ClientSocket *pClient, bool useFile)
{

   string text = StringFormat("{\"account_info\": {\"name\": \"%s\", \"number\": %d, \"currency\": \"%s\", \"leverage\": %d, \"free_margin\": %f, \"balance\": %f, \"equity\": %f}",
                              AccountInfoString(ACCOUNT_NAME),
                              AccountInfoInteger(ACCOUNT_LOGIN),
                              AccountInfoString(ACCOUNT_CURRENCY),
                              AccountInfoInteger(ACCOUNT_LEVERAGE),
                              AccountInfoDouble(ACCOUNT_MARGIN_FREE),
                              AccountInfoDouble(ACCOUNT_BALANCE),
                              AccountInfoDouble(ACCOUNT_EQUITY));

   text += "}";

   Print("Successfully fetched account info.");

   if (useFile)
   {
      if (WriteToFile(filePathSymbolsData, text))
      {
         SendInfo(text, pClient, true);
      }
   }
   else
   {
      if (WriteToSocket(text, pClient))
      {
         SendInfo(text, pClient, true);
      }
   }
}

string GetSymbolDetails(string symbolName)
{
   //--- get data for symbol
   string text = "";

   int spread = (int)SymbolInfoInteger(symbolName, SYMBOL_SPREAD);
   if (spread <= 0)
   {
      // checks if a symbols is active in the trade server
      return text;
   }

   int digits = (int)SymbolInfoInteger(symbolName, SYMBOL_DIGITS);
   int stops_level = (int)SymbolInfoInteger(symbolName, SYMBOL_TRADE_STOPS_LEVEL);
   double point = (double)SymbolInfoDouble(symbolName, SYMBOL_POINT);
   double contract_size = (double)SymbolInfoDouble(symbolName, SYMBOL_TRADE_CONTRACT_SIZE);
   double price_change = (double)SymbolInfoDouble(symbolName, SYMBOL_PRICE_CHANGE);
   double price_volatility = (double)SymbolInfoDouble(symbolName, SYMBOL_PRICE_VOLATILITY);

   double volume_min = (double)SymbolInfoDouble(symbolName, SYMBOL_VOLUME_MIN);
   double volume_max = (double)SymbolInfoDouble(symbolName, SYMBOL_VOLUME_MAX);
   double volume_step = (double)SymbolInfoDouble(symbolName, SYMBOL_VOLUME_STEP);
   double volume_limit = (double)SymbolInfoDouble(symbolName, SYMBOL_VOLUME_LIMIT);

   string category = SymbolInfoString(symbolName, SYMBOL_CATEGORY);
   string currency_base = SymbolInfoString(symbolName, SYMBOL_CURRENCY_BASE);     // Base currency of the symbol
   string currency_profit = SymbolInfoString(symbolName, SYMBOL_CURRENCY_PROFIT); // Profit currency
   string currency_margin = SymbolInfoString(symbolName, SYMBOL_CURRENCY_MARGIN); // Margin currency
   string description = SymbolInfoString(symbolName, SYMBOL_DESCRIPTION);         // String description of the symbol

   // text would contain infomation about the symbol
   // such as Digits, Contract size, Spread, Stop levels, Margin currency
   // Profit currency, calculation, tick size, tick value, initial margin
   // minimal volume, maximal volume
   // volume step, volume limit
   // expiration, GTC mode
   //
   // https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants
   // https://www.mql5.com/en/search#!keyword=symbol_&module=mql5_module_documentation
   // https://www.mql5.com/en/docs/marketinformation/symbolselect

   text += StringFormat("\"%d\": {\"symbol\": \"%s\", \"currency_base\": \"%s\", \"currency_profit\": \"%s\", \"currency_margin\": \"%s\", \"contract_size\": \"%.5f\", \"digits\": \"%d\", \"point\": \"%.5f\",  \"spread\": \"%d\", \"stops_level\": \"%d\", \"price_change\": \"%.5f\", \"price_volatility\": \"%.5f\", \"volume_min\": \"%.5f\", \"volume_max\": \"%.5f\", \"volume_step\": \"%.5f\", \"volume_limit\": \"%.5f\", \"category\": \"%s\", \"description\": \"%s\"}",
                        SymbolIndex(symbolName),
                        symbolName, currency_base,
                        currency_profit, currency_margin,
                        contract_size, digits, point, spread, stops_level,
                        price_change, price_volatility,
                        volume_min, volume_max, volume_step, volume_limit,
                        category, description);

   return text;
}

void GetActiveSymbols(string symbolName, ClientSocket *pClient, bool useFile)
{
   string text = "{";
   bool first = true;
   if (StringLen(symbolName) > 0)
   {

      string details = GetSymbolDetails(symbolName);
      if (StringLen(details) > 0)
      {
         if (!first)
            text += ", ";

         text += details;

         first = false;
      }
   }
   else
   {
      int totalSymbols = SymbolsTotal(false);
      for (int i = 0; i < totalSymbols; i++)
      {
         string SYMBOL_NAME = SymbolName(i, false);

         string details = GetSymbolDetails(SYMBOL_NAME);
         if (StringLen(details) > 0)
         {
            if (!first)
               text += ", ";

            text += details;

            first = false;
         }
      }
   }

   text += "}";

   Print("text: ", text);
   Print("Successfully read symbols.");

   if (useFile)
   {
      if (WriteToFile(filePathSymbolsData, text))
      {
      }
   }
   else
   {
      if (WriteToSocket(text, pClient))
      {
         SendInfo(text, pClient, true);
      }
   }
}

void GetHistoricData(string dataStr, ClientSocket *pClient)
{

   string sep = ",";
   ushort uSep = StringGetCharacter(sep, 0);
   string data[];
   int splits = StringSplit(dataStr, uSep, data);

   if (ArraySize(data) != 4)
   {
      SendError("HISTORIC_DATA_WRONG_FORMAT", "Wrong format for GET_HISTORIC_DATA command: " + dataStr, pClient, false);
      return;
   }

   string symbol = data[0];
   ENUM_TIMEFRAMES timeFrame = StringToTimeFrame(data[1]);
   datetime dateStart = (datetime)StringToInteger(data[2]);
   datetime dateEnd = (datetime)StringToInteger(data[3]);

   if (StringLen(symbol) == 0)
   {
      SendError("HISTORIC_DATA_SYMBOL", "Could not read symbol: " + dataStr, pClient, false);
      return;
   }

   if (!SymbolSelect(symbol, true))
   {
      SendError("HISTORIC_DATA_SELECT_SYMBOL", "Could not select symbol " + symbol + " in market watch. Error: " + ErrorDescription(GetLastError()), pClient, false);
   }

   if (openChartsForHistoricData)
   {
      // if just opnened sleep to give MT4 some time to fetch the data.
      if (OpenChartIfNotOpen(symbol, timeFrame))
         Sleep(200);
   }

   MqlRates rates_array[];

   // Get prices
   int rates_count = 0;

   // Handling ERR_HISTORY_WILL_UPDATED (4066) and ERR_NO_HISTORY_DATA (4073) errors.
   // For non-chart symbols and time frames MT4 often needs a few requests until the data is available.
   // But even after 10 requests it can happen that it is not available. So it is best to have the charts open.
   for (int i = 0; i < 10; i++)
   {
      // if (numBars > 0)
      //    rates_count = CopyRates(symbol, timeFrame, startPos, numBars, rates_array);
      rates_count = CopyRates(symbol, timeFrame, dateStart, dateEnd, rates_array);
      int errorCode = GetLastError();
      // Print("errorCode: ", errorCode);
      if (rates_count > 0 || (errorCode != 4066 && errorCode != 4073))
         break;
      Sleep(200);
   }

   if (rates_count <= 0)
   {
      SendError("HISTORIC_DATA", "Could not get historic data for " + symbol + "_" + data[1] + ": " + ErrorDescription(GetLastError()), pClient, false);
      return;
   }

   bool first = true;
   string text = "{\"" + symbol + "_" + TimeFrameToString(timeFrame) + "\": {";

   for (int i = 0; i < rates_count; i++)
   {

      if (first)
      {
         double daysDifference = ((double)MathAbs(rates_array[i].time - dateStart)) / (24 * 60 * 60);
         if ((timeFrame == PERIOD_MN1 && daysDifference > 33) || (timeFrame == PERIOD_W1 && daysDifference > 10) || (timeFrame < PERIOD_W1 && daysDifference > 3))
         {
            SendInfo(StringFormat("The difference between requested start date and returned start date is relatively large (%.1f days). Maybe the data is not available on MetaTrader.", daysDifference), pClient, false);
         }
         // Print(dateStart, " | ", rates_array[i].time, " | ", daysDifference);
      }
      else
      {
         text += ", ";
      }

      // maybe use integer instead of time string? IntegerToString(rates_array[i].time)
      text += StringFormat("\"%s\": {\"open\": %.5f, \"high\": %.5f, \"low\": %.5f, \"close\": %.5f, \"tick_volume\": %.5f}",
                           TimeToString(rates_array[i].time),
                           rates_array[i].open,
                           rates_array[i].high,
                           rates_array[i].low,
                           rates_array[i].close,
                           rates_array[i].tick_volume);

      first = false;
   }

   text += "}}";
   for (int i = 0; i < 5; i++)
   {
      // We can pick the most efficient
      if (WriteToFile(filePathHistoricData, text))
         break;

      // if (WriteToSocket(text, pClient))
      //    break;

      Sleep(100);
   }
   SendInfo(StringFormat("Successfully read historic data for %s_%s.", symbol, data[1]), pClient, false);
}

void GetHistoricTrades(string dataStr, ClientSocket *pClient, bool useFile)
{

   int lookbackDays = (int)StringToInteger(dataStr);

   if (lookbackDays <= 0)
   {
      SendError("HISTORIC_TRADES", "Lookback days smaller or equal to zero: " + dataStr, pClient, useFile);
      return;
   }

   bool first = true;
   string text = "{";
   HistorySelect(TimeCurrent() - lookbackDays * 24 * 60 * 60, TimeCurrent()); // needed to load the history! mmmmm MT5
   for (int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if (HistoryDealGetInteger(ticket, DEAL_TIME) < TimeCurrent() - lookbackDays * (24 * 60 * 60))
         continue;

      // long orderTicket = HistoryDealGetInteger(ticket, DEAL_ORDER);  // get order which belongs to the deal.
      // if (!HistoryOrderSelect(orderTicket)) continue;
      if (!first)
         text += ", ";
      else
         first = false;
      text += StringFormat("\"%llu\": {\"magic\": %d, \"symbol\": \"%s\", \"lots\": %.2f, \"type\": \"%s\", \"entry\": \"%s\", \"deal_time\": \"%s\", \"deal_price\": %.5f, \"pnl\": %.2f, \"commission\": %.2f, \"swap\": %.2f, \"comment\": \"%s\"}",
                           ticket,
                           HistoryDealGetInteger(ticket, DEAL_MAGIC),
                           HistoryDealGetString(ticket, DEAL_SYMBOL),
                           HistoryDealGetDouble(ticket, DEAL_VOLUME),
                           HistoryDealTypeToString((int)HistoryDealGetInteger(ticket, DEAL_TYPE)),
                           HistoryDealEntryTypeToString((int)HistoryDealGetInteger(ticket, DEAL_ENTRY)),
                           TimeToString(HistoryDealGetInteger(ticket, DEAL_TIME), TIME_DATE | TIME_SECONDS),
                           HistoryDealGetDouble(ticket, DEAL_PRICE),
                           HistoryDealGetDouble(ticket, DEAL_PROFIT),
                           HistoryDealGetDouble(ticket, DEAL_COMMISSION),
                           HistoryDealGetDouble(ticket, DEAL_SWAP),
                           HistoryDealGetString(ticket, DEAL_COMMENT));
   }

   text += "}";
   for (int i = 0; i < 5; i++)
   {
      // We can pick the most efficient
      if (useFile)
      {
         if (WriteToFile(filePathHistoricTrades, text))
            break;
      }
      else
      {
         if (WriteToSocket(text, pClient))
            break;
      }

      Sleep(100);
   }
   SendInfo("Successfully read historic trades.", pClient, useFile);
}

void CheckMarketData()
{
   bool first = true;
   string text = "{";
   for (int i = 0; i < ArraySize(MarketDataSymbols); i++)
   {

      MqlTick lastTick;

      if (SymbolInfoTick(MarketDataSymbols[i], lastTick))
      {

         if (!first)
            text += ", ";

         text += StringFormat("\"%s\": {\"bid\": %.5f, \"ask\": %.5f, \"last\": %.5f, \"tick_value\": %.5f}",
                              MarketDataSymbols[i],
                              lastTick.bid,
                              lastTick.ask,
                              lastTick.last,
                              SymbolInfoDouble(MarketDataSymbols[i], SYMBOL_TRADE_TICK_VALUE));

         first = false;
      }
      else
      {
         // text += "{\"symbol\": \"" + MarketDataSymbols[i] + "\", \"bid\": \"ERROR\", \"ask\": \"ERROR\"}";
         SendError("GET_BID_ASK", "Could not get bid/ask for " + MarketDataSymbols[i] + ". Last error: " + ErrorDescription(GetLastError()), NULL, true);
      }
   }

   text += "}";

   // only write to file if there was a change.
   if (text == lastMarketDataText)
      return;

   if (WriteToFile(filePathMarketData, text))
   {
      lastMarketDataText = text;
   }
}

void CheckBarData()
{

   // Python clients can also subscribe to a rates feed for each tracked instrument

   bool newData = false;
   string text = "{";

   for (int s = 0; s < ArraySize(BarDataInstruments); s++)
   {

      MqlRates curr_rate[];

      int count = BarDataInstruments[s].GetRates(curr_rate, 1);
      // if last rate is returned and its timestamp is greater than the last published...
      if (count > 0 && curr_rate[0].time > BarDataInstruments[s].getLastPublishTimestamp())
      {

         string rates = StringFormat("\"%s\": {\"time\": \"%s\", \"open\": %f, \"high\": %f, \"low\": %f, \"close\": %f, \"tick_volume\":%d}, ",
                                     BarDataInstruments[s].name(),
                                     TimeToString(curr_rate[0].time),
                                     curr_rate[0].open,
                                     curr_rate[0].high,
                                     curr_rate[0].low,
                                     curr_rate[0].close,
                                     curr_rate[0].tick_volume);
         text += rates;
         newData = true;

         // updates the timestamp
         BarDataInstruments[s].setLastPublishTimestamp(curr_rate[0].time);
      }
   }
   if (!newData)
      return;

   text = StringSubstr(text, 0, StringLen(text) - 2) + "}";
   for (int i = 0; i < 5; i++)
   {
      if (WriteToFile(filePathBarData, text))
         break;
      Sleep(100);
   }
}

ENUM_TIMEFRAMES StringToTimeFrame(string tf)
{
   // Standard timeframes
   if (tf == "M1")
      return PERIOD_M1;
   if (tf == "M2")
      return PERIOD_M2;
   if (tf == "M3")
      return PERIOD_M3;
   if (tf == "M4")
      return PERIOD_M4;
   if (tf == "M5")
      return PERIOD_M5;
   if (tf == "M6")
      return PERIOD_M6;
   if (tf == "M10")
      return PERIOD_M10;
   if (tf == "M12")
      return PERIOD_M12;
   if (tf == "M15")
      return PERIOD_M15;
   if (tf == "M20")
      return PERIOD_M20;
   if (tf == "M30")
      return PERIOD_M30;
   if (tf == "H1")
      return PERIOD_H1;
   if (tf == "H2")
      return PERIOD_H2;
   if (tf == "H3")
      return PERIOD_H3;
   if (tf == "H4")
      return PERIOD_H4;
   if (tf == "H6")
      return PERIOD_H6;
   if (tf == "H8")
      return PERIOD_H8;
   if (tf == "H12")
      return PERIOD_H12;
   if (tf == "D1")
      return PERIOD_D1;
   if (tf == "W1")
      return PERIOD_W1;
   if (tf == "MN1")
      return PERIOD_MN1;
   return -1;
}

string TimeFrameToString(ENUM_TIMEFRAMES tf)
{
   // Standard timeframes
   switch (tf)
   {
   case PERIOD_M1:
      return "M1";
   case PERIOD_M2:
      return "M2";
   case PERIOD_M3:
      return "M3";
   case PERIOD_M4:
      return "M4";
   case PERIOD_M5:
      return "M5";
   case PERIOD_M6:
      return "M6";
   case PERIOD_M10:
      return "M10";
   case PERIOD_M12:
      return "M12";
   case PERIOD_M15:
      return "M15";
   case PERIOD_M20:
      return "M20";
   case PERIOD_M30:
      return "M30";
   case PERIOD_H1:
      return "H1";
   case PERIOD_H2:
      return "H2";
   case PERIOD_H3:
      return "H3";
   case PERIOD_H4:
      return "H4";
   case PERIOD_H6:
      return "H6";
   case PERIOD_H8:
      return "H8";
   case PERIOD_H12:
      return "H12";
   case PERIOD_D1:
      return "D1";
   case PERIOD_W1:
      return "W1";
   case PERIOD_MN1:
      return "MN1";
   default:
      return "UNKNOWN";
   }
}

// counts the number of orders with a given magic number. currently not used.
int NumOpenOrdersWithMagic(int magic)
{
   int n = 0;
   for (int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if (!PositionSelectByTicket(ticket) || PositionGetInteger(POSITION_MAGIC) != magic)
         continue;
      n++;
   }
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if (!OrderSelect(ticket) || OrderGetInteger(ORDER_MAGIC) != magic)
         continue;
      n++;
   }
   return n;
}

void CheckOpenOrders()
{
   bool first = true;

   string text = "{\"orders\": {";

   for (int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if (!PositionSelectByTicket(ticket))
         continue;

      if (!first)
         text += ", ";

      // , \"commission\": %.2f
      text += StringFormat("\"%llu\": {\"magic\": %d, \"symbol\": \"%s\", \"lots\": %.2f, \"type\": \"%s\", \"open_price\": %.5f, \"open_time\": \"%s\", \"SL\": %.5f, \"TP\": %.5f, \"pnl\": %.2f, \"swap\": %.2f, \"comment\": \"%s\"}",
                           ticket,
                           PositionGetInteger(POSITION_MAGIC),
                           PositionGetString(POSITION_SYMBOL),
                           PositionGetDouble(POSITION_VOLUME),
                           OrderTypeToString((int)PositionGetInteger(POSITION_TYPE)),
                           PositionGetDouble(POSITION_PRICE_OPEN),
                           TimeToString(PositionGetInteger(POSITION_TIME), TIME_DATE | TIME_SECONDS),
                           PositionGetDouble(POSITION_SL),
                           PositionGetDouble(POSITION_TP),
                           PositionGetDouble(POSITION_PROFIT),
                           // PositionGetDouble(POSITION_COMMISSION),  // commission only exists for deals DEAL_COMMISSION.
                           PositionGetDouble(POSITION_SWAP),
                           PositionGetString(POSITION_COMMENT));

      first = false;
   }

   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if (!OrderSelect(ticket))
         continue;

      if (!first)
         text += ", ";

      text += StringFormat("\"%llu\": {\"magic\": %d, \"symbol\": \"%s\", \"lots\": %.2f, \"type\": \"%s\", \"open_price\": %.5f, \"open_time\": \"%s\", \"SL\": %.5f, \"TP\": %.5f, \"pnl\": %.2f, \"swap\": %.2f, \"comment\": \"%s\"}",
                           ticket,
                           OrderGetInteger(ORDER_MAGIC),
                           OrderGetString(ORDER_SYMBOL),
                           OrderGetDouble(ORDER_VOLUME_CURRENT),
                           OrderTypeToString((int)OrderGetInteger(ORDER_TYPE)),
                           OrderGetDouble(ORDER_PRICE_OPEN),
                           TimeToString(OrderGetInteger(ORDER_TIME_SETUP), TIME_DATE | TIME_SECONDS),
                           OrderGetDouble(ORDER_SL),
                           OrderGetDouble(ORDER_TP),
                           0, // there is no profit for orders, but we still want to keep the same format for all.
                           // OrderGetDouble(ORDER_COMMISSION),  // commission only exists for deals DEAL_COMMISSION.
                           0, // there is no swap for orders, but we still want to keep the same format for all.
                           OrderGetString(ORDER_COMMENT));

      first = false;
   }
   text += "}}";

   // if there are open positions, it will almost always be different because of open profit/loss.
   // update at least once per second in case there was a problem during writing.
   if (text == lastOrderText && GetTickCount() < lastUpdateOrdersMillis + 1000)
      return;
   if (WriteToFile(filePathOrders, text))
   {
      lastUpdateOrdersMillis = GetTickCount();
      lastOrderText = text;
   }
}

bool WriteToFile(string filePath, string text)
{
   int handle = FileOpen(filePath, FILE_WRITE | FILE_TXT | FILE_ANSI); // FILE_COMMON |
   if (handle == -1)
      return false;
   // even an empty string writes two bytes (line break).
   uint numBytesWritten = FileWrite(handle, text);
   FileClose(handle);
   return numBytesWritten > 0;
}

bool WriteToSocket(string text, ClientSocket *pClient, int maxChunkSize = 1024)
{
   uchar response[];
   int len = StringToCharArray(text, response) - 1;
   if (len < 0)
      return false;

   if (!pClient.Send(response, 0, ArraySize(response)))
      return false;

   return true;
}

void SendError(string errorType, string errorDescription, ClientSocket *pClient, bool useFile)
{
   Print("ERROR: " + errorType + " | " + errorDescription);
   // string message = StringFormat("{\"type\": \"ERROR\", \"time\": \"%s %s\", \"error_type\": \"%s\", \"description\": \"%s\"}",
   //                               TimeToString(TimeGMT(), TIME_DATE), TimeToString(TimeGMT(), TIME_SECONDS), errorType, errorDescription);

   CJAVal jsonData;
   jsonData["type"] = "ERROR";
   jsonData["time"] = StringFormat("%s %s", TimeToString(TimeGMT(), TIME_DATE), TimeToString(TimeGMT(), TIME_SECONDS));
   jsonData["error_type"] = errorType;
   jsonData["description"] = errorDescription;

   string jsonStr = jsonData.Serialize();

   SendMessage(jsonStr, pClient, useFile);
}

void SendInfo(string message, ClientSocket *pClient, bool useFile = false)
{
   Print("INFO: " + message);

   CJAVal dataObject;

   if (!dataObject.Deserialize(message))
   {
      Print("failed to deserialize INFO message");
      // Print("Reformating INFO message");
      // dataObject["message"] = message;

      // if (StringFind("{", message) == -1 && StringFind("}", message) == -1)
      // {
      //    Print("JSON markers not found, using file to send message");
      //    SendMessage(message, pClient, true);
      //    return;
      // }
   }

   CJAVal jsonData;
   jsonData["type"] = "INFO";
   jsonData["time"] = StringFormat("%s %s", TimeToString(TimeGMT(), TIME_DATE), TimeToString(TimeGMT(), TIME_SECONDS));
   jsonData["message"].Set(dataObject);

   string jsonStr = jsonData.Serialize();
   // message = StringFormat("{\"type\": \"INFO\", \"time\": \"%s %s\", \"message\": \"\\%s\\\"}",
   //                        TimeToString(TimeGMT(), TIME_DATE), TimeToString(TimeGMT(), TIME_SECONDS), message);
   SendMessage(jsonStr, pClient, useFile);
   return;
}

void SendMessage(string message, ClientSocket *pClient, bool useFile = false)
{
   for (int i = ArraySize(lastMessages) - 1; i >= 1; i--)
   {
      lastMessages[i] = lastMessages[i - 1];
   }

   lastMessages[0].millis = GetTickCount();
   // to make sure that every message has a unique number.
   if (lastMessages[0].millis <= lastMessageMillis)
      lastMessages[0].millis = lastMessageMillis + 1;
   lastMessageMillis = lastMessages[0].millis;
   lastMessages[0].message = message;

   bool first = true;
   string text = "{";
   for (int i = ArraySize(lastMessages) - 1; i >= 0; i--)
   {
      if (StringLen(lastMessages[i].message) == 0)
         continue;
      if (!first)
         text += ", ";
      text += "\"" + IntegerToString(lastMessages[i].millis) + "\": " + lastMessages[i].message;
      first = false;
   }
   text += "}";

   if (text == lastMessageText)
      return;

   if (useFile)
   {
      if (WriteToFile(filePathMessages, text))
      {
      }
   }
   else
   {
      if (WriteToSocket(text, pClient))
      {
      }
   }

   lastMessageText = text;
}

bool OpenChartIfNotOpen(string symbol, ENUM_TIMEFRAMES timeFrame)
{

   // long currentChartID = ChartID();
   long chartID = ChartFirst();

   for (int i = 0; i < maxNumberOfCharts; i++)
   {
      if (StringLen(ChartSymbol(chartID)) > 0)
      {
         if (ChartSymbol(chartID) == symbol && ChartPeriod(chartID) == timeFrame)
         {
            Print(StringFormat("Chart already open (%s, %s).", symbol, TimeFrameToString(timeFrame)));
            return false;
         }
      }
      chartID = ChartNext(chartID);
      if (chartID == -1)
         break;
   }
   // open chart if not yet opened.
   long id = ChartOpen(symbol, timeFrame);
   if (id > 0)
   {
      Print(StringFormat("Chart opened (%s, %s).", symbol, TimeFrameToString(timeFrame)));
      return true;
   }
   else
   {
      SendError("OPEN_CHART", StringFormat("Could not open chart (%s, %s).", symbol, TimeFrameToString(timeFrame)), NULL, false);
      return false;
   }
}

// use string so that we can have the same in MT5.
string OrderTypeToString(int orderType)
{
   if (orderType == POSITION_TYPE_BUY)
      return "buy";
   if (orderType == POSITION_TYPE_SELL)
      return "sell";
   if (orderType == ORDER_TYPE_BUY_LIMIT)
      return "buylimit";
   if (orderType == ORDER_TYPE_SELL_LIMIT)
      return "selllimit";
   if (orderType == ORDER_TYPE_BUY_STOP)
      return "buystop";
   if (orderType == ORDER_TYPE_SELL_STOP)
      return "sellstop";
   return "unknown";
}

int StringToOrderType(string orderTypeStr)
{
   if (orderTypeStr == "buy")
      return POSITION_TYPE_BUY;
   if (orderTypeStr == "sell")
      return POSITION_TYPE_SELL;
   if (orderTypeStr == "buylimit")
      return ORDER_TYPE_BUY_LIMIT;
   if (orderTypeStr == "selllimit")
      return ORDER_TYPE_SELL_LIMIT;
   if (orderTypeStr == "buystop")
      return ORDER_TYPE_BUY_STOP;
   if (orderTypeStr == "sellstop")
      return ORDER_TYPE_SELL_STOP;
   return -1;
}

string HistoryDealTypeToString(int dealType)
{
   if (dealType == DEAL_TYPE_BUY)
      return "buy";
   if (dealType == DEAL_TYPE_SELL)
      return "sell";
   if (dealType == DEAL_TYPE_BUY_CANCELED)
      return "buy canceled";
   if (dealType == DEAL_TYPE_SELL_CANCELED)
      return "sell canceled";
   if (dealType == DEAL_TYPE_BALANCE)
      return "balance";
   if (dealType == DEAL_TYPE_COMMISSION)
      return "commission";
   if (dealType == DEAL_TYPE_BONUS)
      return "bonus";
   if (dealType == DEAL_TYPE_CHARGE)
      return "charge";
   if (dealType == DEAL_TYPE_CREDIT)
      return "credit";
   if (dealType == DEAL_TYPE_CORRECTION)
      return "correction";
   if (dealType == DEAL_TYPE_INTEREST)
      return "interest";
   return "unknown";
}

string HistoryDealEntryTypeToString(int entryType)
{
   if (entryType == DEAL_ENTRY_IN)
      return "entry_in";
   if (entryType == DEAL_ENTRY_OUT)
      return "entry_out";
   if (entryType == DEAL_ENTRY_OUT_BY)
      return "entry_out_by";
   if (entryType == DEAL_ENTRY_INOUT)
      return "in_out";
   if (entryType == DEAL_ENTRY_STATE)
      return "state";
   return "unknown";
}

void ResetCommandIDs(ClientSocket *pClient, bool useFile = false)
{
   ArrayResize(commandIDs, 1000);                       // save the last 1000 command IDs.
   ArrayFill(commandIDs, 0, ArraySize(commandIDs), -1); // fill with -1 so that 0 will not be blocked.
   commandIDindex = 0;

   if (pClient != NULL)
   {
      string text = StringFormat("{\"message\": {\"reset_command_ids\": \"%s\"}", "true");
      text += "}";
      SendInfo(text, pClient, useFile);
   }
}

bool CommandIDfound(int id)
{
   for (int i = 0; i < ArraySize(commandIDs); i++)
      if (id == commandIDs[i])
         return true;
   return false;
}

void ResetFolder()
{
   // FolderDelete(folderName);  // does not always work.
   FolderCreate(folderName);
   FileDelete(filePathMarketData);
   FileDelete(filePathBarData);
   FileDelete(filePathHistoricData);
   FileDelete(filePathSymbolsData);
   FileDelete(filePathOrders);
   FileDelete(filePathMessages);
   for (int i = 0; i < maxCommandFiles; i++)
   {
      FileDelete(filePathCommandsPrefix + IntegerToString(i) + ".txt");
   }
}

// todo: add a list of error descriptions for MT5.
string ErrorDescription(int errorCode)
{
   return "ErrorCode: " + IntegerToString(errorCode);
}

MqlTick tick;
double bid(string symbol)
{
   if (SymbolInfoTick(symbol, tick))
      return tick.bid;
   return SymbolInfoDouble(symbol, SYMBOL_BID);
}

double ask(string symbol)
{
   if (SymbolInfoTick(symbol, tick))
      return tick.ask;
   return SymbolInfoDouble(symbol, SYMBOL_ASK);
}

void printArray(string &arr[])
{
   if (ArraySize(arr) == 0)
      Print("{}");
   string printStr = "{";
   int i;
   for (i = 0; i < ArraySize(arr); i++)
   {
      if (i == ArraySize(arr) - 1)
         printStr += arr[i];
      else
         printStr += arr[i] + ", ";
   }
   Print(printStr + "}");
}

//+------------------------------------------------------------------+
