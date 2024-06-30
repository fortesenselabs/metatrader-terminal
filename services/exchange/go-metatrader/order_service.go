package metatrader

import (
	"context"
	"encoding/json"
	"net/http"
)

// CreateOrderService create order
type CreateOrderService struct {
	c                *Client
	symbol           string
	side             SideType
	orderType        OrderType
	timeInForce      *TimeInForceType
	quantity         *string
	price            *string
	stopLossPrice    *string
	takeProfitPrice  *string
	newClientOrderID *string
}

// Symbol set symbol
func (s *CreateOrderService) Symbol(symbol string) *CreateOrderService {
	s.symbol = symbol
	return s
}

// Side set side
func (s *CreateOrderService) Side(side SideType) *CreateOrderService {
	s.side = side
	return s
}

// Type set type
func (s *CreateOrderService) Type(orderType OrderType) *CreateOrderService {
	s.orderType = orderType
	return s
}

// TimeInForce set timeInForce
func (s *CreateOrderService) TimeInForce(timeInForce TimeInForceType) *CreateOrderService {
	s.timeInForce = &timeInForce
	return s
}

// Quantity set quantity
func (s *CreateOrderService) Quantity(quantity string) *CreateOrderService {
	s.quantity = &quantity
	return s
}

// Price set price
func (s *CreateOrderService) Price(price string) *CreateOrderService {
	s.price = &price
	return s
}

// NewClientOrderID set newClientOrderID
func (s *CreateOrderService) NewClientOrderID(newClientOrderID string) *CreateOrderService {
	s.newClientOrderID = &newClientOrderID
	return s
}

// stopLossPrice set stopLossPrice
func (s *CreateOrderService) StopLossPrice(stopLossPrice string) *CreateOrderService {
	s.stopLossPrice = &stopLossPrice
	return s
}

// takeProfitPrice set takeProfitPrice
func (s *CreateOrderService) TakeProfitPrice(takeProfitPrice string) *CreateOrderService {
	s.takeProfitPrice = &takeProfitPrice
	return s
}

func (s *CreateOrderService) createOrder(ctx context.Context, endpoint string, opts ...RequestOption) (data []byte, err error) {
	r := &request{
		method:   http.MethodPost,
		endpoint: endpoint,
	}
	m := params{
		"symbol": s.symbol,
		"side":   s.side,
		"type":   s.orderType,
	}
	if s.quantity != nil {
		m["quantity"] = *s.quantity
	}
	if s.timeInForce != nil {
		m["timeInForce"] = *s.timeInForce
	}
	if s.price != nil {
		m["price"] = *s.price
	}
	if s.newClientOrderID != nil {
		m["newClientOrderId"] = *s.newClientOrderID
	}
	if s.stopLossPrice != nil {
		m["stopLossPrice"] = *s.stopLossPrice
	}
	if s.takeProfitPrice != nil {
		m["takeProfitPrice"] = *s.takeProfitPrice
	}

	err = r.setBody(m)
	if err != nil {
		return []byte{}, err
	}
	r.setHeader("Content-Type", "application/json")

	data, err = s.c.callAPI(ctx, r, opts...)
	if err != nil {
		return []byte{}, err
	}
	return data, nil
}

// Do send request
func (s *CreateOrderService) Do(ctx context.Context, opts ...RequestOption) (res *CreateOrderResponse, err error) {
	data, err := s.createOrder(ctx, "/api/order", opts...)
	if err != nil {
		return nil, err
	}
	res = new(CreateOrderResponse)
	err = json.Unmarshal(data, res)
	if err != nil {
		return nil, err
	}
	return res, nil
}

// Test send test api to check if the request is valid
func (s *CreateOrderService) Test(ctx context.Context, opts ...RequestOption) (err error) {
	_, err = s.createOrder(ctx, "/api/order/test", opts...)
	return err
}

// CreateOrderResponse define create order response
type CreateOrderResponse struct {
	Symbol                   string `json:"symbol"`
	OrderID                  int64  `json:"orderId"`
	ClientOrderID            string `json:"clientOrderId"`
	TransactTime             int64  `json:"transactTime"`
	Price                    string `json:"price"`
	OrigQuantity             string `json:"origQty"`
	ExecutedQuantity         string `json:"executedQty"`
	CummulativeQuoteQuantity string `json:"cummulativeQuoteQty"`
	IsIsolated               bool   `json:"isIsolated"` // for isolated margin

	Status      OrderStatusType `json:"status"`
	TimeInForce TimeInForceType `json:"timeInForce"`
	Type        OrderType       `json:"type"`
	Side        SideType        `json:"side"`

	// for order response is set to FULL
	Fills                 []*Fill `json:"fills"`
	MarginBuyBorrowAmount string  `json:"marginBuyBorrowAmount"` // for margin
	MarginBuyBorrowAsset  string  `json:"marginBuyBorrowAsset"`
}

// Fill may be returned in an array of fills in a CreateOrderResponse.
type Fill struct {
	Price           string `json:"price"`
	Quantity        string `json:"qty"`
	Commission      string `json:"commission"`
	CommissionAsset string `json:"commissionAsset"`
}

// ListOpenOrdersService list opened orders
type ListOpenOrdersService struct {
	c      *Client
	symbol string
}

// Symbol set symbol
func (s *ListOpenOrdersService) Symbol(symbol string) *ListOpenOrdersService {
	s.symbol = symbol
	return s
}

// Do send request
func (s *ListOpenOrdersService) Do(ctx context.Context, opts ...RequestOption) (res []*Order, err error) {
	r := &request{
		method:   http.MethodGet,
		endpoint: "/api/v3/openOrders",
		secType:  secTypeSigned,
	}
	if s.symbol != "" {
		r.setParam("symbol", s.symbol)
	}
	data, err := s.c.callAPI(ctx, r, opts...)
	if err != nil {
		return []*Order{}, err
	}
	res = make([]*Order, 0)
	err = json.Unmarshal(data, &res)
	if err != nil {
		return []*Order{}, err
	}
	return res, nil
}

// GetOrderService get an order
type GetOrderService struct {
	c                 *Client
	symbol            string
	orderID           *int64
	origClientOrderID *string
}

// Symbol set symbol
func (s *GetOrderService) Symbol(symbol string) *GetOrderService {
	s.symbol = symbol
	return s
}

// OrderID set orderID
func (s *GetOrderService) OrderID(orderID int64) *GetOrderService {
	s.orderID = &orderID
	return s
}

// OrigClientOrderID set origClientOrderID
func (s *GetOrderService) OrigClientOrderID(origClientOrderID string) *GetOrderService {
	s.origClientOrderID = &origClientOrderID
	return s
}

// Do send request
func (s *GetOrderService) Do(ctx context.Context, opts ...RequestOption) (res *Order, err error) {
	r := &request{
		method:   http.MethodGet,
		endpoint: "/api/v3/order",
		secType:  secTypeSigned,
	}
	r.setParam("symbol", s.symbol)
	if s.orderID != nil {
		r.setParam("orderId", *s.orderID)
	}
	if s.origClientOrderID != nil {
		r.setParam("origClientOrderId", *s.origClientOrderID)
	}
	data, err := s.c.callAPI(ctx, r, opts...)
	if err != nil {
		return nil, err
	}
	res = new(Order)
	err = json.Unmarshal(data, res)
	if err != nil {
		return nil, err
	}
	return res, nil
}

// Order define order info
type Order struct {
	Symbol                   string          `json:"symbol"`
	OrderID                  int64           `json:"orderId"`
	OrderListId              int64           `json:"orderListId"`
	ClientOrderID            string          `json:"clientOrderId"`
	Price                    string          `json:"price"`
	OrigQuantity             string          `json:"origQty"`
	ExecutedQuantity         string          `json:"executedQty"`
	CummulativeQuoteQuantity string          `json:"cummulativeQuoteQty"`
	Status                   OrderStatusType `json:"status"`
	TimeInForce              TimeInForceType `json:"timeInForce"`
	Type                     OrderType       `json:"type"`
	Side                     SideType        `json:"side"`
	StopPrice                string          `json:"stopPrice"`
	IcebergQuantity          string          `json:"icebergQty"`
	Time                     int64           `json:"time"`
	UpdateTime               int64           `json:"updateTime"`
	IsWorking                bool            `json:"isWorking"`
	IsIsolated               bool            `json:"isIsolated"`
	OrigQuoteOrderQuantity   string          `json:"origQuoteOrderQty"`
}

// ListOrdersService all account orders; active, canceled, or filled
type ListOrdersService struct {
	c         *Client
	symbol    string
	orderID   *int64
	startTime *int64
	endTime   *int64
	limit     *int
}

// Symbol set symbol
func (s *ListOrdersService) Symbol(symbol string) *ListOrdersService {
	s.symbol = symbol
	return s
}

// OrderID set orderID
func (s *ListOrdersService) OrderID(orderID int64) *ListOrdersService {
	s.orderID = &orderID
	return s
}

// StartTime set starttime
func (s *ListOrdersService) StartTime(startTime int64) *ListOrdersService {
	s.startTime = &startTime
	return s
}

// EndTime set endtime
func (s *ListOrdersService) EndTime(endTime int64) *ListOrdersService {
	s.endTime = &endTime
	return s
}

// Limit set limit
func (s *ListOrdersService) Limit(limit int) *ListOrdersService {
	s.limit = &limit
	return s
}

// Do send request
func (s *ListOrdersService) Do(ctx context.Context, opts ...RequestOption) (res []*Order, err error) {
	r := &request{
		method:   http.MethodGet,
		endpoint: "/api/v3/allOrders",
		secType:  secTypeSigned,
	}
	r.setParam("symbol", s.symbol)
	if s.orderID != nil {
		r.setParam("orderId", *s.orderID)
	}
	if s.startTime != nil {
		r.setParam("startTime", *s.startTime)
	}
	if s.endTime != nil {
		r.setParam("endTime", *s.endTime)
	}
	if s.limit != nil {
		r.setParam("limit", *s.limit)
	}
	data, err := s.c.callAPI(ctx, r, opts...)
	if err != nil {
		return []*Order{}, err
	}
	res = make([]*Order, 0)
	err = json.Unmarshal(data, &res)
	if err != nil {
		return []*Order{}, err
	}
	return res, nil
}

// CancelOrderService cancel an order
type CancelOrderService struct {
	c       *Client
	symbol  string
	orderID *int64
}

// Symbol set symbol
func (s *CancelOrderService) Symbol(symbol string) *CancelOrderService {
	s.symbol = symbol
	return s
}

// OrderID set orderID
func (s *CancelOrderService) OrderID(orderID int64) *CancelOrderService {
	s.orderID = &orderID
	return s
}

// Do send request
func (s *CancelOrderService) Do(ctx context.Context, opts ...RequestOption) (res *CancelOrderResponse, err error) {
	r := &request{
		method:   http.MethodDelete,
		endpoint: "/api/order",
	}
	r.setFormParam("symbol", s.symbol)

	if s.orderID != nil {
		r.setFormParam("orderId", *s.orderID)
	}

	data, err := s.c.callAPI(ctx, r, opts...)
	if err != nil {
		return nil, err
	}
	res = new(CancelOrderResponse)
	err = json.Unmarshal(data, res)
	if err != nil {
		return nil, err
	}
	return res, nil
}

// CancelOpenOrdersService cancel all active orders on a symbol. active orders are orders that have been trigger otherwise known as positions
type CancelOpenOrdersService struct {
	c      *Client
	symbol string
}

// Symbol set symbol
func (s *CancelOpenOrdersService) Symbol(symbol string) *CancelOpenOrdersService {
	s.symbol = symbol
	return s
}

// Do send request
func (s *CancelOpenOrdersService) Do(ctx context.Context, opts ...RequestOption) (res *CancelOpenOrdersResponse, err error) {
	r := &request{
		method:   http.MethodDelete,
		endpoint: "/api/openOrders",
	}
	r.setParam("symbol", s.symbol)
	data, err := s.c.callAPI(ctx, r, opts...)
	if err != nil {
		return &CancelOpenOrdersResponse{}, err
	}

	cancelOpenOrdersResponse := new(CancelOpenOrdersResponse)
	err = json.Unmarshal(data, &cancelOpenOrdersResponse)
	if err != nil {
		return &CancelOpenOrdersResponse{}, err
	}

	return cancelOpenOrdersResponse, nil
}

// CancelOpenOrdersResponse defines cancel open orders response.
type CancelOpenOrdersResponse struct {
	Orders []*CancelOrderResponse `json:"orders"`
}

// CancelOrderResponse may be returned included in a CancelOpenOrdersResponse.
type CancelOrderResponse struct {
	OrderID          int64           `json:"order_id"`
	Symbol           string          `json:"symbol"`
	TransactTime     int64           `json:"transact_time"`
	Price            string          `json:"price"`
	OrigQuantity     string          `json:"orig_qty"`
	ExecutedQuantity string          `json:"executed_qty"`
	Status           OrderStatusType `json:"status"`
	TimeInForce      TimeInForceType `json:"time_in_force"`
	Type             OrderType       `json:"type"`
	Side             SideType        `json:"side"`
}
