from datetime import datetime, date, timezone
from database import db


class Patient(db.Model):
    """
    Patient model representing records in the 'patients' table.
    Stores personal info, blood test markers, and AI-generated remarks.
    """
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(150), nullable=False)
    glucose = db.Column(db.Float, nullable=False)
    haemoglobin = db.Column(db.Float, nullable=False)
    cholesterol = db.Column(db.Float, nullable=False)
    ai_remarks = db.Column(db.Text, nullable=True)
    ai_status = db.Column(db.String(20), default='pending', nullable=False)  # 'completed', 'pending', 'failed'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    @property
    def formatted_dob(self) -> str:
        """Return Date of Birth in standard DD/MM/YYYY format."""
        if isinstance(self.date_of_birth, (date, datetime)):
            return self.date_of_birth.strftime('%d/%m/%Y')
        return str(self.date_of_birth)

    @property
    def input_dob(self) -> str:
        """Return Date of Birth in YYYY-MM-DD format for HTML date inputs."""
        if isinstance(self.date_of_birth, (date, datetime)):
            return self.date_of_birth.strftime('%Y-%m-%d')
        return str(self.date_of_birth)

    def to_dict(self) -> dict:
        """Serialize patient record to dictionary for JSON API responses."""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'date_of_birth': self.formatted_dob,
            'email': self.email,
            'glucose': self.glucose,
            'haemoglobin': self.haemoglobin,
            'cholesterol': self.cholesterol,
            'ai_remarks': self.ai_remarks,
            'ai_status': self.ai_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<Patient id={self.id} name='{self.full_name}' email='{self.email}'>"
