import random
import string
import os
import configparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import signal
import praw

class GracefulExit(Exception):
    pass

def graceful_exit(signum, frame):
    raise GracefulExit()

signal.signal(signal.SIGINT, graceful_exit)

def generate_random_text():
    words = []
    num_words = random.randint(2, 17)

    for _ in range(num_words):
        word_length = random.randint(3, 12)
        word = ''.join(random.choices(string.ascii_lowercase, k=word_length))
        words.append(word)

    return ' '.join(words)

def read_credentials(file_path='reddit_credentials.ini'):
    if not os.path.exists(file_path):
        print(f"Credentials file not found: {file_path}")
        print("Please create a file named 'reddit_credentials.ini' with the following format:")
        print("[reddit]\nclient_id = YOUR_CLIENT_ID\nclient_secret = YOUR_CLIENT_SECRET\nusername = YOUR_USERNAME\npassword = YOUR_PASSWORD")
        exit(1)

    config = configparser.ConfigParser()
    config.read(file_path)

    return (config['reddit']['client_id'],
            config['reddit']['client_secret'],
            config['reddit']['username'],
            config['reddit']['password'])

def process_item(item, item_type, max_retries=5):
    for attempt in range(max_retries):
        try:
            original_content = item.body if item_type == 'comment' else item.title
            random_text = generate_random_text()
            print(f"Replacing original {item_type} '{original_content[:20]}...' with random text.")
            item.edit(random_text)
            print(f"Deleting original {item_type}: '{original_content[:20]}...'")
            item.delete()
            return True
        except praw.exceptions.RedditAPIException as e:
            print(f"Encountered a Reddit API Exception. Maybe hit the rate limit: {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                print(f"\nAttempt {attempt + 1} failed. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"Failed to process {item_type} after {max_retries} attempts.")
    return False

def process_batch(items, item_type, batch_number, total_deleted, total_items):
    print(f"Starting batch {batch_number} for {item_type}s")

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_item, item, item_type) for item in items]
        for future in as_completed(futures):
            if future.result():
                total_deleted += 1

    print(f"Progress: {total_deleted}/{total_items} {item_type}(s) deleted so far.")
    print(f"Finished batch {batch_number} for {item_type}s. Sleeping for five seconds...")
    time.sleep(5)
    return total_deleted

def process_items_in_batches(items, item_type, total_items):
    batch = []
    batch_number = 1
    total_deleted = 0

    for item in items:
        batch.append(item)
        if len(batch) == 50:
            total_deleted = process_batch(batch, item_type, batch_number, total_deleted, total_items)
            batch = []
            batch_number += 1

    if batch:
        total_deleted = process_batch(batch, item_type, batch_number, total_deleted, total_items)

    return total_deleted

def fetch_items(item_listing, sort_type):
    if sort_type in ['controversial', 'top']:
        return list(item_listing(time_filter='all', limit=None))
    else:  # 'new' and 'hot' don't use time_filter
        return list(item_listing(limit=None))

def delete_all_content(reddit, username):
    comments_deleted = 0
    posts_deleted = 0

    try:
        redditor = reddit.redditor(username)
        comments = set()
        posts = set()

        for sort_type in ['controversial', 'top', 'new', 'hot']:
            print(f"Fetching comments sorted by {sort_type}...")
            comments.update(fetch_items(getattr(redditor.comments, sort_type), sort_type))
            print(f"Total unique comments found so far: {len(comments)}")

            print(f"Fetching posts sorted by {sort_type}...")
            posts.update(fetch_items(getattr(redditor.submissions, sort_type), sort_type))
            print(f"Total unique posts found so far: {len(posts)}")

        total_comments = len(comments)
        total_posts = len(posts)

        print(f"Found {total_comments} unique comments and {total_posts} unique posts.")

        comments_deleted = process_items_in_batches(list(comments), 'comment', total_comments)
        posts_deleted = process_items_in_batches(list(posts), 'post', total_posts)

    except GracefulExit:
        print("\nInterrupt received. Stopping content deletion.")

    return comments_deleted, posts_deleted

def main():
    client_id, client_secret, username, password = read_credentials()

    confirmation = input("This will delete ALL your comments and posts. Do you really want to continue? (yes/no): ")
    if confirmation.lower() not in ['yes', 'y']:
        print("Script aborted.")
        exit()

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent='ereddicator',
            validate_on_submit=True
        )
        reddit.user.me()  # Check if authentication succeeded
    except Exception as e:
        print(f"Error: Could not authenticate with the provided credentials. {str(e)}")
        exit()

    print("Deleting all comments and posts...")
    comments_deleted, posts_deleted = delete_all_content(reddit, username)

    print(f"The script deleted {comments_deleted} comments and {posts_deleted} posts.")
    print("Script execution completed.")

if __name__ == "__main__":
    main()
