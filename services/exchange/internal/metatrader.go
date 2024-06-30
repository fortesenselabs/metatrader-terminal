package internal

import (
	"context"
	"exchange/db"
	"exchange/go-metatrader"
	"exchange/utils"
	"fmt"
	"time"

	"github.com/rs/zerolog/log"
)

type MetaTrader struct {
	client *metatrader.Client
	test   bool
	pubsub PubSub
	DB     db.DB
}

// func NewMetaTrader(key, secret string, test bool, pubsub PubSub, DB db.DB) MetaTrader {
func NewMetaTrader(test bool, pubsub PubSub, DB db.DB) MetaTrader {
	log.Trace().Str("type", "metatrader").Bool("test", test).Msg("MetaTrader.Init")

	// metatrader.UseTestnet = test
	client := metatrader.NewClient()

	return MetaTrader{client, test, pubsub, DB}
	// return MetaTrader{client, test}
}

func (m MetaTrader) GetName() string {
	return "METATRADER"
}

func (m MetaTrader) TestMode() bool {
	return m.test
}

func (m MetaTrader) GetAccount() *ExchangeAccount {
	svc := m.client.NewGetAccountService()
	mtAccount, err := svc.Do(context.Background())

	if err != nil {
		log.Error().Err(err).Msg("MetaTrader.UserInfo")
	}

	account := &ExchangeAccount{
		MakerCommission:  0,
		TakerCommission:  0,
		BuyerCommission:  0,
		SellerCommission: 0,
		CanTrade:         mtAccount.CanTrade,
		CanWithdraw:      mtAccount.CanWithdraw,
		CanDeposit:       mtAccount.CanDeposit,
		UpdateTime:       mtAccount.UpdateTime,
		AccountType:      mtAccount.AccountType,
		Balances:         make([]ExchangeBalance, 0, len(mtAccount.Balances)),
		Permissions:      mtAccount.Permissions,
	}

	for _, mtBalance := range mtAccount.Balances {
		// Assuming ExchangeBalance has compatible fields with binance.Balance (modify as needed)
		exchangeBalance := ExchangeBalance{
			Asset:  mtBalance.Symbol,
			Free:   mtBalance.Free,
			Locked: mtBalance.Locked,
		}
		account.Balances = append(account.Balances, exchangeBalance)
	}

	return account
}

func (m MetaTrader) GetBalance() []Balance {
	acc := m.GetAccount()
	balances := []Balance{}

	for _, balance := range acc.Balances {
		asset := balance.Asset
		amt := utils.ParseFloat(balance.Free)

		// remove empty asset filter
		// if amt > ZeroBalance {
		b := Balance{asset, amt}
		balances = append(balances, b)
		// }
	}

	return balances
}

func (m MetaTrader) GetBalanceQuantity(symbol string) (float64, error) {
	info, err := m.client.NewExchangeInfoService().Symbol(symbol).Do(context.Background())
	if err != nil {
		log.Error().Str("symbol", symbol).Err(err).Msg("MetaTrader.GetBalanceQuantity")
		return 0, err
	}

	balances := m.GetBalance()

	asset := info.Symbols[0].BaseAsset

	for _, balance := range balances {
		if balance.Asset == asset {
			return balance.Amount, nil
		}
	}

	log.Error().Str("symbol", symbol).Err(ErrBaseAsset).Msg("MetaTrader.GetBalanceQuantity")
	m.pubsub.Publish(CriticalErrorEvent, CriticalErrorEventPayload{ErrSymbol.Error()})

	return 0, ErrBaseAsset
}

func (m MetaTrader) Dump(symbol string) (dump DumpResponse, err error) {
	log.Info().Str("symbol", symbol).Msg("MetaTrader.Dump")

	quantity, err := m.GetBalanceQuantity(symbol)

	if err != nil {
		log.Error().Err(err).Msg("MetaTrader.Dump.Skip")
		return dump, err
	}

	orderQuantity := utils.ParseOrderQuantity(quantity)

	// TODO: for the dump function in metatrader use the close order functionality in the client SDK
	// reason is because of the way trading is done using metatrader, on crypto exchanges you sell off assets
	// on metatrader you close off positions OR orders
	order, err := m.client.NewCancelOrderService().
		Symbol(symbol).
		Do(context.Background())

	// order, err := m.client.NewCreateOrderService().
	// 	Symbol(symbol).
	// 	Side(metatrader.SideTypeSell).
	// 	Type(metatrader.OrderTypeMarket).
	// 	Quantity(orderQuantity).
	// 	Do(context.Background())

	if err != nil {
		log.Error().Str("quantity", orderQuantity).Err(err).Msg("MetaTrader.Dump.Error")
		m.pubsub.Publish(CriticalErrorEvent, CriticalErrorEventPayload{err.Error()})
		return dump, err
	}

	dump.ID = order.OrderID
	dump.Quantity = utils.ParseFloat(orderQuantity)

	return dump, nil
}

func (m MetaTrader) Trade(side string, symbol string, price, quantity float64) error {
	log.Info().Interface("side", side).Str("symbol", symbol).Float64("quantity", quantity).Msg("MetaTrader.Trade.Init")

	orderQuantity := utils.ParseOrderQuantity(quantity)

	order, err := m.client.NewCreateOrderService().
		Symbol(symbol).
		Side(metatrader.SideType(side)).
		Type(metatrader.OrderTypeMarket).
		Quantity(orderQuantity).
		Do(context.Background())

	finalQuantity := utils.ParseFloat(orderQuantity)

	if err != nil {
		log.Error().Interface("side", side).Float64("price", price).Float64("quantity", finalQuantity).Err(err).Msg("MetaTrader.Trade")
		m.pubsub.Publish(CriticalErrorEvent, CriticalErrorEventPayload{err.Error()})
		return err
	}

	log.Info().Interface("side", side).Float64("price", price).Float64("quantity", finalQuantity).Msg("MetaTrader.Trade.Order")

	payload := OrderEventPayload{order.OrderID, string(order.Side), string(order.Type), symbol, price, finalQuantity}
	// m.pubsub.Publish(OrderEvent, payload)
	fmt.Println(payload)

	return nil
}

func (m MetaTrader) Kline() {
	klineHandler := func(event *metatrader.WsKlineEvent) {
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

		fmt.Println("Kline(): ", kline)
		strategy := m.DB.GetStrategy(symbol)
		m.pubsub.Publish(KlineEvent, KlinePayload{kline, strategy})
	}

	errHandler := func(err error) {
		log.Error().Err(err).Msg("MetaTrader.Kline.Error")

		// Try to restart ws connection
		log.Warn().Msg("MetaTrader.Kline.Recover")
		m.Kline()
	}

	// var configs []db.Configs
	// config := db.Configs{
	// 	Symbol:         "Volatility 75 Index", // "R_50", | Step Index
	// 	Base:           "Volatility 75 Index", // | Step Index
	// 	Quote:          "USD",
	// 	Interval:       "M1",
	// 	Minimum:        0.1,
	// 	AllowedAmount:  0.1,
	// 	TradingEnabled: true,
	// }
	// configs = append(configs, config)
	configs := m.DB.GetConfigs(m.GetName())

	for _, config := range configs {
		log.Info().Str("symbol", config.Symbol).Str("interval", config.Interval).Msg("MetaTrader.Kline.Subscribe")
		go metatrader.WsKlineServe(
			config.Symbol,
			config.Interval,
			true,
			klineHandler,
			errHandler,
		)
	}
}
