import random
import string
import time
import os
import csv
import re
from typing import Dict, List, Set, Union, Callable, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import praw
from prawcore import ResponseException
from prawcore.exceptions import Forbidden, NotFound
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
        self.processed_ids_file = f"ereddicator_{self.username}_processed_ids.txt"
        self.processed_ids = self.load_processed_ids()
        self.interrupt_flag = False
        self.ad_messages = [
            "Original content erased using Ereddicator.",
            "This content has been removed with Ereddicator.",
            "Content deleted with Ereddicator.",
            "This text was edited using Ereddicator.",
            "Ereddicator was used to remove this content.",
            "Content cleared with Ereddicator.",
            "This text was replaced using Ereddicator."
        ]

    @staticmethod
    def parse_ratelimit_time(error_message: str) -> Optional[float]:
        """
        Parse the rate limit time from a Reddit API exception message.

        Args:
            error_message (str): The error message string from Reddit.

        Returns:
            Optional[float]: The required wait time in seconds, or None if not found.
        """
        # Primary pattern: "Take a break for X seconds"
        match = re.search(r"take a break for (\d+)\s+seconds?", error_message, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Fallback pattern: "Try again in X minutes"
        match = re.search(r"try again in (\d+)\s+minutes?", error_message, re.IGNORECASE)
        if match:
            return float(match.group(1)) * 60.0

        # Fallback pattern: "Try again in X seconds" (just in case)
        match = re.search(r"try again in (\d+)\s+seconds?", error_message, re.IGNORECASE)
        if match:
            return float(match.group(1))

        return None

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

    def load_processed_ids(self) -> set:
        """
        Load the set of processed item IDs from a file.
        
        Returns:
            set: A set of processed item IDs.
        """
        processed_ids = set()
        try:
            if os.path.exists(self.processed_ids_file):
                with open(self.processed_ids_file, "r") as f:
                    for line in f:
                        processed_ids.add(line.strip())
                print(f"Loaded {len(processed_ids)} previously processed IDs from {self.processed_ids_file}")
        except Exception as e:
            print(f"Error loading processed IDs: {e}")
        return processed_ids

    def save_processed_ids(self) -> None:
        """
        Save the set of processed item IDs to a file.
        
        Returns:
            None
        """
        try:
            with open(self.processed_ids_file, "w") as f:
                for item_id in self.processed_ids:
                    f.write(f"{item_id}\n")
            print(f"Saved {len(self.processed_ids)} processed IDs to {self.processed_ids_file}")
        except Exception as e:
            print(f"Error saving processed IDs: {e}")

    def get_replacement_text(self) -> str:
        """
        Determines the text to replace the original content.

        This method decides whether to use advertising text, custom text, or random text based
        on user preferences. If advertising is enabled, it has a 50% chance of being used.

        Returns:
            str: The text to use for replacement.
        """
        if self.preferences.advertise_ereddicator and random.random() <= 0.5:
            return random.choice(self.ad_messages)
        if self.preferences.custom_replacement_text:
            return self.preferences.custom_replacement_text
        return self.generate_random_text()

    def _handle_ratelimit_sleep(self, exception: Exception, attempt: int, max_retries: int, context: str = "operation") -> bool:
        """Handles sleep logic for rate limits and other retryable API errors.

        Args:
            exception (Exception): The caught exception.
            attempt (int): The current retry attempt number (0-indexed).
            max_retries (int): The maximum number of retries allowed.
            context (str): A string describing the operation being attempted (for logging).

        Returns:
            bool: True if a retry should be attempted, False otherwise (max retries reached, interrupt, non-retryable error).
        """
        if attempt >= max_retries - 1:
            print(f"Failed {context} after {max_retries} attempts due to persistent error: {exception}")
            return False

        sleep_time = 0
        retry_message_prefix = "API Error"

        if isinstance(exception, praw.exceptions.RedditAPIException):
            error_str = str(exception)
            ratelimit_sleep = self.parse_ratelimit_time(error_str)
            retry_message_prefix = f"Reddit API Exception during {context}"

            if ratelimit_sleep is not None:
                sleep_time = ratelimit_sleep + 0.5
                retry_message = f"Respecting API rate limit. Retrying in {sleep_time:.2f} seconds..."
            else:
                sleep_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                retry_message = f"Rate limit likely (could not parse time). Retrying in {sleep_time:.2f} seconds..."
        else:
             sleep_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
             retry_message = f"Retrying in {sleep_time:.2f} seconds..."
             retry_message_prefix = f"Error during {context}"

        print(f"{retry_message_prefix}: {exception}")
        print(f"{retry_message} (Attempt {attempt + 1}/{max_retries})")

        # Interruptible sleep
        sleep_until = time.time() + sleep_time
        while time.time() < sleep_until:
            if self.interrupt_flag:
                print(f"Interrupt received during wait for {context}.")
                return False
            time.sleep(min(0.1, max(0, sleep_until - time.time())))

        return True

    def get_item_info(
        self, item: Union[praw.models.Comment, praw.models.Submission],
        item_type: str, max_retries: int = 5
    ) -> Tuple[str, Optional[Union[praw.models.Comment, praw.models.Submission]]]:
        """Get item info, with retries for API errors."""
        for attempt in range(max_retries):
            try:
                _ = item._fetch()
                if isinstance(item, praw.models.Comment):
                    return (
                        f"Comment '{item.body[:25]}"
                        f"{'...' if len(item.body) > 25 else ''}' "
                        f"in r/{item.subreddit.display_name}",
                        item
                    )
                if isinstance(item, praw.models.Submission):
                    return (
                        f"Post '{item.title[:25]}"
                        f"{'...' if len(item.title) > 25 else ''}' "
                        f"in r/{item.subreddit.display_name}",
                        item
                    )
                return (
                    f"{item_type.capitalize()} item (ID: {item.id}) of type {type(item).__name__}",
                    item
                )
            except Forbidden:
                 return (
                     f"Access Forbidden (403) whilst accessing {item_type[:-1]} properties. "
                     f"ID: {getattr(item, 'id', 'N/A')}. Skipping item.", None
                 )
            except NotFound:
                 return (
                     f"Not Found (404) whilst accessing {item_type[:-1]} properties. "
                     f"ID: {getattr(item, 'id', 'N/A')}. Skipping item.", None
                 )
            except AttributeError:
                 return f"{item_type.capitalize()} item (ID: {getattr(item, 'id', 'N/A')}) - Attribute error... Skipping item", None
            except ResponseException as e:
                 return f"Encountered an HTTP error whilst getting item info: {e}... Skipping item", None
            except praw.exceptions.RedditAPIException as e:
                 context = f"getting info for {item_type} (ID: {getattr(item, 'id', 'N/A')})"
                 should_retry = self._handle_ratelimit_sleep(e, attempt, max_retries, context)
                 if not should_retry:
                     return (
                         f"API error persisted after {max_retries} attempts when trying to access "
                         f"{item_type.capitalize()} (ID: {getattr(item, 'id', 'N/A')})... Skipping item.",
                         None
                     )
            except Exception as e:
                 if "no data returned" in str(e).lower():
                     return(
                         f"Cannot access the {item_type[:-1]} item with id {getattr(item, 'id', 'N/A')} as it is "
                         "likely deleted, private or banned... Skipping item", None
                     )
                 return (
                    f"Unexpected error occurred when trying to access the "
                    f"{item_type.capitalize()} (ID: {getattr(item, 'id', 'N/A')}): {str(e)}... Skipping item.",
                    None
                )
        return (f"Failed to get item info for {item_type} ID {getattr(item, 'id', 'N/A')} after {max_retries} attempts.", None)

    def edit_item_multiple_times(self, item: Union[praw.models.Comment, praw.models.Submission],
                                 item_type: str, item_info: str, edit_count: int = 3, max_retries: int = 5) -> bool:
        """Edit item, using _handle_ratelimit_sleep for retries."""
        successfully_edited = False
        for i in range(edit_count):
            if self.interrupt_flag: break
            replacement_text = self.get_replacement_text()

            for attempt in range(max_retries):
                try:
                    text_type = (
                        "custom" if replacement_text == self.preferences.custom_replacement_text
                        else "advertising" if replacement_text in self.ad_messages
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
                    if "Your post isn't accessible." in str(e):
                        print(f"'{item_info}' seems deleted. Skipping further edit attempts...")
                        return False

                    context = f"editing {item_type[:-1]} '{item_info}' (Edit {i+1}/{edit_count})"
                    should_retry = self._handle_ratelimit_sleep(e, attempt, max_retries, context)
                    if not should_retry:
                         print(f"Stopping edit attempts for '{item_info}' due to persistent API error or interrupt.")
                         return successfully_edited
                except Exception as e:
                     print(f"Unexpected error during edit attempt {attempt + 1}/{max_retries} for '{item_info}': {e}")
                     if attempt < max_retries - 1:
                          time.sleep(1)
                     else:
                          print(f"Failed edit attempt for '{item_info}' due to unexpected error after {max_retries} tries.")
                          return successfully_edited

            if successfully_edited:
                 time.sleep(0.8)
            else:
                 break

        return successfully_edited

    def process_item(self, item: Union[praw.models.Comment, praw.models.Submission],
                    item_type: str, max_retries: int = 5) -> Tuple[int, int]:
        """Process item, using _handle_ratelimit_sleep for retries."""
        deleted_count = 0
        edited_count = 0

        item_info, refreshed_item = self.get_item_info(item, item_type, max_retries)
        if refreshed_item is None:
            print(item_info)
            return (0, 0)
        item = refreshed_item

        if (
            item_info.startswith("Comment '[deleted]'") or item_info.startswith("Comment '[removed]'")
        ):
            print(f"Skipping already deleted or removed {item_type[:-1]}: {item_info}")
            return (deleted_count, edited_count)

        item_date = datetime.fromtimestamp(item.created_utc)
        if not self.preferences.is_within_date_range(item_date):
            print(
                f"Skipping '{item_type}' from {item_date.strftime('%Y-%m-%d')} "
                f"as it's outside the specified date range.\n"
                f"Item info: {item_info}"
            )
            return (deleted_count, edited_count)

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

        if hasattr(item, "id"):
            if item.id in self.processed_ids:
                print(f"Skipping already processed item with ID: {item.id}")
                return (deleted_count, edited_count)

        for attempt in range(max_retries):
            if self.interrupt_flag: return (deleted_count, edited_count)

            try:
                action_performed = False
                if item_type == "comments":
                    if self.preferences.delete_without_edit_comments:
                        if self.preferences.dry_run:
                            print(f"[DRY RUN] Would delete comment without editing: '{item_info}'")
                            deleted_count = 1
                        else:
                            print(f"Deleting comment without editing: '{item_info}'")
                            item.delete()
                            deleted_count = 1
                            action_performed = True
                    elif self.preferences.only_edit_comments:
                        if self.preferences.dry_run:
                            print(f"[DRY RUN] Would edit comment: '{item_info}'")
                            edited_count = 1
                        else:
                            if self.edit_item_multiple_times(item, item_type, item_info):
                                edited_count = 1
                                action_performed = True
                    else:
                        if self.preferences.dry_run:
                            print(f"[DRY RUN] Would edit and delete comment: '{item_info}'")
                            deleted_count = 1
                        else:
                            if self.edit_item_multiple_times(item, item_type, item_info):
                                print(f"Deleting comment: '{item_info}'")
                                item.delete()
                                deleted_count = 1
                                action_performed = True

                elif item_type == "posts":
                    if item.is_self:
                        if self.preferences.delete_without_edit_posts:
                            if self.preferences.dry_run:
                                print(f"[DRY RUN] Would delete text post without editing: '{item_info}'")
                                deleted_count = 1
                            else:
                                print(f"Deleting text post without editing: '{item_info}'")
                                item.delete()
                                deleted_count = 1
                        elif self.preferences.only_edit_posts:
                            if self.preferences.dry_run:
                                print(f"[DRY RUN] Would edit text post: '{item_info}'")
                                edited_count = 1
                            else:
                                if self.edit_item_multiple_times(item, item_type, item_info):
                                    edited_count = 1
                                action_performed = True
                        else:
                            if self.preferences.dry_run:
                                print(f"[DRY RUN] Would edit and delete text post: '{item_info}'")
                                deleted_count = 1
                            else:
                                if self.edit_item_multiple_times(item, item_type, item_info):
                                    print(f"Deleting text post: '{item_info}'")
                                    item.delete()
                                    deleted_count = 1
                                    action_performed = True
                    else:
                        if not self.preferences.delete_without_edit_posts:
                            print(f"It is impossible to edit content of 'Link {item_info}'.")
                        if not self.preferences.only_edit_posts:
                            if self.preferences.dry_run:
                                print(f"[DRY RUN] Would delete link post: '{item_info}'")
                            else:
                                print(f"Deleting link post: '{item_info}'")
                                item.delete()
                            deleted_count = 1
                            action_performed = True

                elif item_type == "saved":
                    if self.preferences.dry_run:
                        print(f"[DRY RUN] Would unsave item: {item_info}")
                    else:
                        print(f"Unsaving item: {item_info}")
                        item.unsave()
                    deleted_count = 1
                    action_performed = True
                elif item_type in ["upvotes", "downvotes"]:
                    if self.preferences.dry_run:
                        print(f"[DRY RUN] Would clear {item_type[:-1]} on item: {item_info}")
                    else:
                        print(f"Attempting to clear {item_type[:-1]} on item: {item_info}")
                        item.clear_vote()
                        deleted_count = 1
                        action_performed = True
                elif item_type == "hidden":
                    if self.preferences.dry_run:
                        print(f"[DRY RUN] Would unhide post: {item_info}")
                    else:
                        print(f"Unhiding post: {item_info}")
                        item.unhide()
                    deleted_count = 1
                    action_performed = True

                if action_performed:
                    if hasattr(item, "id"):
                        self.processed_ids.add(item.id)
                    return (deleted_count, edited_count)

            except (praw.exceptions.RedditAPIException, ResponseException) as e:
                if isinstance(e, ResponseException) and e.response.status_code == 400:
                     return (deleted_count, edited_count)

                context = f"performing action on {item_type} '{item_info}'"
                should_retry = self._handle_ratelimit_sleep(e, attempt, max_retries, context)
                if not should_retry:
                    return (deleted_count, edited_count)

            except Exception as e:
                 print(f"Unexpected error during action for {item_type} '{item_info}': {e}")
                 break

        print(f"Failed to process {item_type} '{item_info}' after {max_retries} attempts or due to unexpected error.")
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
        print(f"\nStarting batch {batch_number} for {item_type}")
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

        # Content-specific progress reporting
        print("\n====Progress Report====")
        print(f"Batch {batch_number}: Processed {len(items)} items")
        print(f"Total processed so far: {processed_so_far} out of {total_items}")

        if item_type in ["comments", "posts"]:
            if getattr(self.preferences, f"delete_without_edit_{item_type}"):
                print(f"Successfully deleted {total_deleted} {item_type} without editing")
            elif getattr(self.preferences, f"only_edit_{item_type}"):
                print(f"Successfully edited {total_edited} {item_type} in total")
            else:
                print(f"Successfully edited and then deleted {total_deleted} {item_type} in total")
        elif item_type == "saved":
            print(f"Successfully unsaved {total_deleted} items in total")
        elif item_type in ["upvotes", "downvotes"]:
            print(f"Successfully cleared {total_deleted} {item_type} in total")
        elif item_type == "hidden":
            print(f"Successfully unhidden {total_deleted} items in total")
        print("====================\n")

        # Save processed IDs after each batch
        print("Saving processed IDs...")
        self.save_processed_ids()

        print(f"Finished batch {batch_number}. Sleeping for five seconds...")
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

    def get_content_from_csv(
        self, filename: str, karma_threshold: Optional[int] = None,
        max_retries: int = 5
    ) -> Set[Union[praw.models.Comment, praw.models.Submission]]:
        """
        Read content IDs from a Reddit data export CSV file and return filtered Reddit objects.

        Args:
            filename (str): Name of the CSV file (must be either "comments.csv" or "posts.csv")
            karma_threshold (Optional[int]): If set, only include items with karma below this threshold.
                Defaults to None.
            max_retries (int): Maximum number of retry attempts for rate limit handling.

        Returns:
            Set[Union[praw.models.Comment, praw.models.Submission]]: 
                A set of filtered Reddit Comment or Submission objects loaded from the CSV.
        """
        if filename not in ["comments.csv", "posts.csv"]:
            raise ValueError("Filename must be 'comments.csv' or 'posts.csv'")

        content = set()
        filepath = os.path.join(self.preferences.reddit_export_directory, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        print(f"Loading {filename}...")
        rows = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                required_columns = {"id", "body", "date"}
                if not required_columns.issubset(reader.fieldnames):
                     raise KeyError(f"Required columns {required_columns} not found in {filename}")
                rows = list(reader)
        except Exception as e:
             print(f"Error initially reading {filename}: {str(e)}")
             raise

        total_rows = len(rows)
        print(f"Found {total_rows} rows in {filename}. Processing...")

        already_deleted_count = 0
        filtered_count = 0
        failed_count = 0
        date_filtered_count = 0
        processed_count = 0

        for i, row in enumerate(rows):
            processed_count = i + 1
            item_id = row.get("id", "UNKNOWN_ID")

            if processed_count % 50 == 0 or processed_count == total_rows:
                 print(f"Processing item {processed_count}/{total_rows} (ID: {item_id})...")

            item = None
            successful_load = False

            for attempt in range(max_retries):
                 if self.interrupt_flag:
                      print("Interrupt received during CSV processing.")
                      break

                 try:
                     if row.get("body") == "[removed]":
                         already_deleted_count += 1
                         filtered_count += 1
                         successful_load = True
                         break
                     try:
                         created_date = datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S UTC")
                         if not self.preferences.is_within_date_range(created_date):
                             filtered_count += 1
                             date_filtered_count += 1
                             successful_load = True
                             break
                     except ValueError:
                         print(f"Invalid date value in row {processed_count}/{total_rows} (ID: {item_id})")
                         successful_load = True
                         break

                     if filename == "comments.csv":
                         item = self.reddit.comment(id=item_id)
                     elif filename == "posts.csv":
                         item = self.reddit.submission(id=item_id)
                     else:
                         continue

                     try:
                         if karma_threshold is not None and item.score >= karma_threshold:
                             filtered_count += 1
                             successful_load = True; break

                         if self.preferences.preserve_gilded and item.gilded:
                             filtered_count += 1
                             successful_load = True; break

                         if self.preferences.preserve_distinguished and item.distinguished:
                             filtered_count += 1
                             successful_load = True; break

                         content.add(item)
                         successful_load = True
                         break

                     except (praw.exceptions.ClientException, praw.exceptions.PRAWException, AttributeError, NotFound) as item_filter_error:
                         error_str = str(item_filter_error).lower()
                         if "no data returned" in error_str or "not found" in error_str or "forbidden" in error_str:
                              if processed_count % 10 == 0:
                                   print(f"Skipping item {item_id} (Row {processed_count}/{total_rows}): Cannot apply filters due to missing data or access issue: {item_filter_error}")
                              successful_load = False
                              break
                         else:
                              print(f"Unexpected PRAW/Attribute error filtering item {item_id} (Row {processed_count}/{total_rows}): {item_filter_error}")
                              successful_load = False
                              break

                 except (praw.exceptions.RedditAPIException, ResponseException) as api_error:
                      context = f"loading/filtering item {item_id} (Row {processed_count}/{total_rows})"
                      should_retry = self._handle_ratelimit_sleep(api_error, attempt, max_retries, context)
                      if not should_retry:
                           successful_load = False
                           break

                 except Exception as e:
                      print(f"General error processing row {processed_count}/{total_rows} (ID: {item_id}) during attempt {attempt+1}: {str(e)}")
                      successful_load = False
                      break

            if self.interrupt_flag:
                 break

            if not successful_load:
                 failed_count += 1

        print(f"Finished processing {filename}.")
        print(f"Loaded {len(content)} valid items. "
              f"({filtered_count} filtered out [{date_filtered_count} by date, {already_deleted_count} already removed], {failed_count} failed to load/filter)")
        return content

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

    def delete_all_content(self, max_retries_csv: int = 5) -> Tuple[Dict[str, int], Dict[str, int]]:
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
                if (self.preferences.delete_comments or
                    self.preferences.only_edit_comments or
                    self.preferences.delete_without_edit_comments):
                    print(
                        f"Fetching comments from "
                        f"{os.path.join(self.preferences.reddit_export_directory, 'comments.csv')}..."
                    )
                    items["comments"].update(self.get_content_from_csv(
                        "comments.csv",
                        self.preferences.comment_karma_threshold,
                        max_retries=max_retries_csv
                    ))
                if (self.preferences.delete_posts or
                    self.preferences.only_edit_posts or
                    self.preferences.delete_without_edit_posts):
                    print(
                        f"Fetching posts from "
                        f"{os.path.join(self.preferences.reddit_export_directory, 'posts.csv')}..."
                    )
                    items["posts"].update(self.get_content_from_csv(
                        "posts.csv",
                        self.preferences.post_karma_threshold,
                        max_retries=max_retries_csv
                    ))

            # Fetch comments and posts from the API if reddit_export_directory is not set...
            else:
                for sort_type in ["controversial", "top", "new", "hot"]:
                    if (self.preferences.delete_comments or
                        self.preferences.only_edit_comments or
                        self.preferences.delete_without_edit_comments):
                        print(f"Fetching comments from Reddit's API sorted by {sort_type}...")
                        comments = self.fetch_items(getattr(redditor.comments, sort_type), sort_type)
                        if self.preferences.comment_karma_threshold is not None:
                            comments = [c for c in comments if c.score < self.preferences.comment_karma_threshold]
                        if self.preferences.preserve_gilded:
                            comments = [c for c in comments if not c.gilded]
                        if self.preferences.preserve_distinguished:
                            comments = [c for c in comments if not c.distinguished]
                        comments = [c for c in comments if self.preferences.is_within_date_range(datetime.fromtimestamp(c.created_utc))]

                        items["comments"].update(comments)
                        print(f"Total unique comments found so far: {len(items['comments'])}")

                    if (self.preferences.delete_posts or
                        self.preferences.only_edit_posts or
                        self.preferences.delete_without_edit_posts):
                        print(f"Fetching posts from Reddit's API sorted by {sort_type}...")
                        posts = self.fetch_items(getattr(redditor.submissions, sort_type), sort_type)
                        if self.preferences.post_karma_threshold is not None:
                            posts = [p for p in posts if p.score < self.preferences.post_karma_threshold]
                        if self.preferences.preserve_gilded:
                            posts = [p for p in posts if not p.gilded]
                        if self.preferences.preserve_distinguished:
                            posts = [p for p in posts if not p.distinguished]
                        posts = [p for p in posts if self.preferences.is_within_date_range(datetime.fromtimestamp(p.created_utc))]
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
                    or getattr(self.preferences, f"delete_without_edit_{item_type}")
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

            self.save_processed_ids()
        
        return deleted_counts, edited_counts
