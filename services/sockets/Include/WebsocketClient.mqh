//+------------------------------------------------------------------+
//|                                              WebSocketClient.mqh |
//|                        Copyright 2019, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2019, MetaQuotes Software Corp."
#property link      "https://www.mql5.com"
#include <Socket.mqh>
#include <Frame.mqh>


//+------------------------------------------------------------------+
//| defines                                                          |
//+------------------------------------------------------------------+
#define GUID                 "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
#define HEADER_EOL          "\r\n"
#define HEADER_GET          "GET /"
#define HEADER_HOST         "Host: "
#define HEADER_UPGRADE      "Upgrade: websocket"+HEADER_EOL
#define HEADER_CONNECTION   "Connection: Upgrade"+HEADER_EOL
#define HEADER_KEY          "Sec-WebSocket-Key: "
#define HEADER_WS_VERSION   "Sec-WebSocket-Version: 13"+HEADER_EOL+HEADER_EOL
#define HEADER_HTTP         " HTTP/1.1"



enum ENUM_CLOSE_CODE                 // possible reasons for disconnecting sent with a close frame
  {
   NORMAL_CLOSE = 1000,            // normal closure initiated by choice
   GOING_AWAY_CLOSE,               // close code for client navigating away from end point, used in browsers
   PROTOCOL_ERROR_CLOSE,           // close caused by some violation of a protocol, usually application defined
   FRAME_TYPE_ERROR_CLOSE,         // close caused by an endpoint receiving frame type that is not supportted or allowed
   UNDEFINED_CLOSE_1,              // close code is not defined by websocket protocol
   UNUSED_CLOSE_1,                 // unused
   UNUSED_CLOSE_2,                 // values
   ENCODING_TYPE_ERROR_CLOSE,      // close caused data in message is of wrong encoding type, usually referring to strings
   APP_POLICY_ERROR_CLOSE,         // close caused by violation of user policy
   MESSAGE_SIZE_ERROR_CLOSE,       // close caused by endpoint receiving message that is too large
   EXTENSION_ERROR_CLOSE,          // close caused by non compliance to or no support for specified extension of websocket protocol
   SERVER_SIDE_ERROR_CLOSE,        // close caused by some error that occurred on the server
   UNUSED_CLOSE_3 = 1015,          // unused
  };


enum ENUM_WEBSOCKET_STATE
  {
   CLOSED = 0,
   CLOSING,
   CONNECTING,
   CONNECTED
  };




//+------------------------------------------------------------------+
//| CWebSocketClient class                                           |
//+------------------------------------------------------------------+
class CWebSocketClient
  {
private:
   ENUM_WEBSOCKET_STATE  m_wsclient;

   CSocket           m_socket;

   int               m_frames;
   int               m_maxsendsize;
   uint              m_total_len;
   int               m_msgsize;

   uint              m_timeout;
   bool              m_sent;
   uchar             m_txbuf[];
   uchar             m_rxbuf[];
   uchar             m_send[];


   //---
   bool              upgrade(void);
   void              reset(void);
   bool              fillTxBuffer(ENUM_FRAME_TYPE ftype);
   int               send(ENUM_FRAME_TYPE frame_type);
   int               fillRxBuffer(void);
   bool              parse(CFrame& out[]);

public:
                     CWebSocketClient();
                    ~CWebSocketClient();
   //---
   ENUM_WEBSOCKET_STATE ClientState(void);
   void              SetMaxSendSize(int maxsend)   {if(maxsend>=0) m_maxsendsize=maxsend;  else m_maxsendsize=0; }
   bool              Connect(const string url,const uint port,const uint timeout,bool use_tls=false,bool enablelog=false);
   bool              Close(ENUM_CLOSE_CODE close_code=NORMAL_CLOSE,const string msg="");
   int               SendString(const string message);
   int               SendData(uchar& message_buffer[]);
   int               SendPong(const string msg);
   int               SendPing(const string msg);
   int               Readable(void)   {  return(fillRxBuffer());}
   uint              Read(CFrame& out[]);
  };
//+------------------------------------------------------------------+
//| constructor                                                      |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
CWebSocketClient::CWebSocketClient():m_wsclient(0),
   m_timeout(0),
   m_frames(0),
   m_total_len(0),
   m_msgsize(0),
   m_maxsendsize(0),
   m_sent(true)
  {

  }
//+------------------------------------------------------------------+
//| destructor                                                       |
//+------------------------------------------------------------------+
CWebSocketClient::~CWebSocketClient()
  {

  }
//+------------------------------------------------------------------+
//| ClientState()                                                    |
//+------------------------------------------------------------------+
ENUM_WEBSOCKET_STATE CWebSocketClient::ClientState(void)
  {
   if(m_socket.IsConnected())
      return(m_wsclient);
//---
   if(m_wsclient!=CLOSED)
     {
      m_socket.Close();
      m_wsclient=CLOSED;
     }
//---
   return(m_wsclient);
  }
//+------------------------------------------------------------------+
//| reset(): Used to reinitialize class properties                   |
//+------------------------------------------------------------------+
void CWebSocketClient::reset(void)
  {
//---
   m_wsclient=0;
   m_timeout=0;
   m_frames=0;
   m_total_len=0;
   m_msgsize=0;
   m_sent=true;
//---
   if(ArraySize(m_send)>0)
      ArrayFree(m_send);
   if(ArraySize(m_rxbuf)>0)
      ArrayFree(m_rxbuf);
   if(ArraySize(m_txbuf)>0)
      ArrayFree(m_txbuf);
//---
   return;
  }
//+------------------------------------------------------------------+
//|Upgrade(): requests server to accept Websocket protocol connection|
//+------------------------------------------------------------------+
bool CWebSocketClient::upgrade(void)
  {

   const uchar key[] =
     {
      'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
      'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
      'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
      'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
      'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
      'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
      'w', 'x', 'y', 'z', '0', '1', '2', '3',
      '4', '5', '6', '7', '8', '9', '+', '/'
     };

   char   rsp[];
   string result;
   uchar src[16]= {0};
   uchar sh1key[];
   string keystr="";
   uchar dst[];

   for(int i=0; i<16; i++)
     {
      src[i]=(uchar)(255*MathRand()/32767);
     }

   int res=CryptEncode(CRYPT_BASE64,src,key,dst);

   if(res<=0)
     {
      m_socket.Log("Crypt encode error",__LINE__,__FUNCTION__);
      return(false);
     }

   keystr=CharArrayToString(dst,0,WHOLE_ARRAY,CP_UTF8);
   if(keystr=="")
     {
      m_socket.Log("Char array to string error",__LINE__,__FUNCTION__);
      return(false);
     }

   bool upgraded=false;
   bool upgraderequest=false;
   string request;

   int ss=StringFind(m_socket.Address(),"/");
//---
   if(ss>=0)
      request=HEADER_GET+StringSubstr(m_socket.Address(),ss+1)+HEADER_HTTP+HEADER_EOL;
   else
      request=HEADER_GET+HEADER_HTTP+HEADER_EOL;
//---
   if(m_socket.Port()!=80 && m_socket.Port()!=443)
      request+=HEADER_HOST+m_socket.Address()+":"+IntegerToString(m_socket.Port())+HEADER_EOL;
   else
      request+=HEADER_HOST+m_socket.Address()+HEADER_EOL;
//---
   request+=HEADER_UPGRADE+HEADER_CONNECTION+HEADER_KEY+keystr+HEADER_EOL+HEADER_WS_VERSION;
//---
   m_socket.Log(request,__LINE__,__FUNCTION__);
//---
   char req[];
   int  len=StringToCharArray(request,req)-1;
   if(len<0)
     {
      m_socket.Log("string to char array error",__LINE__,__FUNCTION__);
      return(false);
     }
//---
   upgraderequest=(m_socket.Send(req,(uint)len)==len)?true:false;
//---
   if(!upgraderequest)
     {
      m_socket.Log("send error",__LINE__,__FUNCTION__);
      return(false);
     }
//---
   uint leng=0;
   uint   timeout_check=GetTickCount()+m_timeout;
//---
   do
     {
      leng=m_socket.Readable();
      if(leng)
        {
         int rsp_len;
         //--- various reading commands depending on whether the connection is secure or not
         rsp_len=m_socket.Read(rsp,leng,m_timeout);
         //--- analyze the response
         if(rsp_len>0)
           {
            result+=CharArrayToString(rsp,0,rsp_len,CP_UTF8);
            //--- print only the response header
            if(StringFind(result,(HEADER_EOL+HEADER_EOL),0)>=0)
               break;
           }
        }
     }
   while(GetTickCount()<timeout_check);
//---
   m_socket.Log(result,__LINE__,__FUNCTION__);
//---
   uchar _sh1[];
   uchar _dest[];
   uchar resp[];
   string sh1confirm="";

   int y=StringToCharArray(keystr+GUID,_sh1);
   if(y>0)
      ArrayRemove(_sh1,y-1,1);
   else
     {
      m_socket.Log("String to char array error",__LINE__,__FUNCTION__);
     }
//---
   res=0;
   res=CryptEncode(CRYPT_HASH_SHA1,_sh1,sh1key,_dest);
   if(res>0)
      if(CryptEncode(CRYPT_BASE64,_dest,key,resp)>0)
        {
         sh1confirm=CharArrayToString(resp,0,WHOLE_ARRAY,CP_UTF8);
         m_socket.Log(sh1confirm,__LINE__,__FUNCTION__);
        }
      else
        {
         m_socket.Log("Crypt encode error",__LINE__,__FUNCTION__);
        }
//---
   if(StringFind(result,"Sec-WebSocket-Accept: "+sh1confirm)>=0)
     {
      m_wsclient=CONNECTED;
      return(true);
     }
   else
      if(StringFind(result,"Sec-WebSocket-Accept")>=0)
        {
         m_wsclient=CONNECTED;
         return(true);
        }
//---
    return(false);     
  }
//+------------------------------------------------------------------+
//|prepareSendBuffer()prepares array buffer for socket dispatch      |
//+------------------------------------------------------------------+
bool CWebSocketClient::fillTxBuffer(ENUM_FRAME_TYPE ftype)
  {
   uchar header[];
   static int it;
   static int start;
   uchar masking_key[4]= {0};
   int maxsend=(m_maxsendsize<7)?m_msgsize:((m_maxsendsize<126)?m_maxsendsize-6:((m_maxsendsize<65536)?m_maxsendsize-8:m_maxsendsize-14));
//---
   for(int i=0; i<4; i++)
     {
      masking_key[i]=(uchar)(255*MathRand()/32767);
     }
//---
   m_socket.Log("[send]max size - "+IntegerToString(maxsend),__LINE__,__FUNCTION__);
   m_socket.Log("[send]should be max size - "+IntegerToString(m_maxsendsize),__LINE__,__FUNCTION__);
   int message_size=(((start+maxsend)-1)<=(m_msgsize-1))?maxsend:m_msgsize%maxsend;
   bool isfinal=((((start+maxsend)-1)==(m_msgsize-1)) || (message_size<maxsend) ||(message_size<=0))?true:false;
   bool isfirst=(start==0)?true:false;
//---
   m_socket.Log("[send]message size - "+IntegerToString(message_size),__LINE__,__FUNCTION__);
   if(isfirst)
      m_socket.Log("[send]first frame",__LINE__,__FUNCTION__);
   if(isfinal)
      m_socket.Log("[send]final frame",__LINE__,__FUNCTION__);
//---
   if(ArrayResize(header,2 + (message_size >= 126 ? 2 : 0) + (message_size >= 65536 ? 6 : 0) + (4))<0)
     {
      m_socket.Log("array resize error",__LINE__,__FUNCTION__);
      return(false);
     }
//header[0] = (isfinal)? (0x80 | 0x1) :( );
   switch(ftype)
     {
      case CLOSE_FRAME:
         header[0] = uchar(0x80|CLOSE_FRAME);
         m_socket.Log("[building]close frame",__LINE__,__FUNCTION__);
         break;
      case PING_FRAME:
         header[0] = uchar(0x80|PING_FRAME);
         m_socket.Log("[building]ping frame",__LINE__,__FUNCTION__);
         break;
      case PONG_FRAME:
         header[0] = uchar(0x80|PONG_FRAME);
         m_socket.Log("[building]pong frame",__LINE__,__FUNCTION__);
         break;
      default:
         header[0] = (isfinal)? 0x80:0x0;
         m_socket.Log("[building]"+EnumToString(ftype),__LINE__,__FUNCTION__);
         if(isfirst)
            header[0] |=uchar(ftype);
         break;

     }
//---
   if(message_size < 126)
     {
      header[1] = (uchar)(message_size & 0xff) |  0x80 ;
      header[2] = masking_key[0];
      header[3] = masking_key[1];
      header[4] = masking_key[2];
      header[5] = masking_key[3];
     }
   else
      if(message_size < 65536)
        {
         header[1] = 126 |  0x80 ;
         header[2] = (uchar)(message_size >> 8) & 0xff;
         header[3] = (uchar)(message_size >> 0) & 0xff;
         header[4] = masking_key[0];
         header[5] = masking_key[1];
         header[6] = masking_key[2];
         header[7] = masking_key[3];
        }
      else
        {
         header[1] = 127 | 0x80;
         header[2] = (uchar)(message_size >> 56) & 0xff;
         header[3] = (uchar)(message_size >> 48) & 0xff;
         header[4] = (uchar)(message_size >> 40) & 0xff;
         header[5] = (uchar)(message_size >> 32) & 0xff;
         header[6] = (uchar)(message_size >> 24) & 0xff;
         header[7] = (uchar)(message_size >> 16) & 0xff;
         header[8] = (uchar)(message_size >>  8) & 0xff;
         header[9] = (uchar)(message_size >>  0) & 0xff;

         header[10] = masking_key[0];
         header[11] = masking_key[1];
         header[12] = masking_key[2];
         header[13] = masking_key[3];

        }
//---
   if(ArrayResize(m_send,ArraySize(header),message_size)<0)
     {
      m_socket.Log("array resize error",__LINE__,__FUNCTION__);
      return(false);
     }
//---
   ArrayCopy(m_send,header,0,0);
//---
   if(message_size)
     {
      if(ArrayResize(m_send,ArraySize(header)+message_size)<0)
        {
         m_socket.Log("array resize error",__LINE__,__FUNCTION__);
         return(false);
        }
      //---
      ArrayCopy(m_send,m_txbuf,ArraySize(header),start,message_size);
      //---
      int bufsize=ArraySize(m_send);
      //---
      int message_offset = bufsize - message_size;
      //---
      for(int i = 0; i < message_size; i++)
        {
         m_send[message_offset+ i] ^= masking_key[i&0x3];
        }
     }
//---
   if(isfinal)
     {
      it=0;
      start=0;
      m_sent=true;
      ArrayFree(m_txbuf);
     }
   else
     {
      it++;
      start=it*maxsend;
     }
//---
   return(true);

  }
//+------------------------------------------------------------------+
//| receiver()fills rxbuf with raw message                           |
//+------------------------------------------------------------------+
int CWebSocketClient::fillRxBuffer(void)
  {
   uint leng=0;
   int rsp_len=-1;

//---
   uint timeout_check=GetTickCount()+m_timeout;
//---
   do
     {
      leng=m_socket.Readable();
      if(leng)
         rsp_len+=m_socket.Read(m_rxbuf,leng,m_timeout);
      leng=0;
     }
   while(GetTickCount()<timeout_check);
//---
   m_socket.Log("receive size "+IntegerToString(rsp_len),__LINE__,__FUNCTION__);
//---
   int m_rxsize=ArraySize(m_rxbuf);
//---
   if(m_rxsize<3)
      return(0);
//---
   switch((uint)m_rxbuf[1])
     {
      case 126:
         if(m_rxsize<4)
           {
            m_rxsize=0;
           }
         break;
      case 127:
         if(m_rxsize<10)
           {
            m_rxsize=0;
           }
         break;
      default:
         break;
     }
//---
   return(m_rxsize);
  }
//+------------------------------------------------------------------+
//|int  sendMessage() helper                                         |
//+------------------------------------------------------------------+
int  CWebSocketClient::send(ENUM_FRAME_TYPE frame_type)
  {
//---
   bool done=false;
   int bytes_sent=0,sum_sent=0;

   while(!m_sent)
     {
      done=fillTxBuffer(frame_type);
      if(done && m_socket.Writable())
        {
         bytes_sent=m_socket.Send(m_send,(uint)ArraySize(m_send));
         //---
         if(bytes_sent<0)
            break;
         else
           {
            sum_sent+=bytes_sent;
            ArrayFree(m_send);
           }
         //---
        }
      else
         break;
     }
//---
   if(ArraySize(m_send)>0)
      ArrayFree(m_send);
//---
   m_socket.Log("",__LINE__,__FUNCTION__);
//---
   return(sum_sent);
  }
//+------------------------------------------------------------------+
//| parse() cleans up raw data buffer discarding unnecessary elements|
//+------------------------------------------------------------------+
bool CWebSocketClient::parse(CFrame& out[])
  {
   uint i,data_len=0,frames=0;
   uint s=0;
   m_total_len=0;
//---
   int shift=0;
   for(i=0; i<(uint)ArraySize(m_rxbuf); i+=(data_len+shift))
     {
      ++frames;
      m_socket.Log("value of frame is "+IntegerToString(frames)+" Value of i is "+IntegerToString(i),__LINE__,__FUNCTION__);
      switch((uint)m_rxbuf[i+1])
        {
         case 126:
            data_len=((uint)m_rxbuf[i+2]<<8)+((uint)m_rxbuf[i+3]);
            shift=4;
            break;
         case 127:
            data_len=((uint)m_rxbuf[i+2]<<56)+((uint)m_rxbuf[i+3]<<48)+((uint)m_rxbuf[i+4]<<40)+
                     ((uint)m_rxbuf[i+5]<<32)+((uint)m_rxbuf[i+6]<<24)+((uint)m_rxbuf[i+7]<<16)+
                     ((uint)m_rxbuf[i+8]<<8)+((uint)m_rxbuf[i+9]);
            shift=10;
            break;
         default:
            data_len=(uint)m_rxbuf[i+1];
            shift=2;
            break;
        }
      m_total_len+=data_len;
      if(data_len>0)
        {
         if(ArraySize(out)<(int)frames)
           {
            if(ArrayResize(out,frames,1)<=0)
              {
               m_socket.Log("array resize error",__LINE__,__FUNCTION__);
               return(false);
              }
           }
         //---
         if(!out[frames-1].Fill(m_rxbuf,i+shift,data_len))
           {
            m_socket.Log("Error adding new frame",__LINE__,__FUNCTION__);
            return(false);
           }
         //---
         switch((uchar)m_rxbuf[i])
           {
            case 0x1:
               if(out[frames-1].MessageType()==0)
                  out[frames-1].SetMessageType(TEXT_FRAME);
               break;
            case 0x2:
               if(out[frames-1].MessageType()==0)
                  out[frames-1].SetMessageType(BINARY_FRAME);
               break;
            case 0x80:
            case 0x81:
               if(out[frames-1].MessageType()==0)
                  out[frames-1].SetMessageType(TEXT_FRAME);
            case 0x82:
               if(out[frames-1].MessageType()==0)
                  out[frames-1].SetMessageType(BINARY_FRAME);
               m_socket.Log("received last frame",__LINE__,__FUNCTION__);
               out[frames-1].SetFinal();
               break;
            case 0x88:
               m_socket.Log("received close frame",__LINE__,__FUNCTION__);
               out[frames-1].SetMessageType(CLOSE_FRAME);
               if(m_wsclient==CONNECTED)
                 {
                  ArrayCopy(m_txbuf,m_rxbuf,0,i+shift,data_len);
                  m_wsclient=CLOSING;
                 }
               break;
            case 0x89:
               m_socket.Log("received ping frame",__LINE__,__FUNCTION__);
               out[frames-1].SetMessageType(PING_FRAME);
               if(m_wsclient==CONNECTED)
                  ArrayCopy(m_txbuf,m_rxbuf,0,i+shift,data_len);
               break;
            case 0x8a:
               m_socket.Log("received pong frame",__LINE__,__FUNCTION__);
               out[frames-1].SetMessageType(PONG_FRAME);
               break;
            default:
               break;
           }
        }
     }
   //---  
   return(true);  
  }
//+------------------------------------------------------------------+
//| Connect(): Used to establish connection  to websocket server     |
//+------------------------------------------------------------------+
bool CWebSocketClient::Connect(const string url,const uint port,const uint timeout,bool use_tls=false,bool enablelog=false)
  {
   reset();
//---
   m_timeout=timeout;
//---
   if(!m_socket.Open(url,port,m_timeout,use_tls,enablelog))
     {
      m_socket.Log("Connect error",__LINE__,__FUNCTION__);
      return(false);
     }
   else
      m_wsclient=CONNECTING;
//---
   if(!upgrade())
    return(false);
//---
   m_socket.Log("ws client state "+EnumToString(m_wsclient),__LINE__,__FUNCTION__);
//---
   if(m_wsclient!=CONNECTED)
     {
      m_wsclient=CLOSED;
      m_socket.Close();
      reset();
     }
//---
   return(m_wsclient==CONNECTED);
  }
//+------------------------------------------------------------------+
//| Close() inform server client is disconnecting                    |
//+------------------------------------------------------------------+
bool CWebSocketClient::Close(ENUM_CLOSE_CODE close_code = NORMAL_CLOSE,const string close_reason = "")
  {
   ClientState();
//---
   if(m_wsclient==0)
     {
      m_socket.Log("Client Disconnected",__LINE__,__FUNCTION__);
      //---
      return(true);
     }
//---
   if(ArraySize(m_txbuf)<=0)
     {
      if(close_reason!="")
        {
         int len=StringToCharArray(close_reason,m_txbuf,2,120,CP_UTF8)-1;
         if(len<=0)
            return(false);
         else
            ArrayRemove(m_txbuf,len,1);
        }
      else
        {
         if(ArrayResize(m_txbuf,2)<=0)
           {
            m_socket.Log("array resize error",__LINE__,__FUNCTION__);
            return(false);
           }
        }
      m_txbuf[0]=(uchar)(close_code>>8) & 0xff;
      m_txbuf[1]=(uchar)(close_code>>0) & 0xff;
      //---
     }
//---
   m_msgsize=ArraySize(m_txbuf);
   m_sent=false;
//---
   send(CLOSE_FRAME);
//---
   m_socket.Close();
//---
   reset();
//---
   return(true);
//---
  }
//+------------------------------------------------------------------+
//| Send() sends text data to websocket server                       |
//+------------------------------------------------------------------+
int CWebSocketClient::SendString(const string message)
  {
   ClientState();
//---
   if(m_wsclient==CLOSED || m_wsclient==CLOSING)
     {
      m_socket.Log("invalid ws client handle",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   if(message=="")
     {
      m_socket.Log("no message specified",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   int len=StringToCharArray(message,m_txbuf,0,WHOLE_ARRAY,CP_UTF8)-1;
   if(len<=0)
     {
      m_socket.Log("string char array error",__LINE__,__FUNCTION__);
      return(0);
     }
   else
      ArrayRemove(m_txbuf,len,1);
//---
   m_msgsize=ArraySize(m_txbuf);
   m_sent=false;
//---
   return(send(TEXT_FRAME));
  }
//+------------------------------------------------------------------+
//| Send() sends user supplied array buffer                          |
//+------------------------------------------------------------------+
int CWebSocketClient::SendData(uchar& message_buffer[])
  {
   ClientState();
//---
   if(m_wsclient==CLOSED || m_wsclient==CLOSING)
     {
      m_socket.Log("invalid ws client handle",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   if(ArraySize(message_buffer)==0)
     {
      m_socket.Log("array is empty",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   if(ArrayResize(m_txbuf,ArraySize(message_buffer))<0)
     {
      m_socket.Log("array resize error",__LINE__,__FUNCTION__);
      return(0);
     }
   else
      ArrayCopy(m_txbuf,message_buffer);
//---
   m_msgsize=ArraySize(m_txbuf);
   m_sent=false;
//---
   return(send(BINARY_FRAME));
  }
//+------------------------------------------------------------------+
//| SendPong() sends pong response upon receiving ping               |
//+------------------------------------------------------------------+
int CWebSocketClient::SendPong(const string msg="")
  {
   ClientState();
//---
   if(m_wsclient==CLOSED || m_wsclient==CLOSING)
     {
      m_socket.Log("invalid ws client handle",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   if(ArraySize(m_txbuf)<=0)
     {
      if(msg!="")
        {
         int len=StringToCharArray(msg,m_txbuf,0,122,CP_UTF8)-1;
         if(len<=0)
           {
            m_socket.Log("string to char array error",__LINE__,__FUNCTION__);
            return(0);
           }
         else
            ArrayRemove(m_txbuf,len,1);
        }
     }
//---
   m_msgsize=ArraySize(m_txbuf);
   m_sent=false;
//---
   return(send(PONG_FRAME));
  }
//+------------------------------------------------------------------+
//| SendPing() ping  the server                                      |
//+------------------------------------------------------------------+
int CWebSocketClient::SendPing(const string msg="")
  {
   ClientState();
//---
   if(m_wsclient==CLOSED || m_wsclient==CLOSING)
     {
      m_socket.Log("invalid ws client handle",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   if(ArraySize(m_txbuf)<=0)
     {
      if(msg!="")
        {
         int len=StringToCharArray(msg,m_txbuf,0,122,CP_UTF8)-1;
         if(len<=0)
           {
            m_socket.Log("string to char array error",__LINE__,__FUNCTION__);
            return(0);
           }
         else
            ArrayRemove(m_txbuf,len,1);
        }
     }
//---
   m_msgsize=ArraySize(m_txbuf);
   m_sent=false;
//---
   return(send(PING_FRAME));
  }
//+------------------------------------------------------------------+
//|Getmessage() return message frame(s) as uchar array               |
//+------------------------------------------------------------------+
uint CWebSocketClient::Read(CFrame& out[])
  {
   ClientState();
//---
   if(m_wsclient==0)
     {
      m_socket.Log("invalid ws client handle",__LINE__,__FUNCTION__);
      return(0);
     }
//---
   int rx_size=ArraySize(m_rxbuf);
//---
   if(rx_size<=0)
     {
      m_socket.Log("receive buffer is empty, Make sure to call Readable first",__LINE__,__FUNCTION__);
      return(0);
     }
//---clean up rxbuf
   if(!parse(out))
    {
     ArrayFree(m_rxbuf);
     return(0);
    } 
//---
   ArrayFree(m_rxbuf);
//---
   return(m_total_len);
  }

/////////////////////////////////////////////////////////////////////////////////////////////////////////
