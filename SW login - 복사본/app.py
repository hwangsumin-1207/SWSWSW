from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 세션 암호화 키

# 가상의 사용자 데이터베이스
users = {"user1": "password1", "user2": "password2"}

# 사용자별 D-day 저장을 위한 데이터베이스 (예: {username: [dates]})
user_dates = {"user1": [], "user2": []}

# 기본 페이지 (로그인 화면)
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
    user_dates[username] = []  # 새로운 사용자에 대한 날짜 리스트 추가
    return redirect(url_for('index'))

# 로그인 성공 후 페이지
@app.route('/welcome')
def welcome():
    if 'user' in session:
        return render_template('welcome.html', user=session['user'])
    else:
        return redirect(url_for('index'))

# 캘린더 페이지
@app.route('/calendar')
def calendar():
    if 'user' in session:
        # 저장된 날짜를 캘린더에 표시할 수 있도록 전달
        user = session['user']
        saved_dates = user_dates.get(user, [])
        return render_template('calendar.html', saved_dates=saved_dates)
    else:
        return redirect(url_for('index'))

# 특정 날짜 저장
@app.route('/save_date', methods=['POST'])
def save_date():
    if 'user' in session:
        user = session['user']
        date = request.form['date']
        
        if date not in user_dates[user]:
            user_dates[user].append(date)  # 날짜 저장
        
        return redirect(url_for('calendar'))
    else:
        return redirect(url_for('index'))

# 로그아웃 처리
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
