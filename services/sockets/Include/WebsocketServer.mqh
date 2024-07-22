//+------------------------------------------------------------------+
//|                                              WebSocketServer.mqh |
//|                                 Copyright 2024, Fortesense Labs. |
//|                            https://www.github.com/FortesenseLabs |
//+------------------------------------------------------------------+
#include "ServerSocket.mqh"
#include <Frame.mqh>

//+------------------------------------------------------------------+
//| defines                                                          |
//+------------------------------------------------------------------+
#define PORT 7681
#define BUFFER_SIZE 1024
#define GUID "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
#define HEADER_EOL "\r\n"
#define HEADER_UPGRADE "Upgrade: websocket" + HEADER_EOL
#define HEADER_CONNECTION "Connection: Upgrade" + HEADER_EOL
#define HEADER_KEY "Sec-WebSocket-Key: "
#define HEADER_WS_VERSION "Sec-WebSocket-Version: 13" + HEADER_EOL + HEADER_EOL
#define HEADER_HTTP " HTTP/1.1"

enum ENUM_WEBSOCKET_STATE
{
   CLOSED = 0,
   CLOSING,
   CONNECTING,
   CONNECTED
};

//+------------------------------------------------------------------+
//| CWebSocketServer class                                           |
//+------------------------------------------------------------------+
class CWebSocketServer
{
private:
   CSocket m_serverSocket;
   ENUM_WEBSOCKET_STATE m_wsState;
   int m_port;
   int m_frames;
   int m_maxsendsize;
   uint m_total_len;
   int m_msgsize;

   uint m_timeout;
   bool m_running;

   // Helper functions
   bool performHandshake(CSocket &clientSocket);
   void handleClient(CSocket &clientSocket);

public:
   CWebSocketServer();
   ~CWebSocketServer();

   //---
   void SetMaxSendSize(int maxsend)
   {
      if (maxsend >= 0)
         m_maxsendsize = maxsend;
      else
         m_maxsendsize = 0;
   }
   bool Start(const string url, const uint port, const uint timeout, bool use_tls = false, bool enablelog = false);
   bool Close(const string msg = "");
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CWebSocketServer::CWebSocketServer() : m_running(false),
                                       m_timeout(0),
                                       m_frames(0),
                                       m_total_len(0)

{
   m_wsState = CLOSED;
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CWebSocketServer::~CWebSocketServer()
{
   Close();
}

//+------------------------------------------------------------------+
//| Start the server                                                 |
//+------------------------------------------------------------------+
bool CWebSocketServer::Start(const string address, const uint port, const uint timeout, bool use_tls = false, bool enablelog = false)
{
   if (m_running)
      return m_running;

   m_running = true;
   m_serverSocket.Open(address, m_port, m_timeout, false, true);

   while (m_running)
   {
      CSocket clientSocket;
      clientSocket = m_serverSocket.Accept();
      if (clientSocket.IsConnected())
      {
         if (performHandshake(clientSocket))
         {
            m_wsState = CONNECTED;
            handleClient(clientSocket);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Stop the server                                                  |
//+------------------------------------------------------------------+
bool CWebSocketServer::Close(const string close_reason = "")
{
   m_running = false;
   m_serverSocket.Close();
   m_wsState = CLOSED;
}

//+------------------------------------------------------------------+
//| Perform WebSocket handshake                                      |
//+------------------------------------------------------------------+
bool CWebSocketServer::performHandshake(CSocket &clientSocket)
{
   // Read request from client
   uchar request[BUFFER_SIZE];
   int request_len = clientSocket.Read(request, BUFFER_SIZE, m_timeout, false);
   if (request_len <= 0)
   {
      clientSocket.Close();
      return false;
   }

   // Process handshake
   string requestStr = CharArrayToString(request, 0, request_len, CP_UTF8);
   int keyPos = StringFind(requestStr, HEADER_KEY);
   if (keyPos < 0)
   {
      clientSocket.Close();
      return false;
   }
   Print(requestStr);

   // // Extract the key
   // string key = StringSubstr(requestStr, keyPos + StringLen(HEADER_KEY));
   // key = StringTrimRight(key);
   // key = StringTrimLeft(key);
   // int endPos = StringFind(key, HEADER_EOL);
   // key = StringSubstr(key, 0, endPos);

   // // Concatenate with GUID and encode
   // string acceptKey = key + GUID;
   // uchar sha1Key[], base64Key[];
   // CryptEncode(CRYPT_HASH_SHA1, StringToCharArray(acceptKey), sha1Key);
   // CryptEncode(CRYPT_BASE64, sha1Key, base64Key);

   // // Send handshake response
   // string response = "HTTP/1.1 101 Switching Protocols" + HEADER_EOL +
   //                   HEADER_UPGRADE + HEADER_CONNECTION +
   //                   "Sec-WebSocket-Accept: " + CharArrayToString(base64Key, 0, WHOLE_ARRAY, CP_UTF8) + HEADER_EOL + HEADER_EOL;
   // clientSocket.Send(StringToCharArray(response), StringLen(response));

   return true;
}

//+------------------------------------------------------------------+
//| Handle client connection                                         |
//+------------------------------------------------------------------+
void CWebSocketServer::handleClient(CSocket &clientSocket)
{
   uchar buffer[BUFFER_SIZE];
   int len;

   while ((len = clientSocket.Read(buffer, BUFFER_SIZE, m_timeout, false)) > 0)
   {
      // Handle incoming messages from the client
      // Implement message parsing and frame handling here

      // For example, send a pong frame in response to a ping
      if (buffer[0] == 0x89) // Ping frame
      {
         buffer[0] = 0x8A; // Change to pong frame
         clientSocket.Send(buffer, len);
      }
   }

   clientSocket.Close();
   m_wsState = CLOSED;
}
