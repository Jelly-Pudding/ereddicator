import random
import string
import time
import os
import csv
from typing import Dict, List, Union, Callable, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import praw
from prawcore import ResponseException
from prawcore.exceptions import Forbidden
from modules.user_preferences import UserPreferences

class RedditContentRemover:
    """
    A class to handle the removal of Reddit content.

    This class manages the process of fetching and removing various types of Reddit content
    including comments, posts, saved items, upvotes, downvotes, and hidden posts.
    """

    def __init__(self, reddit: praw.Reddit, username: str, preferences: UserPreferences):
        """
        Initialise the RedditContentRemover instance.

        Args:
            reddit (praw.Reddit): An authenticated Reddit instance.
            username (str): The username of the Reddit account.
            preferences (UserPreferences): User preferences for content deletion.
        """
        self.reddit = reddit
        self.username = username
        self.preferences = preferences
        self.total_deleted_dict = {k: 0 for k in ["comments", "posts", "saved", "upvotes", "downvotes", "hidden"]}
        self.total_edited_dict = {k: 0 for k in ["comments", "posts"]}
        self.processed_ids = set()
        self.interrupt_flag = False
        self.ad_text = (
            "Original Content erased using Ereddicator. "
            "Want to wipe your own Reddit history? "
            "Please see https://github.com/Jelly-Pudding/ereddicator for instructions."
        )

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

    def get_replacement_text(self) -> str:
        """
        Determines the text to replace the original content.

        This method decides whether to use advertising text, custom text, or random text based
        on user preferences. If advertising is enabled, it has a 50% chance of being used.

        Returns:
            str: The text to use for replacement.
        """
        if self.preferences.advertise_ereddicator and random.random() < 0.5:
            return self.ad_text
        if self.preferences.custom_replacement_text:
            return self.preferences.custom_replacement_text
        return self.generate_random_text()

    def get_item_info(self, item: Union[praw.models.Comment, praw.models.Submission], item_type: str) -> str:
        """
        Get a string representation of the item for logging purposes.

        Args:
            item (Union[praw.models.Comment, praw.models.Submission]): The Reddit item.
            item_type (str): The type of the item.

        Returns:
            str: A string representation of the item. Returns "FORBIDDEN" if the item cannot be accessed
            (which can happen if the subreddit is private or banned).
        """
        try:
            # Force fetch the data first to trigger any potential 403s. This must be done as otherwise
            # 403s are impossible to catch.
            _ = item._fetch()
            
            if isinstance(item, praw.models.Comment):
                return (
                    f"Comment '{item.body[:25]}"
                    f"{'...' if len(item.body) > 25 else ''}' "
                    f"in r/{item.subreddit.display_name}"
                )
            if isinstance(item, praw.models.Submission):
                return (
                    f"Post '{item.title[:25]}"
                    f"{'...' if len(item.title) > 25 else ''}' "
                    f"in r/{item.subreddit.display_name}"
                )
            return f"{item_type.capitalize()} item (ID: {item.id}) of type {type(item).__name__}"
        except Forbidden:
            return "FORBIDDEN"
        except AttributeError:
            return f"{item_type.capitalize()} item (ID: {getattr(item, 'id', 'N/A')})"

    def edit_item_multiple_times(self, item: Union[praw.models.Comment, praw.models.Submission],
                                 item_type: str, item_info: str, edit_count: int = 3, max_retries: int = 5) -> bool:
        """
        Edit a Reddit item (comment or post) multiple times before deletion, with retry mechanism.

        Args:
            item (Union[praw.models.Comment, praw.models.Submission]): The item to edit.
            item_type (str): The type of item ('comments' or 'posts').
            item_info (str): Pre-computed string representation of the item for logging.
            edit_count (int): The number of times to edit the item. Defaults to 3.
            max_retries (int): Maximum number of retry attempts for each edit. Defaults to 5.

        Returns:
            bool: True if at least one edit was successful, False otherwise.
        """
        successfully_edited = False
        for i in range(edit_count):
            if self.interrupt_flag:
                break
            replacement_text = self.get_replacement_text()
            for attempt in range(max_retries):
                try:
                    text_type = (
                        "custom" if replacement_text == self.preferences.custom_replacement_text
                        else "advertising" if replacement_text == self.ad_text
                        else "random"
                    )
                    print(
                        f"Edit {i+1}/{edit_count}: Editing {item_type[:-1]} '{item_info}' "
                        f"with {text_type} text."
                    )
                    item.edit(replacement_text)
                    successfully_edited = True
                    break
                except praw.exceptions.RedditAPIException as e:
                    if "Your post isn't accessible. Double-check it and try again." in str(e):
                        print(f"'{item_info}' was found to be deleted. Skipping further edit attempts...")
                        return False
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                        print(f"Encountered a Reddit API Exception: {e}")
                        print(
                            f"Likely hit the rate limit. Retrying edit in {sleep_time:.2f} seconds... "
                            f"(Attempt {attempt + 1}/{max_retries})"
                        )
                        for _ in range(int(sleep_time * 10)):
                            if self.interrupt_flag:
                                return successfully_edited
                            time.sleep(0.1)
                    else:
                        print(f"Failed to edit {item_type[:-1]} '{item_info}' after {max_retries} attempts.")
            time.sleep(0.8)
        return successfully_edited

    def process_item(self, item: Union[praw.models.Comment, praw.models.Submission],
                    item_type: str, max_retries: int = 5) -> Tuple[int, int]:
        """
        Process a single Reddit item (comment, post, etc.) for removal or modification.

        Args:
            item (Union[praw.models.Comment, praw.models.Submission]):
                The Reddit item to process. Can be either a Comment or a Submission.
            item_type (str): The type of item ('comments', 'posts', 'saved', 'upvotes', 'downvotes', 'hidden').
            max_retries (int): Maximum number of retry attempts. Defaults to 5.

        Returns:
            Tuple[int, int]: A tuple containing (deleted_count, edited_count).
        """
        deleted_count = 0
        edited_count = 0
        item_info = f"DEFAULT - {item_type.capitalize()} item (ID: {getattr(item, 'id', 'N/A')})"

        try:
            item_info = self.get_item_info(item, item_type)
            if item_info == "FORBIDDEN":
                print(
                    f"Access Forbidden (403) while accessing {item_type[:-1]} properties. "
                    f"ID: {getattr(item, 'id', 'N/A')}. This is likely because the item is in a subreddit "
                    f"which is private or banned. Skipping."
                )
                return (deleted_count, edited_count)
        except Exception as e:
            if "no data returned" in str(e).lower():
                print(
                    f"Skipping {item_type[:-1]} with id {item.id} - can't access the item as it is "
                    "likely in a subreddit that is either private or banned."
                )
                return (deleted_count, edited_count)
            print(f"Error accessing item info: {str(e)}. Skipping item.")
            return (deleted_count, edited_count)
        
        if item_info == f"DEFAULT - {item_type.capitalize()} item (ID: {getattr(item, 'id', 'N/A')})":
            print(f"Unable to get item info for {item_type} (ID: {getattr(item, 'id', 'N/A')}) - item properties may be inaccessible. Skipping.")
            return (deleted_count, edited_count)

        # Skip already deleted or removed content...
        if (
            item_info.startswith("Comment '[deleted]'") or item_info.startswith("Comment '[removed]'")
        ):
            print(f"Skipping already deleted or removed {item_type[:-1]}: {item_info}")
            return (deleted_count, edited_count)

        # Skip if it's not in the date range...
        item_date = datetime.fromtimestamp(item.created_utc)
        if not self.preferences.is_within_date_range(item_date):
            print(
                f"Skipping '{item_type}' from {item_date.strftime('%Y-%m-%d')} "
                f"as it's outside the specified date range.\n"
                f"Item info: {item_info}"
            )
            return (deleted_count, edited_count)

        # Skip based on the Subreddit filtering...
        subreddit_name = item.subreddit.display_name if hasattr(item, "subreddit") else None
        if subreddit_name and not self.preferences.should_process_subreddit(subreddit_name):
            if self.preferences.whitelist_subreddits:
                print(
                    f"Skipping '{item_type}' in r/{subreddit_name} as it's in the whitelist.\n"
                    f"Item info: {item_info}"
                )
            else:
                print(
                    f"Skipping '{item_type}' in r/{subreddit_name} as it's not in the blacklist.\n"
                    f"Item info: {item_info}"
                )
            return (deleted_count, edited_count)

        # Skip already processed items...
        if hasattr(item, "id"):
            if item.id in self.processed_ids:
                print(f"Skipping already processed item with ID: {item.id}")
                return (deleted_count, edited_count)
            self.processed_ids.add(item.id)

        for attempt in range(max_retries):
            if self.interrupt_flag:
                return (deleted_count, edited_count)
            try:
                if item_type == "comments":
                    if self.preferences.only_edit_comments:
                        if self.preferences.dry_run:
                            print(f"[DRY RUN] Would edit comment: '{item_info}'")
                            edited_count = 1
                        else:
                            if self.edit_item_multiple_times(item, item_type, item_info):
                                edited_count = 1
                    else:
                        if self.preferences.dry_run:
                            print(f"[DRY RUN] Would edit and delete comment: '{item_info}'")
                            deleted_count = 1
                        else:
                            if self.edit_item_multiple_times(item, item_type, item_info):
                                print(f"Deleting comment: '{item_info}'")
                                item.delete()
                                deleted_count = 1
                            else:
                                print(f"Not deleting comment due to a failure to edit it: '{item_info}'")
                elif item_type == "posts":
                    if item.is_self:
                        if self.preferences.only_edit_posts:
                            if self.preferences.dry_run:
                                print(f"[DRY RUN] Would edit text post: '{item_info}'")
                                edited_count = 1
                            else:
                                if self.edit_item_multiple_times(item, item_type, item_info):
                                    edited_count = 1
                        else:
                            if self.preferences.dry_run:
                                print(f"[DRY RUN] Would edit and delete text post: '{item_info}'")
                                deleted_count = 1
                            else:
                                if self.edit_item_multiple_times(item, item_type, item_info):
                                    print(f"Deleting Text Post: '{item_info}'")
                                    item.delete()
                                    deleted_count = 1
                                else:
                                    print(f"Not deleting text post due to a failure to edit it: '{item_info}'")
                    else:
                        print(f"It is impossible to edit content of 'Link {item_info}'.")
                        if not self.preferences.only_edit_posts:
                            if self.preferences.dry_run:
                                print(f"[DRY RUN] Would delete link post: '{item_info}'")
                            else:
                                print(f"Deleting Link Post: '{item_info}'")
                                item.delete()
                            deleted_count = 1
                elif item_type == "saved":
                    if self.preferences.dry_run:
                        print(f"[DRY RUN] Would unsave item: {item_info}")
                    else:
                        print(f"Unsaving item: {item_info}")
                        item.unsave()
                    deleted_count = 1
                elif item_type in ["upvotes", "downvotes"]:
                    if self.preferences.dry_run:
                        print(f"[DRY RUN] Would clear {item_type[:-1]} on item: {item_info}")
                    else:
                        print(f"Attempting to clear {item_type[:-1]} on item: {item_info}")
                        item.clear_vote()
                        print(f"Successfully cleared {item_type[:-1]} on item: {item_info}")
                    deleted_count = 1
                elif item_type == "hidden":
                    if self.preferences.dry_run:
                        print(f"[DRY RUN] Would unhide post: {item_info}")
                    else:
                        print(f"Unhiding post: {item_info}")
                        item.unhide()
                    deleted_count = 1
                return (deleted_count, edited_count)
            except (praw.exceptions.RedditAPIException, ResponseException) as e:
                if isinstance(e, ResponseException) and e.response.status_code == 400:
                    print(
                        "Encountered a 400 HTTP error. Skipping as this is likely "
                        "due to trying to upvote/downvote an archived submission. "
                        "Note: You can disable the option to make your votes public "
                        "in Reddit's settings."
                    )
                    return (deleted_count, edited_count)
                if isinstance(e, praw.exceptions.RedditAPIException):
                    print(f"Encountered a Reddit API Exception. Probably hit the rate limit: {e}")
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                    print(f"\nAttempt {attempt + 1} failed. Retrying in {sleep_time:.2f} seconds...")
                    for _ in range(int(sleep_time * 10)):
                        if self.interrupt_flag:
                            return (deleted_count, edited_count)
                        time.sleep(0.1)
                else:
                    print(f"Failed to process {item_type} after {max_retries} attempts.")
        return (deleted_count, edited_count)

    def process_batch(self, items: List[Union[praw.models.Comment, praw.models.Submission]],
                    item_type: str, batch_number: int, total_deleted: int, total_edited: int,
                    total_items: int) -> Tuple[int, int]:
        """
        Process a batch of Reddit items concurrently using threads.

        Args:
            items (List[Union[praw.models.Comment, praw.models.Submission]]): The list of items to process.
            item_type (str): The type of the items ('comments', 'posts', 'saved', 'upvotes', 'downvotes', 'hidden').
            batch_number (int): The batch number being processed.
            total_deleted (int): The cumulative total of deleted items before this batch.
            total_edited (int): The cumulative total of edited items before this batch.
            total_items (int): The total number of items to process.

        Returns:
            Tuple[int, int]: The updated total_deleted and total_edited counts after processing the batch.
        """
        print(f"Starting batch {batch_number} for {item_type}")
        processed_so_far = (batch_number - 1) * 50 + len(items)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.process_item, item, item_type) for item in items]
            for future in as_completed(futures):
                if self.interrupt_flag:
                    executor.shutdown(wait=False)
                    return total_deleted, total_edited
                deleted_count, edited_count = future.result()
                total_deleted += deleted_count
                total_edited += edited_count

        print(
            f"\n\n====Progress: {total_deleted} {item_type} deleted, {total_edited} edited out of "
            f"{processed_so_far} processed so far. There are {total_items} {item_type} to process in total.====\n\n"
        )
        print(f"Finished batch {batch_number} for {item_type}. Sleeping for five seconds...")
        for _ in range(50):
            if self.interrupt_flag:
                return total_deleted, total_edited
            time.sleep(0.1)
        return total_deleted, total_edited

    def process_items_in_batches(self, items: List[Union[praw.models.Comment, praw.models.Submission]],
                                item_type: str, total_items: int) -> Tuple[int, int]:
        """
        Process a list of Reddit items in batches.

        Args:
            items (List[Union[praw.models.Comment, praw.models.Submission]]):
                A list of Reddit items to process. Can be either Comments or Submissions.
            item_type (str): The type of the items ('comments', 'posts', 'saved', 'upvotes', 'downvotes', 'hidden').
            total_items (int): The total number of items to process.

        Returns:
            Tuple[int, int]: The total number of deleted and edited items after processing all batches.
        """
        batch = []
        batch_number = 1
        total_deleted = 0
        total_edited = 0

        for item in items:
            batch.append(item)
            if len(batch) == 50:
                total_deleted, total_edited = self.process_batch(
                    batch, item_type, batch_number, total_deleted, total_edited, total_items
                )
                batch = []
                batch_number += 1

        if batch:
            total_deleted, total_edited = self.process_batch(
                batch, item_type, batch_number, total_deleted, total_edited, total_items
            )

        return total_deleted, total_edited

    def get_content_from_csv(self, filename: str, karma_threshold: Optional[int] = None) -> set:
        """
        Read content IDs from a Reddit data export CSV file and return filtered Reddit objects.

        Args:
            filename (str): Name of the CSV file (must be either "comments.csv" or "posts.csv")
            karma_threshold (Optional[int]): If set, only include items with karma below this threshold.
                Defaults to None.

        Returns:
            set: Set of filtered Reddit Comment or Submission objects loaded from the CSV.
        """
        if filename not in ["comments.csv", "posts.csv"]:
            raise ValueError("Filename must be 'comments.csv' or 'posts.csv'")

        content = set()
        filepath = os.path.join(self.preferences.reddit_export_directory, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        print(f"Loading {filename}...")
        already_deleted_count = 0
        filtered_count = 0
        failed_count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                required_columns = {"id", "body"}
                if not required_columns.issubset(reader.fieldnames):
                    raise KeyError(f"Required columns {required_columns} not found in {filename}")

                for row in reader:
                    try:
                        if row["body"] == "[removed]":
                            already_deleted_count += 1
                            continue

                        if filename == "comments.csv":
                            item = self.reddit.comment(id=row["id"])
                        elif filename == "posts.csv":
                            item = self.reddit.submission(id=row["id"])

                        # Apply filters
                        if karma_threshold is not None and item.score >= karma_threshold:
                            filtered_count += 1
                            continue

                        if self.preferences.preserve_gilded and item.gilded:
                            filtered_count += 1
                            continue

                        if self.preferences.preserve_distinguished and item.distinguished:
                            filtered_count += 1
                            continue

                        content.add(item)

                    except Exception as e:
                        failed_count += 1
                        print(f"Failed to load item {row['id']}: {str(e)}")

            print(f"Loaded {len(content)} items from {filename} "
                f"({filtered_count} filtered out, {already_deleted_count} already deleted, "
                f"{failed_count} failed to load)")
            return content

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            raise

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
        # 'new' and 'hot' do not use 'time_filter'.
        return list(item_listing(limit=None))

    def delete_all_content(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Delete all content for the user.

        This method fetches and processes all types of content (comments, posts, saved items,
        upvotes, downvotes, and hidden posts) for deletion or modification.

        Returns:
            Tuple[Dict[str, int], Dict[str, int]]: Two dictionaries containing the count of
            deleted and edited items for each content type.
        """
        deleted_counts = {k: 0 for k in ["comments", "posts", "saved", "upvotes", "downvotes", "hidden"]}
        edited_counts = {k: 0 for k in ["comments", "posts"]}

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

            # Fetch comments and posts from a Reddit export (if provided)...
            if self.preferences.reddit_export_directory:
                if self.preferences.delete_comments or self.preferences.only_edit_comments:
                    print(
                        f"Fetching comments from "
                        f"{os.path.join(self.preferences.reddit_export_directory, 'comments.csv')}..."
                    )
                    items["comments"].update(self.get_content_from_csv(
                        "comments.csv",
                        self.preferences.comment_karma_threshold
                    ))
                if self.preferences.delete_posts or self.preferences.only_edit_posts:
                    print(
                        f"Fetching posts from "
                        f"{os.path.join(self.preferences.reddit_export_directory, 'posts.csv')}..."
                    )
                    items["posts"].update(self.get_content_from_csv(
                        "posts.csv",
                        self.preferences.post_karma_threshold
                    ))

            # Fetch comments and posts from the API if reddit_export_directory is not set...
            else:
                for sort_type in ["controversial", "top", "new", "hot"]:
                    if self.preferences.delete_comments or self.preferences.only_edit_comments:
                        print(f"Fetching comments from Reddit's API sorted by {sort_type}...")
                        comments = self.fetch_items(getattr(redditor.comments, sort_type), sort_type)
                        if self.preferences.comment_karma_threshold is not None:
                            comments = [c for c in comments if c.score < self.preferences.comment_karma_threshold]
                        if self.preferences.preserve_gilded:
                            comments = [c for c in comments if not c.gilded]
                        if self.preferences.preserve_distinguished:
                            comments = [c for c in comments if not c.distinguished]
                        items["comments"].update(comments)
                        print(f"Total unique comments found so far: {len(items['comments'])}")

                    if self.preferences.delete_posts or self.preferences.only_edit_posts:
                        print(f"Fetching posts from Reddit's API sorted by {sort_type}...")
                        posts = self.fetch_items(getattr(redditor.submissions, sort_type), sort_type)
                        if self.preferences.post_karma_threshold is not None:
                            posts = [p for p in posts if p.score < self.preferences.post_karma_threshold]
                        if self.preferences.preserve_gilded:
                            posts = [p for p in posts if not p.gilded]
                        if self.preferences.preserve_distinguished:
                            posts = [p for p in posts if not p.distinguished]
                        items["posts"].update(posts)
                        print(f"Total unique posts found so far: {len(items['posts'])}")

            # Process posts and comments first because otherwise API errors can appear when it comes to
            # deleting upvotes and downvotes on posts and comments that have been deleted.
            for item_type in ["posts", "comments"]:
                if self.interrupt_flag:
                    break
                if (
                    getattr(self.preferences, f"delete_{item_type}")
                    or getattr(self.preferences, f"only_edit_{item_type}")
                ):
                    total_items = len(items[item_type])
                    print(f"Processing {total_items} {item_type}...")
                    deleted_count, edited_count = self.process_items_in_batches(
                        list(items[item_type]), item_type, total_items
                    )
                    deleted_counts[item_type] += deleted_count
                    edited_counts[item_type] += edited_count

            # Only now fetch other content types...
            if self.preferences.delete_saved:
                print("Fetching saved content...")
                items["saved"] = set(self.reddit.user.me().saved(limit=None))
                print(f"Total saved items found: {len(items['saved'])}")

            if self.preferences.delete_upvotes:
                print("Fetching upvoted content...")
                items["upvotes"] = set(self.reddit.user.me().upvoted(limit=None))
                print(f"Total upvoted items found: {len(items['upvotes'])}")

            if self.preferences.delete_downvotes:
                print("Fetching downvoted content...")
                items["downvotes"] = set(self.reddit.user.me().downvoted(limit=None))
                print(f"Total downvoted items found: {len(items['downvotes'])}")

            if self.preferences.delete_hidden:
                print("Fetching hidden content...")
                items["hidden"] = set(self.reddit.user.me().hidden(limit=None))
                print(f"Total hidden items found: {len(items['hidden'])}")

            # Process remaining items...
            for item_type in ["saved", "upvotes", "downvotes", "hidden"]:
                if self.interrupt_flag:
                    break
                if getattr(self.preferences, f"delete_{item_type}"):
                    total_items = len(items[item_type])
                    print(f"Processing {total_items} {item_type}...")
                    deleted_count, _ = self.process_items_in_batches(
                        list(items[item_type]), item_type, total_items
                    )
                    deleted_counts[item_type] += deleted_count

        finally:
            for item_type, count in deleted_counts.items():
                self.total_deleted_dict[item_type] += count
            for item_type, count in edited_counts.items():
                self.total_edited_dict[item_type] += count

        return deleted_counts, edited_counts
