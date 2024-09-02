package common

import (
	"fmt"
)

// bet Representation of a client's bet.
type bet struct {
	name      string
	surname   string
	id        string
	birthdate string
	number    string
}

// newBet Creates a new bet.
func newBet(name string, surname string, id string, birthdate string, number string) bet {
	return bet{
		name:      name,
		surname:   surname,
		id:        id,
		birthdate: birthdate,
		number:    number,
	}
}

// toBytes parses a client's bet into a slice of bytes.
func (b bet) toBytes() []byte {
	return []byte(fmt.Sprintf("%s,%s,%s,%s,%s;", b.name, b.surname, b.id, b.birthdate, b.number))
}
