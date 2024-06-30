package metatrader

import (
	"context"
	"encoding/json"
	"net/http"
)

// TickerService show tick info
type TickerService struct {
	c      *Client
	symbol string
}

// Symbol set symbol
func (s *TickerService) Symbol(symbol string) *TickerService {
	s.symbol = symbol
	return s
}

// Do send request
func (s *TickerService) Do(ctx context.Context, opts ...RequestOption) (res *Ticker, err error) {
	r := &request{
		method:   http.MethodGet,
		endpoint: "/api/tick",
	}
	r.setParam("symbol", s.symbol)
	data, err := s.c.callAPI(ctx, r, opts...)
	if err != nil {
		return nil, err
	}

	res = new(Ticker)
	err = json.Unmarshal(data, res)
	if err != nil {
		return nil, err
	}
	return res, nil
}

// TickerResponse define tick info with bid and ask
type Ticker struct {
	Time   *int64 `json:"time"`
	Symbol int64  `json:"symbol"`
	Bid    *Bid   `json:"bid"`
	Ask    *Ask   `json:"ask"`
}

type Bid = float64
type Ask = float64
