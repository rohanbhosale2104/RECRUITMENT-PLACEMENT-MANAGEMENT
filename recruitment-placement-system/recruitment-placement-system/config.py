"""Database and application settings. Override with environment variables or edit the defaults."""
import os
DB = dict(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'recruitment_placement_db'),
)
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')
