from tools.search_X.search_X import search_X
from agents import function_tool
from typing import Optional, Dict, List, Any

"""
Twitter/X API Search Tool

This tool requires a Bearer token for the Twitter/X API.
The token can be set through the following steps:

1. Go to the API Settings page in the Streamlit app
2. Enter a valid token in the Twitter Bearer Token field
3. Click the Save button

The token is stored in st.session_state.twitter_bearer_token.

How to obtain a Bearer token:
1. Create and login to a Twitter developer account (developer.twitter.com)
2. Create a project and app
3. Obtain Essential Access level
4. Copy the Bearer Token from the project settings
"""

@function_tool
def search_x_tool(keywords: str, max_results: int) -> Dict[str, Any]:
    """
    Search X(Twitter) for specific keywords and retrieve recent tweets.
    Useful for understanding cryptocurrency market trends, related news, and trader opinions.
    
    Args:
        keywords: Keywords to search for (e.g., "bitcoin price", "ethereum news", "crypto market")
        max_results: Maximum number of tweets to retrieve (default: 10)
    
    Returns:
        Dict: Dictionary containing search results with the following structure:
            - success (bool): Whether the search was successful
            - data (List): When successful, list of tweets
            - query (str): When successful, the search query used
            - timestamp (str): When successful, the search time
            - error (str): When failed, error message
    """
    import traceback
    
    try:
        print(f"search_x_tool called: keywords='{keywords}', max_results={max_results}")
        
        # Apply default value for max_results
        if max_results is None or max_results <= 0:
            print(f"Invalid max_results value ({max_results}), setting to default value 10")
            max_results = 10
            
        # Limit maximum value (Twitter API limit)
        if max_results > 100:
            print(f"max_results too large ({max_results}), limiting to 100")
            max_results = 100
        
        # Create search_X class instance
        x_searcher = search_X()
        
        # Execute search
        result = x_searcher.search(keywords, max_results)
        
        # Log results
        if result['success']:
            print(f"search_x_tool success: {len(result.get('data', []))} results")
        else:
            print(f"search_x_tool failed: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"search_x_tool exception occurred: {str(e)}\n{error_detail}")
        return {
            'success': False,
            'error': f"search_x_tool exception: {str(e)}"
        } 