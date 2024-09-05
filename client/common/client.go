package common

import (
	"encoding/binary"
	"errors"
	"net"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

const headerFinished = 0

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	MaxBatchSize  int
}

// Client Entity that encapsulates how
type Client struct {
	config     ClientConfig
	signalChan chan os.Signal
	conn       net.Conn
	reader     *reader
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	signalChan := make(chan os.Signal, 2)
	signal.Notify(signalChan, syscall.SIGTERM, syscall.SIGINT)

	reader, err := newCSVReader("./agency.csv", config.MaxBatchSize)
	if err != nil {
		log.Criticalf("action: read_file | result: fail | error: %v", err)
		return nil
	}

	return &Client{
		config:     config,
		signalChan: signalChan,
		reader:     reader,
	}
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	c.createClientSocket()

	defer c.reader.closeFile()
	defer c.conn.Close()

	clientID, err := strconv.Atoi(c.config.ID)
	if err != nil || clientID < 0 || clientID > 255 {
		log.Errorf("action: parse client ID: %d | result: fail | error: %v", clientID, err)
		return
	}

	if err := binary.Write(c.conn, binary.BigEndian, byte(clientID)); err != nil {
		log.Errorf("action: send client ID | result: fail | error: %v", err)
		return
	}

	if err := c.sendBets(); err != nil {
		log.Errorf("action: send bets | result: fail | error: %v", err)
		return
	}

	if err := binary.Write(c.conn, binary.BigEndian, int16(headerFinished)); err != nil {
		log.Errorf("action: send finish header | result: fail | error: %v", err)
		return
	}

	if err := c.recvResults(); err != nil {
		log.Errorf("action: receive_results | result: fail | error: %v", err)
	}
}

// sendBets Send the client's bets to the server.
func (c *Client) sendBets() error {
	for {
		batch, err1 := c.reader.readNextBatch()

		b := []byte{}
		for _, bet := range batch {
			b = append(b, bet.toBytes()...)
		}

		// Discard last separator and check if there is any info to send
		b = b[:len(b)-1]
		if len(b) == 0 {
			return nil
		}

		if err2 := c.writeAll(b); err2 == nil && len(b) != 0 {
			log.Infof("action: apuestas_enviadas | result: success | cantidad: %d", len(batch))
		} else if err2 != nil {
			log.Infof("action: apuestas_enviadas | result: fail | cantidad: %d | error: %v", len(batch), err2)
			return err2
		}
		
		buf := make([]byte, 1)
		select {
		case <- c.signalChan:
			return errors.New("exit signal received")
		default:
			if _, err := c.conn.Read(buf); err != nil {
				return err
			}
		}

		// Check if reached EOF
		if err1 != nil {
			return nil
		}
	}
}

// recvResults receives the client's bet winners.
func (c* Client) recvResults() error {
	b := make([]byte, 1024)
	bytesRead, err := c.readAll(b, 2)
	if err != nil {
		return err
	}

	winnersLength := int(binary.BigEndian.Uint16(b[0:2]))
	bytesRead -= 2
	b = b[2:]

	if winnersLength > 1024 {
		bAux := make([]byte, winnersLength)
		bAux = append(bAux, b...)
		b = bAux
	}

	if bytesRead < winnersLength {
		if _, err := c.readAll(b[len(b):], winnersLength); err != nil {
			return err
		}
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", winnersLength / 4)

	_, err = c.conn.Write([]byte("0"))
	return err
}

// writeAll Sends a message to the server in a short-write-safe manner.
func (c *Client) writeAll(b []byte) error {
	if len(b) == 0 {
		return nil
	}

	if err := binary.Write(c.conn, binary.BigEndian, int16(len(b))); err != nil {
		return err
	}

	written := 0
	for written < len(b) {
		n, err := c.conn.Write(b[written:])
		if err != nil {
			return err
		}
		written += n
	}
	return nil
}

// readAll Receives a message from the server in a short-read-safe manner.
func (c *Client) readAll(b []byte, bytesToRead int) (int, error) {
	bytesRead := 0

	for bytesRead < bytesToRead {
		n, err := c.conn.Read(b[bytesRead:])
		if err != nil {
			return bytesRead, err
		}
		bytesRead += n
	}

	return bytesRead, nil
}
