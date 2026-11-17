# Data Dictionary - recruitment_placement_db

Generated from the live MySQL schema (`database_schema.sql`).


## activity_logs

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| log_id | bigint(20) | NO |  | PK, AUTO_INCREMENT |
| user_id | int(11) | YES | NULL | FK -> users.user_id |
| module_name | varchar(60) | NO |  |  |
| action_name | varchar(80) | NO |  |  |
| record_id | varchar(60) | YES | NULL |  |
| description | varchar(500) | YES | NULL |  |
| logged_at | datetime | NO | current_timestamp() |  |

## applications

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| application_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| application_code | varchar(40) | NO |  | UNIQUE |
| candidate_id | int(11) | NO |  | FK -> candidates.candidate_id |
| job_id | int(11) | NO |  | FK -> jobs.job_id |
| applied_at | datetime | NO | current_timestamp() |  |
| eligibility_status | varchar(20) | NO | 'PENDING' |  |
| eligibility_reason | varchar(500) | YES | NULL |  |
| application_status | varchar(30) | NO | 'APPLIED' |  |
| source | varchar(50) | YES | NULL |  |
| assigned_recruiter_id | int(11) | YES | NULL | FK -> users.user_id |
| updated_at | datetime | NO | current_timestamp() |  |

## application_history

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| history_id | bigint(20) | NO |  | PK, AUTO_INCREMENT |
| application_id | int(11) | NO |  | FK -> applications.application_id |
| old_status | varchar(30) | YES | NULL |  |
| new_status | varchar(30) | NO |  |  |
| remarks | varchar(500) | YES | NULL |  |
| changed_by | int(11) | YES | NULL | FK -> users.user_id |
| changed_at | datetime | NO | current_timestamp() |  |

## candidates

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| candidate_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| candidate_code | varchar(30) | NO |  | UNIQUE |
| full_name | varchar(150) | NO |  |  |
| email | varchar(150) | NO |  | UNIQUE |
| mobile | varchar(20) | NO |  | UNIQUE |
| date_of_birth | date | YES | NULL |  |
| gender | varchar(20) | YES | NULL |  |
| qualification | varchar(80) | NO |  |  |
| college | varchar(180) | YES | NULL |  |
| university | varchar(180) | YES | NULL |  |
| passing_year | smallint(6) | NO |  |  |
| percentage | decimal(5,2) | YES | NULL |  |
| cgpa | decimal(4,2) | YES | NULL |  |
| backlog_count | int(11) | NO | 0 |  |
| primary_technology | varchar(80) | YES | NULL |  |
| current_location | varchar(100) | YES | NULL |  |
| preferred_location | varchar(100) | YES | NULL |  |
| profile_status | varchar(20) | NO | 'ACTIVE' |  |
| placement_status | varchar(20) | NO | 'NOT_PLACED' |  |
| created_at | datetime | NO | current_timestamp() |  |
| updated_at | datetime | NO | current_timestamp() |  |

## candidate_skills

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| candidate_skill_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| candidate_id | int(11) | NO |  | FK -> candidates.candidate_id |
| skill_id | int(11) | NO |  | FK -> skills.skill_id |
| proficiency_level | varchar(20) | YES | NULL |  |
| years_experience | decimal(4,1) | NO | 0.0 |  |
| is_primary | tinyint(1) | NO | 0 |  |

## companies

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| company_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| company_code | varchar(30) | NO |  | UNIQUE |
| company_name | varchar(180) | NO |  |  |
| industry | varchar(100) | YES | NULL |  |
| website | varchar(200) | YES | NULL |  |
| location | varchar(120) | YES | NULL |  |
| company_type | varchar(30) | YES | NULL |  |
| hr_name | varchar(120) | YES | NULL |  |
| hr_email | varchar(150) | YES | NULL |  |
| hr_mobile | varchar(20) | YES | NULL |  |
| status | varchar(20) | NO | 'ACTIVE' |  |
| created_at | datetime | NO | current_timestamp() |  |

## interview_feedback

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| feedback_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| interview_id | int(11) | NO |  | UNIQUE, FK -> interview_rounds.interview_id |
| technical_rating | decimal(3,1) | YES | NULL |  |
| communication_rating | decimal(3,1) | YES | NULL |  |
| problem_solving_rating | decimal(3,1) | YES | NULL |  |
| overall_rating | decimal(3,1) | YES | NULL |  |
| recommendation | varchar(30) | NO |  |  |
| remarks | text | YES | NULL |  |
| submitted_by | int(11) | YES | NULL | FK -> users.user_id |
| submitted_at | datetime | NO | current_timestamp() |  |

## interview_rounds

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| interview_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| application_id | int(11) | NO |  | FK -> applications.application_id |
| round_number | int(11) | NO |  |  |
| round_type | varchar(50) | NO |  |  |
| scheduled_date | date | NO |  |  |
| scheduled_time | time | YES | NULL |  |
| mode | varchar(20) | NO |  |  |
| interviewer_name | varchar(120) | YES | NULL |  |
| meeting_or_location | varchar(255) | YES | NULL |  |
| status | varchar(20) | NO | 'SCHEDULED' |  |
| created_at | datetime | NO | current_timestamp() |  |

## jobs

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| job_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| job_code | varchar(40) | NO |  | UNIQUE |
| company_id | int(11) | NO |  | FK -> companies.company_id |
| job_title | varchar(150) | NO |  |  |
| employment_type | varchar(30) | NO | 'FULL_TIME' |  |
| location | varchar(120) | NO |  |  |
| openings | int(11) | NO |  |  |
| min_package_lpa | decimal(6,2) | YES | NULL |  |
| max_package_lpa | decimal(6,2) | YES | NULL |  |
| min_percentage | decimal(5,2) | YES | NULL |  |
| min_passing_year | smallint(6) | YES | NULL |  |
| max_passing_year | smallint(6) | YES | NULL |  |
| max_backlogs | int(11) | NO | 0 |  |
| experience_min_years | decimal(4,1) | NO | 0.0 |  |
| qualification_rule | varchar(255) | YES | NULL |  |
| required_technology | varchar(80) | YES | NULL |  |
| posted_date | date | NO |  |  |
| application_deadline | date | NO |  |  |
| status | varchar(20) | NO | 'OPEN' |  |
| created_by | int(11) | YES | NULL | FK -> users.user_id |
| created_at | datetime | NO | current_timestamp() |  |

## job_skills

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| job_skill_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| job_id | int(11) | NO |  | FK -> jobs.job_id |
| skill_id | int(11) | NO |  | FK -> skills.skill_id |
| minimum_level | varchar(20) | YES | NULL |  |
| mandatory_flag | tinyint(1) | NO | 1 |  |

## locations

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| location_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| city | varchar(100) | NO |  | UNIQUE |
| state | varchar(100) | YES | NULL |  |
| is_active | tinyint(1) | NO | 1 |  |

## offers

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| offer_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| offer_code | varchar(40) | NO |  | UNIQUE |
| application_id | int(11) | NO |  | UNIQUE, FK -> applications.application_id |
| designation | varchar(120) | NO |  |  |
| offered_package_lpa | decimal(6,2) | NO |  |  |
| offer_date | date | NO |  |  |
| expected_joining_date | date | YES | NULL |  |
| offer_status | varchar(20) | NO | 'OFFERED' |  |
| remarks | varchar(500) | YES | NULL |  |
| created_at | datetime | NO | current_timestamp() |  |

## placements

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| placement_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| candidate_id | int(11) | NO |  | FK -> candidates.candidate_id |
| company_id | int(11) | NO |  | FK -> companies.company_id |
| job_id | int(11) | NO |  | FK -> jobs.job_id |
| offer_id | int(11) | NO |  | UNIQUE, FK -> offers.offer_id |
| designation | varchar(120) | NO |  |  |
| final_package_lpa | decimal(6,2) | NO |  |  |
| expected_joining_date | date | YES | NULL |  |
| actual_joining_date | date | YES | NULL |  |
| joining_status | varchar(20) | NO | 'PENDING' |  |
| placement_status | varchar(20) | NO | 'ACTIVE' |  |
| created_at | datetime | NO | current_timestamp() |  |

## qualifications

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| qualification_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| qualification_name | varchar(80) | NO |  | UNIQUE |
| is_active | tinyint(1) | NO | 1 |  |

## roles

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| role_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| role_code | varchar(30) | NO |  | UNIQUE |
| role_name | varchar(80) | NO |  |  |
| is_active | tinyint(1) | NO | 1 |  |
| created_at | datetime | NO | current_timestamp() |  |

## skills

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| skill_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| skill_name | varchar(100) | NO |  | UNIQUE |
| category | varchar(60) | YES | NULL |  |
| is_active | tinyint(1) | NO | 1 |  |

## users

| Column | Type | Null | Default | Key / Constraint |
|---|---|---|---|---|
| user_id | int(11) | NO |  | PK, AUTO_INCREMENT |
| username | varchar(80) | NO |  | UNIQUE |
| password_hash | varchar(255) | NO |  |  |
| full_name | varchar(120) | NO |  |  |
| email | varchar(150) | YES | NULL | UNIQUE |
| role_id | int(11) | NO |  | FK -> roles.role_id |
| status | varchar(20) | NO | 'ACTIVE' |  |
| last_login_at | datetime | YES | NULL |  |
| created_at | datetime | NO | current_timestamp() |  |
