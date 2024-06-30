package internal

import "github.com/adshao/go-binance/v2"

type Kline struct {
	Symbol string  `json:"symbol"`
	Time   int64   `json:"time"`
	Open   float64 `json:"open"`
	High   float64 `json:"high"`
	Low    float64 `json:"low"`
	Close  float64 `json:"close"`
	Volume float64 `json:"volume"`
	Final  bool    `json:"final"`
}

type Indicators struct {
	Rsi        *float64 `json:"rsi"`
	Macd       *float64 `json:"macd"`
	MacdSignal *float64 `json:"macd_signal"`
	MacdHist   *float64 `json:"macd_hist"`
}

type Signal string

type WsKlineEvent struct {
	binance.WsKlineEvent
}

// WsKlineHandler handle websocket kline event
type WsKlineHandler func(event *WsKlineEvent)

// ErrHandler handles errors
type ErrHandler func(err error)

type ExchangeHandler interface {
	GetName() string
	TestMode() bool
	Dump(symbol string) (dump DumpResponse, err error)
	GetAccount() *ExchangeAccount
	GetBalance() []Balance
	GetBalanceQuantity(symbol string) (float64, error)
	Kline()
	Trade(side string, symbol string, price float64, quantity float64) error
}

type ExchangeBalance struct {
	Asset  string `json:"asset"`
	Free   string `json:"free"`
	Locked string `json:"locked"`
}

type ExchangeAccount struct {
	MakerCommission  int64             `json:"makerCommission"`
	TakerCommission  int64             `json:"takerCommission"`
	BuyerCommission  int64             `json:"buyerCommission"`
	SellerCommission int64             `json:"sellerCommission"`
	CanTrade         bool              `json:"canTrade"`
	CanWithdraw      bool              `json:"canWithdraw"`
	CanDeposit       bool              `json:"canDeposit"`
	UpdateTime       uint64            `json:"updateTime"`
	AccountType      string            `json:"accountType"`
	Balances         []ExchangeBalance `json:"balances"`
	Permissions      []string          `json:"permissions"`
}

type ActiveSymbols struct {
	Symbol string `json:"symbol"`
}
