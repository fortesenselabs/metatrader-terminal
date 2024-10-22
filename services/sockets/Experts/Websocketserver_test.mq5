//+------------------------------------------------------------------+
//|                                         Websocketclient_test.mq5 |
//|                        Copyright 2019, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2019, MetaQuotes Software Corp."
#property link "https://www.mql5.com"
#property version "1.00"
#property strict

#include <socket-library-mt4-mt5.mqh>
// #include <WebsocketServer.mqh>

input string Address = "0.0.0.0";
input int Port = 7681;
input bool ExtTLS = false;
input int MaxSize = 256;
input int Timeout = 5000;

// Timer interval in milliseconds
int timerInterval = 1 * 1000;

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

ClientSocket *glbConnection = NULL;

// CWebSocketServer wss;
//---
int sent = -1;
uint received = -1;
//---
// string subject,issuer,serial,thumbprint;
//---
// datetime expiration;
//---
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
  //--- create timer
  EventSetTimer(2);
  // //---
  // wss.SetMaxSendSize(MaxSize);
  // //---
  // // Start the server socket
  // if (wss.Start(Address, Port, Timeout, ExtTLS, true))
  // {
  //   // sent = wss.SendString(_msg);
  //   //--
  //   // Print("sent data is " + IntegerToString(sent));
  //   //---
  //   Print("Server Started....");
  //   return (INIT_SUCCEEDED);
  // }
  // //---
  // return (INIT_FAILED);

  // Create a socket if none already exists
  if (!glbConnection)
  {
    glbConnection = new ClientSocket(8000);
  }

  return (INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
  //--- destroy timer
  EventKillTimer();
  Print("Server closed\n");
  // wss.Close();
}
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
  //---

  if (glbConnection.IsSocketConnected())
  {
    // Socket is okay. Do some action such as sending or receiving
    Print("Hello");
  }

  // Socket may already have been dead, or now detected as failed
  // following the attempt above at sending or receiving.
  // If so, delete the socket and try a new one on the next call to OnTick()
  if (!glbConnection.IsSocketConnected())
  {
    delete glbConnection;
    glbConnection = NULL;
  }
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OnTimer()
{
}
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
