package common

import (
	"bytes"
	"fmt"
	"math"
)

// helpers.go
// AmountToLotSize converts an amount to a lot sized amount
func AmountToLotSize(lot float64, precision int, amount float64) float64 {
	return math.Trunc(math.Floor(amount/lot)*lot*math.Pow10(precision)) / math.Pow10(precision)
}

// ToJSONList convert v to json list if v is a map
func ToJSONList(v []byte) []byte {
	if len(v) > 0 && v[0] == '{' {
		var b bytes.Buffer
		b.Write([]byte("["))
		b.Write(v)
		b.Write([]byte("]"))
		return b.Bytes()
	}
	return v
}

// errors.go
// APIError define API error when response status is 4xx or 5xx
type APIError struct {
	Code    int64  `json:"code"`
	Message string `json:"msg"`
}

// Error return error code and message
func (e APIError) Error() string {
	return fmt.Sprintf("<APIError> code=%d, msg=%s", e.Code, e.Message)
}

// IsAPIError check if e is an API error
func IsAPIError(e error) bool {
	_, ok := e.(*APIError)
	return ok
}
