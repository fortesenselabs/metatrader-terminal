package internal

import (
	"errors"
	"exchange/db"
	"exchange/utils"
	"fmt"
	"strings"
	"time"

	"github.com/ksysoev/deriv-api"
	"github.com/ksysoev/deriv-api/schema"
	"github.com/rs/zerolog/log"
)

// Interval represents interval enum.
var CurrentPeriod int = 60

var (
	ThirtySeconds  = schema.TicksHistoryGranularity(CurrentPeriod / 2)
	Minute         = schema.TicksHistoryGranularity(1 * CurrentPeriod)
	ThreeMinutes   = schema.TicksHistoryGranularity(3 * CurrentPeriod)
	FiveMinutes    = schema.TicksHistoryGranularity(5 * CurrentPeriod)
	FifteenMinutes = schema.TicksHistoryGranularity(15 * CurrentPeriod)
	ThirtyMinutes  = schema.TicksHistoryGranularity(30 * CurrentPeriod)
	Hour           = schema.TicksHistoryGranularity(CurrentPeriod * CurrentPeriod)
	TwoHours       = schema.TicksHistoryGranularity(2 * CurrentPeriod * CurrentPeriod)
	FourHours      = schema.TicksHistoryGranularity(4 * CurrentPeriod * CurrentPeriod)
	SixHours       = schema.TicksHistoryGranularity(6 * CurrentPeriod * CurrentPeriod)
	EightHours     = schema.TicksHistoryGranularity(8 * CurrentPeriod * CurrentPeriod)
	TwelveHours    = schema.TicksHistoryGranularity(12 * CurrentPeriod * CurrentPeriod)
	Day            = schema.TicksHistoryGranularity(24 * CurrentPeriod * CurrentPeriod)
	ThreeDays      = schema.TicksHistoryGranularity(3 * 24 * CurrentPeriod * CurrentPeriod)
	Week           = schema.TicksHistoryGranularity(7 * 24 * CurrentPeriod * CurrentPeriod)
	Month          = schema.TicksHistoryGranularity(4 * 7 * 24 * CurrentPeriod * CurrentPeriod)
)

// TimeInForce represents timeInForce enum.
type TimeInForce string

var (
	GTC = TimeInForce("GTC")
	IOC = TimeInForce("IOC")
)

type IntervalMap map[string]schema.TicksHistoryGranularity

var TimeframeIntervals IntervalMap = IntervalMap{
	"30s": ThirtySeconds,
	"1m":  Minute,
	"5m":  FiveMinutes,
	"15m": FifteenMinutes,
	"30m": ThirtyMinutes,
	"1h":  Hour,
	"2h":  TwoHours,
	"4h":  FourHours,
	"6h":  SixHours,
	"8h":  EightHours,
	"12h": TwelveHours,
	"1d":  Day,
	"3d":  ThreeDays,
	"1w":  Week,
	"1M":  Month,
}

type SideType = string
type OrderType = string
type OrderStatusType string

type Order struct {
	symbol    string
	side      SideType
	orderType OrderType
	quantity  string
}

type CreateDerivOrderResponse struct {
	Symbol           string
	OrderID          int64
	Type             OrderType
	TransactTime     int64
	Price            string
	OrigQuantity     string
	ExecutedQuantity string
	Status           OrderStatusType
	Side             SideType
}

type Deriv struct {
	client            *deriv.DerivAPI
	test              bool
	authorizedAccount schema.AuthorizeResp
	pubsub            PubSub
	DB                db.DB
}

var ErrSymbol = errors.New("symbol not found")

func NewDeriv(appID int, apiToken string, test bool, pubsub PubSub, DB db.DB) Deriv {
	log.Trace().Str("type", "deriv").Bool("test", test).Msg("Deriv.Init")

	client, err := deriv.NewDerivAPI("wss://ws.binaryws.com/websockets/v3", appID, "en", "https://www.binary.com")
	if err != nil {
		log.Error().Err(err).Msg("Deriv.NewDerivAPI")
	}

	// would disconnect the connection at the end of the function,
	// but we want the connection to remain active
	// defer client.Disconnect()

	// First, we need to authorize the connection
	reqAuth := schema.Authorize{Authorize: apiToken}
	authorizedAccount, err := client.Authorize(reqAuth)
	if err != nil {
		log.Error().Err(err).Msg("Deriv.Authorize")
		return Deriv{}
	}

	log.Trace().Str("type", "deriv").Bool("test", test).Msg("Deriv.Connected")

	return Deriv{client, test, authorizedAccount, pubsub, DB}
}

func (d Deriv) GetName() string {
	return "DERIV"
}

func (d Deriv) TestMode() bool {
	return d.test
}

func (d Deriv) GetAccount() *ExchangeAccount {
	response, err := d.client.AccountList(schema.AccountList{AccountList: 1})
	if err != nil {
		log.Error().Err(err).Msg("Deriv.AccountList")
	}
	// fmt.Println(response)
	// fmt.Println(d.authorizedAccount.Authorize.Scopes)
	// fmt.Println("len(d.authorizedAccount.Authorize.AccountList): ", len(d.authorizedAccount.Authorize.AccountList))
	// fmt.Println(*d.authorizedAccount.Authorize.AccountList[0].Currency)
	fiatAccount := response.AccountList[0]

	account := &ExchangeAccount{
		MakerCommission:  0,
		TakerCommission:  0,
		BuyerCommission:  0,
		SellerCommission: 0,
		CanTrade:         true,
		CanWithdraw:      false,
		CanDeposit:       true,
		UpdateTime:       uint64(fiatAccount.CreatedAt),
		AccountType:      strings.ToUpper(fiatAccount.AccountType),
		Balances:         make([]ExchangeBalance, 0, len(response.AccountList)),
		Permissions:      d.authorizedAccount.Authorize.Scopes,
	}

	// for _, accountCategory := range accounts.AccountList {
	// Assuming ExchangeBalance has compatible fields with binance.Balance (modify as needed)
	exchangeBalance := ExchangeBalance{
		Asset:  fiatAccount.Currency,
		Free:   fmt.Sprintf("%v", *d.authorizedAccount.Authorize.Balance), // TODO: add currency balance
		Locked: "0",
	}
	account.Balances = append(account.Balances, exchangeBalance)
	// }

	fmt.Println(*account)

	return account
}

func (d Deriv) GetBalance() []Balance {
	balances := []Balance{}

	// Get Balance
	// TODO: refactor this to consider the balances of all accounts (just like it's binance counterpart)
	// TODO: fix 6:19AM ERR Deriv.Balance error="Permission denied, balances of all accounts require oauth token"
	account, err := d.client.Balance(schema.Balance{Account: "current", Balance: 1})
	if err != nil {
		log.Error().Err(err).Msg("Deriv.Balance")
		return balances
	}

	asset := account.Balance.Currency
	amt := account.Balance.Balance

	if amt > ZeroBalance {
		b := Balance{asset, amt}
		balances = append(balances, b)
	}

	return balances
}

func (d Deriv) GetBalanceQuantity(symbol string) (float64, error) {
	// returns USD balance OR it gets the Symbol in ActiveSymbols Amount
	// check if the symbol is in the list of open positions
	// if true: returns the lot size of the trade
	info, err := d.client.Portfolio(schema.Portfolio{Portfolio: 1})
	if err != nil {
		log.Error().Str("symbol", symbol).Err(err).Msg("Deriv.GetBalanceQuantity")
		return 0, err
	}

	for _, contract := range info.Portfolio.Contracts {
		if *contract.Symbol == symbol {
			return *contract.Payout, nil
		}
	}

	balances := d.GetBalance()

	accountBalance := balances[0]
	if accountBalance.Asset == symbol {
		return accountBalance.Amount, nil
	}

	log.Error().Str("symbol", symbol).Err(ErrSymbol).Msg("Deriv.GetBalanceQuantity")
	d.pubsub.Publish(CriticalErrorEvent, CriticalErrorEventPayload{ErrSymbol.Error()})

	return 0, ErrSymbol
}

func (d Deriv) Dump(symbol string) (dump DumpResponse, err error) {
	log.Info().Str("symbol", symbol).Msg("Deriv.Dump")

	// check if the symbol is in the list of open positions
	// if true: create a dump order (Close the trade)
	// get the quantity of the symbol or currently traded symbol
	quantity, err := d.GetBalanceQuantity(symbol)
	if err != nil {
		log.Error().Err(err).Msg("Deriv.Dump.Skip")
		return dump, err
	}

	orderQuantity := utils.ParseOrderQuantity(quantity)

	//
	// Create a SELL order
	// OR just close all positions related to the symbol
	order, err := d.CreateNewDerivOrder(Order{
		symbol:    "",
		side:      "",
		orderType: "",
		quantity:  "",
	})
	if err != nil {
		log.Error().Str("quantity", orderQuantity).Err(err).Msg("Deriv.Dump.Error")
		d.pubsub.Publish(CriticalErrorEvent, CriticalErrorEventPayload{err.Error()})
		return dump, err
	}

	dump.ID = order.OrderID
	dump.Quantity = utils.ParseFloat(orderQuantity)

	return dump, nil
}

func (d Deriv) Trade(side string, symbol string, price, quantity float64) error {
	log.Info().Interface("side", side).Str("symbol", symbol).Float64("quantity", quantity).Msg("Deriv.Trade.Init")

	orderQuantity := utils.ParseOrderQuantity(quantity)

	order, err := d.CreateNewDerivOrder(Order{
		symbol:    "",
		side:      "",
		orderType: "",
		quantity:  orderQuantity,
	})

	finalQuantity := utils.ParseFloat(orderQuantity)

	if err != nil {
		log.Error().Interface("side", side).Float64("price", price).Float64("quantity", finalQuantity).Err(err).Msg("Deriv.Trade")
		d.pubsub.Publish(CriticalErrorEvent, CriticalErrorEventPayload{err.Error()})
		return err
	}

	log.Info().Interface("side", side).Float64("price", price).Float64("quantity", finalQuantity).Msg("Deriv.Trade.Order")

	payload := OrderEventPayload{order.OrderID, string(order.Side), string(order.Type), symbol, price, finalQuantity}
	d.pubsub.Publish(OrderEvent, payload)

	return nil
}

func (d Deriv) Kline() {
	klineHandler := func(event *WsKlineEvent) {
		symbol := event.Kline.Symbol
		time := time.Now().Unix() * 1000
		open := utils.ParseFloat(event.Kline.Open)
		high := utils.ParseFloat(event.Kline.High)
		low := utils.ParseFloat(event.Kline.Low)
		close := utils.ParseFloat(event.Kline.Close)
		volume := utils.ParseFloat(event.Kline.Volume)
		final := event.Kline.IsFinal

		kline := Kline{symbol, time, open, high, low, close, volume, final}

		log.Info().
			Str("symbol", symbol).
			Float64("open", open).
			Float64("high", high).
			Float64("low", low).
			Float64("close", close).
			Float64("volume", volume).
			Bool("final", final).
			Msg(KlineEvent)

		strategy := d.DB.GetStrategy(symbol)
		d.pubsub.Publish(KlineEvent, KlinePayload{kline, strategy})
	}

	errHandler := func(err error) {
		log.Error().Err(err).Msg("Deriv.Kline.Error")

		// Try to restart ws connection
		log.Warn().Msg("Deriv.Kline.Recover")
		d.Kline()
	}

	configs := d.DB.GetConfigs(d.GetName())

	for _, config := range configs {
		log.Info().Str("symbol", config.Symbol).Str("interval", config.Interval).Msg("Deriv.Kline.Subscribe")
		go d.WsKlineServe(
			config.Symbol,
			config.Interval,
			klineHandler,
			errHandler,
		)
	}
}

// WsKlineServe serve websocket kline handler with a symbol and interval like 15m, 30s
func (d Deriv) WsKlineServe(symbol string, interval string, handler WsKlineHandler, errHandler ErrHandler) (doneC, stopC chan struct{}, err error) {
	doneC = make(chan struct{})
	stopC = make(chan struct{})

	var startTime schema.TicksHistoryAdjustStartTime = 1
	var granularity schema.TicksHistoryGranularity = TimeframeIntervals[interval] // for the interval
	start := 1
	_, sub, err := d.client.SubscribeCandlesHistory(schema.TicksHistory{
		TicksHistory:    symbol,
		AdjustStartTime: &startTime,
		End:             "latest",
		Start:           &start,
		Granularity:     &granularity,
		Count:           10})
	if err != nil {
		log.Error().Err(err).Msg("Deriv.SubscribeCandlesHistory")
		return nil, nil, err
	}

	go func() {
		for tick := range sub.Stream {
			event := new(WsKlineEvent)

			event.Symbol = *tick.Ohlc.Symbol // fmt.Sprintf("", *tick.Ohlc.Symbol)
			event.Time = int64(*tick.Ohlc.Epoch)

			event.Kline.Symbol = *tick.Ohlc.Symbol
			event.Kline.Open = *tick.Ohlc.Open
			event.Kline.Close = *tick.Ohlc.Close
			event.Kline.High = *tick.Ohlc.High
			event.Kline.Low = *tick.Ohlc.Low
			event.Kline.Volume = "0"
			event.Kline.IsFinal = true
			event.Kline.StartTime = int64(*tick.Ohlc.OpenTime)

			// err := json.Unmarshal(message, event)
			// if err != nil {
			// 	errHandler(err)
			// 	return
			// }

			handler(event)
		}
	}()
	return
}

// Create new orders
func (d Deriv) CreateNewDerivOrder(order Order) (*CreateDerivOrderResponse, error) {
	fmt.Println("Symbol:", order.symbol)
	fmt.Println("side:", order.side)
	fmt.Println("orderType:", order.orderType)
	fmt.Println("quantity:", order.quantity)

	amount := 100.0
	barrier := "+0.001"
	duration := 5
	basis := schema.ProposalBasisPayout

	reqProp := schema.Proposal{
		Proposal:     1,
		Amount:       &amount,
		Barrier:      &barrier,
		Basis:        &basis,
		ContractType: schema.ProposalContractTypeCALL,
		Currency:     "USD",
		Duration:     &duration,
		DurationUnit: schema.ProposalDurationUnitT,
		Symbol:       "R_50",
	}

	// Send a proposal request
	proposal, err := d.client.Proposal(reqProp)
	if err != nil {
		log.Error().Err(err).Msg("Deriv.Proposal")
		return nil, err
	}

	buyReq := schema.Buy{
		Buy:   proposal.Proposal.Id,
		Price: 100.0,
	}
	_, buySub, err := d.client.SubscribeBuy(buyReq)
	if err != nil {
		log.Error().Err(err).Msg("Deriv.SubscribeBuy")
		return nil, err
	}

	for proposalOpenContract := range buySub.Stream {
		fmt.Println("Current Spot: ", *proposalOpenContract.ProposalOpenContract.CurrentSpot)
		if *proposalOpenContract.ProposalOpenContract.IsSold == 1 {
			fmt.Println("Contract Result: ", proposalOpenContract.ProposalOpenContract.Status.Value)
			buySub.Forget()
			break
		}
	}

	// res = new(CreateOrderResponse)

	return nil, nil
}

func (d Deriv) GetAssetsInfo() {
	// Get all the assets info
	assets, err := d.client.AssetIndex(schema.AssetIndex{AssetIndex: 1})
	if err != nil {
		log.Error().Err(err).Msg("Deriv.AssetIndex")
		return
	}

	fmt.Println("Assets: ", assets)
}

func (d Deriv) GetActiveSymbols() []ActiveSymbols {
	activeSymbols := []ActiveSymbols{}

	// TODO: add filter, to filter by market type, etc => filter map[string]bool
	// Get all active symbols
	response, err := d.client.ActiveSymbols(schema.ActiveSymbols{ActiveSymbols: "full"})
	if err != nil {
		log.Error().Err(err).Msg("Deriv.ActiveSymbols")
		return activeSymbols
	}

	fmt.Println("Active Symbols: ", response.ActiveSymbols)

	for _, symbol := range response.ActiveSymbols {
		// if symbol.Market != "synthetic_index" {

		// }
		// Access each element's properties within the loop
		fmt.Println("DisplayName:", symbol.DisplayName)
		fmt.Println("Symbol:", symbol.Symbol)
		fmt.Println("SymbolType:", symbol.SymbolType)
		fmt.Println("Market:", symbol.Market)
		fmt.Println("MarketDisplayName:", symbol.MarketDisplayName)
		fmt.Println("ExchangeIsOpen:", symbol.ExchangeIsOpen)
		fmt.Println("ExchangeName:", symbol.ExchangeName)
		fmt.Println("Allow forward starting:", *symbol.AllowForwardStarting)

		// Check if symbol allows forward starting contracts
		if *symbol.AllowForwardStarting == 1 {
			fmt.Println("This symbol allows forward starting contracts")
		} else {
			fmt.Println("This symbol does not allow forward starting contracts")
		}
	}

	return activeSymbols
}

// deriv := internal.NewDeriv(61496, "JnAKRImmByOaIZT", true)

// deriv.GetActiveSymbols()
// deriv.GetAccount()
// deriv.GetBalance()

// go deriv.Kline()

// var configs []db.Configs

// // configs := d.DB.GetConfigs()
// config := db.Configs{
// 	Symbol:         "stpRNG", // "R_50",
// 	Base:           "",
// 	Quote:          "",
// 	Interval:       "1h",
// 	Minimum:        0.1,
// 	AllowedAmount:  0.1,
// 	TradingEnabled: true,
// }
// configs = append(configs, config)

// resp, sub, err := d.client.SubscribeTicks(schema.Ticks{Ticks: "R_50"})
// if err != nil {
// 	log.Error().Err(err).Msg("Deriv.SubscribeTicks")
// 	return
// }

// fmt.Println("Symbol: ", *resp.Tick.Symbol, "Quote: ", *resp.Tick.Quote)
// for tick := range sub.Stream {
// 	// log.Info().Str("symbol", config.Symbol).Str("interval", config.Interval).Msg("Deriv.Kline.Subscribe")

// 	fmt.Println("Symbol: ", *tick.Tick.Symbol, "Quote: ", *tick.Tick.Quote)
// }

// 	resp, sub, err := d.client.SubscribeTicks(schema.Ticks{Ticks: "stpRNG"})
// 	if err != nil {
// 		log.Error().Err(err).Msg("Deriv.SubscribeTicks")
// 		return
// 	}

// 	fmt.Println("Symbol: ", *resp.Tick.Symbol, "Quote: ", *resp.Tick.Quote)

// 	for tick := range sub.Stream {
// 		fmt.Println("Symbol: ", *tick.Tick.Symbol, "Quote: ", *tick.Tick.Quote)
// 	}
