import re
from typing import List, Tuple

def parse_content(content: str) -> Tuple[List[str], List[str]]:
    """
    본문에서 해시태그와 멘션을 추출합니다.
    반환값: (정규화된 해시태그 목록, 멘션된 닉네임#태그 목록)
    """
    if not content:
        return [], []
    
    # 1. 해시태그 파싱: # 문자로 시작하고, 공백이나 특정 특수문자 전까지 추출
    # 제외할 특수문자: 공백, #, @, !, ?, ,, ., ', ", (, ), [, ]
    hashtag_pattern = re.compile(r'#([^\s#@!?,.\'\"\(\)\[\]]+)')
    raw_hashtags = hashtag_pattern.findall(content)
    # 대소문자 통합(소문자화) 및 중복 제거
    normalized_hashtags = list(set(tag.lower() for tag in raw_hashtags if tag))

    # 2. 멘션 파싱: @ 문자로 시작하고, '닉네임#태그' 형식을 정확히 추출
    # 닉네임: 2~12자(한/영/숫자), 태그: 4자(숫자)
    mention_pattern = re.compile(r'@([a-zA-Z0-9가-힣]{2,12}#[0-9]{4})')
    mentions = list(set(mention_pattern.findall(content)))

    return normalized_hashtags, mentions
