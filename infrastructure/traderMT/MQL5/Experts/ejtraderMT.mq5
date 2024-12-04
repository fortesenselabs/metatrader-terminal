//+------------------------------------------------------------------+
//|                                                      ProjectName |
//|                                      Copyright 2020, CompanyName |
//|                                       http://www.companyname.net |
//+------------------------------------------------------------------+

#property copyright "Copyright 2022, ejtrader."
#property link "https://github.com/ejtraderLabs"
#property version "3.04"
#property description "Modified ejtraderMT to use sockets"
#property description "See github link for documentation"

#include <Trade/AccountInfo.mqh>
#include <Trade/DealInfo.mqh>
#include <Trade/Trade.mqh>
#include <ejtraderMT/Json.mqh>
#include <ejtraderMT/StringToEnumInt.mqh>
#include <ejtraderMT/ControlErrors.mqh>
#include <ejtraderMT/socket-library-mt4-mt5.mqh>

// Set ports and host for sockets
input string HOST = "*"; // "127.0.0.1";
input int SYS_PORT = 15555;
input int DATA_PORT = 15556;
input int LIVE_PORT = 15557;
input int STR_PORT = 15558;
input int CHART_INDICATOR_DATA_PORT = 15562;

// Server sockets
ServerSocket *sysSocket;
ServerSocket *dataSocket;
ServerSocket *liveSocket;
ServerSocket *streamSocket;
ServerSocket *chartIndicatorDataSocket; // Add chart indicator data socket

enum ServerSocketType
{
   SYS_SOCKET,
   DATA_SOCKET,
   LIVE_SOCKET,
   STREAM_SOCKET,
   CHART_INDICATOR_DATA_SOCKET
};

// Array of current clients
ClientSocket *sysClients[];
ClientSocket *dataClients[];
ClientSocket *liveClients[];
ClientSocket *streamClients[];
ClientSocket *chartIndicatorDataClients[]; // Add chart indicator data clients

// Load ejtraderMTincludes
// Required:
#include <ejtraderMT/HistoryInfo.mqh>
#include <ejtraderMT/Broker.mqh>
#include <ejtraderMT/Calendar.mqh>
// Optional:
// #include <ejtraderMT/StartIndicator.mqh>
// #include <ejtraderMT/ChartControl.mqh>

// Global variables
input bool debug = true;
input bool liveStream = false;
bool connectedFlag = true;
int deInitReason = -1;

// Variables for handling price data stream
struct SymbolSubscription
{
   string symbol;
   string chartTf;
   datetime lastBar;
};
SymbolSubscription symbolSubscriptions[];
int symbolSubscriptionCount = 0;

// Error handling
ControlErrors mControl;
datetime tm;

//+------------------------------------------------------------------+
//| Bind sockets to ports                                            |
//+------------------------------------------------------------------+
bool BindSockets()
{
   sysSocket = new ServerSocket(SYS_PORT, false);
   if (!sysSocket.Created())
   {
      Print("Failed to bind 'System' socket on port ", SYS_PORT);
      return false;
   }
   Print("Bound 'System' socket on port ", SYS_PORT);

   dataSocket = new ServerSocket(DATA_PORT, false);
   if (!dataSocket.Created())
   {
      Print("Failed to bind 'Data' socket on port ", DATA_PORT);
      return false;
   }
   Print("Bound 'Data' socket on port ", DATA_PORT);

   liveSocket = new ServerSocket(LIVE_PORT, false);
   if (!liveSocket.Created())
   {
      Print("Failed to bind 'Live' socket on port ", LIVE_PORT);
      return false;
   }
   Print("Bound 'Live' socket on port ", LIVE_PORT);

   streamSocket = new ServerSocket(STR_PORT, false);
   if (!streamSocket.Created())
   {
      Print("Failed to bind 'Streaming' socket on port ", STR_PORT);
      return false;
   }
   Print("Bound 'Streaming' socket on port ", STR_PORT);

   chartIndicatorDataSocket = new ServerSocket(CHART_INDICATOR_DATA_PORT, false); // Bind chart indicator data socket
   if (!chartIndicatorDataSocket.Created())
   {
      Print("Failed to bind 'Chart Indicator Data' socket on port ", CHART_INDICATOR_DATA_PORT);
      return false;
   }
   Print("Bound 'Chart Indicator Data' socket on port ", CHART_INDICATOR_DATA_PORT);

   return true;
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{

   // Setting up error reporting
   mControl.SetAlert(true);
   mControl.SetSound(false);
   mControl.SetWriteFlag(false);

   /* Binding sockets on init */
   // Skip reloading of the EA script when the reason to reload is a chart timeframe change
   if (deInitReason != REASON_CHARTCHANGE)
   {

      EventSetMillisecondTimer(1);

      int bindSocketsDelay = 65; // Seconds to wait if binding of sockets fails.
      int bindAttempts = 2;      // Number of binding attempts

      Print("Binding sockets...");

      for (int i = 0; i < bindAttempts; i++)
      {
         if (BindSockets())
            return (INIT_SUCCEEDED);
         else
         {
            Print("Binding sockets failed. Waiting ", bindSocketsDelay, " seconds to try again...");
            Sleep(bindSocketsDelay * 1000);
         }
      }

      Print("Binding of sockets failed permanently.");
      return (INIT_FAILED);
   }

   return (INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   /* Unbinding sockets on deinit */

   deInitReason = reason;

   // Skip reloading of the EA script when the reason to reload is a chart timeframe change
   if (reason != REASON_CHARTCHANGE)
   {
      Print(__FUNCTION__, " Deinitialization reason: ", getUninitReasonText(reason));

      Print("Unbinding 'System' socket on port ", SYS_PORT, "..");
      delete sysSocket;
      sysSocket = NULL;

      Print("Unbinding 'Data' socket on port ", DATA_PORT, "..");
      delete dataSocket;
      dataSocket = NULL;

      Print("Unbinding 'Live' socket on port ", LIVE_PORT, "..");
      delete liveSocket;
      liveSocket = NULL;

      Print("Unbinding 'Streaming' socket on port ", STR_PORT, "..");
      delete streamSocket;
      streamSocket = NULL;

      Print("Unbinding 'Chart Indicator Data' socket on port ", CHART_INDICATOR_DATA_PORT, "..");
      delete chartIndicatorDataSocket;
      chartIndicatorDataSocket = NULL;

      Print("Sockets terminated");

      // Reset
      ResetSubscriptionsAndIndicators();

      EventKillTimer();
   }
}

//+------------------------------------------------------------------+
//| Check if subscribed to symbol and timeframe combination          |
//+------------------------------------------------------------------+
bool HasChartSymbol(string symbol, string chartTF)
{
   for (int i = 0; i < ArraySize(symbolSubscriptions); i++)
   {
      if (symbolSubscriptions[i].symbol == symbol && symbolSubscriptions[i].chartTf == chartTF)
      {
         return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Stream live price data                                           |
//+------------------------------------------------------------------+
void StreamPriceData()
{
   // If liveStream == true, push last candle to liveSocket.

   if (liveStream)
   {
      CJAVal last;
      if (TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         connectedFlag = true;
         for (int i = 0; i < symbolSubscriptionCount; i++)
         {
            string symbol = symbolSubscriptions[i].symbol;
            string chartTF = symbolSubscriptions[i].chartTf;
            datetime lastBar = symbolSubscriptions[i].lastBar;
            CJAVal Data;
            ENUM_TIMEFRAMES period = GetTimeframe(chartTF);

            datetime thisBar = 0;
            float price;
            MqlTick tick;
            MqlRates rates[1];
            int spread[1];

            if (chartTF == "TICK")
            {
               if (SymbolInfoTick(symbol, tick) != true)
               { /*mControl.Check();*/
               }
               thisBar = (datetime)tick.time_msc;
            }
            else
            {
               if (CopyRates(symbol, period, 1, 1, rates) != 1)
               { /*mControl.Check();*/
               }
               if (CopySpread(symbol, period, 1, 1, spread) != 1)
               { /*mControl.Check();*/
                  ;
               }
               thisBar = (datetime)rates[0].time;
            }

            if (lastBar != thisBar)
            {
               if (lastBar != 0) // skip first price data after startup/reset
               {
                  if (chartTF == "TICK")
                  {
                     Data[0] = (long)tick.time_msc;
                     Data[1] = (double)tick.bid;
                     Data[2] = (double)tick.ask;
                  }
                  else
                  {
                     Data[0] = (long)rates[0].time;
                     Data[1] = (double)rates[0].open;
                     Data[2] = (double)rates[0].high;
                     Data[3] = (double)rates[0].low;
                     Data[4] = (double)rates[0].close;
                     Data[5] = (double)rates[0].tick_volume;
                  }
                  last["status"] = (string) "CONNECTED";
                  last["symbol"] = (string)symbol;
                  last["timeframe"] = (string)chartTF;
                  last["data"].Set(Data);

                  string t = last.Serialize();
                  if (debug)
                     Print(t);
                  InformClientSocket(LIVE_SOCKET, t);
                  symbolSubscriptions[i].lastBar = thisBar;
               }
               else
                  symbolSubscriptions[i].lastBar = thisBar;
            }
         }
      }
      else
      {
         // send disconnect message only once
         if (connectedFlag)
         {
            last["status"] = (string) "DISCONNECTED";
            string t = last.Serialize();
            if (debug)
               Print(t);
            InformClientSocket(LIVE_SOCKET, t);
            connectedFlag = false;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Expert timer function                                            |
//+------------------------------------------------------------------+
void OnTimer()
{
   tm = TimeTradeServer();

   // Stream live price data
   StreamPriceData();

   // Process incoming data from sockets
   ProcessServerSocket();
}

//+------------------------------------------------------------------+
//| Request handler                                                  |
//+------------------------------------------------------------------+
void RequestHandler(string &request)
{
   CJAVal incomingMessage;

   ResetLastError();
   // Get data from request
   string msg = request;

   if (debug)
      Print("Processing:" + msg);

   if (!incomingMessage.Deserialize(msg))
   {
      mControl.mSetUserError(65537, GetErrorID(65537));
      CheckError(__FUNCTION__);
   }

   // Send response to System socket that request was received
   // Some historical data requests can take a lot of time
   InformClientSocket(SYS_SOCKET, "OK");

   // Process action command
   string action = incomingMessage["action"].ToStr();

   if (action == "CONFIG")
      ScriptConfiguration(incomingMessage);
   else if (action == "ACCOUNT")
      GetAccountInfo();
   else if (action == "BALANCE")
      GetBalanceInfo();
   else if (action == "HISTORY")
      HistoryInfo(incomingMessage);
   else if (action == "TRADE")
      TradingModule(incomingMessage);
   else if (action == "POSITIONS")
      GetPositions(incomingMessage);
   else if (action == "ORDERS") 
      GetOrders(incomingMessage);
   else if (action == "RESET")
      ResetSubscriptionsAndIndicators();
   else if (action == "CALENDAR")
      GetEconomicCalendar(incomingMessage);
   else
#ifdef START_INDICATOR
       if (action == "INDICATOR")
      IndicatorControl(incomingMessage);
   else
#endif
#ifdef CHART_CONTROL
       if (action == "CHART")
      ChartControl(incomingMessage);
   else
#endif
   {
      mControl.mSetUserError(65538, GetErrorID(65538));
      CheckError(__FUNCTION__);
   }
}

//+------------------------------------------------------------------+
//| Reconfigure the script params                                    |
//+------------------------------------------------------------------+
void ScriptConfiguration(CJAVal &dataObject)
{
   string symbol = dataObject["symbol"].ToStr();
   string chartTF = dataObject["chartTF"].ToStr();

   ArrayResize(symbolSubscriptions, symbolSubscriptionCount + 1);
   symbolSubscriptions[symbolSubscriptionCount].symbol = symbol;
   symbolSubscriptions[symbolSubscriptionCount].chartTf = chartTF;
   // to initialize with value 0 skips the first price
   symbolSubscriptions[symbolSubscriptionCount].lastBar = 0;
   symbolSubscriptionCount++;

   mControl.mResetLastError();
   SymbolInfoString(symbol, SYMBOL_DESCRIPTION);
   if (!CheckError(__FUNCTION__))
      ActionDoneOrError(ERR_SUCCESS, __FUNCTION__, "ERR_SUCCESS");

   // Inform client about the new subscription
   CJAVal response;
   response["status"] = "SUBSCRIBED";
   response["symbol"] = symbol;
   response["timeframe"] = chartTF;
   string t = response.Serialize();
   if (debug)
      Print(t);
   InformClientSocket(SYS_SOCKET, t);
}

//+------------------------------------------------------------------+
//| Account information                                              |
//+------------------------------------------------------------------+
void GetAccountInfo()
{
   CJAVal info;

   info["error"] = false;
   info["broker"] = AccountInfoString(ACCOUNT_COMPANY);
   info["currency"] = AccountInfoString(ACCOUNT_CURRENCY);
   info["server"] = AccountInfoString(ACCOUNT_SERVER);
   info["trading_allowed"] = TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);
   info["bot_trading"] = AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
   info["balance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   info["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   info["margin"] = AccountInfoDouble(ACCOUNT_MARGIN);
   info["margin_free"] = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   info["margin_level"] = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
   info["time"] = string(tm); // sending time to ejtraderMT for localtime dataframe

   string t = info.Serialize();
   if (debug)
      Print(t);
   InformClientSocket(DATA_SOCKET, t);
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void GetEconomicCalendar(CJAVal &dataObject)
{
   string actionType = dataObject["actionType"].ToStr();

   string symbol = dataObject["symbol"].ToStr();
   if (actionType == "DATA")
   {
      CJAVal data, d;

      datetime fromDate = (datetime)dataObject["fromDate"].ToInt();
      datetime toDate = TimeCurrent();
      if (dataObject["toDate"].ToInt() != NULL)
         toDate = (datetime)dataObject["toDate"].ToInt();

      CALENDAR Calendar;
      string Currencies[2];
      int Size;

      if (symbol == NULL)
      {
         Size = Calendar.Set(NULL, CALENDAR_IMPORTANCE_NONE, TimeToString(fromDate, TIME_DATE), TimeToString(toDate, TIME_DATE));
      }
      else
      {
         Currencies[0] = ::SymbolInfoString(symbol, SYMBOL_CURRENCY_BASE);
         Currencies[1] = ::SymbolInfoString(symbol, SYMBOL_CURRENCY_PROFIT);
         // Tomou eventos para todas as moedas (NULL) começando com a menor (NENHUM).
         Size = Calendar.Set(Currencies, CALENDAR_IMPORTANCE_NONE, TimeToString(fromDate, TIME_DATE), TimeToString(toDate, TIME_DATE));
      }

      if (Size)
      {
         for (int i = 0; i < Size; i++)
         {
            string string_split = Calendar[i].ToString();

            string sep = "|"; // A separator as a character
            ushort u_sep;     // The code of the separator character
            string result[];
            u_sep = StringGetCharacter(sep, 0);
            //--- Split the string to substrings
            int k = StringSplit(string_split, u_sep, result);
            for (int b = 0; b < k; b++)
            {
               data[i][b] = result[b];
            }
         }
         d["data"].Set(data);
      }
      else
      {
         d["data"].Add(data);
      }
      Print("Finished preparing Calendar data");

      string t = d.Serialize();
      if (debug)
         Print(t);
      InformClientSocket(DATA_SOCKET, t);
   }
}

//+------------------------------------------------------------------+
//| Balance information                                              |
//+------------------------------------------------------------------+
void GetBalanceInfo()
{
   CJAVal info;
   info["balance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   info["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   info["margin"] = AccountInfoDouble(ACCOUNT_MARGIN);
   info["margin_free"] = AccountInfoDouble(ACCOUNT_MARGIN_FREE);

   string t = info.Serialize();
   if (debug)
      Print(t);
   InformClientSocket(DATA_SOCKET, t);
}

//+------------------------------------------------------------------+
//| Push historical data to socket                                   |
//+------------------------------------------------------------------+
bool PushHistoricalData(CJAVal &data)
{
   string t = data.Serialize();
   if (debug)
      Print(t);
   InformClientSocket(DATA_SOCKET, t);
   return true;
}

//+------------------------------------------------------------------+
//| Convert chart timeframe from string to enum                      |
//+------------------------------------------------------------------+
ENUM_TIMEFRAMES GetTimeframe(string chartTF)
{

   ENUM_TIMEFRAMES tf;
   tf = NULL;

   if (chartTF == "TICK")
      tf = PERIOD_CURRENT;

   if (chartTF == "M1")
      tf = PERIOD_M1;

   if (chartTF == "M5")
      tf = PERIOD_M5;

   if (chartTF == "M15")
      tf = PERIOD_M15;

   if (chartTF == "M30")
      tf = PERIOD_M30;

   if (chartTF == "H1")
      tf = PERIOD_H1;

   if (chartTF == "H2")
      tf = PERIOD_H2;

   if (chartTF == "H3")
      tf = PERIOD_H3;

   if (chartTF == "H4")
      tf = PERIOD_H4;

   if (chartTF == "H6")
      tf = PERIOD_H6;

   if (chartTF == "H8")
      tf = PERIOD_H8;

   if (chartTF == "H12")
      tf = PERIOD_H12;

   if (chartTF == "D1")
      tf = PERIOD_D1;

   if (chartTF == "W1")
      tf = PERIOD_W1;

   if (chartTF == "MN1")
      tf = PERIOD_MN1;

   // if tf == NULL an error will be raised in config function
   return (tf);
}

//+------------------------------------------------------------------+
//| Trade confirmation                                               |
//+------------------------------------------------------------------+
void OrderDoneOrError(bool error, string funcName, CTrade &trade)
{

   CJAVal conf;

   conf["error"] = (bool)error;
   conf["retcode"] = (int)trade.ResultRetcode();
   conf["description"] = (string)GetRetcodeID(trade.ResultRetcode());
   conf["order"] = (int)trade.ResultOrder();
   conf["volume"] = (double)trade.ResultVolume();
   conf["price"] = (double)trade.ResultPrice();
   conf["bid"] = (double)trade.ResultBid();
   conf["ask"] = (double)trade.ResultAsk();
   conf["function"] = (string)funcName;

   string t = conf.Serialize();
   if (debug)
      Print(t);
   InformClientSocket(DATA_SOCKET, t);
}

//+------------------------------------------------------------------+
//| Error reporting                                                  |
//+------------------------------------------------------------------+
bool CheckError(string funcName)
{
   int lastError = mControl.mGetLastError();
   if (lastError)
   {
      string desc = mControl.mGetDesc();
      if (debug)
         Print("Error handling source: ", funcName, " description: ", desc);
      Print("Error handling source: ", funcName, " description: ", desc);
      mControl.Check();
      ActionDoneOrError(lastError, funcName, desc);
      return true;
   }
   else
      return false;
}

//+------------------------------------------------------------------+
//| Action confirmation                                              |
//+------------------------------------------------------------------+
void ActionDoneOrError(int lastError, string funcName, string desc)
{
   CJAVal conf;

   conf["error"] = (bool)true;
   if (lastError == 0)
      conf["error"] = (bool)false;

   conf["lastError"] = (string)lastError;
   conf["description"] = (string)desc;
   conf["function"] = (string)funcName;

   string t = conf.Serialize();
   if (debug)
      Print(t);

   Print("ActionDoneOrError");

   InformClientSocket(SYS_SOCKET, t);
   InformClientSocket(DATA_SOCKET, t);
}

//+------------------------------------------------------------------+
//| Inform Client via socket                                         |
//+------------------------------------------------------------------+
void InformClientSocket(ServerSocketType socketType, string replyMessage)
{
   ClientSocket *clients[];
   int clientCount = 0;
   switch (socketType)
   {
   case SYS_SOCKET:
      ArrayCopy(clients, sysClients);
      break;
   case DATA_SOCKET:
      ArrayCopy(clients, dataClients);
      break;
   case LIVE_SOCKET:
      ArrayCopy(clients, liveClients);
      break;
   case STREAM_SOCKET:
      ArrayCopy(clients, streamClients);
      break;
   case CHART_INDICATOR_DATA_SOCKET:
      ArrayCopy(clients, chartIndicatorDataClients);
      break;
   default:
      return;
   }

   clientCount = ArraySize(clients);
   ArrayResize(clients, clientCount);

   if (socketType != CHART_INDICATOR_DATA_SOCKET)
   {
      for (int i = 0; i < clientCount; i++)
      {
         if (clients[i].IsSocketConnected())
         {
            clients[i].Send(replyMessage);
         }
      }
   }

#ifdef CHART_CONTROL

   // Publish indicator values for the JsonAPIIndicator indicator
   if (clientCount > 0)
   {
      double values[];

      // Ensure that all indicators have finished initialization
      for (int i = 0; i < ArraySize(chartWindowIndicators); i++)
      {
         // Wait for CopyBuffer to return. Ensures that indicator has been initialized
         CopyBuffer(chartWindowIndicators[i].indicatorHandle, 0, 0, 1, values);
      }

      // Send the message to each chart indicator data client
      for (int i = 0; i < clientCount; i++)
      {
         ClientSocket *pClient = clients[i];
         if (pClient.IsSocketConnected())
         {
            pClient.Send(values);
         }
      }
   }

   // Trigger the indicator JsonAPIIndicator to check for new Messages
   for (int i = 0; i < ArraySize(chartWindows); i++)
   {
      long chartId = chartWindows[i].id;
      EventChartCustom(chartId, 222, 222, 222.0);
   }
#endif

   mControl.mResetLastError();
   // mControl.Check();
}

//+------------------------------------------------------------------+
//| Process incoming data from sockets                               |
//+------------------------------------------------------------------+
void ProcessServerSocket()
{
   // Accept new system clients
   ClientSocket *pNewSysClient = NULL;
   do
   {
      pNewSysClient = sysSocket.Accept();
      if (pNewSysClient != NULL)
      {
         int sz = ArraySize(sysClients);
         ArrayResize(sysClients, sz + 1);
         sysClients[sz] = pNewSysClient;
         Print("System connection received!");
      }
   } while (pNewSysClient != NULL);

   // Handle incoming data from system clients
   int ctSysClients = ArraySize(sysClients);
   for (int i = ctSysClients - 1; i >= 0; i--)
   {
      ClientSocket *pClient = sysClients[i];
      string strCommand;
      do
      {
         strCommand = pClient.Receive();
         if (StringLen(strCommand) > 0)
         {
            Print("Command received: ", strCommand);
            // Handle command here
            RequestHandler(strCommand);
         }
      } while (StringLen(strCommand) > 0);
      if (!pClient.IsSocketConnected())
      {
         delete pClient;
         for (int j = i + 1; j < ctSysClients; j++)
         {
            sysClients[j - 1] = sysClients[j];
         }
         ctSysClients--;
         ArrayResize(sysClients, ctSysClients);
      }
   }

   // Accept new data clients
   ClientSocket *pNewDataClient = NULL;
   do
   {
      pNewDataClient = dataSocket.Accept();
      if (pNewDataClient != NULL)
      {
         int sz = ArraySize(dataClients);
         ArrayResize(dataClients, sz + 1);
         dataClients[sz] = pNewDataClient;
         Print("Data connection received!");
      }
   } while (pNewDataClient != NULL);

   // Handle incoming data from data clients
   int ctDataClients = ArraySize(dataClients);
   for (int i = ctDataClients - 1; i >= 0; i--)
   {
      ClientSocket *pClient = dataClients[i];
      string strCommand;
      do
      {
         strCommand = pClient.Receive();
         if (StringLen(strCommand) > 0)
         {
            Print("Data command received: ", strCommand);
            // Handle data command here
            RequestHandler(strCommand);
         }
      } while (StringLen(strCommand) > 0);
      if (!pClient.IsSocketConnected())
      {
         delete pClient;
         for (int j = i + 1; j < ctDataClients; j++)
         {
            dataClients[j - 1] = dataClients[j];
         }
         ctDataClients--;
         ArrayResize(dataClients, ctDataClients);
      }
   }

   // Accept new live clients
   ClientSocket *pNewLiveClient = NULL;
   do
   {
      pNewLiveClient = liveSocket.Accept();
      if (pNewLiveClient != NULL)
      {
         int sz = ArraySize(liveClients);
         ArrayResize(liveClients, sz + 1);
         liveClients[sz] = pNewLiveClient;
         Print("Live connection received!");
      }
   } while (pNewLiveClient != NULL);

   // Handle incoming data from live clients
   int ctLiveClients = ArraySize(liveClients);
   for (int i = ctLiveClients - 1; i >= 0; i--)
   {
      ClientSocket *pClient = liveClients[i];
      string strCommand;
      do
      {
         strCommand = pClient.Receive();
         if (StringLen(strCommand) > 0)
         {
            Print("Live command received: ", strCommand);
            // Handle live command here
            RequestHandler(strCommand);
         }
      } while (StringLen(strCommand) > 0);
      if (!pClient.IsSocketConnected())
      {
         delete pClient;
         for (int j = i + 1; j < ctLiveClients; j++)
         {
            liveClients[j - 1] = liveClients[j];
         }
         ctLiveClients--;
         ArrayResize(liveClients, ctLiveClients);
      }
   }

   // Accept new stream clients
   ClientSocket *pNewStreamClient = NULL;
   do
   {
      pNewStreamClient = streamSocket.Accept();
      if (pNewStreamClient != NULL)
      {
         int sz = ArraySize(streamClients);
         ArrayResize(streamClients, sz + 1);
         streamClients[sz] = pNewStreamClient;
         Print("Stream connection received!");
      }
   } while (pNewStreamClient != NULL);

   // Handle incoming data from stream clients
   int ctStreamClients = ArraySize(streamClients);
   for (int i = ctStreamClients - 1; i >= 0; i--)
   {
      ClientSocket *pClient = streamClients[i];
      string strCommand;
      do
      {
         strCommand = pClient.Receive();
         if (StringLen(strCommand) > 0)
         {
            Print("Stream command received: ", strCommand);
            // Handle stream command here
            RequestHandler(strCommand);
         }
      } while (StringLen(strCommand) > 0);
      if (!pClient.IsSocketConnected())
      {
         delete pClient;
         for (int j = i + 1; j < ctStreamClients; j++)
         {
            streamClients[j - 1] = streamClients[j];
         }
         ctStreamClients--;
         ArrayResize(streamClients, ctStreamClients);
      }
   }

#ifdef CHART_CONTROL

   // Accept new chart indicator data clients
   ClientSocket *pNewChartIndicatorDataClient = NULL;
   do
   {
      pNewChartIndicatorDataClient = chartIndicatorDataSocket.Accept();
      if (pNewChartIndicatorDataClient != NULL)
      {
         int sz = ArraySize(chartIndicatorDataClients);
         ArrayResize(chartIndicatorDataClients, sz + 1);
         chartIndicatorDataClients[sz] = pNewChartIndicatorDataClient;
         Print("Chart Indicator Data connection received!");
      }
   } while (pNewChartIndicatorDataClient != NULL);

   // Handle incoming data from chart indicator data clients
   int ctChartIndicatorDataClients = ArraySize(chartIndicatorDataClients);
   for (int i = ctChartIndicatorDataClients - 1; i >= 0; i--)
   {
      ClientSocket *pClient = chartIndicatorDataClients[i];
      string strCommand;
      do
      {
         strCommand = pClient.Receive();
         if (StringLen(strCommand) > 0)
         {
            Print("Chart Indicator Data command received: ", strCommand);
            // Handle chart indicator data command here
            RequestHandler(strCommand);
         }
      } while (StringLen(strCommand) > 0);
      if (!pClient.IsSocketConnected())
      {
         delete pClient;
         for (int j = i + 1; j < ctChartIndicatorDataClients; j++)
         {
            chartIndicatorDataClients[j - 1] = chartIndicatorDataClients[j];
         }
         ctChartIndicatorDataClients--;
         ArrayResize(chartIndicatorDataClients, ctChartIndicatorDataClients);
      }
   }

   informClientSocket(chartIndicatorDataSocket);

#endif
}

//+------------------------------------------------------------------+
//| Clear symbol subscriptions and indicators                        |
//+------------------------------------------------------------------+
void ResetSubscriptionsAndIndicators()
{

   ArrayFree(symbolSubscriptions);
   symbolSubscriptionCount = 0;

   bool error = false;
#ifdef START_INDICATOR
   for (int i = 0; i < indicatorCount; i++)
   {
      if (!IndicatorRelease(indicators[i].indicatorHandle))
         error = true;
   }
   ArrayFree(indicators);
   indicatorCount = 0;
#endif
#ifdef CHART_CONTROL
   for (int i = 0; i < chartWindowIndicatorCount; i++)
   {
      if (!IndicatorRelease(chartWindowIndicators[i].indicatorHandle))
         error = true;
   }
   ArrayFree(chartWindowIndicators);
   chartWindowIndicatorCount = 0;

   for (int i = 0; i < ArraySize(chartWindows); i++)
   {
      // TODO check if chart exists first: if(ChartGetInteger...
      // if(!IndicatorRelease(chartWindows[i].indicatorHandle)) error = true;
      if (chartWindows[i].id != 0)
         ChartClose(chartWindows[i].id);
   }
   ArrayFree(chartWindows);
#endif

   /*
   if(ArraySize(symbolSubscriptions)!=0 || ArraySize(indicators)!=0 || ArraySize(chartWindows)!=0 || error){
     // Set to only Alert. Fails too often, this happens when i.e. the backtrader script gets aborted unexpectedly
     mControl.Check();
     mControl.mSetUserError(65540, GetErrorID(65540));
     CheckError(__FUNCTION__);
   }
   */
   ActionDoneOrError(ERR_SUCCESS, __FUNCTION__, "ERR_SUCCESS");
}

//+------------------------------------------------------------------+
//| Get retcode message by retcode id                                |
//+------------------------------------------------------------------+
string GetRetcodeID(int retcode)
{

   switch (retcode)
   {
   case 10004:
      return ("TRADE_RETCODE_REQUOTE");
      break;
   case 10006:
      return ("TRADE_RETCODE_REJECT");
      break;
   case 10007:
      return ("TRADE_RETCODE_CANCEL");
      break;
   case 10008:
      return ("TRADE_RETCODE_PLACED");
      break;
   case 10009:
      return ("TRADE_RETCODE_DONE");
      break;
   case 10010:
      return ("TRADE_RETCODE_DONE_PARTIAL");
      break;
   case 10011:
      return ("TRADE_RETCODE_ERROR");
      break;
   case 10012:
      return ("TRADE_RETCODE_TIMEOUT");
      break;
   case 10013:
      return ("TRADE_RETCODE_INVALID");
      break;
   case 10014:
      return ("TRADE_RETCODE_INVALID_VOLUME");
      break;
   case 10015:
      return ("TRADE_RETCODE_INVALID_PRICE");
      break;
   case 10016:
      return ("TRADE_RETCODE_INVALID_STOPS");
      break;
   case 10017:
      return ("TRADE_RETCODE_TRADE_DISABLED");
      break;
   case 10018:
      return ("TRADE_RETCODE_MARKET_CLOSED");
      break;
   case 10019:
      return ("TRADE_RETCODE_NO_MONEY");
      break;
   case 10020:
      return ("TRADE_RETCODE_PRICE_CHANGED");
      break;
   case 10021:
      return ("TRADE_RETCODE_PRICE_OFF");
      break;
   case 10022:
      return ("TRADE_RETCODE_INVALID_EXPIRATION");
      break;
   case 10023:
      return ("TRADE_RETCODE_ORDER_CHANGED");
      break;
   case 10024:
      return ("TRADE_RETCODE_TOO_MANY_REQUESTS");
      break;
   case 10025:
      return ("TRADE_RETCODE_NO_CHANGES");
      break;
   case 10026:
      return ("TRADE_RETCODE_SERVER_DISABLES_AT");
      break;
   case 10027:
      return ("TRADE_RETCODE_CLIENT_DISABLES_AT");
      break;
   case 10028:
      return ("TRADE_RETCODE_LOCKED");
      break;
   case 10029:
      return ("TRADE_RETCODE_FROZEN");
      break;
   case 10030:
      return ("TRADE_RETCODE_INVALID_FILL");
      break;
   case 10031:
      return ("TRADE_RETCODE_CONNECTION");
      break;
   case 10032:
      return ("TRADE_RETCODE_ONLY_REAL");
      break;
   case 10033:
      return ("TRADE_RETCODE_LIMIT_ORDERS");
      break;
   case 10034:
      return ("TRADE_RETCODE_LIMIT_VOLUME");
      break;
   case 10035:
      return ("TRADE_RETCODE_INVALID_ORDER");
      break;
   case 10036:
      return ("TRADE_RETCODE_POSITION_CLOSED");
      break;
   case 10038:
      return ("TRADE_RETCODE_INVALID_CLOSE_VOLUME");
      break;
   case 10039:
      return ("TRADE_RETCODE_CLOSE_ORDER_EXIST");
      break;
   case 10040:
      return ("TRADE_RETCODE_LIMIT_POSITIONS");
      break;
   case 10041:
      return ("TRADE_RETCODE_REJECT_CANCEL");
      break;
   case 10042:
      return ("TRADE_RETCODE_LONG_ONLY");
      break;
   case 10043:
      return ("TRADE_RETCODE_SHORT_ONLY");
      break;
   case 10044:
      return ("TRADE_RETCODE_CLOSE_ONLY");
      break;

   default:
      return ("TRADE_RETCODE_UNKNOWN=" + IntegerToString(retcode));
      break;
   }
}

//+------------------------------------------------------------------+
//| Get error message by error id                                    |
//+------------------------------------------------------------------+
string GetErrorID(int error)
{

   switch (error)
   {
   // Custom errors
   case 65537:
      return ("ERR_DESERIALIZATION");
      break;
   case 65538:
      return ("ERR_WRONG_ACTION");
      break;
   case 65539:
      return ("ERR_WRONG_ACTION_TYPE");
      break;
   case 65540:
      return ("ERR_CLEAR_SUBSCRIPTIONS_FAILED");
      break;
   case 65541:
      return ("ERR_RETRIEVE_DATA_FAILED");
      break;
   case 65542:
      return ("ERR_CVS_FILE_CREATION_FAILED");
      break;

   default:
      return ("ERR_CODE_UNKNOWN=" + IntegerToString(error));
      break;
   }
}

//+------------------------------------------------------------------+
//| Return a textual description of the deinitialization reason code |
//+------------------------------------------------------------------+
string getUninitReasonText(int reasonCode)
{
   string text = "";
   //---
   switch (reasonCode)
   {
   case REASON_ACCOUNT:
      text = "Account was changed";
      break;
   case REASON_CHARTCHANGE:
      text = "Symbol or timeframe was changed";
      break;
   case REASON_CHARTCLOSE:
      text = "Chart was closed";
      break;
   case REASON_PARAMETERS:
      text = "Input-parameter was changed";
      break;
   case REASON_RECOMPILE:
      text = "Program " + __FILE__ + " was recompiled";
      break;
   case REASON_REMOVE:
      text = "Program " + __FILE__ + " was removed from chart";
      break;
   case REASON_TEMPLATE:
      text = "New template was applied to chart";
      break;
   default:
      text = "Another reason";
   }
   //---
   return text;
}
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
