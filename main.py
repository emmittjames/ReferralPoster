import random
import sys
import praw
import configparser
import csv
import json
from datetime import datetime, timedelta

config = configparser.ConfigParser()
config.read("config.ini")

client_id = config["reddit"]["client_id"]
client_secret = config["reddit"]["client_secret"]
user_agent = config["reddit"]["user_agent"]
username = config["reddit"]["username"]
password = config["reddit"]["password"]

def read_subreddits(csv_file):
    subreddits = []
    with open(csv_file, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["last_selected"] = datetime.strptime(row["last_selected"], "%Y-%m-%d %H:%M:%S")
            row["members"] = int(row["members"])
            subreddits.append(row)
    return subreddits

def calculate_weights(subreddits):
    now = datetime.now()
    weights = []
    for subreddit in subreddits:
        days_since_last_selected = (now - subreddit["last_selected"]).days
        if days_since_last_selected < 3:
            weight = 0
        else:
            member_factor = subreddit['members'] / 100
            weight = (1 * days_since_last_selected) * (1 + 0.1 * (member_factor / 1000))
        weights.append(weight)
    return weights

def select_subreddit(subreddits, weights):
    try:
        selected_subreddit = random.choices(population=subreddits, weights=weights, k=1)[0]
    except ValueError:
        print("All subreddits have been posted to recently. Exiting now")
        sys.exit(1)
    return selected_subreddit

def update_subreddit(subreddit, members):
    subreddit["last_selected"] = datetime.now()
    subreddit["members"] = members

def write_subreddits(csv_file, subreddits):
    with open(csv_file, mode="w", newline="") as file:
        fieldnames = ["subreddit", "last_selected", "members"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in subreddits:
            row["last_selected"] = row["last_selected"].strftime("%Y-%m-%d %H:%M:%S")
            row["members"] = int(row["members"])
            writer.writerow(row)

def delete_posts_in_subreddit(reddit, selected_subreddit):
    user = reddit.user.me()
    time_threshold = datetime.now() - timedelta(days=60)
    for submission in user.submissions.new(limit=None):
        if submission.subreddit.display_name.lower() == selected_subreddit["subreddit"].lower():
            submission_age = datetime.fromtimestamp(submission.created_utc)
            if submission_age < time_threshold:
                print(f"Deleting post: {submission.title} in r/{selected_subreddit['subreddit']}")
                submission.delete()

def get_title_and_body(subreddit, is_promo_subreddit):
    with open("messages.json", "r") as file:
        messages = json.load(file)
    sportsbook = "FanDuel"
    if is_promo_subreddit:
        message_type = "special"
    else:
        message_type = "default"
        sportsbook = str(subreddit)
    sportsbook_messages = messages.get(sportsbook, {})
    sportsbook_messages_specific = sportsbook_messages.get(message_type, {})
    referral_link = sportsbook_messages.get("referral_link", "")
    deposit = sportsbook_messages.get("deposit", 10)
    earnings = sportsbook_messages_specific.get("earnings", 10)

    title = sportsbook_messages_specific.get("title", "").format(referral_link=referral_link, earnings=earnings, deposit=deposit)
    body = sportsbook_messages_specific.get("body", "").format(referral_link=referral_link, earnings=earnings, deposit=deposit)

    print(f"Title: {title}")
    print(f"Body: {body}")
    return title, body

def create_post(selected_subreddit, is_promo_subreddit):
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, username=username, password=password)

    print(f"Deleting old posts in {selected_subreddit}...")
    delete_posts_in_subreddit(reddit, selected_subreddit)

    subreddit = reddit.subreddit(selected_subreddit["subreddit"])
    title, body = get_title_and_body(subreddit, is_promo_subreddit)
    try:
        subreddit.submit(title=title, selftext=body)
    except praw.exceptions.RedditAPIException as e:
        flairs = list(subreddit.flair.link_templates)
        flair_id = flairs[0]["id"]
        desired_fairs = ["Referral Code"]
        for flair in flairs:
            if flair["text"] in desired_fairs:
                flair_id = flair["id"]
                break
        subreddit.submit(title=title, selftext=body, flair_id=flair_id)

    return subreddit.subscribers

def main():
    if random.random() < 0.3:
        is_promo_subreddit = False
        csv_file_path = "sportsbook_subreddits.csv"
    else:
        is_promo_subreddit = True
        csv_file_path = "promo_subreddits.csv"

    subreddits = read_subreddits(csv_file_path)

    print("Calculating weights...")
    weights = calculate_weights(subreddits)

    selected_subreddit = select_subreddit(subreddits, weights)
    print(f"Selected subreddit: {selected_subreddit['subreddit']}")

    print("Creating post...")
    members = create_post(selected_subreddit, is_promo_subreddit)

    print("Updating CSV file...")
    update_subreddit(selected_subreddit, members)
    write_subreddits(csv_file_path, subreddits)

    print("All done :D")

if __name__ == "__main__":
    if random.random() < 0.27:
        main()
    else:
        print("Didn't make the cut :(")
