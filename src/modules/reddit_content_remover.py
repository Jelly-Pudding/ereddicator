import random
import string
import time
from typing import Dict, List, Union, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import praw
from prawcore import ResponseException


class RedditContentRemover:
    """
    A class to handle the removal of Reddit content.

    This class manages the process of fetching and removing various types of Reddit content
    including comments, posts, saved items, upvotes, downvotes, and hidden posts.
    """

    def __init__(self, reddit: praw.Reddit, username: str):
        """
        Initialise the RedditContentRemover instance.

        Args:
            reddit (praw.Reddit): An authenticated Reddit instance.
            username (str): The username of the Reddit account.
        """
        self.reddit = reddit
        self.username = username
        self.total_processed_dict = {k: 0 for k in ["comments", "posts", "saved", "upvotes", "downvotes", "hidden"]}
        self.interrupt_flag = False

    @staticmethod
    def generate_random_text() -> str:
        """
        Generates a random string of text.

        Returns:
            str: A randomly generated string of words.
        """
        words = []
        num_words = random.randint(2, 17)
        for _ in range(num_words):
            word_length = random.randint(3, 12)
            word = "".join(random.choices(string.ascii_lowercase, k=word_length))
            words.append(word)
        return " ".join(words)

    def process_item(self, item: Union[praw.models.Comment, praw.models.Submission],
                     item_type: str, processed_counts: Dict[str, int], max_retries: int = 5) -> bool:
        """
        Process a single Reddit item (comment, post, etc.) for removal or modification.

        Args:
            item (Union[praw.models.Comment, praw.models.Submission]):
                The Reddit item to process. Can be either a Comment or a Submission.
            item_type (str): The type of item ('comments', 'posts', 'saved', 'upvotes', 'downvotes', 'hidden').
            processed_counts (Dict[str, int]): A dictionary to keep track of processed items.
            max_retries (int): Maximum number of retry attempts. Defaults to 5.

        Returns:
            bool: True if the item was successfully processed, False otherwise.
        """
        for attempt in range(max_retries):
            if self.interrupt_flag:
                return False
            try:
                if item_type == "comments":
                    original_content = item.body
                    random_text = self.generate_random_text()
                    print(f"Replacing original comment '{original_content[:25]}...' with random text.")
                    item.edit(random_text)
                    print(f"Deleting comment: '{original_content[:25]}...'")
                    item.delete()
                elif item_type == "posts":
                    original_content = item.title
                    random_text = self.generate_random_text()
                    print(f"Replacing original post '{original_content[:25]}...' with random text.")
                    item.edit(random_text)
                    print(f"Deleting post: '{original_content[:25]}...'")
                    item.delete()
                elif item_type == "saved":
                    print(f"Unsaving item: '{getattr(item, 'id', 'N/A')}'")
                    item.unsave()
                elif item_type in ["upvotes", "downvotes"]:
                    print(f"Attempting to clear {item_type[:-1]} on item: '{getattr(item, 'id', 'N/A')}'")
                    item.clear_vote()
                    print(f"Successfully cleared {item_type[:-1]} on item: '{getattr(item, 'id', 'N/A')}'")
                elif item_type == "hidden":
                    print(f"Unhiding post: '{getattr(item, 'id', 'N/A')}'")
                    item.unhide()
                processed_counts[item_type] += 1
                return True
            except (praw.exceptions.RedditAPIException, ResponseException) as e:
                if isinstance(e, ResponseException) and e.response.status_code == 400:
                    print(
                        "Encountered a 400 HTTP error. Skipping as this is likely "
                        "due to trying to upvote/downvote an archived submission. "
                        "Note: You can disable the option to make your votes public "
                        "in Reddit's settings."
                    )
                    return True
                if isinstance(e, praw.exceptions.RedditAPIException):
                    print(f"Encountered a Reddit API Exception. Probably hit the rate limit: {e}")
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                    print(f"\nAttempt {attempt + 1} failed. Retrying in {sleep_time:.2f} seconds...")
                    for _ in range(int(sleep_time * 10)):  # Check interrupt flag every 0.1 seconds
                        if self.interrupt_flag:
                            return False
                        time.sleep(0.1)
                else:
                    print(f"Failed to process {item_type} after {max_retries} attempts.")
        return False

    def process_batch(self, items: List[Union[praw.models.Comment, praw.models.Submission]],
                      item_type: str, batch_number: int, total_processed: int,
                      total_items: int, processed_counts: Dict[str, int]) -> int:
        """
        Process a batch of Reddit items.

        Args:
            items (List[Union[praw.models.Comment, praw.models.Submission]]):
                A list of Reddit items to process. Can be either Comments or Submissions.
            item_type (str): The type of the items ('comments', 'posts', 'saved', 'upvotes', 'downvotes', 'hidden').
            batch_number (int): The current batch number.
            total_processed (int): The total number of items processed so far.
            total_items (int): The total number of items to process.
            processed_counts (Dict[str, int]): A dictionary to keep track of processed items.

        Returns:
            int: The updated total number of processed items.
        """
        print(f"Starting batch {batch_number} for {item_type}")

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self.process_item, item, item_type, processed_counts) for item in items]
            for future in as_completed(futures):
                if self.interrupt_flag:
                    executor.shutdown(wait=False)
                    return total_processed
                if future.result():
                    total_processed += 1

        print(f"Progress: {total_processed}/{total_items} {item_type} processed so far.")
        print(f"Finished batch {batch_number} for {item_type}. Sleeping for five seconds...")
        for _ in range(50):  # Check interrupt flag every 0.1 seconds
            if self.interrupt_flag:
                return total_processed
            time.sleep(0.1)
        return total_processed

    def process_items_in_batches(self, items: List[Union[praw.models.Comment, praw.models.Submission]],
                                 item_type: str, total_items: int,
                                 processed_counts: Dict[str, int]) -> int:
        """
        Process a list of Reddit items in batches.

        Args:
            items (List[Union[praw.models.Comment, praw.models.Submission]]):
                A list of Reddit items to process. Can be either Comments or Submissions.
            item_type (str): The type of the items ('comments', 'posts', 'saved', 'upvotes', 'downvotes', 'hidden').
            total_items (int): The total number of items to process.
            processed_counts (Dict[str, int]): A dictionary to keep track of processed items.

        Returns:
            int: The total number of processed items.
        """
        batch = []
        batch_number = 1
        total_processed = 0

        for item in items:
            batch.append(item)
            if len(batch) == 50:
                total_processed = self.process_batch(
                    batch, item_type, batch_number, total_processed, total_items, processed_counts
                )
                batch = []
                batch_number += 1
        if batch:
            total_processed = self.process_batch(
                batch, item_type, batch_number, total_processed, total_items, processed_counts
            )
        return total_processed

    @staticmethod
    def fetch_items(item_listing: Callable[..., praw.models.ListingGenerator],
                    sort_type: str) -> List[Union[praw.models.Comment, praw.models.Submission]]:
        """
        Fetch Reddit items (comments and submissions) based on the provided listing and sort type.

        Args:
            item_listing (Callable[..., praw.models.ListingGenerator]):
                A method that when called returns a ListingGenerator for Reddit items.
            sort_type (str): The sort type for the listing ('controversial', 'top', 'new', 'hot').

        Returns:
            List[Union[praw.models.Comment, praw.models.Submission]]: A list of fetched Reddit items,
            which can be either Comments or Submissions.
        """
        if sort_type in ["controversial", "top"]:
            return list(item_listing(time_filter="all", limit=None))
        # 'new' and 'hot' do not use use 'time_filter'.
        return list(item_listing(limit=None))

    def delete_all_content(self) -> Dict[str, int]:
        """
        Delete all content for the user.

        This method fetches and processes all types of content (comments, posts, saved items,
        upvotes, downvotes, and hidden posts) for deletion or modification.

        Returns:
            Dict[str, int]: A dictionary containing the count of processed items for each content type.

        Raises:
            SystemExit: If the process is interrupted.
        """
        processed_counts = {
            "comments": 0,
            "posts": 0,
            "saved": 0,
            "upvotes": 0,
            "downvotes": 0,
            "hidden": 0
        }

        try:
            redditor = self.reddit.redditor(self.username)
            items = {
                "comments": set(),
                "posts": set(),
                "saved": set(),
                "upvotes": set(),
                "downvotes": set(),
                "hidden": set()
            }

            # Fetch comments and posts...
            for sort_type in ["controversial", "top", "new", "hot"]:
                print(f"Fetching comments sorted by {sort_type}...")
                items["comments"].update(self.fetch_items(getattr(redditor.comments, sort_type), sort_type))
                print(f"Total unique comments found so far: {len(items['comments'])}")

                print(f"Fetching posts sorted by {sort_type}...")
                items["posts"].update(self.fetch_items(getattr(redditor.submissions, sort_type), sort_type))
                print(f"Total unique posts found so far: {len(items['posts'])}")

            # Fetch other content types...
            print("Fetching saved content...")
            items["saved"] = set(self.reddit.user.me().saved(limit=None))
            print(f"Total saved items found: {len(items['saved'])}")

            print("Fetching upvoted content...")
            items["upvotes"] = set(self.reddit.user.me().upvoted(limit=None))
            print(f"Total upvoted items found: {len(items['upvotes'])}")

            print("Fetching downvoted content...")
            items["downvotes"] = set(self.reddit.user.me().downvoted(limit=None))
            print(f"Total downvoted items found: {len(items['downvotes'])}")

            print("Fetching hidden content...")
            items["hidden"] = set(self.reddit.user.me().hidden(limit=None))
            print(f"Total hidden items found: {len(items['hidden'])}")

            for item_type, item_set in items.items():
                if self.interrupt_flag:
                    break
                total_items = len(item_set)
                print(f"Processing {total_items} {item_type}...")
                self.process_items_in_batches(list(item_set), item_type, total_items, processed_counts)

        finally:
            # Update self.total_processed_dict regardless of whether an exception occurred.
            for item_type, count in processed_counts.items():
                self.total_processed_dict[item_type] += count

        return processed_counts
