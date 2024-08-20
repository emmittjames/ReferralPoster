import praw
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

client_id = config['reddit']['client_id']
client_secret = config['reddit']['client_secret']
user_agent = config['reddit']['user_agent']
username = config['reddit']['username']
password = config['reddit']['password']

def create_post():
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, username=username, password=password)
    subreddit = reddit.subreddit("ReferralCodes")
    subreddit.submit(title='Hello, Reddit!', selftext='This is my first post using PRAW!')

create_post()