기말과제
--------------------------------
추가적으로 설치 필요
--------------------------------
PostgreSQL

위의 터미널 관리자모드로 실행후 
CREATE DATABASE calendar_db; 입력

터미널에서 모듈 설치 필요
pip install flask/
pip install flask flask-socketio/
pip install psycopg2 flask-socketio/


실행 시 User Account 목록이뜸.
이전에 만들어뒀던 계정이 존재할 경우 입력하여 로그인시 기록이 남아있음
계정이 없을경우 아래의 Sign up 버튼을 눌러 계정을 만들고 로그인하면됨.
캘린더와 화면이 뜨면 아래에 년도와 날짜를 입력하고 제목과 설명을 입력 후 D Day 설정을 누르면 아래에 저장됨.
f5를 눌러 새로고침을 할 시 보기 버튼이 활성화되며 누를시 설명이 적힌 창과 새로운 팝업창이 한개 더뜸.
돌아가기 버튼을 누를시 새로운 팝업창이 닫힘.
