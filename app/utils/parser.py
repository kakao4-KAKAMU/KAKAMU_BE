import re
from typing import List, Tuple

TAGGED_CONTENT_PATTERN = re.compile(r'@([^@#\s]+)#(\S+)|#(\S+)')


def parse_content(content: str) -> Tuple[List[str], List[str]]:
    """
    본문에서 해시태그와 멘션을 추출합니다.
    반환값: (해시태그 목록, 멘션된 닉네임#태그 목록)
    """
    if not content:
        return [], []

    hashtags: set[str] = set()
    mentions: set[str] = set()

    for match in TAGGED_CONTENT_PATTERN.finditer(content):
        nickname, mention_tag, hashtag = match.groups()
        if nickname and mention_tag:
            mentions.add(f"{nickname}#{mention_tag}")
        elif hashtag:
            hashtags.add(hashtag)

    return list(hashtags), list(mentions)
