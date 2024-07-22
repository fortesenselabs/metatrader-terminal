//+------------------------------------------------------------------+
//|                                                        Frame.mqh |
//|                        Copyright 2019, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2019, MetaQuotes Software Corp."
#property link      "https://www.mql5.com"

//+------------------------------------------------------------------+
//| enums                                                            |
//+------------------------------------------------------------------+
enum ENUM_FRAME_TYPE     // type of websocket frames (ie, message types)
  {
   CONTINUATION_FRAME = 0x0,
   TEXT_FRAME = 0x1,
   BINARY_FRAME = 0x2,
   CLOSE_FRAME = 8,
   PING_FRAME = 9,
   PONG_FRAME = 0xa,
  };

//+------------------------------------------------------------------+
//| class frame                                                      |
//| represents a websocket message frame                             |
//+------------------------------------------------------------------+



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
class CFrame
  {
private:
   uchar             m_array[];
   uchar             m_isfinal;
   ENUM_FRAME_TYPE   m_msgtype;

   int               Resize(int size) {return(ArrayResize(m_array,size,size));}


public:
                     CFrame():m_isfinal(0),m_msgtype(0) {   }

                    ~CFrame() {      }
   int               Size(void) {return(ArraySize(m_array));}
   bool              Add(const uchar value);
   bool              Fill(const uchar &array[],const int src_start, const int count);
   void              Reset(void);
   uchar             operator[](int index);
   string            ToString(void);
   ENUM_FRAME_TYPE   MessageType(void)  { return(m_msgtype);}
   bool              IsFinal(void) { return(m_isfinal==1);}
   void              SetMessageType(ENUM_FRAME_TYPE mtype) { m_msgtype=mtype;}
   void              SetFinal(void)  { m_isfinal=1;}

  };
//+------------------------------------------------------------------+
//| Receiving an element by index                           |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
uchar CFrame::operator[](int index)
  {
   static uchar invalid_value;
//---
   int max=ArraySize(m_array)-1;
   if(index<0 || index>=ArraySize(m_array))
     {
      PrintFormat("%s index %d is not in range (0-%d)!",__FUNCTION__,index,max);
      return(invalid_value);
     }
//---
   return(m_array[index]);
  }
//+------------------------------------------------------------------+
//| Adding element                                 |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool CFrame::Fill(const uchar &array[],const int src_start,const int count)
  {
   int p_size=Size();
//---
   int size=Resize(p_size+count);
//---
   if(size>0)
      return(ArrayCopy(m_array,array,p_size,src_start,count)==count);
   else
      return(false);
//---
  }
//+------------------------------------------------------------------+
//| Assigning for the array                                 |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool CFrame::Add(const uchar value)
  {
   int size=Resize(Size()+1);
//---
   if(size>0)
      m_array[size-1]=value;
   else
      return(false);
//---
   return(true);
//---
  }
//+------------------------------------------------------------------+
//|  Reset                                 |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CFrame::Reset(void)
  {
   if(Size())
      ArrayFree(m_array);
//---

   m_isfinal=0;

   m_msgtype=0;

  }
//+------------------------------------------------------------------+
//|converting array to string                              |
//+------------------------------------------------------------------+
string CFrame::ToString(void)
  {
   if(Size())
      if(m_msgtype==CLOSE_FRAME)
         return(CharArrayToString(m_array,2,WHOLE_ARRAY,CP_UTF8));
      else
         return(CharArrayToString(m_array,0,WHOLE_ARRAY,CP_UTF8));
   else
      return(NULL);
  }
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
