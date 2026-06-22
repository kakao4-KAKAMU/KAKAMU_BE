# app/models/in_memory.py

# 서버 메모리에 페르소나별 영화 평가 기록을 누적할 전역 딕셔너리
# 구조: persona_evaluations = {"persona_id": {"movie_id": "LIKE" 또는 "DISLIKE"}}
persona_evaluations = {}
