import time
import signal
import sys
from modules.reddit_auth import RedditAuth
from modules.reddit_content_remover import RedditContentRemover


def main():
    is_exe = getattr(sys, "frozen", False)

    # Create an instance of RedditAuth
    auth = RedditAuth(is_exe=is_exe)
    # Get the Reddit instance (this will exit the program if authentication fails).
    reddit = auth.get_reddit_instance()

    confirmation = input("This will remove ALL your Reddit content including comments, "
                         "posts, saved items, votes, and hidden posts. "
                         "Do you really want to continue? (yes/no): ")
    if confirmation.lower() not in ['yes', 'y']:
        print("Script aborted.")
        sys.exit(1)

    run_count = 0
    content_remover = RedditContentRemover(reddit, auth.username)

    def interrupt_handler(signum, frame):
        print("\nInterrupt received. Stopping content removal...")
        content_remover.interrupt_flag = True

    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)

    try:
        while True:
            run_count += 1
            print(f"\nStarting run #{run_count}")
            print("Removing Reddit content...")
            processed_counts = content_remover.delete_all_content()

            if content_remover.interrupt_flag:
                print("Run interrupted.")
                break

            print("\nContent destroyed in this run:")
            for item_type, count in processed_counts.items():
                print(f"{item_type.capitalize()}: {count}")

            if all(count == 0 for count in processed_counts.values()):
                print("\nNo content was destroyed in this run. Stopping runs...")
                break
            print("\nSome content was destroyed. Running the script again in 7 seconds...")
            for _ in range(70):  # Check interrupt every 0.1 seconds
                if content_remover.interrupt_flag:
                    break
                time.sleep(0.1)
            if content_remover.interrupt_flag:
                break

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print(f"\nTotal content destroyed across {run_count} {'run' if run_count == 1 else 'runs'}:")
        for item_type, count in content_remover.total_processed_dict.items():
            print(f"{item_type.capitalize()}: {count}")
        if is_exe:
            print("\nPress Enter to exit...")
            input()


if __name__ == "__main__":
    main()
