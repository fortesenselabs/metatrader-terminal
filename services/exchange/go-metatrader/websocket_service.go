package metatrader

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// Endpoints
const (
	baseWsURL       = "ws://127.0.0.1:8000/ws"
	baseCombinedURL = "ws://127.0.0.1:8000/stream?streams="
)

var (
	// WebsocketTimeout is an interval for sending ping/pong messages if WebsocketKeepalive is enabled
	WebsocketTimeout = time.Second * 60
	// WebsocketKeepalive enables sending ping/pong messages to check the connection stability
	WebsocketKeepalive = false
)

// getWsEndpoint return the base endpoint of the WS according the UseTestnet flag
func getWsEndpoint() string {
	return baseWsURL
}

// getCombinedEndpoint return the base endpoint of the combined stream according the UseTestnet flag
func getCombinedEndpoint() string {
	return baseCombinedURL
}

// WsTickEvent define websocket tick event
type WsTickEvent struct {
	Event  string `json:"event"`
	Time   *int64 `json:"time"`
	Symbol string `json:"symbol"`
	Bid    *Bid   `json:"bid"`
	Ask    *Ask   `json:"ask"`
}

// WsKlineHandler handle websocket kline event
type WsKlineHandler func(event *WsKlineEvent)

// WsCombinedKlineServe is similar to WsKlineServe, but it handles multiple symbols with it interval
func WsCombinedKlineServe(symbols []string, subscribe bool, handler WsKlineHandler, errHandler ErrHandler) (doneC, stopC chan struct{}, err error) {
	endpoint := getCombinedEndpoint()
	for _, symbol := range symbols {
		endpoint += fmt.Sprintf("/tick/%s", symbol)
	}
	endpoint = endpoint[:len(endpoint)-1]
	var cfg *WsConfig

	if subscribe {
		cfg = newWsConfig(endpoint, SUBSCRIBE, "")
	} else {
		cfg = newWsConfig(endpoint, NONE, "")
	}
	wsHandler := func(message []byte) {
		j, err := newJSON(message)
		if err != nil {
			errHandler(err)
			return
		}

		stream := j.Get("stream").MustString()
		data := j.Get("data").MustMap()

		symbol := strings.Split(stream, "@")[0]

		jsonData, _ := json.Marshal(data)

		event := new(WsKlineEvent)
		err = json.Unmarshal(jsonData, event)
		if err != nil {
			errHandler(err)
			return
		}
		event.Symbol = strings.ToUpper(symbol)

		handler(event)
	}
	return wsServe(cfg, wsHandler, errHandler)
}

// WsKlineServe serve websocket kline handler with a symbol and interval like 15m, 30s
func WsKlineServe(symbol string, interval string, subscribe bool, handler WsKlineHandler, errHandler ErrHandler) (doneC, stopC chan struct{}, err error) {
	// Send a request to he subscribe endpoint, to subscribe to events to listen to
	//
	endpoint := fmt.Sprintf("%s/kline/%s/%s", getWsEndpoint(), symbol, interval)
	var cfg *WsConfig

	if subscribe {
		cfg = newWsConfig(endpoint, SUBSCRIBE)
	} else {
		cfg = newWsConfig(endpoint, NONE)
	}
	wsHandler := func(message []byte) {
		event := new(WsKlineEvent)
		err := json.Unmarshal(message, event)
		if err != nil {
			errHandler(err)
			return
		}
		handler(event)
	}
	return wsServe(cfg, wsHandler, errHandler)
}

// WsKlineEvent define websocket kline event
type WsKlineEvent struct {
	Event  string  `json:"event"`
	Time   int64   `json:"time"`
	Symbol string  `json:"symbol"`
	Kline  WsKline `json:"kline"`
}

// WsKline define websocket kline
type WsKline struct {
	StartTime int64  `json:"start_time"`
	EndTime   int64  `json:"end_time"`
	Symbol    string `json:"symbol"`
	Interval  string `json:"interval"`
	Open      string `json:"open"`
	Close     string `json:"close"`
	High      string `json:"high"`
	Low       string `json:"low"`
	Volume    string `json:"volume"`
	IsFinal   bool   `json:"is_final"`
}

// WsAggTradeHandler handle websocket aggregate trade event
type WsAggTradeHandler func(event *WsAggTradeEvent)

// WsAggTradeServe serve websocket aggregate handler with a symbol
func WsAggTradeServe(symbol string, subscribe bool, handler WsAggTradeHandler, errHandler ErrHandler) (doneC, stopC chan struct{}, err error) {
	endpoint := fmt.Sprintf("%s/%s@aggTrade", getWsEndpoint(), strings.ToLower(symbol))
	var cfg *WsConfig

	if subscribe {
		cfg = newWsConfig(endpoint, SUBSCRIBE, "")
	} else {
		cfg = newWsConfig(endpoint, NONE, "")
	}
	wsHandler := func(message []byte) {
		event := new(WsAggTradeEvent)
		err := json.Unmarshal(message, event)
		if err != nil {
			errHandler(err)
			return
		}
		handler(event)
	}
	return wsServe(cfg, wsHandler, errHandler)
}

// WsCombinedAggTradeServe is similar to WsAggTradeServe, but it handles multiple symbolx
func WsCombinedAggTradeServe(symbols []string, subscribe bool, handler WsAggTradeHandler, errHandler ErrHandler) (doneC, stopC chan struct{}, err error) {
	endpoint := getCombinedEndpoint()
	for s := range symbols {
		endpoint += fmt.Sprintf("%s@aggTrade", strings.ToLower(symbols[s])) + "/"
	}
	endpoint = endpoint[:len(endpoint)-1]
	var cfg *WsConfig

	if subscribe {
		cfg = newWsConfig(endpoint, SUBSCRIBE, "")
	} else {
		cfg = newWsConfig(endpoint, NONE, "")
	}
	wsHandler := func(message []byte) {
		j, err := newJSON(message)
		if err != nil {
			errHandler(err)
			return
		}

		stream := j.Get("stream").MustString()
		data := j.Get("data").MustMap()

		symbol := strings.Split(stream, "@")[0]

		jsonData, _ := json.Marshal(data)

		event := new(WsAggTradeEvent)
		err = json.Unmarshal(jsonData, event)
		if err != nil {
			errHandler(err)
			return
		}

		event.Symbol = strings.ToUpper(symbol)

		handler(event)
	}
	return wsServe(cfg, wsHandler, errHandler)
}

// WsAggTradeEvent define websocket aggregate trade event
type WsAggTradeEvent struct {
	Event                 string `json:"e"`
	Time                  int64  `json:"E"`
	Symbol                string `json:"s"`
	AggTradeID            int64  `json:"a"`
	Price                 string `json:"p"`
	Quantity              string `json:"q"`
	FirstBreakdownTradeID int64  `json:"f"`
	LastBreakdownTradeID  int64  `json:"l"`
	TradeTime             int64  `json:"T"`
	IsBuyerMaker          bool   `json:"m"`
	Placeholder           bool   `json:"M"` // add this field to avoid case insensitive unmarshaling
}

// WsTradeHandler handle websocket trade event
type WsTradeHandler func(event *WsTradeEvent)

// WsTradeServe serve websocket handler with a symbol
func WsTradeServe(symbol string, handler WsTradeHandler, subscribe bool, errHandler ErrHandler) (doneC, stopC chan struct{}, err error) {
	endpoint := fmt.Sprintf("%s/%s@trade", getWsEndpoint(), strings.ToLower(symbol))
	var cfg *WsConfig

	if subscribe {
		cfg = newWsConfig(endpoint, SUBSCRIBE, "")
	} else {
		cfg = newWsConfig(endpoint, NONE, "")
	}
	wsHandler := func(message []byte) {
		event := new(WsTradeEvent)
		err := json.Unmarshal(message, event)
		if err != nil {
			errHandler(err)
			return
		}
		handler(event)
	}
	return wsServe(cfg, wsHandler, errHandler)
}

// WsTradeEvent define websocket trade event
type WsTradeEvent struct {
	Event         string `json:"e"`
	Time          int64  `json:"E"`
	Symbol        string `json:"s"`
	TradeID       int64  `json:"t"`
	Price         string `json:"p"`
	Quantity      string `json:"q"`
	BuyerOrderID  int64  `json:"b"`
	SellerOrderID int64  `json:"a"`
	TradeTime     int64  `json:"T"`
	IsBuyerMaker  bool   `json:"m"`
	Placeholder   bool   `json:"M"` // add this field to avoid case insensitive unmarshaling
}

// WsUserDataEvent define user data event
type WsUserDataEvent struct {
	Time              int64             `json:"E"`
	TransactionTime   int64             `json:"T"`
	AccountUpdateTime int64             `json:"u"`
	AccountUpdate     []WsAccountUpdate `json:"B"`
	BalanceUpdate     WsBalanceUpdate
	OrderUpdate       WsOrderUpdate
}

// WsAccountUpdate define account update
type WsAccountUpdate struct {
	Asset  string `json:"a"`
	Free   string `json:"f"`
	Locked string `json:"l"`
}

type WsBalanceUpdate struct {
	Asset  string `json:"a"`
	Change string `json:"d"`
}

type WsOrderUpdate struct {
	Symbol            string          `json:"s"`
	ClientOrderId     string          `json:"c"`
	Side              string          `json:"S"`
	Type              string          `json:"o"`
	TimeInForce       TimeInForceType `json:"f"`
	Volume            string          `json:"q"`
	Price             string          `json:"p"`
	StopPrice         string          `json:"P"`
	IceBergVolume     string          `json:"F"`
	OrderListId       int64           `json:"g"` // for OCO
	OrigCustomOrderId string          `json:"C"` // customized order ID for the original order
	ExecutionType     string          `json:"x"` // execution type for this event NEW/TRADE...
	Status            string          `json:"X"` // order status
	RejectReason      string          `json:"r"`
	Id                int64           `json:"i"` // order id
	LatestVolume      string          `json:"l"` // quantity for the latest trade
	FilledVolume      string          `json:"z"`
	LatestPrice       string          `json:"L"` // price for the latest trade
	FeeAsset          string          `json:"N"`
	FeeCost           string          `json:"n"`
	TransactionTime   int64           `json:"T"`
	TradeId           int64           `json:"t"`
	IsInOrderBook     bool            `json:"w"` // is the order in the order book?
	IsMaker           bool            `json:"m"` // is this order maker?
	CreateTime        int64           `json:"O"`
	FilledQuoteVolume string          `json:"Z"` // the quote volume that already filled
	LatestQuoteVolume string          `json:"Y"` // the quote volume for the latest trade
	QuoteVolume       string          `json:"Q"`
}

// WsAllMarketsStatEvent define array of websocket market statistics events
type WsAllMarketsStatEvent []*WsMarketStatEvent

// WsMarketStatEvent define websocket market statistics event
type WsMarketStatEvent struct {
	Event              string `json:"e"`
	Time               int64  `json:"E"`
	Symbol             string `json:"s"`
	PriceChange        string `json:"p"`
	PriceChangePercent string `json:"P"`
	WeightedAvgPrice   string `json:"w"`
	PrevClosePrice     string `json:"x"`
	LastPrice          string `json:"c"`
	CloseQty           string `json:"Q"`
	BidPrice           string `json:"b"`
	BidQty             string `json:"B"`
	AskPrice           string `json:"a"`
	AskQty             string `json:"A"`
	OpenPrice          string `json:"o"`
	HighPrice          string `json:"h"`
	LowPrice           string `json:"l"`
	BaseVolume         string `json:"v"`
	QuoteVolume        string `json:"q"`
	OpenTime           int64  `json:"O"`
	CloseTime          int64  `json:"C"`
	FirstID            int64  `json:"F"`
	LastID             int64  `json:"L"`
	Count              int64  `json:"n"`
}

// WsAllMiniMarketsStatServeHandler handle websocket that push all mini-ticker market statistics for 24hr
type WsAllMiniMarketsStatServeHandler func(event WsAllMiniMarketsStatEvent)

// WsAllMiniMarketsStatEvent define array of websocket market mini-ticker statistics events
type WsAllMiniMarketsStatEvent []*WsMiniMarketsStatEvent

// WsMiniMarketsStatEvent define websocket market mini-ticker statistics event
type WsMiniMarketsStatEvent struct {
	Event       string `json:"e"`
	Time        int64  `json:"E"`
	Symbol      string `json:"s"`
	LastPrice   string `json:"c"`
	OpenPrice   string `json:"o"`
	HighPrice   string `json:"h"`
	LowPrice    string `json:"l"`
	BaseVolume  string `json:"v"`
	QuoteVolume string `json:"q"`
}
