package api

import (
	"sync"
	"time"
)

type AccountInfo struct {
	Balance         float64 `json:"balance"`
	Equity          float64 `json:"equity"`
	Margin          float64 `json:"margin"`
	FreeMargin      float64 `json:"free_margin"`
	MarginLevel     float64 `json:"margin_level"`
	AccountCurrency string  `json:"account_currency"`
}

type MarketData struct {
	Symbol string  `json:"symbol"`
	Bid    float64 `json:"bid"`
	Ask    float64 `json:"ask"`
}

type Order struct {
	Ticket     int     `json:"ticket"`
	Symbol     string  `json:"symbol"`
	OrderType  string  `json:"order_type"`
	Lots       float64 `json:"lots"`
	OpenPrice  float64 `json:"open_price"`
	StopLoss   float64 `json:"stop_loss"`
	TakeProfit float64 `json:"take_profit"`
	OpenTime   string  `json:"open_time"`
	ClosePrice float64 `json:"close_price"`
	CloseTime  string  `json:"close_time"`
	Comment    string  `json:"comment"`
	Profit     float64 `json:"profit"`
}

type BarData struct {
	Symbol    string  `json:"symbol"`
	Time      string  `json:"time"`
	Open      float64 `json:"open"`
	High      float64 `json:"high"`
	Low       float64 `json:"low"`
	Close     float64 `json:"close"`
	Volume    int     `json:"volume"`
	TimeFrame string  `json:"time_frame"`
}

type HistoricData struct {
	Symbol    string    `json:"symbol"`
	TimeFrame string    `json:"time_frame"`
	Data      []BarData `json:"data"`
}

type HistoricTrades struct {
	Symbol string  `json:"symbol"`
	Trades []Order `json:"trades"`
}

type EventHandler interface {
	OnOrderEvent()
	OnMessage(message string)
	OnTick(symbol string, bid float64, ask float64)
	OnBarData(symbol string, data BarData)
	OnHistoricData(symbol string, data HistoricData)
	OnHistoricTrades(symbol string, trades HistoricTrades)
}

type DWXClient struct {
	EventHandler           EventHandler
	SleepDelay             time.Duration
	MaxRetryCommandSeconds int
	LoadOrdersFromFile     bool
	Verbose                bool
	CommandID              int
	MetaTraderDirPath      string
	Paths                  Paths
	NumCommandFiles        int
	LastMessagesMillis     int64
	LastOpenOrdersStr      string
	LastMessagesStr        string
	LastMarketDataStr      string
	LastBarDataStr         string
	LastHistoricDataStr    string
	LastHistoricTradesStr  string
	LastMarketData         map[string]MarketData
	LastBarData            map[string]BarData
	OpenOrders             map[string]Order
	AccountInfo            AccountInfo
	MarketData             map[string]MarketData
	BarData                map[string]BarData
	HistoricData           map[string]HistoricData
	HistoricTrades         map[string]HistoricTrades
	Active                 bool
	Start                  bool
	Lock                   sync.Mutex
}

type Paths struct {
	Orders         string
	Messages       string
	MarketData     string
	BarData        string
	HistoricData   string
	HistoricTrades string
	OrdersStored   string
	MessagesStored string
	CommandsPrefix string
}

// func (client *DWXClient) readFile(filePath string) string {
// 	for i := 0; i < 10; i++ {
// 		data, err := os.ReadFile(filePath)
// 		if err == nil {
// 			return string(data)
// 		}
// 		time.Sleep(client.sleepDelay)
// 	}
// 	return ""
// }

// func (client *DWXClient) removeFile(filePath string) {
// 	for i := 0; i < 10; i++ {
// 		err := os.Remove(filePath)
// 		if err == nil {
// 			break
// 		}
// 		time.Sleep(client.sleepDelay)
// 	}
// }

// func (client *DWXClient) checkOrders() {
// 	for client.active {
// 		time.Sleep(client.sleepDelay)
// 		if !client.start {
// 			continue
// 		}

// 		text := client.tryReadFile(client.paths.Orders)
// 		if len(text) == 0 || text == client.lastOpenOrdersStr {
// 			continue
// 		}

// 		client.lastOrderStr = text
// 		var data map[string]Order
// 		json.Unmarshal([]byte(text), &data)

// 		client.orders = data

// 		if client.eventHandler != nil {
// 			for ticket, order := range data {
// 				client.eventHandler.OnOrderEvent(ticket, order)
// 			}
// 		}
// 	}
// }
