-- Recruitment & Placement Management System - MySQL schema
DROP DATABASE IF EXISTS recruitment_placement_db;
CREATE DATABASE recruitment_placement_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recruitment_placement_db;

CREATE TABLE roles (
  role_id INT PRIMARY KEY AUTO_INCREMENT,
  role_code VARCHAR(30) NOT NULL UNIQUE,
  role_name VARCHAR(80) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE users (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(150) UNIQUE,
  role_id INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  last_login_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES roles(role_id),
  CONSTRAINT ck_user_status CHECK (status IN ('ACTIVE','INACTIVE','LOCKED'))
);
CREATE TABLE qualifications (
  qualification_id INT PRIMARY KEY AUTO_INCREMENT,
  qualification_name VARCHAR(80) NOT NULL UNIQUE,
  is_active TINYINT(1) NOT NULL DEFAULT 1
);
CREATE TABLE locations (
  location_id INT PRIMARY KEY AUTO_INCREMENT,
  city VARCHAR(100) NOT NULL UNIQUE,
  state VARCHAR(100) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1
);
CREATE TABLE candidates (
  candidate_id INT PRIMARY KEY AUTO_INCREMENT,
  candidate_code VARCHAR(30) NOT NULL UNIQUE,
  full_name VARCHAR(150) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  mobile VARCHAR(20) NOT NULL UNIQUE,
  date_of_birth DATE NULL,
  gender VARCHAR(20) NULL,
  qualification VARCHAR(80) NOT NULL,
  college VARCHAR(180) NULL,
  university VARCHAR(180) NULL,
  passing_year SMALLINT NOT NULL,
  percentage DECIMAL(5,2) NULL,
  cgpa DECIMAL(4,2) NULL,
  backlog_count INT NOT NULL DEFAULT 0,
  primary_technology VARCHAR(80) NULL,
  current_location VARCHAR(100) NULL,
  preferred_location VARCHAR(100) NULL,
  profile_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  placement_status VARCHAR(20) NOT NULL DEFAULT 'NOT_PLACED',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_cand_tech (primary_technology),
  INDEX idx_cand_year (passing_year),
  INDEX idx_cand_placement (placement_status),
  CONSTRAINT ck_cand_pct CHECK (percentage IS NULL OR percentage BETWEEN 0 AND 100),
  CONSTRAINT ck_cand_backlog CHECK (backlog_count >= 0),
  CONSTRAINT ck_cand_profile CHECK (profile_status IN ('ACTIVE','INACTIVE','ON_HOLD','BLACKLISTED')),
  CONSTRAINT ck_cand_place CHECK (placement_status IN ('NOT_PLACED','PLACED'))
);
CREATE TABLE skills (
  skill_id INT PRIMARY KEY AUTO_INCREMENT,
  skill_name VARCHAR(100) NOT NULL UNIQUE,
  category VARCHAR(60) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1
);
CREATE TABLE candidate_skills (
  candidate_skill_id INT PRIMARY KEY AUTO_INCREMENT,
  candidate_id INT NOT NULL,
  skill_id INT NOT NULL,
  proficiency_level VARCHAR(20) NULL,
  years_experience DECIMAL(4,1) NOT NULL DEFAULT 0,
  is_primary TINYINT(1) NOT NULL DEFAULT 0,
  CONSTRAINT uq_cand_skill UNIQUE (candidate_id, skill_id),
  CONSTRAINT fk_cs_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
  CONSTRAINT fk_cs_skill FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);
CREATE TABLE companies (
  company_id INT PRIMARY KEY AUTO_INCREMENT,
  company_code VARCHAR(30) NOT NULL UNIQUE,
  company_name VARCHAR(180) NOT NULL,
  industry VARCHAR(100) NULL,
  website VARCHAR(200) NULL,
  location VARCHAR(120) NULL,
  company_type VARCHAR(30) NULL,
  hr_name VARCHAR(120) NULL,
  hr_email VARCHAR(150) NULL,
  hr_mobile VARCHAR(20) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_comp_name (company_name),
  INDEX idx_comp_status (status),
  CONSTRAINT ck_comp_status CHECK (status IN ('ACTIVE','INACTIVE'))
);
-- NOTE: required_technology is an addition to the spec table; the UI "Required Technology" field and
-- the Technology filter on the Jobs screen need a column to store it.
CREATE TABLE jobs (
  job_id INT PRIMARY KEY AUTO_INCREMENT,
  job_code VARCHAR(40) NOT NULL UNIQUE,
  company_id INT NOT NULL,
  job_title VARCHAR(150) NOT NULL,
  employment_type VARCHAR(30) NOT NULL DEFAULT 'FULL_TIME',
  location VARCHAR(120) NOT NULL,
  openings INT NOT NULL,
  min_package_lpa DECIMAL(6,2) NULL,
  max_package_lpa DECIMAL(6,2) NULL,
  min_percentage DECIMAL(5,2) NULL,
  min_passing_year SMALLINT NULL,
  max_passing_year SMALLINT NULL,
  max_backlogs INT NOT NULL DEFAULT 0,
  experience_min_years DECIMAL(4,1) NOT NULL DEFAULT 0,
  qualification_rule VARCHAR(255) NULL,
  required_technology VARCHAR(80) NULL,
  posted_date DATE NOT NULL,
  application_deadline DATE NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
  created_by INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_job_company FOREIGN KEY (company_id) REFERENCES companies(company_id),
  CONSTRAINT fk_job_user FOREIGN KEY (created_by) REFERENCES users(user_id),
  INDEX idx_job_company (company_id),
  INDEX idx_job_status (status),
  INDEX idx_job_deadline (application_deadline),
  INDEX idx_job_location (location),
  CONSTRAINT ck_job_openings CHECK (openings > 0),
  CONSTRAINT ck_job_package CHECK (min_package_lpa IS NULL OR max_package_lpa IS NULL OR min_package_lpa <= max_package_lpa),
  CONSTRAINT ck_job_dates CHECK (application_deadline >= posted_date),
  CONSTRAINT ck_job_status CHECK (status IN ('DRAFT','OPEN','CLOSED','CANCELLED'))
);
CREATE TABLE job_skills (
  job_skill_id INT PRIMARY KEY AUTO_INCREMENT,
  job_id INT NOT NULL,
  skill_id INT NOT NULL,
  minimum_level VARCHAR(20) NULL,
  mandatory_flag TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT uq_job_skill UNIQUE (job_id, skill_id),
  CONSTRAINT fk_js_job FOREIGN KEY (job_id) REFERENCES jobs(job_id),
  CONSTRAINT fk_js_skill FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);
CREATE TABLE applications (
  application_id INT PRIMARY KEY AUTO_INCREMENT,
  application_code VARCHAR(40) NOT NULL UNIQUE,
  candidate_id INT NOT NULL,
  job_id INT NOT NULL,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  eligibility_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  eligibility_reason VARCHAR(500) NULL,
  application_status VARCHAR(30) NOT NULL DEFAULT 'APPLIED',
  source VARCHAR(50) NULL,
  assigned_recruiter_id INT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uq_candidate_job UNIQUE (candidate_id, job_id),
  CONSTRAINT fk_app_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
  CONSTRAINT fk_app_job FOREIGN KEY (job_id) REFERENCES jobs(job_id),
  CONSTRAINT fk_app_recruiter FOREIGN KEY (assigned_recruiter_id) REFERENCES users(user_id),
  INDEX idx_app_status (application_status),
  INDEX idx_app_recruiter (assigned_recruiter_id),
  CONSTRAINT ck_app_elig CHECK (eligibility_status IN ('PENDING','ELIGIBLE','NOT_ELIGIBLE')),
  CONSTRAINT ck_app_status CHECK (application_status IN ('APPLIED','ELIGIBILITY_VERIFIED','SHORTLISTED','INTERVIEW_SCHEDULED','INTERVIEWED','SELECTED','REJECTED','OFFERED','JOINED','WITHDRAWN'))
);
CREATE TABLE application_history (
  history_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  application_id INT NOT NULL,
  old_status VARCHAR(30) NULL,
  new_status VARCHAR(30) NOT NULL,
  remarks VARCHAR(500) NULL,
  changed_by INT NULL,
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ah_app FOREIGN KEY (application_id) REFERENCES applications(application_id),
  CONSTRAINT fk_ah_user FOREIGN KEY (changed_by) REFERENCES users(user_id),
  INDEX idx_ah_app (application_id),
  INDEX idx_ah_changed (changed_at)
);
CREATE TABLE interview_rounds (
  interview_id INT PRIMARY KEY AUTO_INCREMENT,
  application_id INT NOT NULL,
  round_number INT NOT NULL,
  round_type VARCHAR(50) NOT NULL,
  scheduled_date DATE NOT NULL,
  scheduled_time TIME NULL,
  mode VARCHAR(20) NOT NULL,
  interviewer_name VARCHAR(120) NULL,
  meeting_or_location VARCHAR(255) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_app_round UNIQUE (application_id, round_number),
  CONSTRAINT fk_ir_app FOREIGN KEY (application_id) REFERENCES applications(application_id),
  INDEX idx_ir_date (scheduled_date),
  INDEX idx_ir_status (status),
  CONSTRAINT ck_ir_status CHECK (status IN ('SCHEDULED','COMPLETED','RESCHEDULED','CANCELLED','NO_SHOW')),
  CONSTRAINT ck_ir_mode CHECK (mode IN ('ONLINE','OFFLINE','TELEPHONIC'))
);
CREATE TABLE interview_feedback (
  feedback_id INT PRIMARY KEY AUTO_INCREMENT,
  interview_id INT NOT NULL UNIQUE,
  technical_rating DECIMAL(3,1) NULL,
  communication_rating DECIMAL(3,1) NULL,
  problem_solving_rating DECIMAL(3,1) NULL,
  overall_rating DECIMAL(3,1) NULL,
  recommendation VARCHAR(30) NOT NULL,
  remarks TEXT NULL,
  submitted_by INT NULL,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_if_interview FOREIGN KEY (interview_id) REFERENCES interview_rounds(interview_id),
  CONSTRAINT fk_if_user FOREIGN KEY (submitted_by) REFERENCES users(user_id),
  INDEX idx_if_reco (recommendation),
  CONSTRAINT ck_if_reco CHECK (recommendation IN ('NEXT_ROUND','SELECTED','REJECTED','ON_HOLD'))
);
CREATE TABLE offers (
  offer_id INT PRIMARY KEY AUTO_INCREMENT,
  offer_code VARCHAR(40) NOT NULL UNIQUE,
  application_id INT NOT NULL UNIQUE,
  designation VARCHAR(120) NOT NULL,
  offered_package_lpa DECIMAL(6,2) NOT NULL,
  offer_date DATE NOT NULL,
  expected_joining_date DATE NULL,
  offer_status VARCHAR(20) NOT NULL DEFAULT 'OFFERED',
  remarks VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_offer_app FOREIGN KEY (application_id) REFERENCES applications(application_id),
  INDEX idx_offer_status (offer_status),
  CONSTRAINT ck_offer_status CHECK (offer_status IN ('OFFERED','ACCEPTED','REJECTED','EXPIRED','WITHDRAWN'))
);
CREATE TABLE placements (
  placement_id INT PRIMARY KEY AUTO_INCREMENT,
  candidate_id INT NOT NULL,
  company_id INT NOT NULL,
  job_id INT NOT NULL,
  offer_id INT NOT NULL UNIQUE,
  designation VARCHAR(120) NOT NULL,
  final_package_lpa DECIMAL(6,2) NOT NULL,
  expected_joining_date DATE NULL,
  actual_joining_date DATE NULL,
  joining_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  placement_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pl_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
  CONSTRAINT fk_pl_company FOREIGN KEY (company_id) REFERENCES companies(company_id),
  CONSTRAINT fk_pl_job FOREIGN KEY (job_id) REFERENCES jobs(job_id),
  CONSTRAINT fk_pl_offer FOREIGN KEY (offer_id) REFERENCES offers(offer_id),
  INDEX idx_pl_candidate (candidate_id),
  INDEX idx_pl_company (company_id),
  INDEX idx_pl_joining (joining_status),
  CONSTRAINT ck_pl_joining CHECK (joining_status IN ('PENDING','JOINED','NOT_JOINED','DEFERRED','NO_SHOW')),
  CONSTRAINT ck_pl_status CHECK (placement_status IN ('ACTIVE','CANCELLED'))
);
CREATE TABLE activity_logs (
  log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NULL,
  module_name VARCHAR(60) NOT NULL,
  action_name VARCHAR(80) NOT NULL,
  record_id VARCHAR(60) NULL,
  description VARCHAR(500) NULL,
  logged_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES users(user_id),
  INDEX idx_log_user (user_id),
  INDEX idx_log_module (module_name),
  INDEX idx_log_time (logged_at)
);
