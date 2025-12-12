from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.username = user_data['username']
        self.password_hash = user_data['password']
        self.created_at = user_data.get('created_at', datetime.now())
        self.is_online = user_data.get('is_online', False)
        self.last_seen = user_data.get('last_seen', datetime.now())
        self.is_typing = user_data.get('is_typing', False)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.id
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

class FormSubmission:
    """Model for form submissions"""
    def __init__(self, name, gender, countries, primary_country, description):
        self.id = None
        self.name = name
        self.gender = gender
        self.countries = countries
        self.primary_country = primary_country
        self.description = description
        self.submitted_at = datetime.now()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'countries': self.countries,
            'primary_country': self.primary_country,
            'description': self.description,
            'submitted_at': self.submitted_at.isoformat()
        }

class AWTComponent:
    """Model for AWT components"""
    def __init__(self, name, description, category, methods):
        self.name = name
        self.description = description
        self.category = category
        self.methods = methods
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'methods': self.methods
        }

class Statistics:
    """Model for statistics"""
    def __init__(self):
        self.total_submissions = 0
        self.gender_distribution = {}
        self.country_distribution = {}
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'total_submissions': self.total_submissions,
            'gender_distribution': self.gender_distribution,
            'country_distribution': self.country_distribution
        }
