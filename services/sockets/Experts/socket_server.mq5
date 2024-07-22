// ###################################################################
// Based on the awesome example from: https://www.mql5.com/en/blogs/post/706665
// ###################################################################

#property strict

#include <socket-library-mt4-mt5.mqh>

// Server socket
ServerSocket *glbServerSocket;

// Array of current clients
ClientSocket *glbClients[];

// Watch for need to create timer;
bool glbCreatedTimer = false;

// --------------------------------------------------------------------
// Initialisation - set up server socket
// --------------------------------------------------------------------

void OnInit()
{
   // Create the server socket
   glbServerSocket = new ServerSocket(5000, false);
   if (glbServerSocket.Created())
   {
      Print("Server socket created");

      // Note: this can fail if MT4/5 starts up
      // with the EA already attached to a chart. Therefore,
      // we repeat in OnTick()
      glbCreatedTimer = EventSetMillisecondTimer(100);
   }
   else
   {
      Print("Server socket FAILED - is the port already in use?");
   }
}

// --------------------------------------------------------------------
// Termination - free server socket and any clients
// --------------------------------------------------------------------

void OnDeinit(const int reason)
{
   glbCreatedTimer = false;

   // Delete all clients currently connected
   for (int i = 0; i < ArraySize(glbClients); i++)
   {
      delete glbClients[i];
   }

   // Free the server socket
   delete glbServerSocket;
   Print("Server socket terminated");
}

// --------------------------------------------------------------------
// Timer - accept new connections, and handle incoming data from clients
// --------------------------------------------------------------------

void OnTimer()
{
   string recvMsg = "No data recived";
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

         Print("Connection recived!");
         pNewClient.Send("Connected to the MT5 Server!\r\n");
      }

   } while (pNewClient != NULL);

   // Read incoming data from all current clients, watching for
   // any which now appear to be dead
   int ctClients = ArraySize(glbClients);
   for (int i = ctClients - 1; i >= 0; i--)
   {
      ClientSocket *pClient = glbClients[i];
      // pNewClient.Send("Hellowwwwww\r\n");

      // Keep reading CRLF-terminated lines of input from the client
      // until we run out of data
      string strCommand;
      do
      {
         strCommand = pClient.Receive();

         if (strCommand != "")
            Print(strCommand);

         // Free the server socket
         if (strCommand == "q")
         {
            delete glbServerSocket;
            Print("Server socket terminated");
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

// Use OnTick() to watch for failure to create the timer in OnInit()
void OnTick()
{
   if (!glbCreatedTimer)
      glbCreatedTimer = EventSetMillisecondTimer(100);
}
