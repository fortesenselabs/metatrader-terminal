//+------------------------------------------------------------------+
//|                                                       Socket.mqh |
//|                        Copyright 2019, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2019, MetaQuotes Software Corp."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict


//+------------------------------------------------------------------+
//| structs                                                          |
//+------------------------------------------------------------------+
struct CERT
  {
   string            cert_subject;
   string            cert_issuer;
   string            cert_serial;
   string            cert_thumbprint;
   datetime          cert_expiry;
  };


//+------------------------------------------------------------------+
//| Class CSocket.                                                   |
//| Purpose: Base class of socket operations.                        |
//|                                                                  |
//+------------------------------------------------------------------+


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
class CSocket
  {
private:
   static int        m_usedsockets;   // tracks number of sockets in use in single program
   bool              m_log;           // logging state
   bool              m_usetls;        //  tls state
   uint              m_tx_timeout;    //  send system socket timeout in milliseconds
   uint              m_rx_timeout;    //  receive system socket timeout in milliseconds
   int               m_socket;        //  socket handle
   string            m_address;       //  server address
   uint              m_port;          //  port


   CERT              m_cert;          //  Server certificate info

public:
                     CSocket();
                    ~CSocket();
   //--- methods to get private properties
   int               SocketID(void)           const { return(m_socket); }
   string            Address(void)            const { return(m_address);   }
   uint              Port(void)               const { return(m_port);  }
   bool              IsSecure(void)           const { return(m_usetls); }
   uint              RxTimeout(void)          const { return(m_rx_timeout); }
   uint              TxTimeout(void)          const { return(m_tx_timeout); }
   bool              ServerCertificate(CERT& certificate);


   //--- methods to set private properties
   bool              SetTimeouts(uint tx_timeout, uint rx_timeout);
   //--- general methods for working sockets
   void              Log(const string custom_message,const int line,const string func);
   static uint       SocketsInUse(void)        {   return(m_usedsockets);  }
   bool              Open(const string server,uint port,uint timeout,bool use_tls=false,bool enablelog=false);
   bool              Close(void);
   uint              Readable(void);
   bool              Writable(void);
   bool              IsConnected(void);
   int               Read(uchar& out[],uint out_len,uint ms_timeout,bool read_available);
   int               Send(uchar& in[],uint in_len);

  };

int CSocket::m_usedsockets=0;
//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CSocket::CSocket():m_socket(INVALID_HANDLE),
   m_address(""),
   m_port(0),
   m_usetls(false),
   m_log(false),
   m_rx_timeout(150),
   m_tx_timeout(150)
  {
   ZeroMemory(m_cert);
  }
//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CSocket::~CSocket()
  {
//--- check handle
   if(m_socket!=INVALID_HANDLE)
      Close();
  }
//+------------------------------------------------------------------+
//| set system socket timeouts                                       |
//+------------------------------------------------------------------+
bool CSocket::SetTimeouts(uint tx_timeout,uint rx_timeout)
  {
   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(false);
     }

   if(SocketTimeouts(m_socket,tx_timeout,rx_timeout))
     {
      m_tx_timeout=tx_timeout;
      m_rx_timeout=rx_timeout;
      Log("Socket Timeouts set",__LINE__,__FUNCTION__);
      return(true);
     }

   return(false);
  }

//+------------------------------------------------------------------+
//| certificate                                                      |
//+------------------------------------------------------------------+
bool CSocket::ServerCertificate(CERT& certificate)
  {

   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(false);
     }

   if(SocketTlsCertificate(m_socket,m_cert.cert_subject,m_cert.cert_issuer,m_cert.cert_serial,m_cert.cert_thumbprint,m_cert.cert_expiry))
     {
      certificate=m_cert;
      Log("Server certificate retrieved",__LINE__,__FUNCTION__);
      return(true);
     }

   return(false);

  }
//+------------------------------------------------------------------+
//|connect()                                                         |
//+------------------------------------------------------------------+
bool CSocket::Open(const string server,uint port,uint timeout,bool use_tls=false,bool enablelog=false)
  {
   if(m_socket!=INVALID_HANDLE)
      Close();

   if(m_usedsockets>=128)
     {
      Log("Too many sockets open",__LINE__,__FUNCTION__);
      return(false);
     }

   m_usetls=use_tls;

   m_log=enablelog;

   m_socket=SocketCreate();
   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(false);
     }
   ++m_usedsockets;
   m_address=server;

   if(port==0)
     {
      if(m_usetls)
         m_port=443;
      else
         m_port=80;
     }
   else
      m_port=port;
//---
   if(!m_usetls && m_port==443)
      m_usetls=true;
//---
   Log("Connecting to "+m_address,__LINE__,__FUNCTION__);
//---
   if(m_usetls)
     {
      if(m_port!=443)
        {
         if(SocketConnect(m_socket,server,port,timeout))
            return(SocketTlsHandshake(m_socket,server));
        }
      else
        {
         return(SocketConnect(m_socket,server,port,timeout));
        }
     }

   return(SocketConnect(m_socket,server,port,timeout));
  }
//+------------------------------------------------------------------+
//|close()                                                           |
//+------------------------------------------------------------------+
bool CSocket::Close(void)
  {
//---
   if(m_socket==INVALID_HANDLE)
     {
      Log("Socket Disconnected",__LINE__,__FUNCTION__);
      return(true);
     }
//---
   if(SocketClose(m_socket))
     {
      m_socket=INVALID_HANDLE;
      --m_usedsockets;
      Log("Socket Disconnected from "+m_address,__LINE__,__FUNCTION__);
      m_address="";
      ZeroMemory(m_cert);
      return(true);
     }
//---
   Log("",__LINE__,__FUNCTION__);
   return(false);
  }
//+------------------------------------------------------------------+
//|readable()                                                        |
//+------------------------------------------------------------------+
uint CSocket::Readable(void)
  {
   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   Log("Is Socket Readable ",__LINE__,__FUNCTION__);
//---
   return(SocketIsReadable(m_socket));
  }
//+------------------------------------------------------------------+
//|writable()                                                        |
//+------------------------------------------------------------------+
bool CSocket::Writable(void)
  {
   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(false);
     }
//---
   Log("Is Socket Writable ",__LINE__,__FUNCTION__);
//---
   return(SocketIsWritable(m_socket));
  }
//+------------------------------------------------------------------+
//|isconnected()                                                     |
//+------------------------------------------------------------------+
bool CSocket::IsConnected(void)
  {
   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(false);
     }
//---
   Log("Is Socket Connected ",__LINE__,__FUNCTION__);
//---
   return(SocketIsConnected(m_socket));
  }
//+------------------------------------------------------------------+
//|read()                                                            |
//+------------------------------------------------------------------+
int CSocket::Read(uchar& out[],uint out_len,uint ms_timeout,bool read_available=false)
  {
   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(-1);
     }
//---
   Log("Reading from "+m_address,__LINE__,__FUNCTION__);

   if(m_usetls)
     {
      if(read_available)
         return(SocketTlsReadAvailable(m_socket,out,out_len));
      else
         return(SocketTlsRead(m_socket,out,out_len));
     }
   else
      return(SocketRead(m_socket,out,out_len,ms_timeout));

   return(-1);
  }
//+------------------------------------------------------------------+
//|send()                                                            |
//+------------------------------------------------------------------+
int CSocket::Send(uchar& in[],uint in_len)
  {
   if(m_socket==INVALID_HANDLE)
     {
      Log("Invalid socket",__LINE__,__FUNCTION__);
      return(-1);
     }
//---
   Log("Sending to "+m_address,__LINE__,__FUNCTION__);
//---
   if(m_usetls)
      return(SocketTlsSend(m_socket,in,in_len));
   else
      return(SocketSend(m_socket,in,in_len));
//---
   return(-1);
  }
//+------------------------------------------------------------------+
//|log()                                                             |
//+------------------------------------------------------------------+
void CSocket::Log(const string custom_message,const int line,const string func)
  {
   if(m_log)
     {
      //---
      int eid=GetLastError();
      //---
      if(eid!=0)
        {
         PrintFormat("[MQL error ID: %d][%s][Line: %d][Function: %s]",eid,custom_message,line,func);
         ResetLastError();
         return;
        }
      if(custom_message!="")
         PrintFormat("[%s][Line: %d][Function: %s]",custom_message,line,func);
     }
//---
  }
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
