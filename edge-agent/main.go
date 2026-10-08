package main

import (
	"context"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"aegistwin/edge-agent/pkg/broker"
	"aegistwin/edge-agent/pkg/buffer"
	"aegistwin/edge-agent/pkg/pipeline"
	pb "aegistwin/edge-agent/proto"
)

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func main() {
	log.Println("[AegisTwin Edge Ingestion Agent] Initializing...")

	natsURL := getEnv("NATS_URL", "nats://localhost:4222")
	dbPath := getEnv("BUFFER_DB_PATH", "./edge_buffer.db")
	topicPrefix := getEnv("TOPIC_PREFIX", "aegistwin.telemetry")
	port := getEnv("PORT", "9090")

	// 1. Initialize Event Broker Connector
	eventBroker, err := broker.NewNatsBroker(natsURL)
	if err != nil {
		log.Fatalf("Fatal broker initialization: %v", err)
	}
	defer eventBroker.Close()

	// 2. Initialize Resilient Local Disk Buffer
	localBuffer, err := buffer.NewLocalBuffer(dbPath, 500000)
	if err != nil {
		log.Fatalf("Fatal buffer initialization: %v", err)
	}
	defer localBuffer.Close()

	// 3. Initialize Ingestion Pipeline Workers
	pipe := pipeline.NewTelemetryPipeline(eventBroker, localBuffer, topicPrefix, 100000, 32)
	defer pipe.Stop()

	// 4. HTTP High-Throughput Ingestion Handlers
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		bufCount, _ := localBuffer.Count()
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":           "OPERATIONAL",
			"broker_connected": eventBroker.IsConnected(),
			"buffered_records": bufCount,
		})
	})

	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(pipe.Metrics())
	})

	handleIngest := func(protocol pb.ProtocolType) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			if r.Method != http.MethodPost {
				http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
				return
			}

			// Read payload with size limit (1MB max per telemetry packet)
			body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, 1024*1024))
			if err != nil {
				http.Error(w, "Payload too large or unreadable", http.StatusBadRequest)
				return
			}
			defer r.Body.Close()

			topic := r.Header.Get("X-Telemetry-Topic")
			if topic == "" {
				topic = r.URL.Query().Get("topic")
			}

			if err := pipe.Ingest(protocol, topic, body); err != nil {
				http.Error(w, err.Error(), http.StatusServiceUnavailable)
				return
			}

			w.WriteHeader(http.StatusAccepted)
			w.Write([]byte(`{"status":"ACCEPTED"}`))
		}
	}

	mux.HandleFunc("/ingest/opcua", handleIngest(pb.ProtocolType_PROTOCOL_OPC_UA))
	mux.HandleFunc("/ingest/mqtt", handleIngest(pb.ProtocolType_PROTOCOL_MQTT))
	mux.HandleFunc("/ingest/syslog", handleIngest(pb.ProtocolType_PROTOCOL_SYSLOG))

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 5 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("[Agent] Edge Ingestion Server listening on :%s", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("HTTP server error: %v", err)
		}
	}()

	// Graceful shutdown on signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	log.Println("[Agent] Shutting down edge ingestion agent gracefully...")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	server.Shutdown(ctx)
	log.Println("[Agent] Shutdown complete.")
}
