package middleware

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/LuoZihYuan/gospital/internal/models"
)

// Bulkhead represents a concurrency limiter
type Bulkhead struct {
	semaphore chan struct{}
}

// NewBulkhead creates a new bulkhead with maximum concurrent requests
func NewBulkhead(maxConcurrent int) *Bulkhead {
	return &Bulkhead{
		semaphore: make(chan struct{}, maxConcurrent),
	}
}

// Execute attempts to execute the operation within bulkhead limits
func (b *Bulkhead) Execute(c *gin.Context, next func()) {
	select {
	case b.semaphore <- struct{}{}: // Acquire slot
		defer func() { <-b.semaphore }() // Release slot when done
		next()
	default: // No slots available
		c.JSON(http.StatusServiceUnavailable, models.ErrorResponse{
			Error: models.ErrorDetail{
				Code:    "SERVICE_UNAVAILABLE",
				Message: "Service temporarily unavailable due to high load",
			},
		})
		c.Abort()
	}
}

var (
	// InternalBulkhead for staff operations (medical records, billing)
	InternalBulkhead = NewBulkhead(50)

	// ExternalBulkhead for public operations (appointments, patient portal)
	ExternalBulkhead = NewBulkhead(100)
)

// BulkheadMiddleware applies appropriate bulkhead based on request type
func BulkheadMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Determine if request is internal or external based on header
		if isInternalRequest(c) {
			InternalBulkhead.Execute(c, func() {
				c.Next()
			})
		} else {
			ExternalBulkhead.Execute(c, func() {
				c.Next()
			})
		}
	}
}

// isInternalRequest determines if the request is from internal staff
func isInternalRequest(c *gin.Context) bool {
	// Check X-User-Type header
	// "staff" = internal (doctors, nurses, admin staff)
	// "public" or missing = external (patients, general public)
	userType := c.GetHeader("X-User-Type")
	return userType == "staff"
}
