package api

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

func NewDWXClient(eventHandler EventHandler, metaTraderDirPath string, sleepDelay time.Duration, maxRetryCommandSeconds int, loadOrdersFromFile, verbose bool) *DWXClient {
	if _, err := os.Stat(metaTraderDirPath); os.IsNotExist(err) {
		fmt.Println("ERROR: metaTrader directory path does not exist!")
		os.Exit(1)
	}

	client := &DWXClient{
		EventHandler:           eventHandler,
		SleepDelay:             sleepDelay,
		MaxRetryCommandSeconds: maxRetryCommandSeconds,
		LoadOrdersFromFile:     loadOrdersFromFile,
		Verbose:                verbose,
		CommandID:              0,
		MetaTraderDirPath:      metaTraderDirPath,
		NumCommandFiles:        50,
		Active:                 true,
		Start:                  false,
	}

	client.Paths = Paths{
		Orders:         filepath.Join(metaTraderDirPath, "DWX", "DWX_Orders.txt"),
		Messages:       filepath.Join(metaTraderDirPath, "DWX", "DWX_Messages.txt"),
		MarketData:     filepath.Join(metaTraderDirPath, "DWX", "DWX_Market_Data.txt"),
		BarData:        filepath.Join(metaTraderDirPath, "DWX", "DWX_Bar_Data.txt"),
		HistoricData:   filepath.Join(metaTraderDirPath, "DWX", "DWX_Historic_Data.txt"),
		HistoricTrades: filepath.Join(metaTraderDirPath, "DWX", "DWX_Historic_Trades.txt"),
		OrdersStored:   filepath.Join(metaTraderDirPath, "DWX", "DWX_Orders_Stored.txt"),
		MessagesStored: filepath.Join(metaTraderDirPath, "DWX", "DWX_Messages_Stored.txt"),
		CommandsPrefix: filepath.Join(metaTraderDirPath, "DWX", "DWX_Commands_"),
	}

	client.loadMessages()

	if client.LoadOrdersFromFile {
		client.loadOrders()
	}

	go client.checkMessages()
	go client.checkMarketData()
	go client.checkBarData()
	go client.checkOpenOrders()
	go client.checkHistoricData()

	client.resetCommandIDs()

	if client.EventHandler == nil {
		client.Start = true
	}

	return client
}

// Method to try reading a file
func (client *DWXClient) tryReadFile(filePath string) string {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		// File does not exist, return empty string
		return ""
	}

	var text string
	for attempts := 0; attempts < 10; attempts++ {
		data, err := os.ReadFile(filePath)
		if err == nil {
			text = string(data)
			break // File read successfully, exit the loop
		}

		// Handle specific errors
		if os.IsPermission(err) {
			// Permission error, retry
			continue
		}

		// Print any other unexpected errors
		log.Println(err)
	}

	return text
}

// Method to try removing a file with retries
func (client *DWXClient) tryRemoveFile(filePath string) {
	for i := 0; i < 10; i++ {
		err := os.Remove(filePath)
		if err == nil {
			break // File removed successfully, exit the loop
		}
		// Handle specific errors
		if os.IsPermission(err) || os.IsNotExist(err) {
			// Permission or not found errors, retry
			continue
		}
		// Print any other unexpected errors
		fmt.Println(err)
	}
}

func (client *DWXClient) checkOpenOrders() {
	for client.Active {
		time.Sleep(client.SleepDelay)
		if !client.Start {
			continue
		}

		text := client.tryReadFile(client.Paths.Orders)
		if len(text) == 0 || text == client.LastOpenOrdersStr {
			continue
		}

		client.LastOpenOrdersStr = text
		var data map[string]interface{}
		json.Unmarshal([]byte(text), &data)

		newEvent := false
		// Iterate over open_orders map
		for orderID, order := range client.OpenOrders {
			// Check if order_id is not present in data['orders'].keys()
			if _, ok := data["orders"].(map[string]Order)[orderID]; !ok {
				newEvent = true
				if client.Verbose {
					fmt.Println("Order removed:", order)
				}
			}
		}

		// Iterate over orders in data
		for orderID, order := range data["orders"].(map[string]Order) {
			// Check if order_id is not present in self.openOrders
			if _, ok := client.OpenOrders[orderID]; !ok {
				newEvent = true
				if client.Verbose {
					fmt.Println("New order:", order)
				}
			}
		}

		client.AccountInfo = data["account_info"].(AccountInfo)
		client.OpenOrders = data["orders"].(map[string]Order)

		// Write data to file if loadOrdersFromFile is true
		if client.LoadOrdersFromFile {
			file, err := os.Create(client.Paths.OrdersStored)
			if err != nil {
				fmt.Println("Error creating file:", err)
				return
			}
			defer file.Close()

			jsonData, err := json.Marshal(data)
			if err != nil {
				fmt.Println("Error encoding JSON:", err)
				return
			}

			_, err = file.Write(jsonData)
			if err != nil {
				fmt.Println("Error writing to file:", err)
				return
			}
		}

		if client.EventHandler != nil && newEvent {
			client.EventHandler.OnOrderEvent()
		}
	}
}

func (client *DWXClient) checkMessages() {
	for client.Active {
		time.Sleep(client.SleepDelay)
		if !client.Start {
			continue
		}

		text := client.tryReadFile(client.Paths.Messages)
		if len(text) == 0 || text == client.LastMessagesStr {
			continue
		}

		client.LastMessagesStr = text
		var data map[string]string
		json.Unmarshal([]byte(text), &data)

		for millis, message := range data {
			millisInt, _ := strconv.ParseInt(millis, 10, 64)
			if millisInt > client.LastMessagesMillis {
				client.LastMessagesMillis = millisInt
				if client.EventHandler != nil {
					client.EventHandler.OnMessage(message)
				}
			}
		}

		os.WriteFile(client.Paths.MessagesStored, []byte(text), 0644)
	}
}

func (client *DWXClient) checkMarketData() {
	for client.Active {
		time.Sleep(client.SleepDelay)
		if !client.Start {
			continue
		}

		text := client.tryReadFile(client.Paths.MarketData)
		if len(text) == 0 || text == client.LastMarketDataStr {
			continue
		}

		client.LastMarketDataStr = text
		var data map[string]MarketData
		json.Unmarshal([]byte(text), &data)

		client.MarketData = data

		if client.EventHandler != nil {
			for symbol, marketData := range data {
				client.EventHandler.OnTick(symbol, marketData.Bid, marketData.Ask)
			}
		}

		client.LastMarketData = data
	}
}

func (client *DWXClient) checkBarData() {
	for client.Active {
		time.Sleep(client.SleepDelay)
		if !client.Start {
			continue
		}

		text := client.tryReadFile(client.Paths.BarData)
		if len(text) == 0 || text == client.LastBarDataStr {
			continue
		}

		client.LastBarDataStr = text
		fmt.Println("client.LastBarDataStr: ", client.LastBarDataStr)
		var data map[string]BarData
		json.Unmarshal([]byte(text), &data)

		client.BarData = data

		if client.EventHandler != nil {
			for symbol, barData := range data {
				client.EventHandler.OnBarData(symbol, barData)
			}
		}

		client.LastBarData = data
	}
}

func (client *DWXClient) loadMessages() {
	text := client.tryReadFile(client.Paths.MessagesStored)

	if len(text) > 0 {
		client.LastMessagesStr = text

		var data map[string]interface{}
		err := json.Unmarshal([]byte(text), &data)
		if err != nil {
			log.Printf("Error unmarshalling JSON: %v", err)
			return
		}

		// Update LastMessagesMillis with the latest millis value
		for millis := range data {
			millisInt, err := strconv.ParseInt(millis, 10, 64)
			if err != nil {
				log.Printf("Error converting millis to int: %v", err)
				continue
			}

			if millisInt > client.LastMessagesMillis {
				client.LastMessagesMillis = millisInt
			}
		}
	}
}

func (client *DWXClient) loadOrders() {
	text := client.tryReadFile(client.Paths.OrdersStored)

	if len(text) > 0 {
		client.LastOpenOrdersStr = text

		var data map[string]interface{}
		err := json.Unmarshal([]byte(text), &data)
		if err != nil {
			log.Printf("Error unmarshalling JSON: %v", err)
			return
		}

		fmt.Println("data: ", data)
		accountInfoData, err := json.Marshal(data["account_info"])
		if err != nil {
			log.Printf("Error marshalling account_info: %v", err)
			return
		}
		err = json.Unmarshal(accountInfoData, &client.AccountInfo)
		if err != nil {
			log.Printf("Error unmarshalling account_info: %v", err)
			return
		}

		openOrdersData, err := json.Marshal(data["orders"])
		if err != nil {
			log.Printf("Error marshalling orders: %v", err)
			return
		}
		err = json.Unmarshal(openOrdersData, &client.OpenOrders)
		if err != nil {
			log.Printf("Error unmarshalling orders: %v", err)
			return
		}
	}
}

func (client *DWXClient) checkHistoricData() {
	for client.Active {
		time.Sleep(client.SleepDelay)
		if !client.Start {
			continue
		}

		text := client.tryReadFile(client.Paths.HistoricData)
		if len(text) == 0 || text == client.LastHistoricDataStr {
			continue
		}

		client.LastHistoricDataStr = text
		var data map[string]HistoricData
		json.Unmarshal([]byte(text), &data)

		client.HistoricData = data

		if client.EventHandler != nil {
			for symbol, historicData := range data {
				client.EventHandler.OnHistoricData(symbol, historicData)
			}
		}
	}
}

func (client *DWXClient) checkHistoricTrades() {
	for client.Active {
		time.Sleep(client.SleepDelay)
		if !client.Start {
			continue
		}

		text := client.tryReadFile(client.Paths.HistoricTrades)
		if len(text) == 0 || text == client.LastHistoricTradesStr {
			continue
		}

		client.LastHistoricTradesStr = text
		var data map[string]HistoricTrades
		json.Unmarshal([]byte(text), &data)

		client.HistoricTrades = data

		if client.EventHandler != nil {
			for symbol, historicTrades := range data {
				client.EventHandler.OnHistoricTrades(symbol, historicTrades)
			}
		}
	}
}

func (client *DWXClient) sendCommand(commandType string, params map[string]interface{}) {
	command := map[string]interface{}{
		"type":   commandType,
		"params": params,
	}

	client.Lock.Lock()
	commandID := client.CommandID
	client.CommandID++
	client.Lock.Unlock()

	commandFile := fmt.Sprintf("%s%03d.txt", client.Paths.CommandsPrefix, commandID%client.NumCommandFiles)
	commandData, _ := json.Marshal(command)

	err := os.WriteFile(commandFile, commandData, 0644)
	if err != nil {
		fmt.Println("ERROR: Unable to write command file -", err)
	}
}

func (client *DWXClient) openOrder(symbol string, orderType string, volume float64, openPrice float64, slippage float64, stopLoss float64, takeProfit float64, magicNumber int, comment string, expiration time.Time) {
	params := map[string]interface{}{
		"symbol":      symbol,
		"order_type":  orderType,
		"volume":      volume,
		"open_price":  openPrice,
		"slippage":    slippage,
		"stop_loss":   stopLoss,
		"take_profit": takeProfit,
		"magic":       magicNumber,
		"comment":     comment,
		"expiration":  expiration.Format("2006-01-02 15:04:05"),
	}
	client.sendCommand("OPEN_ORDER", params)
}

func (client *DWXClient) closeOrder(ticket int, lots float64) {
	params := map[string]interface{}{
		"ticket": ticket,
		"lots":   lots,
	}
	client.sendCommand("CLOSE_ORDER", params)
}

func (client *DWXClient) resetCommandIDs() {
	client.Lock.Lock()
	defer client.Lock.Unlock()
	client.CommandID = 0
}
