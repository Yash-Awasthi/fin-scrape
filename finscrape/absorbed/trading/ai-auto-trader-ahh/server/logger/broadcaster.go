package logger

import (
	"encoding/json"
	"sync"
	"time"
)

type LogMessage struct {
	Timestamp time.Time `json:"timestamp"`
	Message   string    `json:"message"`
}

type Broadcaster struct {
	clients    map[chan LogMessage]bool
	buffer     []LogMessage
	bufferSize int
	mu         sync.RWMutex
}

// Global instance
var globalBroadcaster *Broadcaster
var once sync.Once

func GetBroadcaster() *Broadcaster {
	once.Do(func() {
		globalBroadcaster = &Broadcaster{
			clients:    make(map[chan LogMessage]bool),
			buffer:     make([]LogMessage, 0, 1000), // Keep last 1000 lines
			bufferSize: 1000,
		}
	})
	return globalBroadcaster
}

func (b *Broadcaster) Write(p []byte) (n int, err error) {
	// Strip trailing newline if present, as UI usually handles line breaks
	// But preserving them is also fine. Let's keep it simple.
	msgStr := string(p)

	msg := LogMessage{
		Timestamp: time.Now(),
		Message:   msgStr,
	}

	b.mu.Lock()
	defer b.mu.Unlock()

	// Append to buffer
	if len(b.buffer) >= b.bufferSize {
		b.buffer = b.buffer[1:]
	}
	b.buffer = append(b.buffer, msg)

	// Broadcast to clients
	for ch := range b.clients {
		select {
		case ch <- msg:
		default:
			// Drop message if client is too slow to avoid blocking the logger
		}
	}

	return len(p), nil
}

func (b *Broadcaster) Subscribe() (chan LogMessage, []LogMessage) {
	b.mu.Lock()
	defer b.mu.Unlock()

	ch := make(chan LogMessage, 200)
	b.clients[ch] = true

	// Return channel and current history
	history := make([]LogMessage, len(b.buffer))
	copy(history, b.buffer)

	return ch, history
}

func (b *Broadcaster) Unsubscribe(ch chan LogMessage) {
	b.mu.Lock()
	defer b.mu.Unlock()

	if _, ok := b.clients[ch]; ok {
		delete(b.clients, ch)
		close(ch)
	}
}

// For SSE formatting
func (m LogMessage) ToSSE() string {
	data, _ := json.Marshal(m)
	return "data: " + string(data) + "\n\n"
}
