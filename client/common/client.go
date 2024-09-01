package common

import (
	"encoding/binary"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

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

	loop: for {
		batch, err1 := c.reader.readNextBatch(c.config.ID)

		b := []byte{}
		for _, bet := range batch {
			b = append(b, bet.toBytes(c.config.ID)...)
		}

		// Discard last separator
		b = b[:len(b)-1]

		if err2 := c.writeAll(b); err2 == nil && len(b) != 0 {
			log.Infof("action: apuestas_enviadas | result: success | cantidad: %d", len(batch))
		} else if err2 != nil {
			log.Infof("action: apuestas_enviadas | result: fail | cantidad: %d | error: %v", len(batch), err2)
			break loop
		}
		
		if err1 != nil || len(b) == 0 {
			break loop
		}
		
		buf := make([]byte, 1)
		select {
		case <- c.signalChan:
			break loop
		default:
			if _, err := c.conn.Read(buf); err != nil {
				break loop
			}
		}
	}

	c.reader.closeFile()
	c.conn.Close()
}

// writeAll Sends message to the server in a short-write-safe manner.
func (c *Client) writeAll(b []byte) error {
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
