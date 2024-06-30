package main

import (
	"exchange/db"
	"exchange/internal"
	"exchange/utils"
	"os"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func init() {
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})
}

func main() {
	wait := make(chan bool)

	env := utils.GetEnv()

	DB := db.New(env.DatabaseUrl)
	DB.Seed()

	pubsub := internal.NewPubSub(env.NatsUrl, env.NatsUser, env.NatsPass)
	defer pubsub.Close()

	metaTrader := internal.NewMetaTrader(true, pubsub, DB)
	// metaTrader.GetAccount()
	// metaTrader.GetBalance()
	// metaTrader.GetBalanceQuantity("Step Index")
	// metaTrader.Trade(metatrader.SideTypeBuy, metatrader.OrderTypeMarket, "Step Index", 8000, 0.10)
	// metaTrader.Dump("Step Index")

	go metaTrader.Kline()

	internal.RunAsyncApi(DB, metaTrader, pubsub)

	// deriv := internal.NewDeriv(61496, "JnAKRImmByOaIZT", true, pubsub, DB)
	// deriv.GetActiveSymbols("")
	// deriv.GetAccount()
	// deriv.GetBalance()

	// go deriv.Kline()

	// internal.RunAsyncApi(DB, deriv, pubsub)

	// bex := internal.NewBinance(
	// 	env.BinanceApiKey,
	// 	env.BinanceApiSecretKey,
	// 	env.BinanceTestnet,
	// 	pubsub,
	// 	DB,
	// )
	// fmt.Println("bex balances: ", bex.GetBalance())
	// bex.GetBalanceQuantity("BTCUSDT")

	// go bex.Kline()

	// internal.RunAsyncApi(DB, bex, pubsub)

	<-wait
}
