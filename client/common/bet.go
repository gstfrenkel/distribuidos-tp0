package common

import (
	"fmt"
	"os"
)

// bet Representation of a client's bet.
type bet struct {
	name      string
	surname   string
	id        string
	birthdate string
	number    string
}

// newBet Creates a new bet out of envs.
func newBet() bet {
	return bet{
		name:      os.Getenv("NOMBRE"),
		surname:   os.Getenv("APELLIDO"),
		id:        os.Getenv("DOCUMENTO"),
		birthdate: os.Getenv("NACIMIENTO"),
		number:    os.Getenv("NUMERO"),
	}
}

// toBytes parses a client's bet into a slice of bytes.
func (b bet) toBytes() []byte {
	return []byte(fmt.Sprintf("%s,%s,%s,%s,%s;", b.name, b.surname, b.id, b.birthdate, b.number))
}
