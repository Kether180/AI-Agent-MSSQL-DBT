package metrics

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	// HTTP request metrics
	httpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "datamigrate_http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	httpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "datamigrate_http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint"},
	)

	httpRequestsInFlight = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "datamigrate_http_requests_in_flight",
			Help: "Number of HTTP requests currently being processed",
		},
	)

	// Migration metrics
	MigrationsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "datamigrate_migrations_total",
			Help: "Total number of migrations by status",
		},
		[]string{"status"},
	)

	MigrationsInProgress = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "datamigrate_migrations_in_progress",
			Help: "Number of migrations currently in progress",
		},
	)

	MigrationDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "datamigrate_migration_duration_seconds",
			Help:    "Migration duration in seconds",
			Buckets: []float64{1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600},
		},
		[]string{"source_type"},
	)

	// Database metrics
	DBConnectionsActive = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "datamigrate_db_connections_active",
			Help: "Number of active database connections",
		},
	)

	DBQueryDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "datamigrate_db_query_duration_seconds",
			Help:    "Database query duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"operation"},
	)

	// AI Service metrics
	AIRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "datamigrate_ai_requests_total",
			Help: "Total number of AI service requests",
		},
		[]string{"operation", "status"},
	)

	AIRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "datamigrate_ai_request_duration_seconds",
			Help:    "AI service request duration in seconds",
			Buckets: []float64{0.1, 0.5, 1, 2, 5, 10, 30, 60},
		},
		[]string{"operation"},
	)

	// Security metrics
	SecurityEventsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "datamigrate_security_events_total",
			Help: "Total number of security events",
		},
		[]string{"event_type", "severity"},
	)

	AuthAttemptsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "datamigrate_auth_attempts_total",
			Help: "Total number of authentication attempts",
		},
		[]string{"result"},
	)
)

// PrometheusMiddleware returns a Gin middleware for collecting HTTP metrics
func PrometheusMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Skip metrics endpoint itself
		if c.Request.URL.Path == "/metrics" {
			c.Next()
			return
		}

		httpRequestsInFlight.Inc()
		start := time.Now()

		c.Next()

		httpRequestsInFlight.Dec()
		duration := time.Since(start).Seconds()

		status := strconv.Itoa(c.Writer.Status())
		endpoint := c.FullPath()
		if endpoint == "" {
			endpoint = "unknown"
		}

		httpRequestsTotal.WithLabelValues(c.Request.Method, endpoint, status).Inc()
		httpRequestDuration.WithLabelValues(c.Request.Method, endpoint).Observe(duration)
	}
}

// Handler returns the Prometheus HTTP handler for the /metrics endpoint
func Handler() gin.HandlerFunc {
	h := promhttp.Handler()
	return func(c *gin.Context) {
		h.ServeHTTP(c.Writer, c.Request)
	}
}

// RecordMigrationStarted records when a migration starts
func RecordMigrationStarted() {
	MigrationsInProgress.Inc()
	MigrationsTotal.WithLabelValues("started").Inc()
}

// RecordMigrationCompleted records when a migration completes
func RecordMigrationCompleted(sourceType string, duration time.Duration) {
	MigrationsInProgress.Dec()
	MigrationsTotal.WithLabelValues("completed").Inc()
	MigrationDuration.WithLabelValues(sourceType).Observe(duration.Seconds())
}

// RecordMigrationFailed records when a migration fails
func RecordMigrationFailed() {
	MigrationsInProgress.Dec()
	MigrationsTotal.WithLabelValues("failed").Inc()
}

// RecordAuthAttempt records an authentication attempt
func RecordAuthAttempt(success bool) {
	if success {
		AuthAttemptsTotal.WithLabelValues("success").Inc()
	} else {
		AuthAttemptsTotal.WithLabelValues("failure").Inc()
	}
}

// RecordSecurityEvent records a security event
func RecordSecurityEvent(eventType, severity string) {
	SecurityEventsTotal.WithLabelValues(eventType, severity).Inc()
}

// RecordAIRequest records an AI service request
func RecordAIRequest(operation string, success bool, duration time.Duration) {
	status := "success"
	if !success {
		status = "failure"
	}
	AIRequestsTotal.WithLabelValues(operation, status).Inc()
	AIRequestDuration.WithLabelValues(operation).Observe(duration.Seconds())
}
