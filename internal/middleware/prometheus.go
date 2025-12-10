package middleware

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// Request metrics
	HttpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "path", "status"},
	)

	HttpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10},
		},
		[]string{"method"},
	)

	HttpRequestsInFlight = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "http_requests_in_flight",
			Help: "Current number of HTTP requests being processed",
		},
	)

	// CPU Circuit breaker metrics
	CpuCircuitBreakerState = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "cpu_circuit_breaker_state",
			Help: "CPU circuit breaker state (0=closed, 1=open)",
		},
	)

	CpuCircuitBreakerRejections = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "cpu_circuit_breaker_rejections_total",
			Help: "Total number of requests rejected by CPU circuit breaker",
		},
	)

	CpuUsagePercent = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "cpu_usage_percent",
			Help: "Current CPU usage percentage",
		},
	)

	// Database circuit breaker metrics
	MysqlCircuitBreakerState = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "mysql_circuit_breaker_state",
			Help: "MySQL circuit breaker state (0=closed, 1=half-open, 2=open)",
		},
	)

	DynamodbCircuitBreakerState = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "dynamodb_circuit_breaker_state",
			Help: "DynamoDB circuit breaker state (0=closed, 1=half-open, 2=open)",
		},
	)
)

// PrometheusMiddleware collects HTTP metrics
func PrometheusMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Skip metrics endpoint
		if c.Request.URL.Path == "/metrics" {
			c.Next()
			return
		}

		HttpRequestsInFlight.Inc()
		start := time.Now()

		c.Next()

		duration := time.Since(start).Seconds()
		status := strconv.Itoa(c.Writer.Status())
		method := c.Request.Method
		path := normalizePath(c.FullPath())

		HttpRequestsTotal.WithLabelValues(method, path, status).Inc()
		HttpRequestDuration.WithLabelValues(method).Observe(duration)
		HttpRequestsInFlight.Dec()
	}
}

// normalizePath returns a normalized path for metrics labels
func normalizePath(path string) string {
	if path == "" {
		return "unknown"
	}
	return path
}

// UpdateCPUCircuitBreakerMetrics updates CPU circuit breaker metrics
func UpdateCPUCircuitBreakerMetrics(isOpen bool, currentCPU float64) {
	if isOpen {
		CpuCircuitBreakerState.Set(1)
	} else {
		CpuCircuitBreakerState.Set(0)
	}
	CpuUsagePercent.Set(currentCPU)
}

// IncrementCPURejections increments the CPU circuit breaker rejection counter
func IncrementCPURejections() {
	CpuCircuitBreakerRejections.Inc()
}

// CircuitBreakerStateToInt converts gobreaker state to int for Prometheus
// 0=closed, 1=half-open, 2=open
func CircuitBreakerStateToInt(stateName string) float64 {
	switch stateName {
	case "closed":
		return 0
	case "half-open":
		return 1
	case "open":
		return 2
	default:
		return 0
	}
}

// UpdateMySQLCircuitBreakerState updates MySQL circuit breaker state metric
func UpdateMySQLCircuitBreakerState(stateName string) {
	MysqlCircuitBreakerState.Set(CircuitBreakerStateToInt(stateName))
}

// UpdateDynamoDBCircuitBreakerState updates DynamoDB circuit breaker state metric
func UpdateDynamoDBCircuitBreakerState(stateName string) {
	DynamodbCircuitBreakerState.Set(CircuitBreakerStateToInt(stateName))
}
