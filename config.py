"""
Configuration Management
========================

This module handles application configuration for different environments.
It provides secure configuration management with validation and environment-specific settings.

Key Features:
- Environment-based configuration (development/production)
- Configuration validation
- Secure defaults
- Environment variable management
- Security settings for production

Author: Books Manager Team
Version: 1.0.0
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with environment variable validation."""
    
    # Database configuration
    DATABASE_HOST = os.getenv('HOST')
    DATABASE_PORT = int(os.getenv('PORT', 5432))
    DATABASE_NAME = os.getenv('DB')
    DATABASE_USER = os.getenv('USER')
    DATABASE_PASSWORD = os.getenv('PASSWORD')
    
    # App settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # API settings
    OPEN_LIBRARY_API_BASE = os.getenv('OPEN_LIBRARY_API_BASE', 'https://openlibrary.org')
    
    # Security settings
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration values are present."""
        required_vars = ['HOST', 'DB', 'USER', 'PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        if cls.SECRET_KEY == 'your-secret-key-change-in-production':
            print("WARNING: Using default secret key. Change SECRET_KEY in production!")

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'
    
    @classmethod
    def validate_config(cls):
        """Additional validation for production."""
        super().validate_config()
        
        if cls.SECRET_KEY == 'your-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production environment")
        
        if not cls.SESSION_COOKIE_SECURE:
            raise ValueError("SESSION_COOKIE_SECURE must be True in production")

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}