# [X_agent.py]
import tweepy
import streamlit as st
from datetime import datetime
import traceback

class search_X:
    def __init__(self):
        self.bearer_token = st.session_state.get('twitter_bearer_token', '')
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """트위터 API v2 클라이언트 초기화"""
        if not self.bearer_token:
            print("Twitter Bearer Token이 설정되지 않았습니다.")
            return
        try:
            self.client = tweepy.Client(bearer_token=self.bearer_token)
            print("Twitter API 클라이언트 초기화 성공")
        except Exception as e:
            error_detail = traceback.format_exc()
            print(f"Twitter API 클라이언트 초기화 실패: {str(e)}\n{error_detail}")

    def search(self, keywords, max_results=10):
        """
        LLM으로부터 제공받은 검색어로 X(Twitter)를 검색하고 결과만 반환
        - keywords: LLM이 제공한 검색어 (예: "bitcoin price")
        - max_results: 반환할 최대 트윗 수 (기본값: 10)
        """
        # 토큰 확인
        if not self.bearer_token:
            return {'success': False, 'error': 'Twitter Bearer Token이 설정되지 않았습니다. API 설정 페이지에서 토큰을 설정해주세요.'}
            
        # 클라이언트 초기화 확인
        if not self.client:
            # 클라이언트 재초기화 시도
            self._initialize_client()
            if not self.client:
                return {'success': False, 'error': 'X API 클라이언트 초기화 실패. 토큰이 유효한지 확인해주세요.'}

        try:
            # 검색 쿼리: LLM에서 받은 키워드 그대로 사용
            query = f"{keywords} -is:retweet"  # 기본 필터로 리트윗 제외
            print(f"X 검색 시도 중: 쿼리='{query}', max_results={max_results}")
            
            tweets = self.client.search_recent_tweets(
                query=query,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username'],
                expansions=['author_id'],
                max_results=max_results
            )

            if not tweets.data:
                print(f"검색 결과 없음: '{keywords}'")
                return {'success': False, 'error': f"'{keywords}'에 대한 검색 결과 없음"}

            # 사용자 정보 매핑
            users = {user.id: user for user in tweets.includes['users']}
            results = []
            for tweet in tweets.data:
                author = users[tweet.author_id]
                results.append({
                    'text': tweet.text,
                    'user': author.username,
                    'created_at': tweet.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count']
                })

            print(f"X 검색 성공: {len(results)}개 결과 찾음")
            return {
                'success': True,
                'data': results,
                'query': query,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except tweepy.errors.Unauthorized as e:
            error_msg = f'Twitter API 인증 오류: {str(e)}. Bearer 토큰이 유효한지 확인해주세요.'
            print(error_msg)
            return {'success': False, 'error': error_msg}
        except tweepy.errors.TooManyRequests as e:
            error_msg = f'Twitter API 요청 한도 초과: {str(e)}. 잠시 후 다시 시도해주세요.'
            print(error_msg)
            return {'success': False, 'error': error_msg}
        except tweepy.errors.BadRequest as e:
            error_msg = f'Twitter API 잘못된 요청: {str(e)}. 검색어를 확인해주세요.'
            print(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_detail = traceback.format_exc()
            error_msg = f'X 검색 중 오류 발생: {str(e)}'
            print(f"{error_msg}\n{error_detail}")
            return {'success': False, 'error': error_msg}

# 테스트용 코드
# if __name__ == "__main__":
#     agent = search_X()
#     result = agent.search("bitcoin")
#     print(result)