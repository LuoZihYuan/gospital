"""
Locust load testing for Gospital API

4 Test Scenarios:
1. InternalUser - Tests inward-facing APIs (staff operations)
2. ExternalUser - Tests outward-facing APIs (public operations)
3. DynamoDBUser - Tests DynamoDB operations (medical records, invoices)
4. MySQLUser - Tests MySQL operations (patients, doctors, appointments)

Run with:
    locust -f locustfile.py --host=http://your-alb-url
"""

from locust import HttpUser, TaskSet, task, between
import random
from datetime import datetime, timedelta


# Shared test data
TEST_PATIENT_IDS = []
TEST_DOCTOR_IDS = []
TEST_APPOINTMENT_IDS = []
TEST_DEPARTMENT_IDS = ["DEPT-001", "DEPT-002", "DEPT-003"]
TEST_RECORD_IDS = []
TEST_INVOICE_IDS = []


def generate_patient_data():
  """Generate random patient data"""
  return {
    "firstName": f"Patient{random.randint(1000, 9999)}",
    "lastName": f"Test{random.randint(1000, 9999)}",
    "dateOfBirth": "1985-03-15",
    "gender": random.choice(["male", "female", "other"]),
    "email": f"patient{random.randint(1000, 9999)}@test.com",
    "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
    "bloodType": random.choice(["A+", "B+", "O+", "AB+", "A-", "B-", "O-", "AB-"]),
  }


def generate_doctor_data():
  """Generate random doctor data"""
  specialties = [
    "Cardiology",
    "Pediatrics",
    "Orthopedics",
    "Emergency Medicine",
    "Oncology",
  ]
  return {
    "firstName": f"Dr{random.randint(1000, 9999)}",
    "lastName": f"Test{random.randint(1000, 9999)}",
    "email": f"doctor{random.randint(1000, 9999)}@hospital.com",
    "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
    "specialty": random.choice(specialties),
    "licenseNumber": f"MD{random.randint(100000, 999999)}",
    "departmentId": random.choice(TEST_DEPARTMENT_IDS),
    "yearsOfExperience": random.randint(1, 30),
  }


def generate_appointment_data(patient_id, doctor_id):
  """Generate random appointment data"""
  date = datetime.now() + timedelta(days=random.randint(1, 30))
  hour = random.randint(8, 16)
  return {
    "patientId": patient_id,
    "doctorId": doctor_id,
    "appointmentDate": date.strftime("%Y-%m-%d"),
    "startTime": f"{hour:02d}:00:00",
    "endTime": f"{hour:02d}:30:00",
    "reason": "Regular checkup",
  }


def generate_medical_record_data(patient_id, doctor_id):
  """Generate random medical record data"""
  return {
    "patientId": patient_id,
    "doctorId": doctor_id,
    "visitDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "chiefComplaint": "Routine examination",
    "diagnosis": "Healthy",
    "symptoms": ["No symptoms"],
    "treatment": "Continue regular exercise",
    "vitalSigns": {"bloodPressure": "120/80", "heartRate": 72, "temperature": 98.6},
  }


def generate_invoice_data(patient_id):
  """Generate random invoice data"""
  today = datetime.now().strftime("%Y-%m-%d")
  due = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
  return {
    "patientId": patient_id,
    "invoiceDate": today,
    "dueDate": due,
    "items": [
      {
        "description": "Consultation",
        "quantity": 1,
        "unitPrice": 150.00,
        "amount": 150.00,
      },
      {"description": "Lab Tests", "quantity": 2, "unitPrice": 75.00, "amount": 150.00},
    ],
  }


class InternalTasks(TaskSet):
  """Tasks for internal/staff users - medical records and billing"""

  @task(3)
  def create_medical_record(self):
    """Create a medical record"""
    if not TEST_PATIENT_IDS or not TEST_DOCTOR_IDS:
      return

    data = generate_medical_record_data(
      random.choice(TEST_PATIENT_IDS), random.choice(TEST_DOCTOR_IDS)
    )

    with self.client.post(
      "/api/v1/medical-records",
      json=data,
      headers={"X-User-Type": "staff"},
      catch_response=True,
    ) as response:
      if response.status_code == 201:
        record = response.json()
        TEST_RECORD_IDS.append(record.get("recordId"))
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(2)
  def get_medical_record(self):
    """Get a medical record by ID"""
    if not TEST_RECORD_IDS:
      return

    record_id = random.choice(TEST_RECORD_IDS)
    self.client.get(
      f"/api/v1/medical-records/{record_id}",
      headers={"X-User-Type": "staff"},
      name="/api/v1/medical-records/[recordId]",
    )

  @task(3)
  def create_invoice(self):
    """Create an invoice"""
    if not TEST_PATIENT_IDS:
      return

    data = generate_invoice_data(random.choice(TEST_PATIENT_IDS))

    with self.client.post(
      "/api/v1/billing/invoices",
      json=data,
      headers={"X-User-Type": "staff"},
      catch_response=True,
    ) as response:
      if response.status_code == 201:
        invoice = response.json()
        TEST_INVOICE_IDS.append(invoice.get("invoiceId"))
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(2)
  def get_invoice(self):
    """Get an invoice by ID"""
    if not TEST_INVOICE_IDS:
      return

    invoice_id = random.choice(TEST_INVOICE_IDS)
    self.client.get(
      f"/api/v1/billing/invoices/{invoice_id}",
      headers={"X-User-Type": "staff"},
      name="/api/v1/billing/invoices/[invoiceId]",
    )

  @task(1)
  def update_payment_status(self):
    """Update invoice payment status"""
    if not TEST_INVOICE_IDS:
      return

    invoice_id = random.choice(TEST_INVOICE_IDS)
    data = {
      "paymentStatus": random.choice(["paid", "pending", "overdue"]),
      "paymentMethod": "credit_card",
      "amountPaid": 300.00,
    }

    self.client.put(
      f"/api/v1/billing/invoices/{invoice_id}/payment",
      json=data,
      headers={"X-User-Type": "staff"},
      name="/api/v1/billing/invoices/[invoiceId]/payment",
    )


class ExternalTasks(TaskSet):
  """Tasks for external/public users - patient portal and appointments"""

  @task(3)
  def create_patient(self):
    """Register a new patient"""
    data = generate_patient_data()

    with self.client.post(
      "/api/v1/patients",
      json=data,
      headers={"X-User-Type": "public"},
      catch_response=True,
    ) as response:
      if response.status_code == 201:
        patient = response.json()
        TEST_PATIENT_IDS.append(patient.get("patientId"))
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(5)
  def list_patients(self):
    """Search/list patients"""
    self.client.get(
      "/api/v1/patients?page=1&limit=20", headers={"X-User-Type": "public"}
    )

  @task(3)
  def get_patient(self):
    """Get patient details"""
    if not TEST_PATIENT_IDS:
      return

    patient_id = random.choice(TEST_PATIENT_IDS)
    self.client.get(
      f"/api/v1/patients/{patient_id}",
      headers={"X-User-Type": "public"},
      name="/api/v1/patients/[patientId]",
    )

  @task(5)
  def list_doctors(self):
    """List available doctors"""
    self.client.get(
      "/api/v1/doctors?page=1&limit=20", headers={"X-User-Type": "public"}
    )

  @task(4)
  def list_departments(self):
    """List departments"""
    self.client.get("/api/v1/departments", headers={"X-User-Type": "public"})

  @task(2)
  def create_appointment(self):
    """Book an appointment"""
    if not TEST_PATIENT_IDS or not TEST_DOCTOR_IDS:
      return

    data = generate_appointment_data(
      random.choice(TEST_PATIENT_IDS), random.choice(TEST_DOCTOR_IDS)
    )

    with self.client.post(
      "/api/v1/appointments",
      json=data,
      headers={"X-User-Type": "public"},
      catch_response=True,
    ) as response:
      if response.status_code == 201:
        appointment = response.json()
        TEST_APPOINTMENT_IDS.append(appointment.get("appointmentId"))
        response.success()
      elif response.status_code == 400:
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(3)
  def list_appointments(self):
    """List appointments"""
    self.client.get(
      "/api/v1/appointments?page=1&limit=20", headers={"X-User-Type": "public"}
    )


class DynamoDBTasks(TaskSet):
  """Tasks focused on DynamoDB operations - medical records and invoices"""

  @task(4)
  def create_medical_record(self):
    """Create medical record (DynamoDB write)"""
    if not TEST_PATIENT_IDS or not TEST_DOCTOR_IDS:
      return

    data = generate_medical_record_data(
      random.choice(TEST_PATIENT_IDS), random.choice(TEST_DOCTOR_IDS)
    )

    with self.client.post(
      "/api/v1/medical-records", json=data, catch_response=True
    ) as response:
      if response.status_code == 201:
        record = response.json()
        TEST_RECORD_IDS.append(record.get("recordId"))
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(6)
  def get_medical_record(self):
    """Get medical record (DynamoDB read)"""
    if not TEST_RECORD_IDS:
      return

    record_id = random.choice(TEST_RECORD_IDS)
    self.client.get(
      f"/api/v1/medical-records/{record_id}", name="/api/v1/medical-records/[recordId]"
    )

  @task(5)
  def get_patient_medical_records(self):
    """Get patient's medical history (DynamoDB query by GSI)"""
    if not TEST_PATIENT_IDS:
      return

    patient_id = random.choice(TEST_PATIENT_IDS)
    self.client.get(
      f"/api/v1/patients/{patient_id}/medical-records",
      name="/api/v1/patients/[patientId]/medical-records",
    )

  @task(2)
  def update_medical_record(self):
    """Update medical record (DynamoDB update)"""
    if not TEST_RECORD_IDS:
      return

    record_id = random.choice(TEST_RECORD_IDS)
    data = {"diagnosis": "Updated diagnosis", "treatment": "Updated treatment plan"}

    self.client.put(
      f"/api/v1/medical-records/{record_id}",
      json=data,
      name="/api/v1/medical-records/[recordId]",
    )

  @task(4)
  def create_invoice(self):
    """Create invoice (DynamoDB write)"""
    if not TEST_PATIENT_IDS:
      return

    data = generate_invoice_data(random.choice(TEST_PATIENT_IDS))

    with self.client.post(
      "/api/v1/billing/invoices", json=data, catch_response=True
    ) as response:
      if response.status_code == 201:
        invoice = response.json()
        TEST_INVOICE_IDS.append(invoice.get("invoiceId"))
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(6)
  def get_invoice(self):
    """Get invoice (DynamoDB read)"""
    if not TEST_INVOICE_IDS:
      return

    invoice_id = random.choice(TEST_INVOICE_IDS)
    self.client.get(
      f"/api/v1/billing/invoices/{invoice_id}",
      name="/api/v1/billing/invoices/[invoiceId]",
    )

  @task(3)
  def get_patient_invoices(self):
    """Get patient's invoices (DynamoDB query by GSI)"""
    if not TEST_PATIENT_IDS:
      return

    patient_id = random.choice(TEST_PATIENT_IDS)
    self.client.get(
      f"/api/v1/patients/{patient_id}/invoices",
      name="/api/v1/patients/[patientId]/invoices",
    )


class MySQLTasks(TaskSet):
  """Tasks focused on MySQL operations - patients, doctors, appointments"""

  @task(4)
  def create_patient(self):
    """Create patient (MySQL write)"""
    data = generate_patient_data()

    with self.client.post(
      "/api/v1/patients", json=data, catch_response=True
    ) as response:
      if response.status_code == 201:
        patient = response.json()
        TEST_PATIENT_IDS.append(patient.get("patientId"))
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(8)
  def list_patients(self):
    """List patients with filters (MySQL complex query)"""
    params = {
      "page": random.randint(1, 5),
      "limit": 20,
      "status": random.choice(["active", "inactive", ""]),
    }
    self.client.get("/api/v1/patients", params=params)

  @task(6)
  def get_patient(self):
    """Get patient by ID (MySQL read with JOIN)"""
    if not TEST_PATIENT_IDS:
      return

    patient_id = random.choice(TEST_PATIENT_IDS)
    self.client.get(
      f"/api/v1/patients/{patient_id}", name="/api/v1/patients/[patientId]"
    )

  @task(2)
  def update_patient(self):
    """Update patient (MySQL update)"""
    if not TEST_PATIENT_IDS:
      return

    patient_id = random.choice(TEST_PATIENT_IDS)
    data = {"phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"}

    self.client.put(
      f"/api/v1/patients/{patient_id}", json=data, name="/api/v1/patients/[patientId]"
    )

  @task(3)
  def create_doctor(self):
    """Create doctor (MySQL write)"""
    data = generate_doctor_data()

    with self.client.post(
      "/api/v1/doctors", json=data, catch_response=True
    ) as response:
      if response.status_code == 201:
        doctor = response.json()
        TEST_DOCTOR_IDS.append(doctor.get("doctorId"))
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(8)
  def list_doctors(self):
    """List doctors (MySQL query with JOIN)"""
    params = {
      "page": random.randint(1, 5),
      "limit": 20,
      "specialty": random.choice(["Cardiology", "Pediatrics", ""]),
    }
    self.client.get("/api/v1/doctors", params=params)

  @task(5)
  def get_departments(self):
    """List departments (MySQL read)"""
    self.client.get("/api/v1/departments")

  @task(3)
  def create_appointment(self):
    """Create appointment (MySQL write with availability check)"""
    if not TEST_PATIENT_IDS or not TEST_DOCTOR_IDS:
      return

    data = generate_appointment_data(
      random.choice(TEST_PATIENT_IDS), random.choice(TEST_DOCTOR_IDS)
    )

    with self.client.post(
      "/api/v1/appointments", json=data, catch_response=True
    ) as response:
      if response.status_code == 201:
        appointment = response.json()
        TEST_APPOINTMENT_IDS.append(appointment.get("appointmentId"))
        response.success()
      elif response.status_code == 400:
        response.success()
      else:
        response.failure(f"Failed: {response.status_code}")

  @task(7)
  def list_appointments(self):
    """List appointments (MySQL complex query with JOINs)"""
    params = {
      "page": random.randint(1, 5),
      "limit": 20,
      "status": random.choice(["scheduled", "completed", ""]),
    }
    self.client.get("/api/v1/appointments", params=params)


class InternalUser(HttpUser):
  """
  Simulates internal staff users accessing medical records and billing.
  Tests inward-facing APIs with bulkhead protection (50 concurrent).
  """

  tasks = [InternalTasks]
  wait_time = between(1, 3)
  weight = 2

  def on_start(self):
    """Setup: Ensure we have some test data"""
    response = self.client.get("/api/v1/departments")
    if response.status_code == 200:
      data = response.json()
      global TEST_DEPARTMENT_IDS
      TEST_DEPARTMENT_IDS = [d["departmentId"] for d in data.get("data", [])]


class ExternalUser(HttpUser):
  """
  Simulates external public users accessing patient portal and appointments.
  Tests outward-facing APIs with bulkhead protection (100 concurrent).
  """

  tasks = [ExternalTasks]
  wait_time = between(2, 5)
  weight = 1

  def on_start(self):
    """Setup: Get departments"""
    response = self.client.get("/api/v1/departments")
    if response.status_code == 200:
      data = response.json()
      global TEST_DEPARTMENT_IDS
      TEST_DEPARTMENT_IDS = [d["departmentId"] for d in data.get("data", [])]


class DynamoDBUser(HttpUser):
  """
  Simulates users primarily accessing DynamoDB operations.
  Tests medical records and invoice operations.
  """

  tasks = [DynamoDBTasks]
  wait_time = between(1, 2)
  weight = 1


class MySQLUser(HttpUser):
  """
  Simulates users primarily accessing MySQL operations.
  Tests patients, doctors, appointments, departments.
  """

  tasks = [MySQLTasks]
  wait_time = between(1, 2)
  weight = 1
