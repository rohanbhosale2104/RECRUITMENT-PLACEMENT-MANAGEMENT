import re
from datetime import date, datetime
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
from markupsafe import Markup
from werkzeug.security import check_password_hash
import config
from db import q, x, tx, close_db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.teardown_appcontext(close_db)
PER = 10
TECHS = ['Java', 'Python', 'Testing', 'Data Analytics']
QUALS = ['BE', 'BTech', 'MCA', 'BSc', 'MSc']
YEARS = ['2022', '2023', '2024', '2025', '2026', '2027']
COLORS = {'green': ['ACTIVE', 'OPEN', 'SELECTED', 'JOINED', 'ACCEPTED', 'COMPLETED', 'ELIGIBLE'],
          'blue': ['ELIGIBILITY_VERIFIED', 'SHORTLISTED', 'SCHEDULED', 'OFFERED', 'ONLINE'],
          'purple': ['INTERVIEW_SCHEDULED', 'PLACED', 'INTERVIEWED'],
          'amber': ['ON_HOLD', 'RESCHEDULED', 'DEFERRED', 'PENDING', 'TELEPHONIC'],
          'red': ['CLOSED', 'REJECTED', 'NO_SHOW', 'CANCELLED', 'EXPIRED', 'NOT_JOINED', 'NOT_ELIGIBLE', 'BLACKLISTED']}


@app.template_filter('badge')
def badge(s):
    s = s or '-'
    cls = next((f'b-{c}' for c, v in COLORS.items() if s in v), 'b-grey')
    return Markup(f'<span class="badge {cls}">{s}</span>')


@app.template_filter('d')
def fmt_date(v, f='%d-%b-%Y'):
    return v.strftime(f) if hasattr(v, 'strftime') else (v or '-')


@app.template_filter('t')
def fmt_time(v):
    if v is None: return ''
    secs = int(v.total_seconds()) if hasattr(v, 'total_seconds') else 0
    return datetime(2000, 1, 1, secs // 3600, secs % 3600 // 60).strftime('%I:%M %p')


@app.template_global()
def O(items, all_=False):
    out = [('', 'All')] if all_ else []
    return out + [(i, i) if isinstance(i, str) else i for i in items]


@app.context_processor
def inject():
    return dict(user=session.get('user'), today=date.today())


@app.before_request
def guard():
    if request.endpoint in ('login', 'static'): return
    if 'uid' not in session: return redirect(url_for('login'))


def log(module, action, rec, desc):
    x("INSERT INTO activity_logs (user_id,module_name,action_name,record_id,description) VALUES (%s,%s,%s,%s,%s)",
      (session.get('uid'), module, action, str(rec), desc))


def hist(app_id, old, new, remarks):
    x("INSERT INTO application_history (application_id,old_status,new_status,remarks,changed_by) VALUES (%s,%s,%s,%s,%s)",
      (app_id, old, new, remarks, session.get('uid')))
    x("UPDATE applications SET application_status=%s WHERE application_id=%s", (new, app_id))


def next_code(prefix, table, col, width=4):
    n = q(f"SELECT COALESCE(MAX({table[:-1]}_id),0)+1 n FROM {table}", one=True)['n']
    return f"{prefix}-{date.today().year}-{n:0{width}d}"


def err_msg(e):
    m = getattr(e, 'msg', str(e))
    if 'Duplicate' in m or e.errno == 1062:
        if 'email' in m: return 'Email already exists.'
        if 'mobile' in m: return 'Mobile number already exists.'
        if 'uq_candidate_job' in m: return 'Candidate has already applied for this job.'
        if 'job_code' in m: return 'Job code already exists.'
        if 'company_code' in m: return 'Company code already exists.'
        return 'Duplicate record: ' + m
    if e.errno == 3819 or 'CONSTRAINT' in m or e.errno == 4025: return 'A data rule was violated: ' + m
    return 'Database error: ' + m


def eligibility(c, j):
    r = []
    if c['profile_status'] != 'ACTIVE': r.append(f"Profile status is {c['profile_status']}")
    if j['min_percentage'] is not None and (c['percentage'] or 0) < j['min_percentage']:
        r.append(f"Percentage {float(c['percentage'] or 0):.1f} is below required {float(j['min_percentage']):.1f}")
    if j['min_passing_year'] and c['passing_year'] < j['min_passing_year'] or j['max_passing_year'] and c['passing_year'] > j['max_passing_year']:
        r.append(f"Passing year {c['passing_year']} outside {j['min_passing_year']}-{j['max_passing_year']}")
    if c['backlog_count'] > j['max_backlogs']: r.append(f"Backlogs {c['backlog_count']} exceed allowed {j['max_backlogs']}")
    quals = [s.strip() for s in (j['qualification_rule'] or '').split(',') if s.strip()]
    if quals and c['qualification'] not in quals: r.append(f"Qualification {c['qualification']} not allowed")
    if j['required_technology'] and c['primary_technology'] != j['required_technology']:
        r.append(f"Technology {c['primary_technology']} does not match {j['required_technology']}")
    return ('NOT_ELIGIBLE', 'Candidate does not meet the eligibility criteria: ' + '; '.join(r)) if r else ('ELIGIBLE', 'Meets all criteria')


def num(v, default=None):
    try: return float(v) if v not in (None, '') else default
    except ValueError: return default


# ---------------- auth ----------------
@app.route('/')
def index(): return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    f, error = {}, None
    if request.method == 'POST':
        f = request.form
        u = q("SELECT u.*, r.role_code, r.role_name FROM users u JOIN roles r ON r.role_id=u.role_id WHERE (u.username=%s OR u.email=%s)",
              (f['username'].strip(), f['username'].strip()), one=True)
        if not u or not check_password_hash(u['password_hash'], f['password']): error = 'Invalid username or password.'
        elif u['status'] != 'ACTIVE': error = 'This account is not active.'
        elif u['role_code'] != f.get('role'): error = 'Selected role does not match this user.'
        else:
            with tx():
                x("UPDATE users SET last_login_at=NOW() WHERE user_id=%s", (u['user_id'],))
                session.update(uid=u['user_id'], user=dict(name=u['full_name'], role=u['role_name'], code=u['role_code']))
                log('AUTH', 'LOGIN', u['user_id'], f"User {u['username']} logged in")
            return redirect(url_for('dashboard'))
    return render_template('login.html', f=f, error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- dashboard ----------------
FUNNEL = [('APPLIED', 'Applications'), ('SHORTLISTED', 'Shortlisted'), ('INTERVIEW_SCHEDULED', 'Interviewed'), ('SELECTED', 'Selected'), ('JOINED', 'Joined')]


def funnel(where='', args=()):
    rows = q(f"SELECT h.new_status s, COUNT(DISTINCT h.application_id) n FROM application_history h JOIN applications a ON a.application_id=h.application_id "
             f"JOIN candidates c ON c.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id {where} GROUP BY h.new_status", args)
    d = {r['s']: r['n'] for r in rows}
    top = max(d.get('APPLIED', 0), 1)
    return [dict(label=l, n=d.get(k, 0), w=max(round(100 * d.get(k, 0) / top), 4)) for k, l in FUNNEL]


@app.route('/dashboard')
def dashboard():
    one = lambda s: q(s, one=True)['n']
    s = dict(cand=one("SELECT COUNT(*) n FROM candidates"), active=one("SELECT COUNT(*) n FROM candidates WHERE profile_status='ACTIVE'"),
             comp=one("SELECT COUNT(*) n FROM companies WHERE status='ACTIVE'"), jobs=one("SELECT COUNT(*) n FROM jobs WHERE status='OPEN'"),
             apps=one("SELECT COUNT(*) n FROM applications"), ints=one("SELECT COUNT(*) n FROM interview_rounds WHERE status IN ('SCHEDULED','RESCHEDULED') AND scheduled_date=CURDATE()"),
             sel=one("SELECT COUNT(*) n FROM applications WHERE application_status='SELECTED'"), placed=one("SELECT COUNT(*) n FROM placements WHERE joining_status='JOINED'"))
    upcoming = q("""SELECT ir.*, cd.full_name, co.company_name FROM interview_rounds ir JOIN applications a ON a.application_id=ir.application_id
        JOIN candidates cd ON cd.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id JOIN companies co ON co.company_id=j.company_id
        WHERE ir.status IN ('SCHEDULED','RESCHEDULED') ORDER BY ir.scheduled_date, ir.scheduled_time LIMIT 5""")
    jobs = q("SELECT j.*, co.company_name FROM jobs j JOIN companies co ON co.company_id=j.company_id ORDER BY j.posted_date DESC, j.job_id DESC LIMIT 5")
    pl = q("""SELECT cd.full_name, co.company_name, p.designation, p.final_package_lpa, p.joining_status FROM placements p JOIN candidates cd ON cd.candidate_id=p.candidate_id
        JOIN companies co ON co.company_id=p.company_id ORDER BY p.created_at DESC LIMIT 5""")
    return render_template('dashboard.html', s=s, upcoming=upcoming, jobs=jobs, pl=pl, fun=funnel(), active='dashboard')


# ---------------- candidates ----------------
@app.route('/candidates')
def candidates():
    a = request.args; cond, p = [], []
    for key, col in (('cid', 'c.candidate_code'), ('name', 'c.full_name'), ('mobile', 'c.mobile'), ('email', 'c.email')):
        if a.get(key): cond.append(f"{col} LIKE %s"); p.append(f"%{a[key].strip()}%")
    for key, col in (('tech', 'c.primary_technology'), ('year', 'c.passing_year'), ('qual', 'c.qualification')):
        if a.get(key): cond.append(f"{col}=%s"); p.append(a[key])
    st = a.get('status')
    if st == 'PLACED': cond.append("c.placement_status='PLACED'")
    elif st: cond.append("c.profile_status=%s"); p.append(st)
    w = ('WHERE ' + ' AND '.join(cond)) if cond else ''
    total = q(f"SELECT COUNT(*) n FROM candidates c {w}", p, one=True)['n']
    page = max(int(a.get('page', 1) or 1), 1)
    rows = q(f"SELECT c.* FROM candidates c {w} ORDER BY c.candidate_id LIMIT {PER} OFFSET {(page - 1) * PER}", p)
    pages = max((total + PER - 1) // PER, 1)
    qs = {k: v for k, v in a.items() if k != 'page' and v}
    return render_template('candidates.html', rows=rows, total=total, page=page, pages=pages, qs=qs, a=a, active='candidates', techs=TECHS, quals=QUALS, years=YEARS)


def cand_form_data():
    f = request.form; e = {}
    if not f.get('full_name', '').strip(): e['full_name'] = 'Please enter candidate name.'
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', f.get('email', '')): e['email'] = 'Enter a valid email address.'
    if not re.match(r'^\d{10}$', f.get('mobile', '')): e['mobile'] = 'Mobile number must contain 10 digits.'
    pct = num(f.get('percentage'))
    if pct is None or not 0 <= pct <= 100: e['percentage'] = 'Percentage must be between 0 and 100.'
    if not f.get('college', '').strip(): e['college'] = 'Please enter college name.'
    bk = f.get('backlog_count', '')
    if not bk.isdigit(): e['backlog_count'] = 'Backlog count cannot be negative.'
    if not f.get('passing_year', '').isdigit(): e['passing_year'] = 'Select passing year.'
    return e, pct


@app.route('/candidates/new', methods=['GET', 'POST'])
@app.route('/candidates/<int:cid>/edit', methods=['GET', 'POST'])
def candidate_form(cid=None):
    skills = q("SELECT * FROM skills WHERE is_active=1 ORDER BY skill_name")
    f, e = {}, {}
    if request.method == 'POST':
        f = request.form.to_dict(); f['skills'] = request.form.getlist('skills'); e, pct = cand_form_data()
        if not e:
            try:
                with tx():
                    v = (f['full_name'].strip(), f['email'].strip(), f['mobile'], f.get('date_of_birth') or None, f.get('gender') or None, f['qualification'], f['college'].strip(),
                         f.get('university') or None, int(f['passing_year']), pct, int(f['backlog_count']), f['primary_technology'], f.get('current_location') or None,
                         f.get('preferred_location') or None, f['profile_status'])
                    if cid:
                        x("""UPDATE candidates SET full_name=%s,email=%s,mobile=%s,date_of_birth=%s,gender=%s,qualification=%s,college=%s,university=%s,passing_year=%s,percentage=%s,
                             backlog_count=%s,primary_technology=%s,current_location=%s,preferred_location=%s,profile_status=%s WHERE candidate_id=%s""", v + (cid,))
                    else:
                        cid = x("""INSERT INTO candidates (full_name,email,mobile,date_of_birth,gender,qualification,college,university,passing_year,percentage,backlog_count,
                                   primary_technology,current_location,preferred_location,profile_status,candidate_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                v + (f"TMP-{datetime.now():%f}",))
                        x("UPDATE candidates SET candidate_code=%s WHERE candidate_id=%s", (f"CAN-{date.today().year}-{cid:04d}", cid))
                    x("DELETE FROM candidate_skills WHERE candidate_id=%s", (cid,))
                    for sid in f['skills']:
                        x("INSERT INTO candidate_skills (candidate_id,skill_id,proficiency_level) VALUES (%s,%s,%s)", (cid, int(sid), f.get('skill_level') or None))
                    log('CANDIDATES', 'SAVE_CANDIDATE', cid, f"Candidate {f['full_name']} saved")
                flash('Candidate saved successfully.', 'ok')
                return redirect(url_for('candidate_details', cid=cid))
            except mysql.connector.Error as ex:
                msg = err_msg(ex); k = 'email' if 'Email' in msg else 'mobile' if 'Mobile' in msg else None
                if k: e[k] = msg
                else: flash(msg, 'err')
    elif cid:
        c = q("SELECT * FROM candidates WHERE candidate_id=%s", (cid,), one=True)
        if not c: return redirect(url_for('candidates'))
        f = {k: ('' if v is None else v) for k, v in c.items()}
        f['percentage'] = float(c['percentage'] or 0); f['date_of_birth'] = c['date_of_birth'].isoformat() if c['date_of_birth'] else ''
        f['skills'] = [str(r['skill_id']) for r in q("SELECT skill_id FROM candidate_skills WHERE candidate_id=%s", (cid,))]
        lv = q("SELECT proficiency_level FROM candidate_skills WHERE candidate_id=%s LIMIT 1", (cid,), one=True); f['skill_level'] = lv['proficiency_level'] if lv else ''
    else:
        f = dict(profile_status='ACTIVE', backlog_count=0, skills=[])
    return render_template('candidate_form.html', f=f, e=e, cid=cid, skills=[(str(s['skill_id']), s['skill_name']) for s in skills], active='candidates', techs=TECHS, quals=QUALS)


@app.route('/candidates/<int:cid>')
def candidate_details(cid):
    c = q("SELECT * FROM candidates WHERE candidate_id=%s", (cid,), one=True)
    if not c: return redirect(url_for('candidates'))
    sk = q("SELECT s.skill_name, cs.proficiency_level, cs.is_primary FROM candidate_skills cs JOIN skills s ON s.skill_id=cs.skill_id WHERE cs.candidate_id=%s", (cid,))
    apps = q("""SELECT a.*, co.company_name, j.job_code, j.job_title FROM applications a JOIN jobs j ON j.job_id=a.job_id JOIN companies co ON co.company_id=j.company_id
                WHERE a.candidate_id=%s ORDER BY a.applied_at DESC""", (cid,))
    ints = q("""SELECT ir.*, co.company_name FROM interview_rounds ir JOIN applications a ON a.application_id=ir.application_id JOIN jobs j ON j.job_id=a.job_id
                JOIN companies co ON co.company_id=j.company_id WHERE a.candidate_id=%s ORDER BY ir.scheduled_date DESC""", (cid,))
    offers = q("""SELECT o.*, co.company_name, p.joining_status, p.actual_joining_date, a.application_id FROM offers o JOIN applications a ON a.application_id=o.application_id
                  JOIN jobs j ON j.job_id=a.job_id JOIN companies co ON co.company_id=j.company_id LEFT JOIN placements p ON p.offer_id=o.offer_id WHERE a.candidate_id=%s""", (cid,))
    return render_template('candidate_details.html', c=c, sk=sk, apps=apps, ints=ints, offers=offers, active='candidates')


# ---------------- companies ----------------
@app.route('/companies', methods=['GET', 'POST'])
def companies():
    f, e = {}, {}
    if request.method == 'POST':
        f = request.form.to_dict(); cid = f.get('company_id')
        for k, m in (('company_name', 'Please enter company name.'), ('industry', 'Please enter industry.'), ('location', 'Please enter location.'), ('hr_name', 'Please enter HR name.')):
            if not f.get(k, '').strip(): e[k] = m
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', f.get('hr_email', '')): e['hr_email'] = 'Enter a valid email address.'
        if f.get('hr_mobile') and not re.match(r'^\d{10}$', f['hr_mobile']): e['hr_mobile'] = 'Mobile number must contain 10 digits.'
        if not e:
            v = (f['company_name'].strip(), f['industry'].strip(), f.get('website') or None, f['location'].strip(), f['company_type'], f['hr_name'].strip(), f['hr_email'].strip(), f.get('hr_mobile') or None, f['status'])
            try:
                with tx():
                    if cid:
                        x("UPDATE companies SET company_name=%s,industry=%s,website=%s,location=%s,company_type=%s,hr_name=%s,hr_email=%s,hr_mobile=%s,status=%s WHERE company_id=%s", v + (cid,))
                    else:
                        n = q("SELECT COALESCE(MAX(company_id),0)+1 n FROM companies", one=True)['n']
                        cid = x("INSERT INTO companies (company_name,industry,website,location,company_type,hr_name,hr_email,hr_mobile,status,company_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", v + (f"COM-{n:03d}",))
                    log('COMPANIES', 'SAVE_COMPANY', cid, f"Company {f['company_name']} saved")
                flash('Company saved successfully.', 'ok'); return redirect(url_for('companies'))
            except mysql.connector.Error as ex: flash(err_msg(ex), 'err')
    elif request.args.get('edit'):
        r = q("SELECT * FROM companies WHERE company_id=%s", (request.args['edit'],), one=True)
        f = {k: ('' if v is None else v) for k, v in (r or {}).items()}; f['company_id'] = (r or {}).get('company_id', '')
    a = request.args; cond, p = [], []
    if a.get('name'): cond.append("c.company_name LIKE %s"); p.append(f"%{a['name']}%")
    if a.get('industry'): cond.append("c.industry LIKE %s"); p.append(f"%{a['industry']}%")
    if a.get('location'): cond.append("c.location LIKE %s"); p.append(f"%{a['location']}%")
    if a.get('status'): cond.append("c.status=%s"); p.append(a['status'])
    w = ('WHERE ' + ' AND '.join(cond)) if cond else ''
    rows = q(f"SELECT c.*, (SELECT COUNT(*) FROM jobs j WHERE j.company_id=c.company_id AND j.status='OPEN') open_jobs FROM companies c {w} ORDER BY c.company_id", p)
    return render_template('companies.html', rows=rows, f=f, e=e, a=a, active='companies')


# ---------------- jobs ----------------
@app.route('/jobs')
def jobs():
    a = request.args; cond, p = [], []
    if a.get('code'): cond.append("j.job_code LIKE %s"); p.append(f"%{a['code']}%")
    for k, col in (('company', 'j.company_id'), ('tech', 'j.required_technology'), ('status', 'j.status'), ('etype', 'j.employment_type')):
        if a.get(k): cond.append(f"{col}=%s"); p.append(a[k])
    if a.get('location'): cond.append("j.location LIKE %s"); p.append(f"%{a['location']}%")
    w = ('WHERE ' + ' AND '.join(cond)) if cond else ''
    rows = q(f"SELECT j.*, c.company_name, (SELECT COUNT(*) FROM applications x WHERE x.job_id=j.job_id) apps FROM jobs j JOIN companies c ON c.company_id=j.company_id {w} ORDER BY j.job_id", p)
    cnt = {r['status']: r['n'] for r in q("SELECT status, COUNT(*) n FROM jobs GROUP BY status")}
    comps = [(str(c['company_id']), c['company_name']) for c in q("SELECT company_id, company_name FROM companies ORDER BY company_name")]
    return render_template('jobs.html', rows=rows, cnt=cnt, a=a, comps=comps, techs=TECHS, active='jobs')


@app.route('/jobs/new', methods=['GET', 'POST'])
@app.route('/jobs/<int:jid>/edit', methods=['GET', 'POST'])
def job_form(jid=None):
    comps = [(str(c['company_id']), c['company_name']) for c in q("SELECT company_id, company_name FROM companies WHERE status='ACTIVE' ORDER BY company_name")]
    skills = [(str(s['skill_id']), s['skill_name']) for s in q("SELECT * FROM skills ORDER BY skill_name")]
    f, e = {}, {}
    if request.method == 'POST':
        f = request.form.to_dict(); f['quals'] = request.form.getlist('quals'); f['skills'] = request.form.getlist('skills')
        for k, m in (('job_code', 'Please enter job code.'), ('job_title', 'Please enter job title.'), ('location', 'Please enter location.')):
            if not f.get(k, '').strip(): e[k] = m
        op = f.get('openings', '')
        if not op.isdigit() or int(op) <= 0: e['openings'] = 'Number of openings must be greater than zero.'
        pmin, pmax = num(f.get('min_package')), num(f.get('max_package'))
        if pmin is not None and pmax is not None and pmin > pmax: e['min_package'] = 'Minimum package cannot exceed maximum package.'
        mp = num(f.get('min_percentage'))
        if mp is None or not 0 <= mp <= 100: e['min_percentage'] = 'Percentage must be between 0 and 100.'
        if not f['quals']: e['quals'] = 'Select at least one qualification.'
        if not f.get('posted_date') or not f.get('application_deadline'): e['application_deadline'] = 'Posted date and deadline are required.'
        elif f['application_deadline'] < f['posted_date']: e['application_deadline'] = 'Application deadline cannot be before posted date.'
        if not e:
            v = (int(f['company_id']), f['job_title'].strip(), f['employment_type'], f['location'].strip(), int(op), pmin, pmax, mp, int(f['min_year']) if f.get('min_year') else None,
                 int(f['max_year']) if f.get('max_year') else None, int(f.get('max_backlogs') or 0), num(f.get('experience'), 0), ', '.join(f['quals']), f['required_technology'],
                 f['posted_date'], f['application_deadline'], f['status'])
            try:
                with tx():
                    if jid:
                        x("""UPDATE jobs SET company_id=%s,job_title=%s,employment_type=%s,location=%s,openings=%s,min_package_lpa=%s,max_package_lpa=%s,min_percentage=%s,min_passing_year=%s,
                             max_passing_year=%s,max_backlogs=%s,experience_min_years=%s,qualification_rule=%s,required_technology=%s,posted_date=%s,application_deadline=%s,status=%s,job_code=%s WHERE job_id=%s""",
                          v + (f['job_code'].strip(), jid))
                    else:
                        jid = x("""INSERT INTO jobs (company_id,job_title,employment_type,location,openings,min_package_lpa,max_package_lpa,min_percentage,min_passing_year,max_passing_year,
                                   max_backlogs,experience_min_years,qualification_rule,required_technology,posted_date,application_deadline,status,job_code,created_by) VALUES
                                   (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", v + (f['job_code'].strip(), session['uid']))
                    x("DELETE FROM job_skills WHERE job_id=%s", (jid,))
                    for sid in f['skills']: x("INSERT INTO job_skills (job_id,skill_id,mandatory_flag) VALUES (%s,%s,1)", (jid, int(sid)))
                    log('JOBS', 'SAVE_JOB', f['job_code'], f"Job {f['job_code']} saved")
                flash('Job saved successfully.', 'ok'); return redirect(url_for('jobs'))
            except mysql.connector.Error as ex:
                m = err_msg(ex)
                if 'Job code' in m: e['job_code'] = m
                else: flash(m, 'err')
    elif jid:
        r = q("SELECT * FROM jobs WHERE job_id=%s", (jid,), one=True)
        if not r: return redirect(url_for('jobs'))
        f = dict(job_code=r['job_code'], company_id=str(r['company_id']), job_title=r['job_title'], openings=r['openings'], employment_type=r['employment_type'], location=r['location'],
                 min_package=r['min_package_lpa'] or '', max_package=r['max_package_lpa'] or '', min_percentage=r['min_percentage'] or '', min_year=r['min_passing_year'] or '', max_year=r['max_passing_year'] or '',
                 max_backlogs=r['max_backlogs'], experience=r['experience_min_years'], required_technology=r['required_technology'], status=r['status'],
                 posted_date=r['posted_date'].isoformat(), application_deadline=r['application_deadline'].isoformat(),
                 quals=[s.strip() for s in (r['qualification_rule'] or '').split(',')], skills=[str(s['skill_id']) for s in q("SELECT skill_id FROM job_skills WHERE job_id=%s", (jid,))])
        for k in ('min_package', 'max_package', 'min_percentage', 'experience'): f[k] = float(f[k]) if f[k] != '' else ''
    else:
        f = dict(employment_type='FULL_TIME', status='DRAFT', max_backlogs=0, posted_date=date.today().isoformat(), quals=[], skills=[])
    return render_template('job_form.html', f=f, e=e, jid=jid, comps=comps, skills=skills, techs=TECHS, quals=QUALS, active='jobs')


# ---------------- applications ----------------
APP_SQL = """SELECT a.*, cd.full_name, cd.candidate_code, co.company_name, j.job_code, j.job_title, u.full_name recruiter FROM applications a
    JOIN candidates cd ON cd.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id JOIN companies co ON co.company_id=j.company_id LEFT JOIN users u ON u.user_id=a.assigned_recruiter_id"""


@app.route('/applications', methods=['GET', 'POST'])
def applications():
    if request.method == 'POST':  # new application
        cid, jid = request.form.get('candidate_id'), request.form.get('job_id')
        job = q("SELECT * FROM jobs WHERE job_id=%s", (jid,), one=True)
        if not cid or not job: flash('Select a candidate and a job.', 'err')
        elif job['status'] != 'OPEN' or job['application_deadline'] < date.today(): flash('This job is not open for applications.', 'err')
        else:
            try:
                with tx():
                    n = q("SELECT COALESCE(MAX(application_id),0)+1 n FROM applications", one=True)['n']
                    aid = x("INSERT INTO applications (application_code,candidate_id,job_id,source,assigned_recruiter_id) VALUES (%s,%s,%s,'Recruiter',%s)",
                            (f"APP-{date.today().year}-{n:04d}", cid, jid, session['uid']))
                    hist(aid, None, 'APPLIED', 'Application submitted'); log('APPLICATIONS', 'CREATE_APPLICATION', aid, 'Application created')
                flash('Application created.', 'ok')
            except mysql.connector.Error as ex: flash(err_msg(ex), 'err')
        return redirect(url_for('applications'))
    a = request.args; cond, p = [], []
    for k, col in (('code', 'a.application_code'),):
        if a.get(k): cond.append(f"{col} LIKE %s"); p.append(f"%{a[k]}%")
    if a.get('candidate'): cond.append("cd.full_name LIKE %s"); p.append(f"%{a['candidate']}%")
    for k, col in (('company', 'j.company_id'), ('job', 'a.job_id'), ('status', 'a.application_status')):
        if a.get(k): cond.append(f"{col}=%s"); p.append(a[k])
    if a.get('from'): cond.append("DATE(a.applied_at)>=%s"); p.append(a['from'])
    if a.get('to'): cond.append("DATE(a.applied_at)<=%s"); p.append(a['to'])
    w = ('WHERE ' + ' AND '.join(cond)) if cond else ''
    rows = q(f"{APP_SQL} {w} ORDER BY a.application_id", p)
    cnt = {r['s']: r['n'] for r in q("SELECT application_status s, COUNT(*) n FROM applications GROUP BY application_status")}
    h = None
    if a.get('history'):
        h = q("SELECT h.*, u.full_name FROM application_history h LEFT JOIN users u ON u.user_id=h.changed_by WHERE h.application_id=%s ORDER BY h.changed_at, h.history_id", (a['history'],))
    comps = [(str(c['company_id']), c['company_name']) for c in q("SELECT company_id, company_name FROM companies ORDER BY company_name")]
    jobs_ = [(str(j['job_id']), f"{j['job_code']} - {j['job_title']}") for j in q("SELECT job_id, job_code, job_title FROM jobs ORDER BY job_id")]
    open_jobs = [(str(j['job_id']), f"{j['job_code']} - {j['job_title']} ({j['company_name']})") for j in q("SELECT j.job_id,j.job_code,j.job_title,c.company_name FROM jobs j JOIN companies c ON c.company_id=j.company_id WHERE j.status='OPEN' ORDER BY j.job_id")]
    cands = [(str(c['candidate_id']), f"{c['candidate_code']} - {c['full_name']}") for c in q("SELECT candidate_id,candidate_code,full_name FROM candidates WHERE profile_status='ACTIVE' ORDER BY candidate_id")]
    return render_template('applications.html', rows=rows, cnt=cnt, a=a, h=h, comps=comps, jobs=jobs_, open_jobs=open_jobs, cands=cands, active='applications')


@app.route('/applications/<int:aid>/<action>', methods=['POST'])
def application_action(aid, action):
    ap = q("SELECT * FROM applications WHERE application_id=%s", (aid,), one=True)
    if not ap: return redirect(url_for('applications'))
    try:
        with tx():
            if action == 'eligibility':
                c = q("SELECT * FROM candidates WHERE candidate_id=%s", (ap['candidate_id'],), one=True); j = q("SELECT * FROM jobs WHERE job_id=%s", (ap['job_id'],), one=True)
                st, reason = eligibility(c, j)
                x("UPDATE applications SET eligibility_status=%s, eligibility_reason=%s WHERE application_id=%s", (st, reason, aid))
                if ap['application_status'] == 'APPLIED':
                    hist(aid, 'APPLIED', 'ELIGIBILITY_VERIFIED' if st == 'ELIGIBLE' else 'REJECTED', reason)
                flash(reason, 'ok' if st == 'ELIGIBLE' else 'err')
            elif action == 'shortlist':
                if ap['application_status'] != 'ELIGIBILITY_VERIFIED': flash('Only applications with verified eligibility can be shortlisted. Run Check Eligibility first.', 'err')
                else: hist(aid, ap['application_status'], 'SHORTLISTED', 'Shortlisted by recruiter'); flash('Application shortlisted.', 'ok')
            elif action == 'reject':
                if ap['application_status'] in ('REJECTED', 'JOINED', 'OFFERED'): flash('This application cannot be rejected now.', 'err')
                else: hist(aid, ap['application_status'], 'REJECTED', request.form.get('remarks') or 'Rejected by recruiter'); flash('Application rejected.', 'ok')
            log('APPLICATIONS', action.upper(), aid, f"{action} on application {ap['application_code']}")
    except mysql.connector.Error as ex: flash(err_msg(ex), 'err')
    return redirect(url_for('applications'))


# ---------------- interviews ----------------
IV_SQL = """SELECT ir.*, a.application_code, a.application_id, cd.full_name, co.company_name, j.job_code FROM interview_rounds ir JOIN applications a ON a.application_id=ir.application_id
    JOIN candidates cd ON cd.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id JOIN companies co ON co.company_id=j.company_id"""


@app.route('/interviews', methods=['GET', 'POST'])
def interviews():
    f, e = {}, {}
    if request.method == 'POST':
        f = request.form.to_dict(); iid = f.get('interview_id')
        if not f.get('interview_date'): e['interview_date'] = 'Select interview date.'
        elif f['interview_date'] < date.today().isoformat(): e['interview_date'] = 'Interview date cannot be in the past.'
        if not f.get('interview_time'): e['interview_time'] = 'Select interview time.'
        if not iid and not f.get('application_id'): e['application_id'] = 'Select an eligible application.'
        if not e:
            try:
                with tx():
                    if iid:
                        x("UPDATE interview_rounds SET scheduled_date=%s,scheduled_time=%s,mode=%s,interviewer_name=%s,round_type=%s,status='RESCHEDULED' WHERE interview_id=%s",
                          (f['interview_date'], f['interview_time'], f['mode'], f.get('interviewer') or None, f['round_type'], iid)); log('INTERVIEWS', 'RESCHEDULE', iid, 'Interview rescheduled')
                        flash('Interview rescheduled.', 'ok')
                    else:
                        aid = int(f['application_id']); ap = q("SELECT * FROM applications WHERE application_id=%s", (aid,), one=True)
                        if ap['application_status'] not in ('SHORTLISTED', 'INTERVIEW_SCHEDULED', 'INTERVIEWED'): raise ValueError('Application must be shortlisted before scheduling an interview.')
                        rn = q("SELECT COALESCE(MAX(round_number),0)+1 n FROM interview_rounds WHERE application_id=%s", (aid,), one=True)['n']
                        new = x("INSERT INTO interview_rounds (application_id,round_number,round_type,scheduled_date,scheduled_time,mode,interviewer_name) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                (aid, rn, f['round_type'], f['interview_date'], f['interview_time'], f['mode'], f.get('interviewer') or None))
                        hist(aid, ap['application_status'], 'INTERVIEW_SCHEDULED', f"Interview round {rn} scheduled"); log('INTERVIEWS', 'SCHEDULE', new, f"Round {rn} scheduled")
                        flash('Interview scheduled.', 'ok')
                return redirect(url_for('interviews'))
            except ValueError as ex: flash(str(ex), 'err')
            except mysql.connector.Error as ex: flash(err_msg(ex), 'err')
    elif request.args.get('reschedule'):
        r = q("SELECT * FROM interview_rounds WHERE interview_id=%s", (request.args['reschedule'],), one=True)
        if r: f = dict(interview_id=r['interview_id'], round_type=r['round_type'], interview_date=r['scheduled_date'].isoformat(), interview_time=fmt_time24(r['scheduled_time']), mode=r['mode'], interviewer=r['interviewer_name'] or '')
    elif request.args.get('application'): f = dict(application_id=request.args['application'], round_type='TECHNICAL', mode='ONLINE')
    a = request.args; cond, p = [], []
    if a.get('candidate'): cond.append("cd.full_name LIKE %s"); p.append(f"%{a['candidate']}%")
    if a.get('company'): cond.append("j.company_id=%s"); p.append(a['company'])
    if a.get('status'): cond.append("ir.status=%s"); p.append(a['status'])
    w = ('WHERE ' + ' AND '.join(cond)) if cond else ''
    rows = q(f"{IV_SQL} {w} ORDER BY ir.scheduled_date DESC, ir.scheduled_time", p)
    cnt = q("""SELECT SUM(scheduled_date=CURDATE() AND status IN ('SCHEDULED','RESCHEDULED')) today, SUM(scheduled_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 7 DAY) AND status IN ('SCHEDULED','RESCHEDULED')) week,
               SUM(status='COMPLETED' AND NOT EXISTS (SELECT 1 FROM interview_feedback fb WHERE fb.interview_id=interview_rounds.interview_id)) pend, SUM(status='NO_SHOW') ns FROM interview_rounds""", one=True)
    up = q(f"{IV_SQL} WHERE ir.status IN ('SCHEDULED','RESCHEDULED') AND ir.scheduled_date>=CURDATE() ORDER BY ir.scheduled_date, ir.scheduled_time LIMIT 3")
    elig = [(str(r['application_id']), f"{r['application_code']} - {r['full_name']} - {r['company_name']} - {r['job_code']}") for r in q(f"{APP_SQL} WHERE a.application_status IN ('SHORTLISTED','INTERVIEW_SCHEDULED','INTERVIEWED') ORDER BY a.application_id")]
    comps = [(str(c['company_id']), c['company_name']) for c in q("SELECT company_id, company_name FROM companies ORDER BY company_name")]
    fb = {r['interview_id'] for r in q("SELECT interview_id FROM interview_feedback")}
    return render_template('interviews.html', rows=rows, cnt=cnt, up=up, f=f, e=e, a=a, elig=elig, comps=comps, fb=fb, active='interviews')


def fmt_time24(v):
    if v is None: return ''
    s = int(v.total_seconds()); return f"{s // 3600:02d}:{s % 3600 // 60:02d}"


@app.route('/interviews/<int:iid>/noshow', methods=['POST'])
def interview_noshow(iid):
    with tx():
        x("UPDATE interview_rounds SET status='NO_SHOW' WHERE interview_id=%s", (iid,)); log('INTERVIEWS', 'NO_SHOW', iid, 'Marked no-show')
    flash('Interview marked as no-show.', 'ok'); return redirect(url_for('interviews'))


# ---------------- placement process ----------------
@app.route('/placement-process', methods=['GET', 'POST'])
def placement_process():
    aid = request.values.get('application', type=int)
    if request.method == 'POST' and aid:
        act = request.form.get('action'); f = request.form
        try:
            with tx():
                ap = q("SELECT a.*, j.job_title, j.company_id FROM applications a JOIN jobs j ON j.job_id=a.job_id WHERE a.application_id=%s", (aid,), one=True)
                if act == 'feedback':
                    ir = q("SELECT * FROM interview_rounds WHERE interview_id=%s AND application_id=%s", (f['interview_id'], aid), one=True)
                    if not ir: raise ValueError('Select an interview round.')
                    if q("SELECT 1 x FROM interview_feedback WHERE interview_id=%s", (ir['interview_id'],)): raise ValueError('Feedback already submitted for this round.')
                    r = [num(f.get(k)) for k in ('technical', 'communication', 'problem_solving', 'overall')]
                    reco = f['recommendation']
                    x("INSERT INTO interview_feedback (interview_id,technical_rating,communication_rating,problem_solving_rating,overall_rating,recommendation,remarks,submitted_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                      (ir['interview_id'], *r, reco, f.get('remarks') or None, session['uid']))
                    x("UPDATE interview_rounds SET status='COMPLETED' WHERE interview_id=%s", (ir['interview_id'],))
                    new = {'NEXT_ROUND': 'INTERVIEWED', 'SELECTED': 'SELECTED', 'REJECTED': 'REJECTED', 'ON_HOLD': 'INTERVIEWED'}[reco]
                    hist(aid, ap['application_status'], new, f"Round {ir['round_number']} feedback: {reco}"); log('PLACEMENT', 'FEEDBACK', aid, reco)
                    flash('Feedback saved and application updated.', 'ok')
                elif act == 'offer':
                    if ap['application_status'] != 'SELECTED': raise ValueError('An offer can only be created for a SELECTED application.')
                    pk = num(f.get('package'))
                    if not f.get('designation') or pk is None or not f.get('offer_date'): raise ValueError('Designation, package and offer date are required.')
                    n = q("SELECT COALESCE(MAX(offer_id),0)+1 n FROM offers", one=True)['n']
                    x("INSERT INTO offers (offer_code,application_id,designation,offered_package_lpa,offer_date,expected_joining_date) VALUES (%s,%s,%s,%s,%s,%s)",
                      (f"OFR-{date.today().year}-{n:03d}", aid, f['designation'], pk, f['offer_date'], f.get('expected_joining') or None))
                    hist(aid, 'SELECTED', 'OFFERED', 'Offer issued'); log('PLACEMENT', 'CREATE_OFFER', aid, 'Offer created'); flash('Offer created.', 'ok')
                elif act == 'offer_status':
                    st = f['offer_status']; of = q("SELECT * FROM offers WHERE application_id=%s", (aid,), one=True)
                    if not of: raise ValueError('No offer exists for this application.')
                    x("UPDATE offers SET offer_status=%s WHERE offer_id=%s", (st, of['offer_id']))
                    if st in ('REJECTED', 'WITHDRAWN') and ap['application_status'] == 'OFFERED': hist(aid, 'OFFERED', 'WITHDRAWN', f'Offer {st.lower()}')
                    log('PLACEMENT', 'OFFER_STATUS', aid, st); flash(f'Offer status updated to {st}.', 'ok')
                elif act in ('joining', 'placed'):
                    of = q("SELECT * FROM offers WHERE application_id=%s", (aid,), one=True)
                    if not of or of['offer_status'] != 'ACCEPTED': raise ValueError('Joining can only be confirmed for an ACCEPTED offer.')
                    js = 'JOINED' if act == 'placed' else f.get('joining_status', 'PENDING')
                    ajd = f.get('actual_joining') or (date.today().isoformat() if js == 'JOINED' else None)
                    pl = q("SELECT * FROM placements WHERE offer_id=%s", (of['offer_id'],), one=True)
                    if pl: x("UPDATE placements SET joining_status=%s, actual_joining_date=%s WHERE placement_id=%s", (js, ajd, pl['placement_id']))
                    else: x("INSERT INTO placements (candidate_id,company_id,job_id,offer_id,designation,final_package_lpa,expected_joining_date,actual_joining_date,joining_status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (ap['candidate_id'], ap['company_id'], ap['job_id'], of['offer_id'], of['designation'], of['offered_package_lpa'], of['expected_joining_date'], ajd, js))
                    if js == 'JOINED':
                        x("UPDATE candidates SET placement_status='PLACED' WHERE candidate_id=%s", (ap['candidate_id'],))
                        if ap['application_status'] != 'JOINED': hist(aid, ap['application_status'], 'JOINED', 'Candidate joined')
                    log('PLACEMENT', 'JOINING', aid, js); flash(f'Joining recorded: {js}.', 'ok')
        except ValueError as ex: flash(str(ex), 'err')
        except mysql.connector.Error as ex: flash(err_msg(ex), 'err')
        return redirect(url_for('placement_process', application=aid, tab=request.form.get('tab', 1)))
    ctx = dict(active='placement-process', ap=None)
    if aid:
        ctx['ap'] = q(f"{APP_SQL} WHERE a.application_id=%s", (aid,), one=True)
        ctx['rounds'] = q("SELECT ir.*, fb.feedback_id FROM interview_rounds ir LEFT JOIN interview_feedback fb ON fb.interview_id=ir.interview_id WHERE ir.application_id=%s ORDER BY round_number", (aid,))
        ctx['round_opts'] = [(r['interview_id'], f"Round {r['round_number']} - {r['round_type']} ({r['status']})") for r in ctx['rounds'] if not r['feedback_id']]
        ctx['fbs'] = q("SELECT fb.*, ir.round_number FROM interview_feedback fb JOIN interview_rounds ir ON ir.interview_id=fb.interview_id WHERE ir.application_id=%s ORDER BY ir.round_number", (aid,))
        ctx['offer'] = q("SELECT * FROM offers WHERE application_id=%s", (aid,), one=True)
        ctx['pl'] = q("SELECT p.* FROM placements p JOIN offers o ON o.offer_id=p.offer_id WHERE o.application_id=%s", (aid,), one=True)
    ctx['tab'] = request.args.get('tab', 1, type=int)
    ctx['pending'] = q(f"{APP_SQL} WHERE a.application_status IN ('INTERVIEW_SCHEDULED','INTERVIEWED','SELECTED','OFFERED') ORDER BY a.application_id")
    ctx['pls'] = q("""SELECT a.application_id, cd.full_name, co.company_name, o.designation, o.offered_package_lpa, o.offer_status, o.expected_joining_date, p.joining_status
        FROM offers o JOIN applications a ON a.application_id=o.application_id JOIN candidates cd ON cd.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id
        JOIN companies co ON co.company_id=j.company_id LEFT JOIN placements p ON p.offer_id=o.offer_id ORDER BY o.offer_id""")
    return render_template('placement_process.html', **ctx)


# ---------------- reports ----------------
@app.route('/reports')
def reports():
    a = request.args; cond, p = [], []
    if a.get('from'): cond.append("DATE(a.applied_at)>=%s"); p.append(a['from'])
    if a.get('to'): cond.append("DATE(a.applied_at)<=%s"); p.append(a['to'])
    if a.get('tech'): cond.append("c.primary_technology=%s"); p.append(a['tech'])
    if a.get('company'): cond.append("j.company_id=%s"); p.append(a['company'])
    if a.get('recruiter'): cond.append("a.assigned_recruiter_id=%s"); p.append(a['recruiter'])
    if a.get('year'): cond.append("c.passing_year=%s"); p.append(a['year'])
    W = ('WHERE ' + ' AND '.join(cond)) if cond else ''
    base = "FROM applications a JOIN candidates c ON c.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id JOIN companies co ON co.company_id=j.company_id LEFT JOIN users u ON u.user_id=a.assigned_recruiter_id LEFT JOIN offers o ON o.application_id=a.application_id LEFT JOIN placements p ON p.offer_id=o.offer_id"
    fun = funnel(W, p); fd = {r['label']: r['n'] for r in fun}
    k = q(f"SELECT COUNT(DISTINCT a.application_id) apps, COUNT(DISTINCT o.offer_id) offers, COUNT(DISTINCT CASE WHEN p.joining_status='JOINED' THEN p.placement_id END) joined {base} {W}", p, one=True)
    ints = q(f"SELECT COUNT(*) n FROM interview_rounds ir JOIN applications a ON a.application_id=ir.application_id JOIN candidates c ON c.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id {W}", p, one=True)['n']
    kpi = dict(apps=k['apps'], ints=ints, sel=fd['Selected'], joined=k['joined'], pct=round(100 * k['joined'] / k['offers'], 1) if k['offers'] else 0)
    grp = lambda col: q(f"SELECT {col} name, COUNT(DISTINCT a.application_id) apps, COUNT(DISTINCT o.offer_id) offers, COUNT(DISTINCT CASE WHEN p.joining_status='JOINED' THEN p.placement_id END) joined {base} {W} GROUP BY {col} ORDER BY joined DESC, apps DESC", p)
    rec = q(f"SELECT u.full_name name, COUNT(DISTINCT a.application_id) apps, COUNT(DISTINCT ir.interview_id) ints, COUNT(DISTINCT CASE WHEN p.joining_status='JOINED' THEN p.placement_id END) joined {base} LEFT JOIN interview_rounds ir ON ir.application_id=a.application_id {W} GROUP BY u.user_id, u.full_name ORDER BY joined DESC", p)
    pend = q(f"{IV_SQL} WHERE ir.status='SCHEDULED' ORDER BY ir.scheduled_date, ir.scheduled_time")
    aging = q("SELECT j.job_code, c.company_name, j.job_title, j.openings, GREATEST(DATEDIFF(CURDATE(), j.posted_date),0) days FROM jobs j JOIN companies c ON c.company_id=j.company_id WHERE j.status='OPEN' ORDER BY days DESC")
    recs = [(str(r['user_id']), r['full_name']) for r in q("SELECT user_id, full_name FROM users WHERE role_id=2")]
    comps = [(str(c['company_id']), c['company_name']) for c in q("SELECT company_id, company_name FROM companies ORDER BY company_name")]
    return render_template('reports.html', kpi=kpi, fun=fun, by_company=grp('co.company_name'), by_tech=grp('c.primary_technology'), rec=rec, pend=pend, aging=aging, a=a, recs=recs, comps=comps, techs=TECHS, years=YEARS, active='reports')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
