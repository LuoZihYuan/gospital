package main

import (
	"github.com/gin-gonic/gin"

	_ "github.com/LuoZihYuan/gospital/docs" // Import generated docs
	"github.com/LuoZihYuan/gospital/internal/handlers"
	"github.com/LuoZihYuan/gospital/internal/middleware"
)

// CPU Circuit Breaker Configuration
const (
	cpuOverloadThreshold = 95.0 // CPU percentage to open circuit (reject requests)
	cpuRecoveryThreshold = 85.0 // CPU percentage to close circuit (resume requests)
)

// SetupRouter configures all routes for the API
func SetupRouter(
	rootHandler *handlers.RootHandler,
	patientHandler *handlers.PatientHandler,
	doctorHandler *handlers.DoctorHandler,
	appointmentHandler *handlers.AppointmentHandler,
	departmentHandler *handlers.DepartmentHandler,
	medicalRecordHandler *handlers.MedicalRecordHandler,
	invoiceHandler *handlers.InvoiceHandler,
) *gin.Engine {
	router := gin.Default()

	// Initialize CPU circuit breaker
	cpuCircuitBreaker := middleware.NewCPUCircuitBreaker(cpuOverloadThreshold, cpuRecoveryThreshold)

	// Root endpoints (no middleware - always available)
	router.GET("/health", rootHandler.HealthCheck)
	router.GET("/metrics", rootHandler.Metrics)
	router.GET("/swagger/*any", rootHandler.Swagger)

	// API routes (with Prometheus metrics and CPU circuit breaker protection)
	api := router.Group("/api")
	api.Use(middleware.PrometheusMiddleware())
	api.Use(middleware.CPUCircuitBreakerMiddleware(cpuCircuitBreaker))
	{
		// API v1 routes
		v1 := api.Group("/v1")
		{
			// Patient routes
			patients := v1.Group("/patients")
			{
				patients.POST("", patientHandler.CreatePatient)
				patients.GET("", patientHandler.ListPatients)
				patients.GET("/:patientId", patientHandler.GetPatientByID)
				patients.PUT("/:patientId", patientHandler.UpdatePatient)
				patients.DELETE("/:patientId", patientHandler.DeactivatePatient)
				patients.GET("/:patientId/medical-records", patientHandler.GetPatientMedicalRecords)
				patients.GET("/:patientId/invoices", patientHandler.GetPatientInvoices)
			}

			// Doctor routes
			doctors := v1.Group("/doctors")
			{
				doctors.POST("", doctorHandler.CreateDoctor)
				doctors.GET("", doctorHandler.ListDoctors)
				doctors.GET("/:doctorId", doctorHandler.GetDoctorByID)
				doctors.PUT("/:doctorId", doctorHandler.UpdateDoctor)
				doctors.GET("/:doctorId/availability", doctorHandler.GetDoctorAvailability)
			}

			// Appointment routes
			appointments := v1.Group("/appointments")
			{
				appointments.POST("", appointmentHandler.CreateAppointment)
				appointments.GET("", appointmentHandler.ListAppointments)
				appointments.GET("/:appointmentId", appointmentHandler.GetAppointmentByID)
				appointments.PUT("/:appointmentId", appointmentHandler.UpdateAppointment)
				appointments.DELETE("/:appointmentId", appointmentHandler.CancelAppointment)
			}

			// Department routes
			departments := v1.Group("/departments")
			{
				departments.GET("", departmentHandler.GetAllDepartments)
				departments.GET("/:departmentId", departmentHandler.GetDepartmentByID)
				departments.GET("/:departmentId/doctors", departmentHandler.GetDoctorsInDepartment)
			}

			// Medical Record routes
			medicalRecords := v1.Group("/medical-records")
			{
				medicalRecords.POST("", medicalRecordHandler.CreateMedicalRecord)
				medicalRecords.GET("/:recordId", medicalRecordHandler.GetMedicalRecordByID)
				medicalRecords.PUT("/:recordId", medicalRecordHandler.UpdateMedicalRecord)
			}

			// Billing/Invoice routes
			billing := v1.Group("/billing")
			{
				invoices := billing.Group("/invoices")
				{
					invoices.POST("", invoiceHandler.CreateInvoice)
					invoices.GET("/:invoiceId", invoiceHandler.GetInvoiceByID)
					invoices.PUT("/:invoiceId/payment", invoiceHandler.UpdatePaymentStatus)
				}
			}
		}
	}

	return router
}
