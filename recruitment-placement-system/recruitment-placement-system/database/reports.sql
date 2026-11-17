USE recruitment_placement_db;
-- 1. Candidate count by technology
SELECT primary_technology, COUNT(*) AS candidates FROM candidates GROUP BY primary_technology ORDER BY candidates DESC;
-- 2. Open jobs by company
SELECT c.company_name, COUNT(j.job_id) AS open_jobs, SUM(j.openings) AS total_openings
FROM jobs j JOIN companies c ON c.company_id = j.company_id WHERE j.status = 'OPEN' GROUP BY c.company_id, c.company_name ORDER BY open_jobs DESC;
-- 3. Applications by status
SELECT application_status, COUNT(*) AS total FROM applications GROUP BY application_status ORDER BY total DESC;
-- 4. Recruitment funnel (applications that reached each stage, from the audit trail)
SELECT new_status AS stage, COUNT(DISTINCT application_id) AS applications FROM application_history
WHERE new_status IN ('APPLIED','ELIGIBILITY_VERIFIED','SHORTLISTED','INTERVIEW_SCHEDULED','SELECTED','OFFERED','JOINED')
GROUP BY new_status ORDER BY applications DESC;
-- 5. Company-wise placements
SELECT c.company_name, COUNT(p.placement_id) AS placed_count FROM placements p JOIN companies c ON c.company_id = p.company_id
WHERE p.joining_status = 'JOINED' GROUP BY c.company_id, c.company_name ORDER BY placed_count DESC;
-- 6. Technology-wise placements
SELECT cd.primary_technology, COUNT(p.placement_id) AS placed_count FROM placements p JOIN candidates cd ON cd.candidate_id = p.candidate_id
WHERE p.joining_status = 'JOINED' GROUP BY cd.primary_technology ORDER BY placed_count DESC;
-- 7. Recruiter performance
SELECT u.full_name AS recruiter, COUNT(DISTINCT a.application_id) AS applications,
       COUNT(DISTINCT ir.interview_id) AS interviews,
       COUNT(DISTINCT CASE WHEN a.application_status = 'JOINED' THEN a.application_id END) AS joined
FROM applications a JOIN users u ON u.user_id = a.assigned_recruiter_id
LEFT JOIN interview_rounds ir ON ir.application_id = a.application_id
GROUP BY u.user_id, u.full_name ORDER BY joined DESC, applications DESC;
-- 8. Pending interviews
SELECT ir.interview_id, cd.full_name, co.company_name, ir.round_type, ir.scheduled_date, ir.scheduled_time, ir.mode
FROM interview_rounds ir JOIN applications a ON a.application_id = ir.application_id
JOIN candidates cd ON cd.candidate_id = a.candidate_id JOIN jobs j ON j.job_id = a.job_id
JOIN companies co ON co.company_id = j.company_id
WHERE ir.status = 'SCHEDULED' ORDER BY ir.scheduled_date, ir.scheduled_time;
-- 9. Offer-to-joining conversion
SELECT COUNT(*) AS total_offers, SUM(p.joining_status = 'JOINED') AS joined,
       ROUND(100 * SUM(p.joining_status = 'JOINED') / COUNT(*), 1) AS offer_to_join_pct
FROM offers o LEFT JOIN placements p ON p.offer_id = o.offer_id;
-- 10. Job aging
SELECT j.job_code, c.company_name, j.job_title, DATEDIFF(CURDATE(), j.posted_date) AS days_open
FROM jobs j JOIN companies c ON c.company_id = j.company_id WHERE j.status = 'OPEN' ORDER BY days_open DESC;
-- 11. Transaction rollback demonstration (sample data stays unchanged)
START TRANSACTION;
  UPDATE applications SET application_status = 'WITHDRAWN' WHERE application_id = 1;
  INSERT INTO application_history (application_id, old_status, new_status, remarks, changed_by) VALUES (1, 'APPLIED', 'WITHDRAWN', 'demo', 1);
ROLLBACK;
