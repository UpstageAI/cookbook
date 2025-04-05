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
        """Initialize Twitter API v2 client"""
        if not self.bearer_token:
            print("Twitter Bearer Token is not set.")
            return
        try:
            self.client = tweepy.Client(bearer_token=self.bearer_token)
            print("Twitter API client initialization successful")
        except Exception as e:
            error_detail = traceback.format_exc()
            print(f"Twitter API client initialization failed: {str(e)}\n{error_detail}")

    def search(self, keywords, max_results=10):
        """
        Search X(Twitter) with keywords provided by LLM and return results
        - keywords: Search terms provided by the LLM (e.g., "bitcoin price")
        - max_results: Maximum number of tweets to return (default: 10)
        """
        # Check token
        if not self.bearer_token:
            return {'success': False, 'error': 'Twitter Bearer Token is not set. Please set the token in the API Settings page.'}
            
        # Check client initialization
        if not self.client:
            # Try to reinitialize client
            self._initialize_client()
            if not self.client:
                return {'success': False, 'error': 'X API client initialization failed. Please check if your token is valid.'}

        try:
            # Search query: Use keywords directly from LLM
            query = f"{keywords} -is:retweet"  # Basic filter to exclude retweets
            print(f"Attempting X search: query='{query}', max_results={max_results}")
            
            tweets = self.client.search_recent_tweets(
                query=query,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username'],
                expansions=['author_id'],
                max_results=max_results
            )

            if not tweets.data:
                print(f"No search results for: '{keywords}'")
                return {'success': False, 'error': f"No search results for '{keywords}'"}

            # Map user information
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

            print(f"X search successful: {len(results)} results found")
            return {
                'success': True,
                'data': results,
                'query': query,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except tweepy.errors.Unauthorized as e:
            error_msg = f'Twitter API authentication error: {str(e)}. Please check if your Bearer token is valid.'
            print(error_msg)
            return {'success': False, 'error': error_msg}
        except tweepy.errors.TooManyRequests as e:
            error_msg = f'Twitter API request limit exceeded: {str(e)}. Please try again later.'
            print(error_msg)
            return {'success': False, 'error': error_msg}
        except tweepy.errors.BadRequest as e:
            error_msg = f'Twitter API bad request: {str(e)}. Please check your search terms.'
            print(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_detail = traceback.format_exc()
            error_msg = f'Error occurred during X search: {str(e)}'
            print(f"{error_msg}\n{error_detail}")
            return {'success': False, 'error': error_msg}
