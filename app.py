from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from pathlib import Path
import sqlite3, json, shutil, uuid, os

ROOT = Path(__file__).parent
# Use a mounted persistent disk in production; fall back to the local project DB for development.
DB = Path(os.getenv('DATABASE_PATH', str(ROOT / 'data' / 'gateprep.db')))
DB.parent.mkdir(parents=True, exist_ok=True)
app = FastAPI(title='GATE Prep Hub API', version='2.0.0')

RESOURCES = [
('Official syllabus','Official GATE DA 2027 syllabus PDF','Syllabus','Official', 'https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/DA_GATE2027_Syllabus.pdf','Official IIT Madras syllabus. Always use this revised 2027 syllabus as the source of truth.'),
('Official exam portal','GATE 2027 official website','Exam & PYQ','Official','https://gate2027.iitm.ac.in/','Notifications, exam details and official updates from IIT Madras.'),
('Official pattern','GATE 2027 question paper pattern','Exam & PYQ','Official','https://gate2027.iitm.ac.in/question_paper_pattern','CBT format, question types, duration and marking rules.'),
('Official downloads','GATE 2027 downloads and previous papers','Exam & PYQ','Official','https://gate2027.iitm.ac.in/download','Official question papers and answer keys where published.'),
('GATE DA 2026 paper','Official GATE DA 2026 question paper PDF','Exam & PYQ','Official','https://gate2027.iitm.ac.in/static/doc/download/2026/QPs/DA.pdf','Official GATE 2026 DA question paper from IIT Guwahati.'),
('GATE DA 2026 answer key','Official GATE DA 2026 answer key PDF','Exam & PYQ','Official','https://gate2027.iitm.ac.in/static/doc/download/2026/Keys/DA_Keys.pdf','Official answer key. Use alongside the corresponding master question paper.'),
('GATE DA 2025 paper','Official GATE DA 2025 question paper PDF','Exam & PYQ','Official','https://gate2027.iitm.ac.in/static/doc/download/2025/DA2025.pdf','Official GATE 2025 DA question paper.'),
('GATE DA 2025 answer key','Official GATE DA 2025 answer key PDF','Exam & PYQ','Official','https://gate2027.iitm.ac.in/static/doc/download/2025_Key/DA_Keys.pdf','Official GATE 2025 DA answer key.'),
('GATE DA 2024 paper','Official GATE DA 2024 question paper PDF','Exam & PYQ','Official','https://gate2027.iitm.ac.in/static/doc/download/2024/DA24S1.pdf','Official GATE 2024 DA question paper.'),
('GATE DA 2024 answer key','Official GATE DA 2024 final answer key PDF','Exam & PYQ','Official','https://gate2027.iitm.ac.in/static/doc/download/2024/DAFinalAnswerKey.pdf','Official GATE 2024 DA final answer key.'),
('GATE 2026 archive','GATE 2026 official downloads archive','Exam & PYQ','Official','https://gate2026.iitg.ac.in/download.html','Year-wise papers and answer keys from the organising institute.'),
('NPTEL','NPTEL course catalogue','Courses','IIT / NPTEL','https://nptel.ac.in/courses','Free-to-audit IIT courses. Certificate exams may have a fee.'),
('SWAYAM','SWAYAM course catalogue','Courses','Government','https://swayam.gov.in/','Government of India online courses; check course audit and certificate terms.'),
('MIT OCW','MIT OpenCourseWare','Courses','University','https://ocw.mit.edu/','Free lecture notes, assignments and course materials.'),
('MIT Linear Algebra','MIT 18.06 Linear Algebra','Linear Algebra','University','https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/','Gilbert Strang lectures, problem sets and exams.'),
('Khan Academy Statistics','Statistics and probability','Probability & Statistics','Learning platform','https://www.khanacademy.org/math/statistics-probability','Structured explanations and practice for probability and statistics.'),
('StatQuest','StatQuest with Josh Starmer','Machine Learning','Video lectures','https://statquest.org/','Visual explanations of statistics, machine learning and AI.'),
('3Blue1Brown','Essence of linear algebra','Linear Algebra','Video lectures','https://www.3blue1brown.com/topics/linear-algebra','Intuitive visual lessons on vectors, matrices and transformations.'),
('3Blue1Brown calculus','Essence of calculus','Calculus & Optimization','Video lectures','https://www.3blue1brown.com/topics/calculus','Visual intuition for derivatives, integrals and calculus.'),
('Python docs','Official Python tutorial','Programming & DSA','Documentation','https://docs.python.org/3/tutorial/','Python language fundamentals and reference.'),
('Python practice','Exercism Python track','Programming & DSA','Practice','https://exercism.org/tracks/python','Practice Python through small exercises and feedback.'),
('VisuAlgo','Algorithm visualisations','Programming & DSA','Interactive','https://visualgo.net/en','Visualise searching, sorting, trees and graph algorithms.'),
('OpenDSA','OpenDSA learning modules','Programming & DSA','University','https://opendsa-server.cs.vt.edu/','Interactive data structures and algorithms learning material.'),
('SQLBolt','Interactive SQL lessons','DBMS & Warehousing','Interactive','https://sqlbolt.com/','Browser-based SQL lessons and exercises.'),
('Mode SQL','SQL tutorial','DBMS & Warehousing','Practice','https://mode.com/sql-tutorial/','SQL concepts and hands-on examples.'),
('PostgreSQL tutorial','PostgreSQL official tutorial','DBMS & Warehousing','Documentation','https://www.postgresql.org/docs/current/tutorial.html','Relational database and SQL fundamentals.'),
('Kaggle Learn','Kaggle micro-courses','Machine Learning','Practice','https://www.kaggle.com/learn','Hands-on Python, pandas, data visualisation and ML courses.'),
('Google ML Crash Course','Machine Learning Crash Course','Machine Learning','University / Industry','https://developers.google.com/machine-learning/crash-course','Free ML lessons, interactive visualisations and exercises.'),
('scikit-learn','scikit-learn user guide','Machine Learning','Documentation','https://scikit-learn.org/stable/user_guide.html','Reliable reference for classical ML algorithms and evaluation.'),
('Andrew Ng ML','Machine Learning Specialization','Machine Learning','Course','https://www.coursera.org/specializations/machine-learning-introduction','Course overview; audit availability and fees can change.'),
('Dive into Deep Learning','Dive into Deep Learning textbook','Machine Learning','Open textbook','https://d2l.ai/','Interactive open textbook for deep learning.'),
('AIMA','Artificial Intelligence: A Modern Approach resources','Artificial Intelligence','Textbook resources','https://aima.cs.berkeley.edu/','Companion resources for search, logic and AI.'),
('Berkeley AI','UC Berkeley CS188 materials','Artificial Intelligence','University','https://inst.eecs.berkeley.edu/~cs188/','Lecture material and projects covering AI search and reasoning.'),
('MIT Probability','MIT probability and statistics courses','Probability & Statistics','University','https://ocw.mit.edu/search/?q=probability','Open course materials for probability and statistics.'),
('MIT Algorithms','MIT algorithms courses','Programming & DSA','University','https://ocw.mit.edu/search/?q=algorithms','Lecture notes and problem sets for algorithms.'),
('NIST statistics','NIST Engineering Statistics Handbook','Probability & Statistics','Reference','https://www.itl.nist.gov/div898/handbook/','Detailed reference for statistical methods and distributions.'),
('OpenIntro Statistics','OpenIntro Statistics textbook','Probability & Statistics','Open textbook','https://www.openintro.org/book/os/','Free statistics textbook and datasets.'),
('Pandas','Pandas documentation','Programming & DSA','Documentation','https://pandas.pydata.org/docs/','Data manipulation and analysis reference.'),
('NumPy','NumPy documentation','Linear Algebra','Documentation','https://numpy.org/doc/stable/','Numerical computing and array operations.'),
('Google Colab','Google Colaboratory','Programming & DSA','Tools','https://colab.research.google.com/','Run Python notebooks in the browser.'),
('GATE Overflow','GATE Overflow','Practice & Community','Community','https://gateoverflow.in/','Community explanations and discussion; cross-check answers against official keys.'),
('GeeksforGeeks','DSA and CS tutorials','Programming & DSA','Practice','https://www.geeksforgeeks.org/','Supplementary explanations and coding practice.'),
('IndiaBix','Quantitative aptitude practice','General Aptitude','Practice','https://www.indiabix.com/','Extra aptitude practice; not an official GATE source.'),
('GATE DA community papers','Community-maintained DA PYQ index','Exam & PYQ','Community','https://github.com/DS-AI-GATE/dsai-gate/tree/main/PYQ','Convenient index of DA papers; verify documents against official GATE releases.')
]

SYLLABUS = [
('Probability and Statistics',['Counting: permutations and combinations','Probability axioms, sample space and events','Independent and mutually exclusive events','Marginal, conditional and joint probability','Bayes theorem and conditional expectation','Mean, median, mode, variance and standard deviation','Correlation and covariance','Random variables, PMF, PDF and CDF','Uniform, Bernoulli, binomial, exponential, Poisson and normal distributions','t and chi-squared distributions','Conditional PDF and central limit theorem','Confidence intervals, z-test, t-test and chi-squared test']),
('Linear Algebra',['Vector spaces and subspaces','Linear dependence and independence','Matrices and matrix properties','Projection, orthogonal and idempotent matrices','Quadratic forms and linear systems','Gaussian elimination, rank and nullity','Eigenvalues and eigenvectors','Determinants and projections','LU decomposition and singular value decomposition']),
('Calculus and Optimization',['Functions of one variable','Limits, continuity and differentiability','Taylor series','Maxima and minima','Single-variable optimization']),
('Programming, Data Structures and Algorithms',['Python programming','Stacks, queues and linked lists','Trees and hash tables','Linear and binary search','Selection, bubble and insertion sort','Merge sort and quicksort','Introduction to graph theory','Graph traversals and shortest paths']),
('Database Management and Warehousing',['ER model and relational model','Relational algebra and tuple calculus','SQL and integrity constraints','Normal forms and normalization','File organization, indexing and data types','Data transformation: normalization, discretization, sampling and compression','Data warehouse schemas and multidimensional models','Concept hierarchies and measures']),
('Machine Learning',['Regression and classification','Simple and multiple linear regression','Ridge and logistic regression','k-nearest neighbours and naive Bayes','Linear discriminant analysis and SVM','Decision trees and bias-variance trade-off','LOO and k-fold cross-validation','Multi-layer perceptron and feed-forward neural networks','Clustering: k-means, k-medoid and hierarchical','Single-linkage and multiple-linkage','Dimensionality reduction and PCA']),
('Artificial Intelligence',['Informed and uninformed search','Adversarial search','Propositional and predicate logic','Reasoning under uncertainty','Conditional independence representation','Exact inference through variable elimination','Approximate inference through sampling']),
('General Aptitude',['Verbal aptitude','Quantitative aptitude','Analytical aptitude','Spatial aptitude'])
]

QUESTIONS = [
{'subject':'Probability and Statistics','topic':'Conditional probability','type':'MCQ','marks':1,'prompt':'A fair coin is tossed twice. Given that at least one toss is a head, what is the probability that both tosses are heads?','options':['1/4','1/3','1/2','2/3'],'answer':'1/3','explanation':'The equally likely outcomes after excluding TT are HH, HT and TH. Only HH has two heads, so the probability is 1/3.','source':'Original practice question'},
{'subject':'Linear Algebra','topic':'Matrix rank','type':'MCQ','marks':1,'prompt':'What is the rank of the matrix [[1, 2], [2, 4]]?','options':['0','1','2','4'],'answer':'1','explanation':'The second row is twice the first row, so there is only one linearly independent row.','source':'Original practice question'},
{'subject':'Calculus and Optimization','topic':'Derivatives','type':'NAT','marks':1,'prompt':'For f(x) = x² - 6x + 11, enter the x-coordinate of its minimum.','options':[],'answer':'3','explanation':'f\'(x)=2x-6. Setting the derivative to zero gives x=3; the second derivative is positive.','source':'Original practice question'},
{'subject':'Programming, Data Structures and Algorithms','topic':'Complexity','type':'MCQ','marks':1,'prompt':'What is the time complexity of binary search on a sorted array of n elements?','options':['O(1)','O(log n)','O(n)','O(n log n)'],'answer':'O(log n)','explanation':'Each comparison halves the remaining search interval.','source':'Original practice question'},
{'subject':'Database Management and Warehousing','topic':'SQL','type':'MCQ','marks':1,'prompt':'Which SQL clause filters groups after aggregation?','options':['WHERE','ORDER BY','HAVING','DISTINCT'],'answer':'HAVING','explanation':'WHERE filters rows before grouping; HAVING filters groups after aggregation.','source':'Original practice question'},
{'subject':'Machine Learning','topic':'Bias variance','type':'MCQ','marks':2,'prompt':'A model has very low training error and high test error. Which issue is most likely?','options':['Underfitting','Overfitting','High bias only','Data normalisation'],'answer':'Overfitting','explanation':'A large generalisation gap indicates the model fits training data too closely.','source':'Original practice question'},
{'subject':'Artificial Intelligence','topic':'Search algorithms','type':'MCQ','marks':1,'prompt':'In A* search, which evaluation function is commonly used?','options':['f(n)=h(n)','f(n)=g(n)','f(n)=g(n)+h(n)','f(n)=g(n)-h(n)'],'answer':'f(n)=g(n)+h(n)','explanation':'A* combines the path cost so far g(n) and heuristic estimate h(n).','source':'Original practice question'},
{'subject':'General Aptitude','topic':'Percentages','type':'NAT','marks':1,'prompt':'A value increases from 80 to 100. Enter the percentage increase.','options':[],'answer':'25','explanation':'Percentage increase = (20/80) × 100 = 25%.','source':'Original practice question'}
]

SCHEMA = '''
CREATE TABLE IF NOT EXISTS resources(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,description TEXT,category TEXT,provider TEXT,url TEXT UNIQUE,notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS syllabus(id INTEGER PRIMARY KEY AUTOINCREMENT,subject TEXT NOT NULL,topic TEXT NOT NULL,completed INTEGER DEFAULT 0,confidence INTEGER DEFAULT 0,notes TEXT,UNIQUE(subject,topic));
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,subject TEXT,due_date TEXT,minutes INTEGER DEFAULT 30,done INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,subject TEXT,body TEXT NOT NULL,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS bookmarks(id INTEGER PRIMARY KEY AUTOINCREMENT,resource_id INTEGER UNIQUE REFERENCES resources(id));
CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,minutes INTEGER NOT NULL,subject TEXT,session_date TEXT DEFAULT CURRENT_DATE);
CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT,subject TEXT,topic TEXT,qtype TEXT,marks INTEGER,prompt TEXT,options TEXT,answer TEXT,explanation TEXT,source TEXT);
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,question_id INTEGER,answer TEXT,is_correct INTEGER,attempted_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS flashcards(id INTEGER PRIMARY KEY AUTOINCREMENT,subject TEXT,front TEXT,back TEXT,due_at TEXT DEFAULT CURRENT_TIMESTAMP,ease REAL DEFAULT 2.5,interval_days INTEGER DEFAULT 0,repetitions INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS uploads(id INTEGER PRIMARY KEY AUTOINCREMENT,filename TEXT,mime_type TEXT,size_bytes INTEGER,content BLOB,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
'''

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c

def init_db():
    with conn() as c:
        c.executescript(SCHEMA)
        upload_cols = [r['name'] for r in c.execute('PRAGMA table_info(uploads)')]
        if 'content' not in upload_cols: c.execute('ALTER TABLE uploads ADD COLUMN content BLOB')
        if c.execute('SELECT COUNT(*) FROM resources').fetchone()[0] == 0:
            c.executemany('INSERT OR IGNORE INTO resources(title,description,category,provider,url,notes) VALUES(?,?,?,?,?,?)', RESOURCES)
        if c.execute('SELECT COUNT(*) FROM syllabus').fetchone()[0] == 0:
            for subject, topics in SYLLABUS:
                c.executemany('INSERT OR IGNORE INTO syllabus(subject,topic) VALUES(?,?)', [(subject,t) for t in topics])
        if c.execute('SELECT COUNT(*) FROM questions').fetchone()[0] == 0:
            c.executemany('INSERT INTO questions(subject,topic,qtype,marks,prompt,options,answer,explanation,source) VALUES(?,?,?,?,?,?,?,?,?)',[(q['subject'],q['topic'],q['type'],q['marks'],q['prompt'],json.dumps(q['options']),q['answer'],q['explanation'],q['source']) for q in QUESTIONS])
        if c.execute('SELECT COUNT(*) FROM flashcards').fetchone()[0] == 0:
            cards=[('Probability and Statistics','What is Bayes theorem?','P(A|B) = P(B|A)P(A) / P(B), for P(B)>0.'),('Linear Algebra','What is the rank of a matrix?','The dimension of its row space or column space; equivalently, the number of pivots.'),('Calculus and Optimization','What condition is necessary for an interior differentiable local extremum?','The first derivative is zero. This is necessary but not sufficient.'),('Programming, Data Structures and Algorithms','What is binary search time complexity?','O(log n) on a sorted random-access collection.'),('Machine Learning','What is overfitting?','When a model captures noise or peculiarities in training data and generalises poorly.')]
            c.executemany('INSERT INTO flashcards(subject,front,back) VALUES(?,?,?)',cards)

init_db()

class TaskIn(BaseModel): title:str; subject:str='General'; due_date:str=''; minutes:int=30
class NoteIn(BaseModel): title:str; subject:str='General'; body:str
class ProgressIn(BaseModel): completed:int|None=None; confidence:int|None=None; notes:str|None=None
class AnswerIn(BaseModel): answer:str
class SessionIn(BaseModel): minutes:int; subject:str='Focus session'
class CardIn(BaseModel): subject:str; front:str; back:str

@app.get('/api/health')
def health(): return {'status':'ok','database':'SQLite','database_path':str(DB)}
@app.get('/api/dashboard')
def dashboard():
    with conn() as c:
        total=c.execute('SELECT COUNT(*) FROM syllabus').fetchone()[0]; done=c.execute('SELECT COUNT(*) FROM syllabus WHERE completed=1').fetchone()[0]
        task_total=c.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]; task_done=c.execute('SELECT COUNT(*) FROM tasks WHERE done=1').fetchone()[0]
        mins=c.execute('SELECT COALESCE(SUM(minutes),0) FROM sessions').fetchone()[0]
        attempts=c.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]; correct=c.execute('SELECT COALESCE(SUM(is_correct),0) FROM attempts').fetchone()[0]
        subjects=[dict(r) for r in c.execute('SELECT subject,COUNT(*) total,SUM(completed) done,ROUND(AVG(confidence),1) confidence FROM syllabus GROUP BY subject ORDER BY subject')]
        upcoming=[dict(r) for r in c.execute('SELECT * FROM tasks WHERE done=0 ORDER BY CASE WHEN due_date="" THEN 1 ELSE 0 END,due_date LIMIT 5')]
        return {'topics_total':total,'topics_done':done,'progress':round(done/total*100) if total else 0,'tasks_total':task_total,'tasks_done':task_done,'study_minutes':mins,'attempts':attempts,'accuracy':round(correct/attempts*100) if attempts else 0,'subjects':subjects,'upcoming':upcoming,'resources':c.execute('SELECT COUNT(*) FROM resources').fetchone()[0]}
@app.get('/api/resources')
def get_resources(q:str='',category:str='All'):
    with conn() as c:
        sql='SELECT r.*,CASE WHEN b.id IS NULL THEN 0 ELSE 1 END bookmarked FROM resources r LEFT JOIN bookmarks b ON b.resource_id=r.id WHERE (r.title LIKE ? OR r.description LIKE ? OR r.provider LIKE ?)'
        args=[f'%{q}%']*3
        if category!='All': sql+=' AND r.category=?'; args.append(category)
        sql+=' ORDER BY r.category,r.title'
        return [dict(r) for r in c.execute(sql,args)]
@app.get('/api/categories')
def categories():
    with conn() as c: return [r[0] for r in c.execute('SELECT DISTINCT category FROM resources ORDER BY category')]
@app.post('/api/resources')
def add_resource(data:dict):
    with conn() as c:
        try:
            cur=c.execute('INSERT INTO resources(title,description,category,provider,url,notes) VALUES(?,?,?,?,?,?)',(data.get('title'),data.get('description',''),data.get('category','Other'),data.get('provider','User added'),data.get('url'),data.get('notes','')))
            return {'id':cur.lastrowid}
        except sqlite3.IntegrityError: raise HTTPException(409,'This resource URL already exists.')
@app.get('/api/syllabus')
def get_syllabus():
    with conn() as c:
        rows=[dict(r) for r in c.execute('SELECT * FROM syllabus ORDER BY id')]
        groups={}
        for r in rows: groups.setdefault(r['subject'],[]).append(r)
        return groups
@app.patch('/api/syllabus/{topic_id}')
def update_syllabus(topic_id:int,data:ProgressIn):
    fields=[]; vals=[]
    for k in ['completed','confidence','notes']:
        v=getattr(data,k)
        if v is not None: fields.append(f'{k}=?'); vals.append(v)
    if not fields: return {'ok':True}
    vals.append(topic_id)
    with conn() as c:
        c.execute(f'UPDATE syllabus SET {", ".join(fields)} WHERE id=?',vals)
        if c.total_changes==0: raise HTTPException(404,'Topic not found')
    return {'ok':True}
@app.get('/api/tasks')
def tasks():
    with conn() as c: return [dict(r) for r in c.execute('SELECT * FROM tasks ORDER BY done,due_date,id DESC')]
@app.post('/api/tasks')
def create_task(data:TaskIn):
    with conn() as c:
        cur=c.execute('INSERT INTO tasks(title,subject,due_date,minutes) VALUES(?,?,?,?)',(data.title,data.subject,data.due_date,data.minutes)); return {'id':cur.lastrowid}
@app.patch('/api/tasks/{task_id}')
def toggle_task(task_id:int):
    with conn() as c: c.execute('UPDATE tasks SET done=1-done WHERE id=?',(task_id,)); return {'ok':True}
@app.delete('/api/tasks/{task_id}')
def delete_task(task_id:int):
    with conn() as c: c.execute('DELETE FROM tasks WHERE id=?',(task_id,)); return {'ok':True}
@app.get('/api/notes')
def notes():
    with conn() as c: return [dict(r) for r in c.execute('SELECT * FROM notes ORDER BY updated_at DESC')]
@app.post('/api/notes')
def save_note(data:NoteIn):
    with conn() as c:
        c.execute('INSERT INTO notes(title,subject,body,updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP)',(data.title,data.subject,data.body)); return {'ok':True}
@app.delete('/api/notes/{note_id}')
def delete_note(note_id:int):
    with conn() as c: c.execute('DELETE FROM notes WHERE id=?',(note_id,)); return {'ok':True}
@app.get('/api/bookmarks')
def bookmarks():
    with conn() as c: return [dict(r) for r in c.execute('SELECT r.* FROM resources r JOIN bookmarks b ON b.resource_id=r.id ORDER BY r.title')]
@app.post('/api/bookmarks/{resource_id}')
def toggle_bookmark(resource_id:int):
    with conn() as c:
        if c.execute('SELECT 1 FROM bookmarks WHERE resource_id=?',(resource_id,)).fetchone(): c.execute('DELETE FROM bookmarks WHERE resource_id=?',(resource_id,)); return {'bookmarked':False}
        c.execute('INSERT OR IGNORE INTO bookmarks(resource_id) VALUES(?)',(resource_id,)); return {'bookmarked':True}
@app.get('/api/questions')
def questions(subject:str='All',limit:int=50):
    with conn() as c:
        if subject=='All': rows=c.execute('SELECT id,subject,topic,qtype,marks,prompt,options,source FROM questions ORDER BY RANDOM() LIMIT ?',(limit,))
        else: rows=c.execute('SELECT id,subject,topic,qtype,marks,prompt,options,source FROM questions WHERE subject=? ORDER BY RANDOM() LIMIT ?',(subject,limit))
        return [{**dict(r),'options':json.loads(r['options'])} for r in rows]
@app.post('/api/questions/{qid}/answer')
def answer(qid:int,data:AnswerIn):
    with conn() as c:
        q=c.execute('SELECT answer,explanation FROM questions WHERE id=?',(qid,)).fetchone()
        if not q: raise HTTPException(404,'Question not found')
        ok=data.answer.strip().lower()==q['answer'].strip().lower()
        c.execute('INSERT INTO attempts(question_id,answer,is_correct) VALUES(?,?,?)',(qid,data.answer,int(ok)))
        return {'correct':ok,'answer':q['answer'],'explanation':q['explanation']}
@app.get('/api/flashcards')
def flashcards():
    with conn() as c: return [dict(r) for r in c.execute('SELECT * FROM flashcards ORDER BY id')]
@app.post('/api/flashcards')
def add_card(data:CardIn):
    with conn() as c: cur=c.execute('INSERT INTO flashcards(subject,front,back) VALUES(?,?,?)',(data.subject,data.front,data.back)); return {'id':cur.lastrowid}
@app.post('/api/sessions')
def add_session(data:SessionIn):
    with conn() as c: c.execute('INSERT INTO sessions(minutes,subject) VALUES(?,?)',(data.minutes,data.subject)); return {'ok':True}
@app.get('/api/analytics')
def analytics():
    with conn() as c:
        bysubject=[dict(r) for r in c.execute('SELECT q.subject,COUNT(*) attempts,SUM(a.is_correct) correct,ROUND(AVG(a.is_correct)*100,1) accuracy FROM attempts a JOIN questions q ON q.id=a.question_id GROUP BY q.subject')]
        daily=[dict(r) for r in c.execute('SELECT session_date, SUM(minutes) minutes FROM sessions GROUP BY session_date ORDER BY session_date DESC LIMIT 14')]
        return {'by_subject':bysubject,'daily':daily}
@app.post('/api/upload')
async def upload(file:UploadFile=File(...)):
    safe=Path(file.filename).name
    if Path(safe).suffix.lower() not in ['.pdf','.doc','.docx','.ppt','.pptx','.txt','.md','.csv','.xlsx','.png','.jpg','.jpeg']:
        raise HTTPException(400,'File type not supported')
    content=await file.read()
    size=len(content)
    if size > 25*1024*1024: raise HTTPException(413,'Maximum upload size is 25 MB')
    with conn() as c:
        cur=c.execute('INSERT INTO uploads(filename,mime_type,size_bytes,content) VALUES(?,?,?,?)',(safe,file.content_type or 'application/octet-stream',size,content))
        return {'id':cur.lastrowid,'filename':safe,'size_bytes':size}
@app.get('/api/uploads')
def uploads():
    with conn() as c: return [dict(r) for r in c.execute('SELECT id,filename,mime_type,size_bytes,created_at FROM uploads ORDER BY id DESC')]
@app.get('/api/uploads/{upload_id}')
def download_upload(upload_id:int):
    with conn() as c: row=c.execute('SELECT * FROM uploads WHERE id=?',(upload_id,)).fetchone()
    if not row: raise HTTPException(404,'File not found')
    if row['content'] is None: raise HTTPException(410,'This older upload is not stored in the database; please upload it again.')
    return Response(content=row['content'],media_type=row['mime_type'],headers={'Content-Disposition':f'attachment; filename="{row["filename"]}"'})
@app.get('/api/export')
def export_data():
    with conn() as c:
        data={}
        for table in ['resources','syllabus','tasks','notes','bookmarks','sessions','questions','attempts','flashcards']:
            data[table]=[dict(r) for r in c.execute(f'SELECT * FROM {table}')]
        data['uploads']=[dict(r) for r in c.execute('SELECT id,filename,mime_type,size_bytes,created_at FROM uploads')]
        return data
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
@app.get('/')
def home(): return FileResponse(ROOT/'static'/'index.html')
