import json
import os
import sys
import time

from getpass import getpass

from bs4 import BeautifulSoup
from datetime import datetime
from NwalaTextUtils.textutils import genericErrorInfo
from NwalaTextUtils.textutils import getLinks

from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus

from util import paral_rehydrate_tweets
from util import readTextFromFile
from util import rehydrate_tweet
from util import write_tweets_to_jsonl_file
from util import writeTextToFile

def is_twitter_user_auth(links, cur_page_uri):
    """
    Checks if the user is authenticated on Twitter.

    This function determines if the current page indicates a logged-in Twitter user
    by analyzing the current page URI and a list of extracted links.

    Parameters:
        links (list): A list of dictionaries, where each dictionary contains a 'link' key with a URL.
        cur_page_uri (str): The current page URL.

    Returns:
        bool: True if the user is authenticated on Twitter, otherwise False.
    """
    # Check if the current URL indicates a logged-in user's homepage.
    if cur_page_uri.strip().startswith('https://twitter.com/home'):
        return True

    # List of URLs that indicate an authenticated Twitter session.
    logged_in_links = ['https://twitter.com/home', 'https://t.co/']

    # Loop through the list of extracted links to check for any logged-in indicators.
    for l in links:
        for log_l in logged_in_links:
            # If any link starts with a known logged-in URL, return True.
            if l['link'].startswith(log_l):
                return True

    # If none of the checks passed, return False indicating the user is not authenticated.
    return False


def scroll_up(page):
    """
    Scrolls up to the top of the page using JavaScript.

    Parameters:
        page: The Playwright page object.
    """
    # Evaluate JavaScript to scroll to the top of the page smoothly.
    page.evaluate("window.scrollTo({'top': 0, 'left': 0, 'behavior': 'smooth'});")


def scroll_down(page):
    """
    Scrolls down to the bottom of the page using JavaScript.

    Parameters:
        page: The Playwright page object.
    """
    # Evaluate JavaScript to scroll to the bottom of the page smoothly.
    page.evaluate("window.scrollTo({'top': document.body.scrollHeight, 'left': 0, 'behavior': 'smooth'});")


def post_tweet(browser_dets, msg, button_name='Post', after_post_sleep=2.5, **kwargs):
    """
    Posts a tweet or replies to an existing tweet.

    Parameters:
        browser_dets (dict): Dictionary containing browser context and page details.
        msg (str): The message to post.
        button_name (str): The label of the button to click ('Post' or 'Reply'). Defaults to 'Post'.
        after_post_sleep (float): Time in seconds to wait after posting to ensure tweet is sent. Defaults to 2.5.
        **kwargs: 
            get_new_tweet_link (bool): If True, returns the link to the newly posted tweet. Defaults to False.
            twitter_account (str): The Twitter account handle to search for the new tweet. Required if get_new_tweet_link is True.
            reply_to_link (str): If provided, posts a reply to this tweet link instead of creating a new tweet.
            typing_delay_milli (int): Delay in milliseconds between typing each character. Defaults to 60.

    Returns:
        dict: A dictionary containing 'tweet_link' if a new tweet was posted and the link was retrieved.
    """
    # Return an empty dictionary if no browser details are provided.
    if len(browser_dets) == 0:
        return {}

    # Extract additional options from kwargs.
    get_new_tweet_link = kwargs.get('get_new_tweet_link', False)
    twitter_accnt = kwargs.get('twitter_account', '')
    reply_to_link = kwargs.get('reply_to_link', '')
    typing_delay_milli = kwargs.get('typing_delay_milli', 60)

    # If replying to a specific tweet, navigate to the tweet link.
    if reply_to_link != '':
        button_name = 'Reply'
        browser_dets['page'].goto(reply_to_link)
        time.sleep(3)

    # Click the tweet or reply button.
    eval_str = f''' 
    reply_buttons = document.querySelectorAll('[aria-label$="{button_name}"]');
    reply_buttons[reply_buttons.length-1].click();
    '''
    browser_dets['page'].evaluate(eval_str)
    time.sleep(1)  # Short delay before typing

    # Type the tweet message with a specified typing delay.
    browser_dets['page'].keyboard.type(msg, delay=typing_delay_milli)

    # Click the button to post the tweet.
    browser_dets['page'].evaluate('document.querySelectorAll("[data-testid=\'tweetButton\']")[0].click();')

    # Added sleep to ensure the tweet is properly posted.
    time.sleep(after_post_sleep)
    tweet_link = ''

    # If requested, get the link to the newly posted tweet.
    if get_new_tweet_link is True and twitter_accnt != '':
        # Search for recent tweets from the specified account.
        tweets = get_search_tweets(browser_dets, f'(from:{twitter_accnt})')
        # Filter out tweets without an 'id_str' field.
        tweets['tweets'] = [t for t in tweets['tweets'] if 'id_str' in t]

        if len(tweets['tweets']) != 0:
            # Sort tweets by ID in descending order to get the latest one.
            tweets['tweets'] = sorted(tweets['tweets'], key=lambda k: k['id_str'], reverse=True)

        for t in tweets['tweets']:
            # Construct the URL for the most recent tweet.
            tweet_link = 'https://twitter.com/{}/status/{}'.format(t['user']['screen_name'], t['id_str'])
            print(f'\tposted tweet: {tweet_link}')
            break

    return {
        'tweet_link': tweet_link
    }
    
def color_tweet(page, tweet_link):
    """
    Highlights a tweet on the Twitter page by changing its background color and outline.

    Parameters:
        page: The Playwright page object representing the current browser page.
        tweet_link (str): The specific tweet link to identify and highlight.
    """
    # Query to find the tweet element based on the link provided.
    query_slc = f'''article = document.querySelectorAll('[href="{tweet_link}"]');'''
    
    # Execute JavaScript on the page to color the tweet.
    page.evaluate(query_slc + '''
        if (article.length != 0) {
            article = article[0];
            article.style.backgroundColor = 'red'; // Change background color to red.
            i = 0;
            
            // Traverse up to find the 'ARTICLE' element and apply custom styles.
            while (i < 1000) {
                if (article.nodeName == 'ARTICLE') {
                    article.style.outline = "thick solid red"; // Add a thick red outline.
                    article.className = "cust-tweet"; // Add a custom class for the tweet.
                    break;
                }
                article = article.parentElement; // Move up the DOM tree.
                i++;
            }
        }
    ''')


def get_tweet_ids_user_timeline_page(screen_name, page, max_tweets):
    """
    Extracts tweet IDs from a user's timeline page.

    Parameters:
        screen_name (str): The Twitter handle of the user (without '@').
        page: The Playwright page object representing the current browser page.
        max_tweets (int): The maximum number of tweets to retrieve.

    Returns:
        list: A list of dictionaries containing tweet details including:
              - tweet ID
              - associated screen name
              - tweet timestamp
              - whether it's a retweet or not
    """
    empty_result_count = 0  # Counter to track consecutive empty results.
    prev_len = 0  # Tracks the number of tweets fetched in the previous iteration.
    tweets = []  # List to store the final tweet details.
    tweet_links = set()  # A set to avoid duplicate tweet links.
    tweet_dets = {}  # Dictionary to store tweet metadata.
    break_flag = False  # Flag to exit the loop when max tweets are reached.

    while True:
        # Get the page content and parse it with BeautifulSoup.
        page_html = page.content()
        soup = BeautifulSoup(page_html, 'html.parser')
        articles = soup.find_all('article')

        # Loop through all the 'article' elements found on the page.
        for i in range(len(articles)):
            t = articles[i]

            # Check if the tweet is a retweet.
            is_retweet = t.find('span', {'data-testid': 'socialContext'})
            is_retweet = False if is_retweet is None else is_retweet.text.strip().lower().endswith(' retweeted')

            tweet_datetime = ''
            tweet_link = t.find('time')

            # Extract the tweet link and timestamp.
            if tweet_link is None:
                tweet_link = ''
            else:
                tweet_datetime = tweet_link.get('datetime', '')
                tweet_link = tweet_link.parent.get('href', '')

            tweet_link = tweet_link.strip()
            if tweet_link == '':
                print('\ttweet_link is blank, skipping')
                continue

            # Filter out tweets not authored by the specified screen_name if screen_name is provided.
            if screen_name != '' and is_retweet is False and tweet_link.lower().startswith(f'/{screen_name}/') is False:
                print(f'\tskipping non-{screen_name} (re)tweet, tweet_link: "{tweet_link}"')
                continue

            # Optionally, highlight the tweet on the page.
            # color_tweet(page, tweet_link)

            # Store tweet details.
            tweet_dets[tweet_link] = {'datetime': tweet_datetime, 'is_retweet': is_retweet}
            tweet_links.add(tweet_link)

            print('\textracted {} tweets'.format(len(tweet_links)))
            # Check if the desired number of tweets has been reached.
            if len(tweet_links) == max_tweets:
                break_flag = True
                print(f'breaking reached ({len(tweet_links)}) maximum: {max_tweets}')
                break

        # Exit the loop if the break flag is set.
        if break_flag is True:
            break

        # If no new tweets are found, increment the counter.
        empty_result_count = empty_result_count + 1 if prev_len == len(tweet_links) else 0
        if empty_result_count > 5:
            print('No new tweets found, so breaking')
            break

        prev_len = len(tweet_links)
        print('\tthrottling/scrolling, then sleeping for 2 second\n')

        # Scroll down to load more tweets and wait for the page to update.
        scroll_down(page)
        time.sleep(2)

    # Process and structure the extracted tweet links.
    for tlink in tweet_links:
        stat_screen_name, tid = tlink.split('/status/')
        twt_uri_dets = {
            'tid': tid,
            'status_screen_name': stat_screen_name[1:],  # Remove leading '/'.
            'datetime': tweet_dets[tlink]['datetime']
        }
        twt_uri_dets['notes'] = {'timeline_screen_name': screen_name, 'is_retweet': tweet_dets[tlink]['is_retweet']}
        tweets.append(twt_uri_dets)

    # Sort tweets by tweet ID before returning.
    tweets = sorted(tweets, key=lambda x: x['tid'])
    return tweets

def get_timeline_tweets(browser_dets, screen_name, max_tweets=20):
    """
    Retrieves tweets from a user's timeline on Twitter.

    Parameters:
        browser_dets (dict): Contains the browser context and page details.
        screen_name (str): The Twitter screen name (username) of the user.
        max_tweets (int): The maximum number of tweets to retrieve. Default is 20.

    Returns:
        dict: A dictionary containing the URL of the timeline and a list of tweets (if any).
    """
    screen_name = screen_name.strip()
    uri = f'https://twitter.com/{screen_name}/with_replies'
    payload = {'self': uri, 'tweets': []}
    
    # If max_tweets is negative or there is no valid browser context, return empty payload
    if max_tweets < 0 or len(browser_dets) == 0 or screen_name == '':
        return {}

    print(f'\nget_timeline_tweets(): {screen_name}')
    
    # Navigate to the user's timeline
    browser_dets['page'].goto(uri)

    # Retrieve tweet IDs from the timeline page
    tweet_ids = get_tweet_ids_user_timeline_page(screen_name, browser_dets['page'], max_tweets)
    
    # Rehydrate tweets from the retrieved tweet IDs
    payload['tweets'] = paral_rehydrate_tweets(tweet_ids)

    return payload

def get_search_tweets(browser_dets, query, max_tweets=20):
    """
    Retrieves tweets based on a search query on Twitter.

    Parameters:
        browser_dets (dict): Contains the browser context and page details.
        query (str): The search query string to search for on Twitter.
        max_tweets (int): The maximum number of tweets to retrieve. Default is 20.

    Returns:
        dict: A dictionary containing the search query URL and a list of tweets (if any).
    """
    query = query.strip()
    uri = 'https://twitter.com/search?q=' + quote_plus(query) + '&f=live&src=typd'
    payload = {'self': uri, 'tweets': []}
    
    # If max_tweets is negative or there is no valid browser context, return empty payload
    if max_tweets < 0 or len(browser_dets) == 0 or query == '':
        return payload

    print('\nget_search_tweets():')
    
    # Navigate to the search results page
    browser_dets['page'].goto(uri)
    
    # Retrieve tweet IDs from the search results page
    tweet_ids = get_tweet_ids_user_timeline_page('', browser_dets['page'], max_tweets)
    
    # Rehydrate tweets from the retrieved tweet IDs
    payload['tweets'] = paral_rehydrate_tweets(tweet_ids)

    return payload

def try_to_login(page, username, password):
    """
    Attempts to log in to Twitter using the provided credentials.

    Parameters:
        page (object): The Playwright page object used to interact with the browser.
        username (str): The Twitter username.
        password (str): The Twitter password.
    """
    print('\ntry_to_login()')
    
    # Strip any unnecessary spaces from username and password
    username = username.strip()
    password = password.strip()

    # If either username or password is empty, exit the function
    if username == '' or password == '':
        return
        
    # Fill in the username field and submit
    page.get_by_role('textbox').fill(username)
    page.keyboard.press('Enter')
    
    # Fill in the password field and submit
    page.get_by_label('Password', exact=True).type(password, delay=20)
    page.keyboard.press('Enter')


def get_auth_twitter_pg(playwright, callback_uri='', headless=False, **kwargs):
    """
    Authenticates a Twitter session using Playwright, either by using unsafe credentials
    stored in files or prompting the user for login details. It launches the browser, 
    navigates to the Twitter login page, and waits until the user is authenticated.

    Parameters:
        playwright: The Playwright object used to launch the browser.
        callback_uri (str): Optional callback URL to navigate to after successful authentication.
        headless (bool): Whether to run the browser in headless mode (default is False).
        **kwargs: Optional keyword arguments such as:
            - 'unsafe_cred_path': Path where unsafe Twitter credentials are stored.
            - 'browser_storage_path': Path for browser session storage.

    Returns:
        dict: Contains the browser, context, page, and authenticated username if login is successful.
    """
    print('\nget_auth_twitter_pg()')

    # Get parameters from kwargs or set default paths
    unsafe_cred_path = kwargs.get('unsafe_cred_path', '')
    browser_storage_path = kwargs.get('browser_storage_path', './playwright-browser-storage/')

    # Ensure paths end with '/'
    unsafe_cred_path = unsafe_cred_path if unsafe_cred_path.endswith('/') or unsafe_cred_path == '' else f'{unsafe_cred_path}/'
    browser_storage_path = browser_storage_path if browser_storage_path.endswith('/') or browser_storage_path == '' else f'{browser_storage_path}/'

    # Prioritize browser_storage_path if both are set
    unsafe_cred_path = unsafe_cred_path if browser_storage_path == '' else ''
    browser_storage_path = './playwright-browser-storage/' if unsafe_cred_path == '' and browser_storage_path == '' else browser_storage_path

    # If unsafe credentials path is provided, attempt to retrieve credentials from files or prompt for them
    if(unsafe_cred_path != ''):
        print('\t--- Unsafe login ---')

        # Check if stored credentials exist
        if( os.path.exists(f'{unsafe_cred_path}unsafe_twitter_username.txt') and os.path.exists(f'{unsafe_cred_path}unsafe_twitter_password.txt') ):
            username = readTextFromFile(f'{unsafe_cred_path}unsafe_twitter_username.txt').strip()
            password = readTextFromFile(f'{unsafe_cred_path}unsafe_twitter_password.txt').strip()
            print(f'retrieved username from {unsafe_cred_path}unsafe_twitter_username.txt')
            print(f'retrieved password from {unsafe_cred_path}unsafe_twitter_password.txt')

        # If credentials are missing, prompt for them and store them
        if(username == '' or password == ''):
            username = input('\n\tEnter Twitter username: ')
            password = getpass('\tEnter Twitter password: ')

            username = username.strip()
            password = password.strip()

            writeTextToFile(f'{unsafe_cred_path}unsafe_twitter_username.txt', username)
            writeTextToFile(f'{unsafe_cred_path}unsafe_twitter_password.txt', password)

    # Initialize browser and context based on storage path
    browser = None
    chromium = playwright.firefox  # You can choose between chromium, firefox, or webkit

    if(browser_storage_path == ''):
        browser = chromium.launch(headless=headless)  # Launch a new browser instance
        context = browser.new_context()
    else:
        os.makedirs(browser_storage_path, exist_ok=True)  # Ensure the storage path exists
        context = chromium.launch_persistent_context(browser_storage_path, headless=headless)  # Launch persistent context

    sleep_seconds = 3  # Delay between retries to check authentication status
    page = context.new_page()  # Open a new page in the browser
    page.goto('https://twitter.com/login')  # Navigate to Twitter login page

    # If unsafe credentials are provided, attempt to log in
    if(unsafe_cred_path != ''):
        time.sleep(sleep_seconds)
        try_to_login(page, username, password)  # Login using the provided credentials

    while(True):
        print(f'\twaiting for login, sleeping for {sleep_seconds} seconds')
        time.sleep(sleep_seconds)

        # Retrieve the page content and links to check if authenticated
        page_html = page.content()
        page_links = getLinks(uri='', html=page_html, fromMainTextFlag=False)
        scroll_down(page)  # Scroll down to trigger any dynamic content loading

        # Check if the user is authenticated
        if(is_twitter_user_auth(page_links, page.url)):
            print('\tauthenticated')

            # If a callback URI is provided, navigate to it
            if(callback_uri != ''):
                page.goto(callback_uri)
                print(f'\tauthenticated, loaded {callback_uri}')

            # Sleep briefly before returning context information
            print('\tsleeping for 3 seconds')
            time.sleep(3)

            return {
                'page': page,
                'context': context,
                'browser': browser,
                'authenticated_screen_name': username  # Return the authenticated username
            }

    return {}

def main():
    """
    Main function for testing rehydration of a tweet using a specific token.

    This function demonstrates how to call the rehydrate_tweet function, passing
    a specific tweet ID and a token for accessing the necessary data.

    Returns:
        None
    """
    # Example test of tweet rehydration
    token = '122123'
    res = rehydrate_tweet('1573024393751859200', token=token)
    print(json.dumps(res, ensure_ascii=True))  # Print the rehydrated tweet details

    return  # Exit the function

if __name__ == "__main__":
    main()
