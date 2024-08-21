import random
import string
import os
import configparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import signal
import praw
from prawcore import ResponseException

TOTAL_PROCESSED = {k: 0 for k in ['comments', 'posts', 'saved', 'upvotes', 'downvotes', 'hidden']}

def graceful_exit(signum, frame):
    print("\nInterrupt received. Stopping content removal and exiting...")
    raise SystemExit()

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

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

def process_item(item, item_type, processed_counts, max_retries=5):
    for attempt in range(max_retries):
        try:
            if item_type == 'comment':
                original_content = item.body
                random_text = generate_random_text()
                print(f"Replacing original comment '{original_content[:25]}...' with random text.")
                item.edit(random_text)
                print(f"Deleting comment: '{original_content[:25]}...'")
                item.delete()
            elif item_type == 'post':
                original_content = item.title
                random_text = generate_random_text()
                print(f"Replacing original post '{original_content[:25]}...' with random text.")
                item.edit(random_text)
                print(f"Deleting post: '{original_content[:25]}...'")
                item.delete()
            elif item_type == 'saved':
                print(f"Unsaving item: '{getattr(item, 'id', 'N/A')}'")
                item.unsave()
            elif item_type in ['upvotes', 'downvotes']:
                print(f"Attempting to clear {item_type[:-1]} on item: '{getattr(item, 'id', 'N/A')}'")
                item.clear_vote()
                print(f"Successfully cleared {item_type[:-1]} on item: '{getattr(item, 'id', 'N/A')}'")
            elif item_type == 'hidden':
                print(f"Unhiding post: '{getattr(item, 'id', 'N/A')}'")
                item.unhide()
            processed_counts[item_type] += 1
            return True
        except (praw.exceptions.RedditAPIException, ResponseException) as e:
            if isinstance(e, ResponseException) and e.response.status_code == 400:
                print("Encountered a 400 HTTP error. Skipping as this is likely due to trying to upvote/downvote an archived submission.")
                print("Note: You can disable the option to make your votes public in Reddit's settings.")
                return True
            if isinstance(e, praw.exceptions.RedditAPIException):
                print(f"Encountered a Reddit API Exception. Probably hit the rate limit: {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                print(f"\nAttempt {attempt + 1} failed. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"Failed to process {item_type} after {max_retries} attempts.")
    return False

def process_batch(items, item_type, batch_number, total_processed, total_items, processed_counts):
    print(f"Starting batch {batch_number} for {item_type}")

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_item, item, item_type, processed_counts) for item in items]
        for future in as_completed(futures):
            if future.result():
                total_processed += 1

    print(f"Progress: {total_processed}/{total_items} {item_type}(s) processed so far.")
    print(f"Finished batch {batch_number} for {item_type}s. Sleeping for five seconds...")
    time.sleep(5)
    return total_processed

def process_items_in_batches(items, item_type, total_items, processed_counts):
    batch = []
    batch_number = 1
    total_processed = 0

    for item in items:
        batch.append(item)
        if len(batch) == 50:
            total_processed = process_batch(batch, item_type, batch_number, total_processed, total_items, processed_counts)
            batch = []
            batch_number += 1

    if batch:
        total_processed = process_batch(batch, item_type, batch_number, total_processed, total_items, processed_counts)

    return total_processed

def fetch_items(item_listing, sort_type):
    if sort_type in ['controversial', 'top']:
        return list(item_listing(time_filter='all', limit=None))
    else:  # 'new' and 'hot' don't use time_filter
        return list(item_listing(limit=None))

def delete_all_content(reddit, username):
    processed_counts = {
        'comments': 0,
        'posts': 0,
        'saved': 0,
        'upvotes': 0,
        'downvotes': 0,
        'hidden': 0
    }

    try:
        redditor = reddit.redditor(username)
        items = {
            'comments': set(),
            'posts': set(),
            'saved': set(),
            'upvotes': set(),
            'downvotes': set(),
            'hidden': set()
        }

        # Fetch comments and posts
        for sort_type in ['controversial', 'top', 'new', 'hot']:
            print(f"Fetching comments sorted by {sort_type}...")
            items['comments'].update(fetch_items(getattr(redditor.comments, sort_type), sort_type))
            print(f"Total unique comments found so far: {len(items['comments'])}")

            print(f"Fetching posts sorted by {sort_type}...")
            items['posts'].update(fetch_items(getattr(redditor.submissions, sort_type), sort_type))
            print(f"Total unique posts found so far: {len(items['posts'])}")

        # Fetch other content types
        print("Fetching saved content...")
        items['saved'] = set(reddit.user.me().saved(limit=None))
        print(f"Total saved items found: {len(items['saved'])}")

        print("Fetching upvoted content...")
        items['upvotes'] = set(reddit.user.me().upvoted(limit=None))
        print(f"Total upvoted items found: {len(items['upvotes'])}")

        print("Fetching downvoted content...")
        items['downvotes'] = set(reddit.user.me().downvoted(limit=None))
        print(f"Total downvoted items found: {len(items['downvotes'])}")

        print("Fetching hidden content...")
        items['hidden'] = set(reddit.user.me().hidden(limit=None))
        print(f"Total hidden items found: {len(items['hidden'])}")

        for item_type, item_set in items.items():
            total_items = len(item_set)
            print(f"Processing {total_items} {item_type}...")
            process_items_in_batches(list(item_set), item_type, total_items, processed_counts)

    except SystemExit:
        raise  # Re-raise the SystemExit exception to be caught in the main function
    finally:
        # Update TOTAL_PROCESSED regardless of whether an exception occurred
        for item_type, count in processed_counts.items():
            TOTAL_PROCESSED[item_type] += count

    return processed_counts

def main():
    client_id, client_secret, username, password = read_credentials()

    confirmation = input("This will remove ALL your Reddit content including comments, posts, saved items, votes, and hidden posts. Do you really want to continue? (yes/no): ")
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

    run_count = 0
    try:
        while True:
            run_count += 1
            print(f"\nStarting run #{run_count}")
            print("Removing Reddit content...")
            try:
                processed_counts = delete_all_content(reddit, username)
            except SystemExit:
                print("Run interrupted.")
                break
            
            print("\nContent destroyed in this run:")
            for item_type, count in processed_counts.items():
                print(f"{item_type.capitalize()}: {count}")

            if all(count == 0 for count in processed_counts.values()):
                print("\nNo content was destroyed in this run.")
                print("Script execution completed.")
                break
            else:
                print("\nSome content was destroyed. Running the script again in 7 seconds...")
                time.sleep(7)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print(f"\nTotal content destroyed across {run_count} {'run' if run_count == 1 else 'runs'}:")
        for item_type, count in TOTAL_PROCESSED.items():
            print(f"{item_type.capitalize()}: {count}")

if __name__ == "__main__":
    main()
