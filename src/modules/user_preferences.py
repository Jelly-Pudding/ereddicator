from typing import Optional
from dataclasses import dataclass

@dataclass
class UserPreferences:
    """
    A class to store and manage user preferences for Reddit content management.

    This class uses boolean flags to indicate which types of content the user wants to delete or edit,
    includes karma thresholds for comments and posts, and an option to occasionally advertise
    Ereddicator when editing text before deletion. Content with karma above or equal to
    the threshold will be preserved.

    Attributes:
        delete_comments (bool): Flag to delete comments.
        delete_posts (bool): Flag to delete posts.
        delete_saved (bool): Flag to unsave saved items.
        delete_upvotes (bool): Flag to remove upvotes.
        delete_downvotes (bool): Flag to remove downvotes.
        delete_hidden (bool): Flag to unhide hidden posts.
        only_edit_comments (bool): Flag to only edit comments without deleting.
        only_edit_posts (bool): Flag to only edit posts without deleting.
        comment_karma_threshold (Optional[int]): Karma threshold for comments. Comments with karma
            greater than or equal to this value will be kept. If None, all selected comments will be deleted.
        post_karma_threshold (Optional[int]): Karma threshold for posts. Posts with karma
            greater than or equal to this value will be kept. If None, all selected posts will be deleted.
        advertise_ereddicator (bool): Flag to occasionally advertise Ereddicator when editing text before deletion.
    """

    delete_comments: bool = True
    delete_posts: bool = True
    delete_saved: bool = True
    delete_upvotes: bool = True
    delete_downvotes: bool = True
    delete_hidden: bool = True
    only_edit_comments: bool = False
    only_edit_posts: bool = False
    comment_karma_threshold: Optional[int] = None
    post_karma_threshold: Optional[int] = None
    advertise_ereddicator: bool = False

    def any_selected(self) -> bool:
        """
        Check if any content type is selected for deletion or modification.

        Returns:
            bool: True if at least one content type is selected for deletion or modification, False otherwise.
        """
        return any(getattr(self, field) for field in self.__dataclass_fields__ if field.startswith('delete_') or field.startswith('only_edit_'))
