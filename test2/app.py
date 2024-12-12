from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit
import psycopg2
import psycopg2.extras
import datetime
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = 'your-secret-key'
socketio = SocketIO(app)

def get_db():
    return psycopg2.connect(
        host='localhost',
        database='calendar_db',
        user='postgres',
        password='root',  # PostgreSQL 설치시 설정한 비밀번호로 변경
        port=5432
    )

def create_tables():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # users 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    password VARCHAR(120) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ddays 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ddays (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    title VARCHAR(200),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # saved_dates 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_dates (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    title VARCHAR(200),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
        conn.commit()
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['id']
                return redirect(url_for('welcome'))
            else:
                return render_template('index.html', error="Invalid credentials")
    finally:
        conn.close()

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def process_signup():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 사용자 존재 확인
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return render_template('signup.html', error="Username already exists")
            
            # 새 사용자 추가
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
                (username, password)
            )
            conn.commit()
            return redirect(url_for('index'))
    except Exception as e:
        conn.rollback()
        return render_template('signup.html', error=str(e))
    finally:
        conn.close()

@app.route('/welcome')
def welcome():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                "SELECT username FROM users WHERE id = %s",
                (session['user_id'],)
            )
            user = cursor.fetchone()
            return render_template('welcome.html', user=user['username'])
    finally:
        conn.close()

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # D-Day 조회
            cursor.execute(
                """SELECT date, title 
                   FROM ddays 
                   WHERE user_id = %s 
                   ORDER BY date DESC LIMIT 1""",
                (session['user_id'],)
            )
            dday = cursor.fetchone()
            
            # 저장된 날짜들 조회
            cursor.execute(
                """SELECT date, title, description 
                   FROM saved_dates 
                   WHERE user_id = %s 
                   ORDER BY date""",
                (session['user_id'],)
            )
            saved_dates = cursor.fetchall()
            
            # 날짜 형식 변환
            if dday:
                dday['date'] = dday['date'].strftime('%Y-%m-%d')
            saved_dates = [{
                'date': date['date'].strftime('%Y-%m-%d'),
                'title': date['title'],
                'description': date['description']
            } for date in saved_dates]
                
            return render_template('calendar.html', 
                                 dday_date=dday['date'] if dday else None,
                                 saved_dates=saved_dates)
    finally:
        conn.close()

@app.route('/set_dday', methods=['POST'])
def set_dday():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'})
        
    year = int(request.form['year'])
    month = int(request.form['month'])
    day = int(request.form['day'])
    title = request.form['title']
    description = request.form['description']
    date = datetime.date(year, month, day)
    
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 기존 D-Day 삭제
            cursor.execute(
                "DELETE FROM ddays WHERE user_id = %s",
                (session['user_id'],)
            )
            
            # 새 D-Day 추가
            cursor.execute(
                """INSERT INTO ddays (user_id, date, title, description)
                   VALUES (%s, %s, %s, %s)""",
                (session['user_id'], date, title, description)
            )
            
            # Saved Date 추가
            cursor.execute(
                """INSERT INTO saved_dates (user_id, date, title, description)
                   VALUES (%s, %s, %s, %s)""",
                (session['user_id'], date, title, description)
            )
            
        conn.commit()
        return jsonify({
            'status': 'success',
            'new_dday': date.strftime('%Y-%m-%d'),
            'title': title
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

def calculate_dday(dday_date):
    now = datetime.datetime.now().date()
    delta = dday_date - now
    return delta.days

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        conn = get_db()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(
                    """SELECT date FROM ddays 
                       WHERE user_id = %s 
                       ORDER BY date DESC LIMIT 1""",
                    (session['user_id'],)
                )
                dday = cursor.fetchone()
                if dday:
                    days_left = calculate_dday(dday['date'])
                    emit('dday_update', {'days': days_left})
        finally:
            conn.close()

def update_dday():
    while True:
        try:
            conn = get_db()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(
                    """SELECT u.username, d.date 
                       FROM users u 
                       JOIN ddays d ON u.id = d.user_id"""
                )
                results = cursor.fetchall()
                
                for result in results:
                    days_left = calculate_dday(result['date'])
                    socketio.emit('dday_update', {
                        'user': result['username'],
                        'days': days_left
                    })
        except Exception as e:
            print(f"Error in update_dday: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
            time.sleep(1)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    create_tables()
    
    thread = Thread(target=update_dday)
    thread.daemon = True
    thread.start()
    
    socketio.run(app, debug=True)