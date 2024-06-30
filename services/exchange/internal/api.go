package internal

import (
	"encoding/json"
	"exchange/db"
	"exchange/utils"

	"github.com/adshao/go-binance/v2"
	"github.com/nats-io/nats.go"
	"github.com/rs/zerolog/log"
)

func RunAsyncApi(DB db.DB, exchangeHandler ExchangeHandler, pubsub PubSub) {
	log.Trace().Str("Exchange.Name", exchangeHandler.GetName()).Msg("Internal.AsyncApi.Init")

	pubsub.Subscribe(GetStrategyEvent, func(m *nats.Msg) {
		var request GetStrategyRequest
		utils.Unmarshal(m.Data, &request)

		payload := GetStrategyResponse{
			Strategy: DB.GetStrategy(request.Symbol),
		}

		pubsub.Publish(m.Reply, payload)
	})

	pubsub.Subscribe(UpdateStrategyEvent, func(m *nats.Msg) {
		var request UpdateStrategyRequest
		utils.Unmarshal(m.Data, &request)

		DB.UpdateStrategy(request.Strategy)

		log.Trace().Msg("Internal.Strategy.Update")
		var payload any
		pubsub.Publish(m.Reply, payload)
	})

	pubsub.Subscribe(GetConfigsEvent, func(m *nats.Msg) {
		payload := GetConfigsResponse{
			Configs: DB.GetConfigs(exchangeHandler.GetName()),
		}

		pubsub.Publish(m.Reply, payload)
	})

	pubsub.Subscribe(DumpEvent, func(m *nats.Msg) {
		var request DumpRequest
		utils.Unmarshal(m.Data, &request)

		symbol := request.Symbol
		// exchange := "" // request.Exchange

		config := DB.GetConfig(symbol, exchangeHandler.GetName())

		log.Warn().Str("symbol", symbol).Msg("Internal.Dump.Trading.Disable")
		DB.UpdateConfigTradingEnabled(symbol, exchangeHandler.GetName(), false)

		DB.DeletePosition(symbol)
		log.Warn().Str("symbol", symbol).Msg("Internal.Dump.Positions")

		payload, err := exchangeHandler.Dump(symbol)

		if config.TradingEnabled {
			DB.UpdateConfigTradingEnabled(symbol, exchangeHandler.GetName(), true)
			log.Warn().Str("symbol", symbol).Msg("Internal.Dump.Trading.Enable")
		}

		if err != nil {
			return
		}

		log.Info().Str("symbol", symbol).Int64("ID", payload.ID).Float64("quantity", payload.Quantity).Msg("Internal.Dump.Complete")
		pubsub.Publish(m.Reply, payload)
	})

	pubsub.Subscribe(UpdateTradingEnabledEvent, func(m *nats.Msg) {
		var request UpdateTradingEnabledRequest
		utils.Unmarshal(m.Data, &request)

		DB.UpdateConfigTradingEnabled(request.Symbol, exchangeHandler.GetName(), request.Enabled)

		log.Trace().Str("symbol", request.Symbol).Bool("enabled", request.Enabled).Msg("Internal.Config.TradingEnabled")
		var payload any
		pubsub.Publish(m.Reply, payload)
	})

	pubsub.Subscribe(UpdateAllowedAmountEvent, func(m *nats.Msg) {
		var request UpdateAllowedAmountRequest
		utils.Unmarshal(m.Data, &request)

		DB.UpdateConfigAllowedAmount(request.Symbol, exchangeHandler.GetName(), request.Amount)

		log.Trace().Str("symbol", request.Symbol).Float64("amount", request.Amount).Msg("Internal.Config.AllowedAmount")
		var payload any
		pubsub.Publish(m.Reply, payload)
	})

	pubsub.Subscribe(DataFrameEvent, func(p DataFrameEventPayload) {
		ListenTrade(DB, pubsub, exchangeHandler, p.Kline, p.Signal)
	})

	pubsub.Subscribe(GetBalanceEvent, func(m *nats.Msg) {
		response := GetBalanceResponse{
			Test:    exchangeHandler.TestMode(),
			Balance: exchangeHandler.GetBalance(),
		}

		pubsub.Publish(m.Reply, response)
	})

	pubsub.Subscribe(GetPositionsEvent, func(m *nats.Msg) {
		response := GetPositionsResponse{
			Positions: DB.GetPositions(),
		}

		pubsub.Publish(m.Reply, response)
	})

	pubsub.Subscribe(GetTradesEvent, func(m *nats.Msg) {
		response := GetTradesResponse{
			Trades: DB.GetTrades(),
		}

		pubsub.Publish(m.Reply, response)
	})

	pubsub.Subscribe(GetStatsEvent, func(m *nats.Msg) {
		var response GetStatsResponse

		trades := DB.GetTrades()

		if len(trades) != 0 {
			stats := CalculateStats(trades)
			response = GetStatsResponse{&stats}
		}

		pubsub.Publish(m.Reply, response)
	})

	pubsub.Subscribe(GetDataFrameEvent, func(m *nats.Msg) {
		var request GetDataFrameRequest
		utils.Unmarshal(m.Data, &request)

		var response GetDataFrameResponse
		var data []DataFrameEventPayload

		js := pubsub.JetStream()
		sub, err := js.PullSubscribe(DataFrameEvent, "client")

		if err != nil {
			log.Error().Err(err).Msg("Internal.DataFrame.PullSubscribe")
			return
		}

		msgs, err := sub.Fetch(request.Size)

		if err != nil {
			log.Error().Err(err).Msg("Internal.DataFrame.Fetch")
			return
		}

		for _, msg := range msgs {
			var frame DataFrameEventPayload

			if err := json.Unmarshal(msg.Data, &frame); err != nil {
				log.Error().Err(err).Msg("Internal.DataFrame.Unmarshal")
				return
			}

			data = append(data, frame)
		}

		response.DataFrame = data

		pubsub.Publish(m.Reply, response)
	})
}

func ListenTrade(DB db.DB, pubsub PubSub, exchangeHandler ExchangeHandler, kline Kline, signal Signal) {
	if signal == "NONE" || !kline.Final {
		return
	}

	symbol := kline.Symbol

	config := DB.GetConfig(symbol, exchangeHandler.GetName())

	if !config.TradingEnabled {
		log.Warn().Str("symbol", symbol).Bool("enabled", config.TradingEnabled).Interface("signal", signal).Msg("Trade.Skip")
		return
	}

	log.Trace().Str("symbol", symbol).Interface("signal", signal).Msg("Trade.Listen")

	position := DB.GetPosition(symbol)
	var holding bool = position.Symbol != ""

	allowedAmt := config.AllowedAmount
	closePrice := kline.Close

	switch signal {
	case Signal(binance.SideTypeBuy):
		if holding {
			log.Warn().Bool("holding", holding).Msg("Trade.Buy.Skip")
			return
		}

		quantity := utils.ToFixed(utils.GetMinQuantity(allowedAmt, closePrice), 4)

		err := exchangeHandler.Trade(string(binance.SideTypeBuy), symbol, closePrice, quantity)
		if err != nil {
			return
		}

		DB.CreatePosition(symbol, closePrice, quantity)
		log.Trace().Float64("price", closePrice).Float64("quantity", quantity).Msg("Trade.Buy.Complete")

	case Signal(binance.SideTypeSell):
		if !holding {
			log.Warn().Bool("holding", holding).Msg("Trade.Sell.Skip")
			return
		}

		quantity := position.Quantity

		err := exchangeHandler.Trade(string(binance.SideTypeSell), symbol, closePrice, quantity)

		if err != nil {
			exchangeHandler.Dump(symbol)
			return
		}

		entry := position.Price
		DB.DeletePosition(symbol)
		trade := DB.CreateTrade(symbol, entry, closePrice, quantity)

		payload := TradeEventPayload{trade.ID, trade.Symbol, trade.Entry, trade.Exit, trade.Quantity, trade.Time}
		pubsub.Publish(TradeEvent, payload)

		log.Trace().Float64("price", closePrice).Float64("quantity", quantity).Msg("Trade.Sell.Complete")
	default:
	}
}

func CalculateStats(trades []db.Trades) (stats Stats) {
	for _, trade := range trades {
		percentage := ((trade.Exit - trade.Entry) / trade.Entry) * 100
		price := trade.Quantity * trade.Exit
		amount := (percentage * price) / 100

		if amount > 0 {
			stats.Profit += amount
		} else {
			stats.Loss += -1 * amount
		}
	}

	stats.Total = stats.Profit + stats.Loss
	return
}
