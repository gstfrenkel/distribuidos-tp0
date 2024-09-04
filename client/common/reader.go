package common

import (
	"encoding/csv"
	"os"
)

const (
	endSeparatorLength = 1
	batchLength = 4
	maxPayloadLength = 8192
	maxBatchLength = maxPayloadLength + endSeparatorLength - batchLength
)

type reader struct {
	file         *os.File
	reader       *csv.Reader
	maxBatchSize int
	extraBet     *bet
}

// NewCSVReader Initializes a new CSVReader
func newCSVReader(filePath string, maxBatchSize int) (*reader, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	return &reader{file: file, reader: csv.NewReader(file), maxBatchSize: maxBatchSize}, nil
}

// readNextBatch Reads a series of new bets until either maxBatchLength or r.maxBatchSize are reached.
func (r *reader) readNextBatch() ([]bet, error) {
	bets := []bet{}
	batchSize := 0

	if r.extraBet != nil {
		bets = append(bets, *r.extraBet)
		batchSize += len(r.extraBet.toBytes())
	}

	for len(bets) < r.maxBatchSize {
		newBet, err := r.readNextBet()
		if err != nil {
			return bets, err
		}

		if batchSize + len(newBet.toBytes()) > maxBatchLength {
			r.extraBet = newBet
			break
		}

		batchSize += len(newBet.toBytes())
		bets = append(bets, *newBet)
	}

	return bets, nil
}

// readNextBet Reads a new bet from r.reader.
func (r *reader) readNextBet() (*bet, error) {
	bet, err := r.reader.Read()
	if err != nil {
		return nil, err
	}
	newBet := newBet(bet[0], bet[1], bet[2], bet[3], bet[4])
	return &newBet, nil
}

func (r *reader) closeFile() {
	r.file.Close()
}