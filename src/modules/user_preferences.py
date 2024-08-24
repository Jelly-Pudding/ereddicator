from typing import Optional
from dataclasses import dataclass


@dataclass
class UserPreferences:
    """
    A class to store and manage user preferences for Reddit content management.

    This class uses boolean flags to indicate which types of content the user wants to delete,
    and includes karma thresholds for comments and posts. Content with karma above or equal to
    the threshold will be preserved.

    Attributes:
        delete_comments (bool): Flag to delete comments.
        delete_posts (bool): Flag to delete posts.
        delete_saved (bool): Flag to unsave saved items.
        delete_upvotes (bool): Flag to remove upvotes.
        delete_downvotes (bool): Flag to remove downvotes.
        delete_hidden (bool): Flag to unhide hidden posts.
        comment_karma_threshold (Optional[int]): Karma threshold for comments. Comments with karma
            greater than or equal to this value will be kept. If None, all selected comments will be deleted.
        post_karma_threshold (Optional[int]): Karma threshold for posts. Posts with karma
            greater than or equal to this value will be kept. If None, all selected posts will be deleted.
    """

    delete_comments: bool = True
    delete_posts: bool = True
    delete_saved: bool = True
    delete_upvotes: bool = True
    delete_downvotes: bool = True
    delete_hidden: bool = True
    comment_karma_threshold: Optional[int] = None
    post_karma_threshold: Optional[int] = None

    @classmethod
    def from_user_input(cls) -> 'UserPreferences':
        """
        Create a UserPreferences instance based on user input.

        This method prompts the user to choose which content types they want to delete
        and set karma thresholds for comments and posts.

        Returns:
            UserPreferences: An instance of UserPreferences with user-selected preferences.
        """
        print("\nPlease select which content types you want to delete:")
        preferences = cls()
        for field in ["comments", "posts", "saved", "upvotes", "downvotes", "hidden"]:
            response = input(f"Delete {field}? (Y/n): ").strip().lower()
            setattr(preferences, f"delete_{field}", response != "n")

        if preferences.delete_comments:
            threshold = input("Enter karma threshold for comments to keep (>= value), or '*' to delete all: ")
            preferences.comment_karma_threshold = None if threshold == "*" else int(threshold)

        if preferences.delete_posts:
            threshold = input("Enter karma threshold for posts to keep (>= value), or '*' to delete all: ")
            preferences.post_karma_threshold = None if threshold == "*" else int(threshold)

        return preferences

    def any_selected(self) -> bool:
        """
        Check if any content type is selected for deletion or modification.

        Returns:
            bool: True if at least one content type is selected for deletion or modification, False otherwise.
        """
        return any(getattr(self, field) for field in self.__dataclass_fields__ if field.startswith('delete_'))
