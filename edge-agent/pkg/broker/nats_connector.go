package broker

import (
	"errors"
	"log"
	"sync/atomic"
	"time"

	"github.com/nats-io/nats.go"
)

var (
	ErrBrokerDisconnected = errors.New("event broker is currently disconnected")
)

type EventBroker interface {
	Publish(subject string, data []byte) error
	IsConnected() bool
	ReconnectNotify() <-chan struct{}
	Close()
}

type NatsBroker struct {
	nc            *nats.Conn
	connected     int32 // atomic boolean
	reconnectChan chan struct{}
}

// NewNatsBroker connects to the NATS event bus with resilient auto-reconnection.
func NewNatsBroker(urls string) (*NatsBroker, error) {
	b := &NatsBroker{
		reconnectChan: make(chan struct{}, 1),
	}

	opts := []nats.Option{
		nats.MaxReconnects(-1), // Reconnect indefinitely
		nats.ReconnectWait(1 * time.Second),
		nats.PingInterval(5 * time.Second),
		nats.MaxPingsOutstanding(3),
		nats.DisconnectErrHandler(func(c *nats.Conn, err error) {
			atomic.StoreInt32(&b.connected, 0)
			log.Printf("[Broker] Disconnected from NATS: %v", err)
		}),
		nats.ReconnectHandler(func(c *nats.Conn) {
			atomic.StoreInt32(&b.connected, 1)
			log.Printf("[Broker] Reconnected to NATS at %s", c.ConnectedUrl())
			// Notify flusher non-blockingly
			select {
			case b.reconnectChan <- struct{}{}:
			default:
			}
		}),
		nats.ClosedHandler(func(c *nats.Conn) {
			atomic.StoreInt32(&b.connected, 0)
			log.Printf("[Broker] NATS connection closed permanently")
		}),
	}

	nc, err := nats.Connect(urls, opts...)
	if err != nil {
		// ponytail: allow agent to boot even if broker is initially down; edge agent queues to local buffer
		log.Printf("[Broker] Initial connection failed (%v). Operating in offline-buffered mode.", err)
		atomic.StoreInt32(&b.connected, 0)
		return b, nil
	}

	b.nc = nc
	atomic.StoreInt32(&b.connected, 1)
	log.Printf("[Broker] Successfully connected to NATS at %s", nc.ConnectedUrl())
	return b, nil
}

// Publish pushes raw bytes to the specified subject if broker is connected.
func (b *NatsBroker) Publish(subject string, data []byte) error {
	if !b.IsConnected() || b.nc == nil {
		return ErrBrokerDisconnected
	}
	return b.nc.Publish(subject, data)
}

// IsConnected returns whether the broker connection is currently healthy.
func (b *NatsBroker) IsConnected() bool {
	return atomic.LoadInt32(&b.connected) == 1
}

// ReconnectNotify returns a channel signaling successful reconnection.
func (b *NatsBroker) ReconnectNotify() <-chan struct{} {
	return b.reconnectChan
}

// Close gracefully terminates the broker connection.
func (b *NatsBroker) Close() {
	atomic.StoreInt32(&b.connected, 0)
	if b.nc != nil {
		b.nc.Drain()
	}
}
