import random
import sys
import praw
import configparser
import csv
from datetime import datetime

config = configparser.ConfigParser()
config.read("config.ini")

client_id = config["reddit"]["client_id"]
client_secret = config["reddit"]["client_secret"]
user_agent = config["reddit"]["user_agent"]
username = config["reddit"]["username"]
password = config["reddit"]["password"]

csv_file_path = "subreddits.csv"

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
            weight = (1 * days_since_last_selected) * (1 + 0.3 * (member_factor / 1000))
        weights.append(weight)
    return weights

def select_subreddit(subreddits, weights):
    try:
        selected_subreddit = random.choices(population=subreddits, weights=weights, k=1)[0]
    except ValueError:
        print("All subreddits have been posted to recently. Exiting now.")
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

def create_post(selected_subreddit):
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, username=username, password=password)
    subreddit = reddit.subreddit(selected_subreddit)
    subreddit.submit(title="Test title", selftext="Test body")
    return subreddit.subscribers

def main():
    subreddits = read_subreddits(csv_file_path)

    print("Calculating weights...")
    weights = calculate_weights(subreddits)

    selected_subreddit = select_subreddit(subreddits, weights)
    print(f"Selected subreddit: {selected_subreddit['subreddit']}")

    print("Creating post...")
    members = create_post(selected_subreddit)

    print("Updating CSV file...")
    update_subreddit(selected_subreddit, members)
    write_subreddits(csv_file_path, subreddits)

    print("All done :D")

if __name__ == "__main__":
    if random.random() < 0.1:
        main()
