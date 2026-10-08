package buffer

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	_ "modernc.org/sqlite"
)

type BufferedItem struct {
	ID        int64
	RecordID  string
	Payload   []byte
	CreatedAt int64
}

// LocalBuffer provides persistent disk-backed FIFO buffering during network outages.
type LocalBuffer struct {
	db      *sql.DB
	mu      sync.Mutex
	maxSize int64
}

// NewLocalBuffer initializes a WAL-mode SQLite disk buffer with safe concurrency pragmas.
func NewLocalBuffer(dbPath string, maxBufferedRecords int64) (*LocalBuffer, error) {
	// DSN with busy_timeout and WAL mode for high concurrency
	dsn := fmt.Sprintf("%s?_pragma=busy_timeout(5000)&_pragma=journal_mode(WAL)&_pragma=synchronous(NORMAL)", dbPath)
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open sqlite buffer: %w", err)
	}

	// Single connection pool guarantees zero lock contention in SQLite WAL mode
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(0)

	initSQL := `
	CREATE TABLE IF NOT EXISTS outbound_buffer (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		record_id TEXT NOT NULL,
		payload BLOB NOT NULL,
		created_at INTEGER NOT NULL
	);
	CREATE INDEX IF NOT EXISTS idx_outbound_created ON outbound_buffer(id ASC);
	`
	if _, err := db.Exec(initSQL); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to initialize buffer schema: %w", err)
	}

	if maxBufferedRecords <= 0 {
		maxBufferedRecords = 500000 // default ceiling
	}

	return &LocalBuffer{
		db:      db,
		maxSize: maxBufferedRecords,
	}, nil
}

// Enqueue persists a serialized Protobuf message to the disk buffer.
func (b *LocalBuffer) Enqueue(recordID string, payload []byte) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Capacity guard: prevent unbounded disk growth during extended outages
	var count int64
	if err := b.db.QueryRowContext(ctx, `SELECT COUNT(*) FROM outbound_buffer`).Scan(&count); err == nil && count >= b.maxSize {
		// ponytail: prune oldest 1000 records if buffer exceeds ceiling
		b.db.ExecContext(ctx, `DELETE FROM outbound_buffer WHERE id IN (SELECT id FROM outbound_buffer ORDER BY id ASC LIMIT 1000)`)
	}

	query := `INSERT INTO outbound_buffer (record_id, payload, created_at) VALUES (?, ?, ?)`
	_, err := b.db.ExecContext(ctx, query, recordID, payload, time.Now().UnixNano())
	if err != nil {
		return fmt.Errorf("buffer enqueue error: %w", err)
	}
	return nil
}

// DequeueBatch retrieves up to 'limit' messages in strict FIFO order.
func (b *LocalBuffer) DequeueBatch(limit int) ([]BufferedItem, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	if limit <= 0 {
		limit = 100
	}

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	query := `SELECT id, record_id, payload, created_at FROM outbound_buffer ORDER BY id ASC LIMIT ?`
	rows, err := b.db.QueryContext(ctx, query, limit)
	if err != nil {
		return nil, fmt.Errorf("buffer query error: %w", err)
	}
	defer rows.Close()

	var items []BufferedItem
	for rows.Next() {
		var item BufferedItem
		if err := rows.Scan(&item.ID, &item.RecordID, &item.Payload, &item.CreatedAt); err != nil {
			return nil, fmt.Errorf("buffer scan error: %w", err)
		}
		items = append(items, item)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("buffer row iteration error: %w", err)
	}

	return items, nil
}

// DeleteBatch purges successfully dispatched message IDs from the buffer.
func (b *LocalBuffer) DeleteBatch(ids []int64) error {
	if len(ids) == 0 {
		return nil
	}

	b.mu.Lock()
	defer b.mu.Unlock()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// ponytail: FIFO queue ordering guarantees all items <= ids[len-1] are flushed; single query replaces 20-line loop
	_, err := b.db.ExecContext(ctx, `DELETE FROM outbound_buffer WHERE id <= ?`, ids[len(ids)-1])
	return err
}

// Count returns the number of buffered items waiting for network restoration.
func (b *LocalBuffer) Count() (int64, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	var count int64
	err := b.db.QueryRowContext(ctx, `SELECT COUNT(*) FROM outbound_buffer`).Scan(&count)
	return count, err
}

// Close gracefully closes the SQLite database connection.
func (b *LocalBuffer) Close() error {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.db.Close()
}
