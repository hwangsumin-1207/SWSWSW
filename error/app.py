from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit
import datetime
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 세션 암호화 키
socketio = SocketIO(app)

# 가상의 사용자 데이터베이스
users = {"user1": "password1", "user2": "password2"}

# 사용자별 D-Day와 저장된 날짜 저장
user_ddays = {"user1": datetime.datetime(2024, 12, 25), "user2": datetime.datetime(2024, 12, 31)}
user_saved_dates = {"user1": [], "user2": []}  # 사용자별 저장된 날짜 리스트 (날짜, 제목, 설명 포함)

@app.route('/')
def index():
    return render_template('index.html')

# 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username] == password:
        session['user'] = username  # 세션에 사용자 저장
        return redirect(url_for('welcome'))
    else:
        return render_template('index.html', error="Invalid credentials")

# 회원가입 페이지
@app.route('/signup')
def signup():
    return render_template('signup.html')

# 회원가입 처리
@app.route('/signup', methods=['POST'])
def process_signup():
    username = request.form['username']
    password = request.form['password']
    
    if username in users:
        return render_template('signup.html', error="Username already exists")
    
    users[username] = password  # 새로운 사용자 추가
    user_ddays[username] = None  # 새로운 사용자에 대한 D-Day 추가
    user_saved_dates[username] = []  # 새로운 사용자에 대한 Saved Dates 추가
    return redirect(url_for('index'))

# 로그인 성공 후 페이지
@app.route('/welcome')
def welcome():
    if 'user' in session:
        return render_template('welcome.html', user=session['user'])
    else:
        return redirect(url_for('index'))

# 캘린더 페이지
@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if 'user' in session:
        user = session['user']
        dday_date = user_ddays.get(user, None)
        saved_dates = user_saved_dates.get(user, [])
        
        # 검색어 받기
        search_query = request.args.get('search', '').lower()  # search 파라미터 받기 (소문자로 변환)
        
        # 검색 결과 필터링
        if search_query:
            filtered_dates = [
                date_info for date_info in saved_dates
                if search_query in date_info['title'].lower() or search_query in date_info['date']
            ]
        else:
            filtered_dates = saved_dates  # 검색어가 없으면 전체 리스트 반환

        return render_template('calendar.html', dday_date=dday_date, saved_dates=saved_dates, filtered_dates=filtered_dates, search_query=search_query)
    else:
        return redirect(url_for('index'))

# D-Day 설정
@app.route('/set_dday', methods=['POST'])
def set_dday():
    if 'user' in session:
        user = session['user']
        year = int(request.form['year'])
        month = int(request.form['month'])
        day = int(request.form['day'])
        title = request.form['title']
        description = request.form['description']
        new_date = datetime.datetime(year, month, day)

        # D-Day 저장
        user_ddays[user] = new_date
        user_saved_dates[user].append({
            'date': new_date.strftime('%Y-%m-%d'),
            'title': title,
            'description': description
        })

        # D-Day 정보 클라이언트로 보내기
        socketio.emit('dday_update', {
            'days': (new_date - datetime.datetime.now()).days,
            'seconds': int((new_date - datetime.datetime.now()).total_seconds())
        })

        return jsonify({'status': 'success', 'new_dday': new_date.strftime('%Y-%m-%d')})
    else:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

if __name__ == "__main__":
    socketio.run(app)




