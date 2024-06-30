package metatrader

import (
	"crypto/rand"
	"fmt"
	"io"

	"github.com/gorilla/websocket"
)

var ID string

// WsRequestMethod is an enum for WebSocket request methods
type WsRequestMethod string

const (
	NONE               WsRequestMethod = "NONE"
	SUBSCRIBE          WsRequestMethod = "SUBSCRIBE"
	UNSUBSCRIBE        WsRequestMethod = "UNSUBSCRIBE"
	LIST_SUBSCRIPTIONS WsRequestMethod = "LIST_SUBSCRIPTIONS"
)

// WsHandler handle raw websocket message
type WsHandler func(message []byte)

// ErrHandler handles errors
type ErrHandler func(err error)

// WsConfig webservice configuration
type WsConfig struct {
	Endpoint string
	ID       string
	Method   WsRequestMethod
	Params   interface{}
}

func newWsConfig(endpoint string, method WsRequestMethod, params ...interface{}) *WsConfig {
	ID = generateUUID()
	return &WsConfig{
		Endpoint: endpoint,
		ID:       ID,
		Method:   method,
		Params:   params,
	}
}

// wsServe connects to the WebSocket server and handles messages and errors
var wsServe = func(cfg *WsConfig, handler WsHandler, errHandler ErrHandler) (doneC, stopC chan struct{}, err error) {
	fmt.Println("cfg.Endpoint: ", cfg.Endpoint)
	c, _, err := websocket.DefaultDialer.Dial(cfg.Endpoint, nil)
	if err != nil {
		return nil, nil, err
	}

	c.SetReadLimit(655350)

	doneC = make(chan struct{})
	stopC = make(chan struct{})

	// Construct a JSON message from the WsConfig struct
	msg := map[string]interface{}{
		"id":     cfg.ID,
		"method": cfg.Method,
	}

	if cfg.Params != nil {
		msg["params"] = cfg.Params
	}

	// Send the constructed JSON message
	err = c.WriteJSON(msg)
	if err != nil {
		return nil, nil, err
	}

	go func() {
		// This function will exit either on error from
		// websocket.Conn.ReadMessage or when the stopC channel is
		// closed by the client.
		defer close(doneC)
		if WebsocketKeepalive {
			keepAlive(cfg, c)
		}
		// Wait for the stopC channel to be closed.  We do that in a
		// separate goroutine because ReadMessage is a blocking
		// operation.
		silent := false
		go func() {
			select {
			case <-stopC:
				silent = true
			case <-doneC:
			}
			c.Close()
		}()
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				if !silent {
					errHandler(err)
				}
				return
			}
			handler(message)
		}
	}()
	return
}

// keepAlive sends periodic ping messages to keep the WebSocket connection alive
func keepAlive(cfg *WsConfig, c *websocket.Conn) {
	go func() {
		for {
			// Construct a JSON message from the WsConfig struct
			msg := map[string]interface{}{
				"id":     cfg.ID,
				"method": cfg.Method,
			}

			if cfg.Params != nil {
				msg["params"] = cfg.Params
			}

			// Send the constructed JSON message
			err := c.WriteJSON(msg)
			if err != nil {
				return
			}

		}
	}()
}

// generateUUID generates a random UUID
func generateUUID() string {
	uuid := make([]byte, 16)
	_, err := io.ReadFull(rand.Reader, uuid)
	if err != nil {
		panic(err)
	}

	// Set the variant and version as per RFC 4122
	uuid[8] = uuid[8]&^0xc0 | 0x80
	uuid[6] = uuid[6]&^0xf0 | 0x40

	return fmt.Sprintf("%x-%x-%x-%x-%x",
		uuid[0:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:16])
}
