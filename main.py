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

def get_title_and_body(promo_subreddit):
    # referral_link = "https://refer.sportsbook.fanduel.com/#/land/e9a4f1cf-e1be-43b8-aeae-fc86dc0684f9"
    # if promo_subreddit:
    #     title = "Get $300 on FanDuel Sportsbook"
    #     body = (
    #         "Sign up using this [referral link](https://refer.sportsbook.fanduel.com/#/land/e9a4f1cf-e1be-43b8-aeae-fc86dc0684f9), deposit $10, and place any winning bet with that $10 to qualify!\n\n"
    #         "You will then receive $300 in bonus bets from FanDuel.\n\n"
    #         "My recommendation:\n"
    #         "1. Place the original $10 deposit on a high-odds bet to keep your money safe (look for bets that are -10000 and lower, these can easily be found in the “alternate total points” section of games).\n"
    #         "2. With the $300 in bonus bets, split it between both teams in any matchup ($150 on each side). This way, no matter which team wins, you guarantee a profit."
    #     )
    # else:
    #     title = "Referral code for $50 in bonus bets"
    #     body = (
    #         f"Referral link: {referral_link}\n\n"
    #         "The only terms are that you must deposit $10 and make any bet. After that you will be awarded $50!"
    #     )
    with open("messages.json", "r") as file:
        messages = json.load(file)
    sportsbook = "fanduel"
    sportsbook_messages = messages.get(sportsbook, {})
    if promo_subreddit:
        message_type = "special"
    else:
        message_type = "default"
    referral_link = sportsbook_messages.get("referral_link", "")
    deposit = default_earnings.get("deposit", 10)
    earnings = sportsbook.get(message_type, {}).get("earnings", 10)

    title = sportsbook.get(message_type, {}).get("title", "").format(referral_link=referral_link, earnings=earnings, deposit=deposit)
    body = sportsbook.get(message_type, {}).get("body", "").format(referral_link=referral_link, earnings=earnings, deposit=deposit)
    if sportsbook == "fanduel":

    return title, body

def create_post(selected_subreddit, promo_subreddit):
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, username=username, password=password)

    print(f"Deleting old posts in {selected_subreddit}...")
    delete_posts_in_subreddit(reddit, selected_subreddit)

    subreddit = reddit.subreddit(selected_subreddit["subreddit"])
    title, body = get_title_and_body(promo_subreddit)
    subreddit.submit(title=title, selftext=body)
    return subreddit.subscribers

def main():
    if random.random() < 0.3:
        promo_subreddit = False
        csv_file_path = "sportsbook_subreddits.csv"
    else:
        promo_subreddit = True
        csv_file_path = "promo_subreddits.csv"

    subreddits = read_subreddits(csv_file_path)

    print("Calculating weights...")
    weights = calculate_weights(subreddits)

    selected_subreddit = select_subreddit(subreddits, weights)
    print(f"Selected subreddit: {selected_subreddit['subreddit']}")

    print("Creating post...")
    members = create_post(selected_subreddit, promo_subreddit)

    print("Updating CSV file...")
    update_subreddit(selected_subreddit, members)
    write_subreddits(csv_file_path, subreddits)

    print("All done :D")

if __name__ == "__main__":
    if random.random() < 0.27:
        main()
    else:
        print("Didn't make the cut :(")
