from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import datetime
import time

app = Flask(__name__)
socketio = SocketIO(app)

# 기본 D-Day 설정 (예: 2024년 12월 25일)
dday_date = datetime.datetime(2024, 12, 25)

@app.route('/')
def index():
    return render_template('index.html', dday_date=dday_date)

@app.route('/set_dday', methods=['POST'])
def set_dday():
    global dday_date
    # 사용자가 입력한 날짜 정보를 받아서 D-Day를 설정
    year = int(request.form['year'])
    month = int(request.form['month'])
    day = int(request.form['day'])
    dday_date = datetime.datetime(year, month, day)
    
    # D-Day가 변경되었음을 클라이언트에게 알리기
    return jsonify({'status': 'success', 'new_dday': dday_date.strftime('%Y-%m-%d')})


def calculate_dday():
    """D-Day를 계산하는 함수"""
    now = datetime.datetime.now()
    delta = dday_date - now
    return delta.days, delta.seconds

@socketio.on('connect')
def handle_connect():
    """클라이언트가 연결될 때 D-Day 정보를 보내기"""
    days_left, seconds_left = calculate_dday()
    emit('dday_update', {'days': days_left, 'seconds': seconds_left})

def update_dday():
    """실시간으로 D-Day를 갱신하는 함수"""
    while True:
        time.sleep(1)  # 1초마다 업데이트
        days_left, seconds_left = calculate_dday()
        socketio.emit('dday_update', {'days': days_left, 'seconds': seconds_left})
        
if __name__ == '__main__':
    from threading import Thread
    # 실시간 업데이트를 위한 백그라운드 스레드 실행
    thread = Thread(target=update_dday)
    thread.daemon = True
    thread.start()

    socketio.run(app)
