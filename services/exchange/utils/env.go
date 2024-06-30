package utils

import (
	"fmt"

	"github.com/kelseyhightower/envconfig"
)

type Env struct {
	BinanceTestnet      bool   `envconfig:"BINANCE_TESTNET"`
	BinanceApiKey       string `envconfig:"BINANCE_API_KEY"`
	BinanceApiSecretKey string `envconfig:"BINANCE_SECRET_KEY"`

	NatsUrl  string `envconfig:"NATS_URL"`
	NatsUser string `envconfig:"NATS_USER"`
	NatsPass string `envconfig:"NATS_PASS"`

	DatabaseUrl string `envconfig:"DATABASE_URL"`
}

func GetEnv() Env {
	var env Env
	envconfig.MustProcess("", &env)
	return env
}

func GetDynamicEnv() Env {
	var env Env
	envconfig.MustProcess("", &env)
	fmt.Println("env vars: ", env)
	return env
}

// TODO:
// Store and Get the following from the DB
// BinanceTestnet      bool   `envconfig:"BINANCE_TESTNET"`
// BinanceApiKey       string `envconfig:"BINANCE_API_KEY"`
// BinanceApiSecretKey string `envconfig:"BINANCE_SECRET_KEY"`
