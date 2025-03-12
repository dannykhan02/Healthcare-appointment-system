from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

# Association Table for Many-to-Many Relationship between Doctors and Specializations
doctor_specializations = db.Table(
    'doctor_specializations',
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctors.id'), primary_key=True),
    db.Column('specialization_id', db.Integer, db.ForeignKey('specializations.id'), primary_key=True)
)

# Enum for User Roles
class UserRoles(enum.Enum):
    ADMIN = 'ADMIN'
    DOCTOR = 'DOCTOR'
    NURSE = 'NURSE'
    PATIENT = 'PATIENT'
    RECEPTIONIST = 'RECEPTIONIST'

# Enum for Evaluation Status
class EvaluationStatus(enum.Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

    def __str__(self):
        return self.value

# Enum for Appointment Status
class AppointmentStatus(enum.Enum):
    SCHEDULED = 'scheduled'
    SENT_FOR_EVALUATION = 'sent_for_evaluation'
    COMPLETED = 'completed'
    CANCELED = 'canceled'
    RESCHEDULED = 'rescheduled'

    def __str__(self):
        return self.value

# Enum for Payment Methods
class PaymentMethods(enum.Enum):
    MPESA = 'MPesa'
    PAYSTACK = 'Paystack'
    CASH = 'Cash'
    INSURANCE = 'Insurance'

    def __str__(self):
        return self.value

# Enum for Appointment Types
class AppointmentTypes(enum.Enum):
    CONSULTATION = 'Consultation'
    FOLLOW_UP = 'Follow-up'
    EMERGENCY = 'Emergency'
    PROCEDURE = 'Procedure'
    TEST = 'Test'

    def __str__(self):
        return self.value

# Enum for Gender
class Gender(enum.Enum):
    MALE = 'Male'
    FEMALE = 'Female'
    OTHER = 'Other'

    def __str__(self):
        return self.value

# Base User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    userfullnames = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    role = db.Column(db.Enum(UserRoles), nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def as_dict(self):
        return {
            'id': self.id,
            'userfullnames': self.userfullnames,
            'email': self.email,
            'phone_number': self.phone_number,
            'role': self.role.value,
            'gender': self.gender.value if self.gender else None,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'address': self.address,
            'created_at': self.created_at.isoformat(),
        }

# Hospital Model
class Hospital(db.Model):
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    address = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    departments = db.relationship('Department', back_populates='hospital')
    doctors = db.relationship('Doctor', back_populates='hospital')

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone_number': self.phone_number,
            'email': self.email,
            'website': self.website,
            'description': self.description,
        }

# Department Model
class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    doctors = db.relationship('Doctor', back_populates='department')
    nurses = db.relationship('Nurse', back_populates='department')
    receptionists = db.relationship('Receptionist', back_populates='department')

    hospital = db.relationship('Hospital', back_populates='departments')

    def as_dict(self):
        return {
            'id': self.id,
            'hospital_id': self.hospital_id,
            'name': self.name,
            'description': self.description,
        }

class Doctor(User):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    location = db.Column(db.String(255), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    biography = db.Column(db.Text, nullable=True)

    patients = db.relationship('Patient', back_populates='doctor', foreign_keys='Patient.doctor_id')
    evaluations = db.relationship('Evaluation', back_populates='doctor')
    appointments = db.relationship('Appointment', back_populates='doctor')
    schedules = db.relationship('DoctorSchedule', back_populates='doctor')
    specializations = db.relationship('Specialization', secondary=doctor_specializations, back_populates='doctors')
    department = db.relationship('Department', back_populates='doctors')
    hospital = db.relationship('Hospital', back_populates='doctors')

    # Correct the relationship name
    medication_records = db.relationship('MedicationRecord', back_populates='doctor')

    def as_dict(self):
        return {
            'id': self.id,
            'userfullnames': self.userfullnames,
            'email': self.email,
            'phone_number': self.phone_number,
            'role': self.role.value,
            'gender': self.gender.value if self.gender else None,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'address': self.address,
            'created_at': self.created_at.isoformat(),
            'location': self.location,
            'department_id': self.department_id,
            'hospital_id': self.hospital_id,
            'biography': self.biography,
            'specializations': [specialization.as_dict() for specialization in self.specializations],
            'schedules': [schedule.as_dict() for schedule in self.schedules],
        }


# Specialization Model
class Specialization(db.Model):
    __tablename__ = 'specializations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    doctors = db.relationship('Doctor', secondary=doctor_specializations, back_populates='specializations')

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }

# Doctor Schedule Model
class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedules'
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(15), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    available = db.Column(db.Boolean, default=True)

    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    doctor = db.relationship('Doctor', back_populates='schedules')

    appointments = db.relationship('Appointment', back_populates='doctor_schedule')

    def as_dict(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'available': self.available,
        }

class Patient(User):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    doctor = db.relationship("Doctor", back_populates="patients", foreign_keys=[doctor_id])

    blood_group = db.Column(db.String(10), nullable=True)
    genotype = db.Column(db.String(10), nullable=True)
    known_conditions = db.Column(db.Text, nullable=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    billing = db.relationship("Billing", back_populates="patient", uselist=False)
    evaluations = db.relationship('Evaluation', back_populates='patient')
    appointments = db.relationship('Appointment', back_populates='patient')
    payments = db.relationship("Payment", backref="patient", lazy='dynamic')
    insurance = db.relationship("Insurance", backref="patient", lazy='dynamic')
    reviews = db.relationship("Review", backref="patient", lazy='dynamic')
    allergies = db.relationship("Allergy", back_populates="patient", lazy='dynamic')

    # Correct the relationship name
    medication_records = db.relationship("MedicationRecord", back_populates="patient", lazy='dynamic')

    def as_dict(self):
        return {
            'id': self.id,
            'userfullnames': self.userfullnames,
            'email': self.email,
            'phone_number': self.phone_number,
            'role': self.role.value if self.role else None,
            'gender': self.gender.value if self.gender else None,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.userfullnames if self.doctor else None,
            'blood_group': self.blood_group,
            'genotype': self.genotype,
            'known_conditions': self.known_conditions,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'billing': self.billing.as_dict() if self.billing else None,
            'evaluations': [evaluation.as_dict() for evaluation in self.evaluations],
            'appointments': [appointment.as_dict() for appointment in self.appointments],
            'payments': [payment.as_dict() for payment in self.payments],
            'insurance': [insurance.as_dict() for insurance in self.insurance],
            'reviews': [review.as_dict() for review in self.reviews],
            'allergies': [allergy.as_dict() for allergy in self.allergies],
            'medication_records': [medication_record.as_dict() for medication_record in self.medication_records],
        }


class Allergy(db.Model):
    __tablename__ = 'allergies'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    allergen_name = db.Column(db.String(100), nullable=False)
    reaction = db.Column(db.Text, nullable=True)
    diagnosis_date = db.Column(db.Date, nullable=True)

    patient = db.relationship('Patient', back_populates='allergies')

    def as_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'allergen_name': self.allergen_name,
            'reaction': self.reaction,
            'diagnosis_date': self.diagnosis_date.isoformat() if self.diagnosis_date else None,
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.Enum(PaymentMethods), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    transaction_id = db.Column(db.String(255), unique=True)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)

# Insurance Model
class Insurance(db.Model):
    __tablename__ = 'insurance'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(100), nullable=False)
    policy_number = db.Column(db.String(100), nullable=False, unique=True)
    coverage_details = db.Column(db.Text, nullable=True)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)

# Review Model
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    appointment_type = db.Column(db.Enum(AppointmentTypes), default=AppointmentTypes.CONSULTATION)
    notes = db.Column(db.Text, nullable=True)

    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=True)
    receptionist_id = db.Column(db.Integer, db.ForeignKey('receptionists.id'), nullable=True)
    doctor_schedule_id = db.Column(db.Integer, db.ForeignKey('doctor_schedules.id'), nullable=True)

    doctor_schedule = db.relationship('DoctorSchedule', back_populates='appointments')
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    nurse = db.relationship('Nurse', back_populates='appointments')
    receptionist = db.relationship('Receptionist', back_populates='appointments')

    # Correct the relationship name
    evaluation = db.relationship('Evaluation', uselist=False, back_populates='appointment')

    def as_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'scheduled_time': self.scheduled_time.isoformat(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'reason': self.reason,
            'appointment_type': self.appointment_type.value if self.appointment_type else None,
            'notes': self.notes,
            'nurse_id': self.nurse_id,
            'receptionist_id': self.receptionist_id,
            'doctor_schedule_id': self.doctor_schedule_id,
        }



class Billing(db.Model):
    __tablename__ = 'billing'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    amount_due = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.Enum(PaymentMethods), nullable=True)
    payment_status = db.Column(db.String(50), default='Pending')
    billing_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    patient = db.relationship('Patient', back_populates='billing')

    # Remove direct foreign keys to appointments and evaluations
    # appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', use_alter=True))
    # appointment = db.relationship("Appointment", backref="billing", foreign_keys=[appointment_id], lazy='dynamic')
    # evaluation = db.relationship('Evaluation', back_populates='billing')
    # evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'amount_due': self.amount_due,
            'amount_paid': self.amount_paid,
            'balance': self.balance,
            'payment_method': self.payment_method.value if self.payment_method else None,
            'payment_status': self.payment_status,
            'billing_date': self.billing_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'notes': self.notes,
        }

# Nurse Model
class Nurse(User):
    __tablename__ = 'nurses'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    evaluations = db.relationship('Evaluation', back_populates='nurse')
    appointments = db.relationship('Appointment', back_populates='nurse')

    department = db.relationship('Department', back_populates='nurses')

# Receptionist Model
class Receptionist(User):
    __tablename__ = 'receptionists'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    appointments = db.relationship('Appointment', back_populates='receptionist')

    department = db.relationship('Department', back_populates='receptionists')

    def as_dict(self):
        return {
            'id': self.id,
            'department_id': self.department_id,
        }
class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    blood_pressure_systolic = db.Column(db.Integer, nullable=True)
    blood_pressure_diastolic = db.Column(db.Integer, nullable=True)
    pulse_rate = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    respiratory_rate = db.Column(db.Integer, nullable=True)
    oxygen_saturation = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    symptoms = db.Column(db.Text, nullable=False)
    tests_required = db.Column(db.Text)
    preliminary_diagnosis = db.Column(db.Text, nullable=True)
    final_diagnosis = db.Column(db.Text, nullable=True)
    evaluation_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assigned_time = db.Column(db.DateTime, nullable=True)
    evaluation_status = db.Column(db.Enum(EvaluationStatus), default=EvaluationStatus.PENDING, nullable=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)

    appointment = db.relationship('Appointment', back_populates='evaluation')
    patient = db.relationship('Patient', back_populates='evaluations')
    nurse = db.relationship('Nurse', back_populates='evaluations')
    doctor = db.relationship('Doctor', back_populates='evaluations')
    test_reports = db.relationship('TestReport', backref='evaluation', lazy=True)
    prescriptions = db.relationship('Prescription', back_populates='evaluation', lazy=True)

    # Correct the relationship name
    diagnosis = db.relationship('Diagnosis', uselist=False, back_populates='evaluation')

    def as_dict(self):
        return {
            'id': self.id,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'pulse_rate': self.pulse_rate,
            'temperature': self.temperature,
            'respiratory_rate': self.respiratory_rate,
            'oxygen_saturation': self.oxygen_saturation,
            'height': self.height,
            'weight': self.weight,
            'symptoms': self.symptoms,
            'tests_required': self.tests_required,
            'preliminary_diagnosis': self.preliminary_diagnosis,
            'final_diagnosis': self.final_diagnosis,
            'evaluation_time': self.evaluation_time.isoformat(),
            'assigned_time': self.assigned_time.isoformat() if self.assigned_time else None,
            'evaluation_status': self.evaluation_status.value,
            'patient_id': self.patient_id,
            'nurse_id': self.nurse_id,
            'doctor_id': self.doctor_id,
            'appointment_id': self.appointment_id,
        }


# Diagnosis Model
class Diagnosis(db.Model):
    __tablename__ = 'diagnoses'
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), nullable=False, unique=True)
    diagnosis_code = db.Column(db.String(50), nullable=False)
    diagnosis_name = db.Column(db.String(255), nullable=False)
    diagnosis_notes = db.Column(db.Text, nullable=True)

    evaluation = db.relationship('Evaluation', back_populates='diagnosis', uselist=False)

    def as_dict(self):
        return {
            'id': self.id,
            'evaluation_id': self.evaluation_id,
            'diagnosis_code': self.diagnosis_code,
            'diagnosis_name': self.diagnosis_name,
            'diagnosis_notes': self.diagnosis_notes,
        }

# Prescription Model
class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medication = db.Column(db.String(255), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, nullable=True)

    evaluation = db.relationship('Evaluation', back_populates='prescriptions')
    medication_records = db.relationship('MedicationRecord', back_populates='prescription', lazy=True)

    def as_dict(self):
        return {
            'id': self.id,
            'evaluation_id': self.evaluation_id,
            'doctor_id': self.doctor_id,
            'medication': self.medication,
            'dosage': self.dosage,
            'instructions': self.instructions,
        }

class TestReport(db.Model):
    __tablename__ = 'test_reports'
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), nullable=False)
    test_type = db.Column(db.String(100), nullable=False)
    result = db.Column(db.Text, nullable=False)
    report_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def as_dict(self):
        return {
            'id': self.id,
            'evaluation_id': self.evaluation_id,
            'test_type': self.test_type,
            'result': self.result,
            'report_date': self.report_date.isoformat(),
        }

class MedicationRecord(db.Model):
    __tablename__ = 'medication_records'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medication_name = db.Column(db.String(255), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    route_of_administration = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    prescription = db.relationship('Prescription', back_populates='medication_records')
    patient = db.relationship('Patient', back_populates='medication_records')
    doctor = db.relationship('Doctor', back_populates='medication_records')

    def as_dict(self):
        return {
            'id': self.id,
            'prescription_id': self.prescription_id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'medication_name': self.medication_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'route_of_administration': self.route_of_administration,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

