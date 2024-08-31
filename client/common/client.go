package common

import (
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
}

// Client Entity that encapsulates how
type Client struct {
	config     ClientConfig
	signalChan chan os.Signal
	conn       net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	signalChan := make(chan os.Signal, 2)
	signal.Notify(signalChan, syscall.SIGTERM, syscall.SIGINT)

	return &Client{
		config:     config,
		signalChan: signalChan,
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

	bet := newBet()

	err := c.writeAll(bet.toBytes(c.config.ID))
	if err == nil {
		log.Infof("action: apuesta_enviada | result: success | dni: %s | numero: %s", bet.id, bet.number)
	} else {
		log.Errorf("action: apuesta_enviada | result: fail | dni: %s | numero: %s | error: %v", bet.id, bet.number, err)
	}
}

// writeAll Sends message to the server in a short-write-safe manner.
func (c *Client) writeAll(b []byte) error {
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
