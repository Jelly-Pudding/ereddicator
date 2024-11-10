import tkinter as tk
import time
import signal
import sys
import os
import threading
import praw
from modules.reddit_auth import RedditAuth
from modules.reddit_content_remover import RedditContentRemover
from modules.user_preferences import UserPreferences
from modules.gui import RedditContentRemoverGUI


def run_content_remover(preferences: UserPreferences, reddit: praw.Reddit, auth: RedditAuth) -> None:
    """
    Execute the content removal process based on user preferences.

    This function initialises the content remover, sets up interrupt handlers,
    and runs the content removal process in a loop until all content is removed
    or an interrupt is received.

    Args:
        preferences (UserPreferences): User-defined preferences for content removal.
        reddit (praw.Reddit): Authenticated Reddit instance for API interactions.
        auth (RedditAuth): Reddit authentication object containing user information.

    Raises:
        Exception: Any unexpected errors during the content removal process.
    """
    if not preferences.any_selected():
        print("No content types selected for deletion or editing. Exiting.")
        return

    run_count = 0
    content_remover = RedditContentRemover(reddit, auth.username, preferences)

    def interrupt_handler(signum, frame):
        print("\nInterrupt received. Stopping content removal...")
        print("Forcing exit in 5 seconds if graceful shutdown fails...")
        content_remover.interrupt_flag = True

        # Set a timer to force exit if graceful shutdown doesn't work
        def force_exit():
            print("\nForcing exit...")
            os._exit(1)

        timer = threading.Timer(5.0, force_exit)
        timer.start()

    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)

    try:
        while True:
            run_count += 1
            print(f"\nStarting run #{run_count}")
            print("Processing Reddit content...")
            deleted_counts, edited_counts = content_remover.delete_all_content()

            if content_remover.interrupt_flag:
                print("Run interrupted.")
                break

            print("\nContent processed in this run:")
            for item_type, count in deleted_counts.items():
                print(f"{item_type.capitalize()} deleted: {count}")
            for item_type, count in edited_counts.items():
                print(f"{item_type.capitalize()} edited: {count}")

            if all(count == 0 for count in deleted_counts.values()):
                print("\nNo content was deleted in this run. Stopping runs...")
                break
            print("\nSome content was deleted. Running the script again in 7 seconds...")
            for _ in range(70):  # Check interrupt every 0.1 seconds
                if content_remover.interrupt_flag:
                    break
                time.sleep(0.1)
            if content_remover.interrupt_flag:
                break

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print(f"\nTotal content processed across {run_count} {'run' if run_count == 1 else 'runs'}:")
        for item_type, count in content_remover.total_deleted_dict.items():
            print(f"{item_type.capitalize()} deleted: {count}")
        for item_type, count in content_remover.total_edited_dict.items():
            print(f"{item_type.capitalize()} edited: {count}")
        if auth.is_exe:
            print("\nPress Enter to exit...")
            input()


def main():
    is_exe = getattr(sys, "frozen", False)
    if is_exe:
        print("Please enter your credential information in the window that pops up. "
              "Always leave this terminal displaying this message open when running Ereddicator.")
    # Create an instance of RedditAuth and get the Reddit instance
    auth = RedditAuth(is_exe=is_exe)
    reddit = auth.get_reddit_instance()

    root = tk.Tk()
    root.tk.call("tk", "scaling", 1.0)  # This ensures consistent sizing across different DPI settings
    _ = RedditContentRemoverGUI(root, start_removal_callback=lambda prefs: run_content_remover(prefs, reddit, auth))
    root.mainloop()


if __name__ == "__main__":
    main()
