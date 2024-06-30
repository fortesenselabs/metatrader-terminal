package main

import (
	"fmt"
	"metatrader-server/api"
	"time"
)

// Example implementation of EventHandler interface
type ProcessorEventHandler struct {
	DWXClient              *api.DWXClient
	MTFilesDir             string
	SleepDelay             time.Duration
	MaxRetryCommandSeconds int
}

// 5 ms for sleepDelay
// retry to send the commend for 10 seconds if not successful.
func NewProcessorEventHandler(MTFilesDir string, sleepDelay int, maxRetryCommandSeconds int, verbose bool) ProcessorEventHandler {
	if sleepDelay <= 0 {
		sleepDelay = 5
	}

	if maxRetryCommandSeconds <= 0 {
		maxRetryCommandSeconds = 10
	}

	handler := ProcessorEventHandler{
		DWXClient:              nil,
		MTFilesDir:             MTFilesDir,
		SleepDelay:             time.Duration(sleepDelay) * time.Millisecond,
		MaxRetryCommandSeconds: maxRetryCommandSeconds,
	}

	handler.DWXClient = api.NewDWXClient(&handler, handler.MTFilesDir, handler.SleepDelay, handler.MaxRetryCommandSeconds, true, true)

	time.Sleep(1 * time.Second)

	handler.DWXClient.Active = true

	// account information is stored in self.dwx.account_info.
	fmt.Println("Account info:", handler.DWXClient.AccountInfo)

	return handler
}

func (h *ProcessorEventHandler) OnOrderEvent() {
	fmt.Println("Order event detected.")
}

func (h *ProcessorEventHandler) OnMessage(message string) {
	fmt.Println("Message received:", message)
}

func (h *ProcessorEventHandler) OnTick(symbol string, bid float64, ask float64) {
	fmt.Println("Tick received for", symbol, "Bid:", bid, "Ask:", ask)
}

func (h *ProcessorEventHandler) OnBarData(symbol string, data api.BarData) {
	fmt.Println("Bar data received for", symbol, "Data:", data)
}

func (h *ProcessorEventHandler) OnHistoricData(symbol string, data api.HistoricData) {
	fmt.Println("Historic data received for", symbol, "Data:", data)
}

func (h *ProcessorEventHandler) OnHistoricTrades(symbol string, trades api.HistoricTrades) {
	fmt.Println("Historic trades received for", symbol, "Trades:", trades)
}

func main() {
	const MT_FILES_DIR = "/home/fortesenselabs/.wine/drive_c/Program Files/Metatrader 5/MQL5/Files"

	processor := NewProcessorEventHandler(MT_FILES_DIR, 5, 10, true)

	for processor.DWXClient.Active {
		time.Sleep(1)
	}
}
