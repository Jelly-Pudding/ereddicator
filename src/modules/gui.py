import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Callable
from tkcalendar import DateEntry
from datetime import datetime
from modules.user_preferences import UserPreferences


class CredentialsInputGUI:
    """
    A GUI class for inputting Reddit API credentials.
    """

    def __init__(self, master: tk.Tk) -> None:
        """
        Initialise the CredentialsInputGUI.

        Args:
            master (tk.Tk): The root window for this GUI.
        """
        self.master = master
        self.master.title("Reddit API Credentials")
        self.master.configure(bg="#2b2b2b")

        self.credential_entries = {}
        self.show_password = tk.BooleanVar(value=False)
        self.submitted_credentials = None
        self.create_widgets()
        self.center_window()

        # Adjust window size after creating widgets.
        self.master.update()
        self.master.geometry(f"{self.master.winfo_reqwidth()}x{self.master.winfo_reqheight()}")
        self.master.resizable(False, False)

    def center_window(self):
        """
        Center the credentials window on the screen.
        """
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self) -> None:
        """
        Create and arrange the widgets for the credentials input GUI.
        """
        main_frame = tk.Frame(self.master, bg="#2b2b2b")
        main_frame.pack(padx=10, pady=10)

        fields = ["Client ID", "Client Secret", "Username", "Password", "Two Factor Code"]

        for i, field in enumerate(fields):
            label = tk.Label(main_frame, text=field + ":", bg="#2b2b2b", fg="#ffffff")
            label.grid(row=i, column=0, padx=(0, 10), pady=5, sticky='e')

            entry = tk.Entry(main_frame, bg="#3c3c3c", fg="#ffffff", width=30)
            entry.grid(row=i, column=1, pady=5, sticky="ew")

            if field == "Password":
                entry.config(show="*")
                show_password_cb = tk.Checkbutton(main_frame, text="Show", variable=self.show_password,
                                                  command=lambda e=entry: self.toggle_password_visibility(e),
                                                  bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b")
                show_password_cb.grid(row=i, column=2, padx=(5, 0))

            if field == "Two Factor Code":
                entry.insert(0, "Only change me if you use 2FA")

            self.credential_entries[field.lower()] = entry

        submit_button = tk.Button(main_frame, text="Submit", command=self.submit, bg="#ffffff", fg="#000000")
        submit_button.grid(row=len(fields), column=0, columnspan=3, pady=(10, 0))

        main_frame.grid_columnconfigure(1, weight=1)

    def toggle_password_visibility(self, entry: tk.Entry) -> None:
        """
        Toggle the visibility of the password in the entry widget.

        Args:
            entry (tk.Entry): The password entry widget.
        """
        entry.config(show="" if self.show_password.get() else "*")

    def submit(self) -> None:
        """
        Validate and submit the entered credentials.
        """
        credentials = {}
        for field, entry in self.credential_entries.items():
            value = entry.get().strip()
            if not value and field != "two factor code":
                messagebox.showerror("Error", f"{field} cannot be empty")
                return
            if field == "two factor code" and (value.lower() == "only change me if you use 2fa" or value == ""):
                continue
            credentials[field] = value

        self.submitted_credentials = credentials
        self.master.quit()

    def get_credentials(self) -> Dict[str, str]:
        """
        Retrieve the credentials entered by the user.

        Returns:
            Dict[str, str]: A dictionary containing the user's credentials with keys
                            'client id', 'client secret', 'username', 'password',
                            and 'two factor code'.
        """
        self.master.mainloop()
        return self.submitted_credentials


class RedditContentRemoverGUI:
    """
    A GUI class for the main Reddit Content Remover application.
    """

    def __init__(self, master: tk.Tk, start_removal_callback: Callable[[UserPreferences], None]) -> None:
        """
        Initialise the RedditContentRemoverGUI.

        Args:
            master (tk.Tk): The root window for this GUI.
            start_removal_callback (Callable[[UserPreferences], None]): Callback function to start content removal.
        """
        self.master = master
        self.start_removal_callback = start_removal_callback
        master.title("Ereddicator")
        master.configure(bg="#2b2b2b")
        master.resizable(False, False)

        self.preferences = UserPreferences()
        self.create_widgets()
        self.centre_window()

    def centre_window(self):
        """
        Centre the window on the screen.
        """
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

    def on_entry_click(self, event, entry):
        """
        Handle the event when an entry field is clicked.
        Remove the placeholder text if it's present.
        """
        if entry.get() == "You can leave this blank.":
            entry.delete(0, "end")
            entry.config(fg="white")

    def on_focus_out(self, event, entry):
        """
        Handle the event when focus leaves an entry field.
        Restore the placeholder text if the field is empty.
        """
        if entry.get() == "":
            entry.insert(0, "You can leave this blank.")
            entry.config(fg="grey")

    def select_directory(self) -> None:
        """Handle directory selection for Reddit data export."""
        directory = filedialog.askdirectory(title="Select Reddit Data Export Directory")
        if directory:
            self.export_directory_entry.delete(0, tk.END)  # Clear the entry first
            self.export_directory_entry.insert(0, directory)
            self.export_directory_entry.config(fg="white")

    def create_widgets(self) -> None:
        """Create and arrange the widgets for the main GUI."""
        main_frame = tk.Frame(self.master, bg="#2b2b2b")
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.content_vars = {}
        self.only_edit_vars = {}
        self.delete_without_edit_vars = {}
        self.preserve_vars = {}

        checkbox_frame = tk.Frame(main_frame, bg="#2b2b2b")
        checkbox_frame.pack(fill="x", pady=10)

        left_column = tk.Frame(checkbox_frame, bg="#2b2b2b")
        left_column.pack(side="left", fill="y", expand=True)
        right_column = tk.Frame(checkbox_frame, bg='#2b2b2b')
        right_column.pack(side="right", fill="y", expand=True)

        # Comments
        comment_frame = tk.LabelFrame(left_column, text="Comment Options",
                                    bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        comment_frame.pack(anchor="w", pady=5, padx=5, fill="x")

        self.content_vars["comments"] = tk.BooleanVar(value=False)
        self.only_edit_vars["comments"] = tk.BooleanVar(value=True)
        self.delete_without_edit_vars["comments"] = tk.BooleanVar(value=False)

        tk.Checkbutton(comment_frame, text="Edit then delete comments",
                    variable=self.content_vars["comments"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13),
                    command=lambda: self.update_checkboxes("comments", "edit_then_delete")
                    ).pack(anchor="w", pady=2)

        tk.Checkbutton(comment_frame, text="Only edit comments",
                    variable=self.only_edit_vars["comments"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13),
                    command=lambda: self.update_checkboxes("comments", "only_edit")
                    ).pack(anchor="w", pady=2)

        tk.Checkbutton(comment_frame, text="Delete comments without editing",
                    variable=self.delete_without_edit_vars["comments"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13),
                    command=lambda: self.update_checkboxes("comments", "delete_without_edit")
                    ).pack(anchor="w", pady=2)

        # Posts
        post_frame = tk.LabelFrame(right_column, text="Post Options",
                                bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        post_frame.pack(anchor="w", pady=5, padx=5, fill="x")

        self.content_vars["posts"] = tk.BooleanVar(value=False)
        self.only_edit_vars["posts"] = tk.BooleanVar(value=True)
        self.delete_without_edit_vars["posts"] = tk.BooleanVar(value=False)

        tk.Checkbutton(post_frame, text="Edit then delete posts",
                    variable=self.content_vars["posts"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13),
                    command=lambda: self.update_checkboxes("posts", "edit_then_delete")
                    ).pack(anchor="w", pady=2)

        tk.Checkbutton(post_frame, text="Only edit posts",
                    variable=self.only_edit_vars["posts"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13),
                    command=lambda: self.update_checkboxes("posts", "only_edit")
                    ).pack(anchor="w", pady=2)

        tk.Checkbutton(post_frame, text="Delete posts without editing",
                    variable=self.delete_without_edit_vars["posts"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13),
                    command=lambda: self.update_checkboxes("posts", "delete_without_edit")
                    ).pack(anchor="w", pady=2)

        # Other content types
        other_frame = tk.LabelFrame(main_frame, text="Other Content Options",
                                bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        other_frame.pack(fill="x", pady=10)

        # Create two columns for other options
        other_left = tk.Frame(other_frame, bg="#2b2b2b")
        other_left.pack(side="left", fill="y", expand=True)
        other_right = tk.Frame(other_frame, bg="#2b2b2b")
        other_right.pack(side="right", fill="y", expand=True)

        # Saved and Hidden
        self.content_vars["saved"] = tk.BooleanVar(value=True)
        self.content_vars["hidden"] = tk.BooleanVar(value=True)
        tk.Checkbutton(other_left, text="Delete saved", variable=self.content_vars["saved"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13)).pack(anchor="w", pady=2)
        tk.Checkbutton(other_right, text="Delete hidden", variable=self.content_vars["hidden"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13)).pack(anchor="w", pady=2)

        # Upvotes and Downvotes
        self.content_vars["upvotes"] = tk.BooleanVar(value=True)
        self.content_vars["downvotes"] = tk.BooleanVar(value=True)
        tk.Checkbutton(other_left, text="Delete upvotes", variable=self.content_vars["upvotes"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13)).pack(anchor="w", pady=2)
        tk.Checkbutton(other_right, text="Delete downvotes", variable=self.content_vars["downvotes"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13)).pack(anchor="w", pady=2)

        # Miscellaneous options
        misc_frame = tk.LabelFrame(main_frame, text="Miscellaneous Options",
                                bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        misc_frame.pack(fill="x", pady=10)

        # Create two columns for miscellaneous options
        misc_left = tk.Frame(misc_frame, bg="#2b2b2b")
        misc_left.pack(side="left", fill="y", expand=True)
        misc_right = tk.Frame(misc_frame, bg="#2b2b2b")
        misc_right.pack(side="right", fill="y", expand=True)

        # Preserve Gilded and Distinguished
        self.preserve_vars["gilded"] = tk.BooleanVar(value=False)
        self.preserve_vars["distinguished"] = tk.BooleanVar(value=False)
        tk.Checkbutton(misc_left, text="Preserve gilded", variable=self.preserve_vars["gilded"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13)).pack(anchor="w", pady=2)
        tk.Checkbutton(misc_right, text="Preserve mod distinguished", variable=self.preserve_vars["distinguished"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b",
                    activebackground="#2b2b2b", activeforeground="#ffffff",
                    font=("Arial", 13)).pack(anchor="w", pady=2)

        # Advertising option with question mark
        self.advertise_var = tk.BooleanVar(value=True)
        advertise_frame = tk.Frame(main_frame, bg="#2b2b2b")
        advertise_frame.pack(fill="x", pady=10)

        advertise_cb = tk.Checkbutton(advertise_frame,
                                    text="Advertise Ereddicator",
                                    variable=self.advertise_var,
                                    bg="#2b2b2b",
                                    fg="#ffffff",
                                    selectcolor="#2b2b2b",
                                    activebackground="#2b2b2b",
                                    activeforeground="#ffffff",
                                    font=("Arial", 13))
        advertise_cb.pack(side="left", pady=0)

        ad_question_button = tk.Button(advertise_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        ad_question_button.pack(side="left", padx=(5, 10))

        ad_tooltip_text = "Occasionally replaces content with an Ereddicator ad when editing."
        self.create_tooltip(ad_question_button, ad_tooltip_text)

        # Dry Run option
        dry_run_frame = tk.Frame(main_frame, bg="#2b2b2b")
        dry_run_frame.pack(fill="x", pady=10)

        self.dry_run_var = tk.BooleanVar(value=False)
        dry_run_cb = tk.Checkbutton(dry_run_frame,
                                    text="Dry Run",
                                    variable=self.dry_run_var,
                                    bg="#2b2b2b",
                                    fg="#ffffff",
                                    selectcolor="#2b2b2b",
                                    activebackground="#2b2b2b",
                                    activeforeground="#ffffff",
                                    font=("Arial", 13))
        dry_run_cb.pack(side="left", pady=0)

        dry_run_question_button = tk.Button(dry_run_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        dry_run_question_button.pack(side="left", padx=(5, 10))

        dry_run_tooltip_text = "When enabled this simulates the removal process without actually making any changes."
        self.create_tooltip(dry_run_question_button, dry_run_tooltip_text)

        # Comment karma threshold with question mark
        karma_frame = tk.Frame(main_frame, bg="#2b2b2b")
        karma_frame.pack(fill="x", pady=10)

        self.comment_label = tk.Label(karma_frame, text="Comment Karma Threshold:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        self.comment_label.pack(side="left", padx=(0, 10))
        self.comment_threshold = tk.Entry(karma_frame, bg="#3c3c3c", fg="#ffffff", font=("Arial", 12), width=10, disabledbackground="#3c3c3c", disabledforeground="#ffffff")
        self.comment_threshold.pack(side="left")
        self.comment_threshold.insert(0, "*")

        comment_question_button = tk.Button(karma_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        comment_question_button.pack(side="left", padx=(5, 10))

        comment_tooltip_text = "Use '*' to delete all comments, or enter a number to keep comments with karma greater than or equal to that number."
        self.create_tooltip(comment_question_button, comment_tooltip_text)

        # Post karma threshold with question mark
        karma_frame2 = tk.Frame(main_frame, bg="#2b2b2b")
        karma_frame2.pack(fill="x", pady=10)

        self.post_label = tk.Label(karma_frame2, text="Post Karma Threshold:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        self.post_label.pack(side="left", padx=(0, 10))
        self.post_threshold = tk.Entry(karma_frame2, bg="#3c3c3c", fg="#ffffff", font=("Arial", 12), width=10, disabledbackground="#3c3c3c", disabledforeground="#ffffff")
        self.post_threshold.pack(side="left")
        self.post_threshold.insert(0, "*")

        post_question_button = tk.Button(karma_frame2, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        post_question_button.pack(side="left", padx=(5, 10))

        post_tooltip_text = "Use '*' to delete all posts, or enter a number to keep posts with karma greater than or equal to that number."
        self.create_tooltip(post_question_button, post_tooltip_text)

        # Whitelist Subreddits input
        whitelist_frame = tk.Frame(main_frame, bg="#2b2b2b")
        whitelist_frame.pack(fill="x", pady=10)

        whitelist_label = tk.Label(whitelist_frame, text="Whitelist Subreddits:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        whitelist_label.pack(side="left", padx=(0, 10))
        self.whitelist_entry = tk.Entry(whitelist_frame, bg="#3c3c3c", fg="#ffffff", font=("Arial", 12), width=30)
        self.whitelist_entry.pack(side="left")
        self.whitelist_entry.insert(0, "You can leave this blank.")
        self.whitelist_entry.config(fg='grey')

        whitelist_question_button = tk.Button(whitelist_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        whitelist_question_button.pack(side="left", padx=(5, 10))

        whitelist_tooltip_text = "Comma-separated list of subreddits to NOT process. E.g.: aww,funny,showerthoughts"
        self.create_tooltip(whitelist_question_button, whitelist_tooltip_text)

        # Blacklist Subreddits input
        blacklist_frame = tk.Frame(main_frame, bg="#2b2b2b")
        blacklist_frame.pack(fill="x", pady=10)

        blacklist_label = tk.Label(blacklist_frame, text="Blacklist Subreddits:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        blacklist_label.pack(side="left", padx=(0, 10))
        self.blacklist_entry = tk.Entry(blacklist_frame, bg="#3c3c3c", fg="#ffffff", font=("Arial", 12), width=30)
        self.blacklist_entry.pack(side="left")
        self.blacklist_entry.insert(0, "You can leave this blank.")
        self.blacklist_entry.config(fg='grey')

        blacklist_question_button = tk.Button(blacklist_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        blacklist_question_button.pack(side="left", padx=(5, 10))

        blacklist_tooltip_text = "Comma-separated list of subreddits to EXCLUSIVELY process. E.g.: politics,worldnews,ukpolitics"
        self.create_tooltip(blacklist_question_button, blacklist_tooltip_text)

        # Bind focus events to handle placeholder text
        self.whitelist_entry.bind("<FocusIn>", lambda event: self.on_entry_click(event, self.whitelist_entry))
        self.whitelist_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, self.whitelist_entry))
        self.blacklist_entry.bind("<FocusIn>", lambda event: self.on_entry_click(event, self.blacklist_entry))
        self.blacklist_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, self.blacklist_entry))

        # Custom replacement text
        custom_text_frame = tk.Frame(main_frame, bg="#2b2b2b")
        custom_text_frame.pack(fill="x", pady=10)

        custom_text_label = tk.Label(custom_text_frame, text="Custom replacement text:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        custom_text_label.pack(side="left", padx=(0, 10))

        self.custom_text_entry = tk.Entry(custom_text_frame, bg="#3c3c3c", fg="#ffffff", font=("Arial", 12), width=30)
        self.custom_text_entry.pack(side="left")
        self.custom_text_entry.insert(0, "You can leave this blank.")
        self.custom_text_entry.config(fg='grey')

        custom_text_question_button = tk.Button(custom_text_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        custom_text_question_button.pack(side="left", padx=(5, 10))

        custom_text_tooltip = "Enter custom text to replace your content.\nIf left blank, random text will replace your text."
        self.create_tooltip(custom_text_question_button, custom_text_tooltip)

        # Bind focus events to handle placeholder text
        self.custom_text_entry.bind("<FocusIn>", lambda event: self.on_entry_click(event, self.custom_text_entry))
        self.custom_text_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, self.custom_text_entry))

        # Date range options
        date_frame = tk.Frame(main_frame, bg="#2b2b2b")
        date_frame.pack(fill="x", pady=10)

        start_date_label = tk.Label(date_frame, text="Start Date:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        start_date_label.pack(side="left", padx=(0, 10))
        self.start_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', 
                                          borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date_entry.pack(side="left", padx=(0, 20))
        self.start_date_entry.delete(0, tk.END)  # Clear the default date

        end_date_label = tk.Label(date_frame, text="End Date:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        end_date_label.pack(side="left", padx=(0, 10))
        self.end_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', 
                                        borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date_entry.pack(side="left")
        self.end_date_entry.delete(0, tk.END)  # Clear the default date

        date_question_button = tk.Button(date_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        date_question_button.pack(side="left", padx=(5, 10))

        date_tooltip_text = "Set date range for content processing. Leave blank to include all dates."
        self.create_tooltip(date_question_button, date_tooltip_text)

        # Handle Reddit generated export folder
        export_frame = tk.Frame(main_frame, bg="#2b2b2b")
        export_frame.pack(fill="x", pady=10)

        export_label = tk.Label(export_frame, text="Reddit Export Directory:", 
                              bg="#2b2b2b", fg="#ffffff", font=("Arial", 13))
        export_label.pack(side="left", padx=(0, 10))

        self.export_directory_entry = tk.Entry(export_frame, bg="#3c3c3c", 
                                             fg="grey", font=("Arial", 12), width=30)
        self.export_directory_entry.pack(side="left")
        self.export_directory_entry.insert(0, "Optional: Select folder containing Reddit data export")
        self.export_directory_entry.config(fg='grey')

        browse_button = tk.Button(export_frame, text="Browse", 
                                command=self.select_directory,
                                bg="#ffffff", fg="#000000")
        browse_button.pack(side="left", padx=(5, 5))

        export_question_button = tk.Button(export_frame, text="?", 
                                         font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        export_question_button.pack(side="left", padx=(5, 0))

        export_tooltip_text = (
            "This is optional. Handles content that Reddit's API does not retrieve."
            " Go to reddit.com/settings/data-request. Wait for Reddit's message,"
            " and download and extract the ZIP file. Select the extracted folder here."
        )
        self.create_tooltip(export_question_button, export_tooltip_text)

        self.export_directory_entry.bind("<FocusIn>", 
            lambda event: self.on_entry_click(event, self.export_directory_entry))
        self.export_directory_entry.bind("<FocusOut>", 
            lambda event: self.on_focus_out(event, self.export_directory_entry))

        # Removal button
        self.start_button = tk.Button(main_frame, text="Start Content Removal", command=self.start_removal,
                                    bg="#ffffff", fg="#000000", font=("Arial", 14))
        self.start_button.pack(pady=(20, 20))

    def create_tooltip(self, widget: tk.Widget, text: str, max_width: int = 50) -> None:
        """
        Create a tooltip for a widget with text wrapping.

        Args:
            widget (tk.Widget): The widget to attach the tooltip to.
            text (str): The text to display in the tooltip.
            max_width (int): Maximum width of a line in characters before wrapping.
        """
        tooltipwindow = None

        def wrap_text(text: str, max_width: int) -> str:
            """Wrap text to a maximum width."""
            words = text.split()
            lines = []
            current_line = []
            current_length = 0

            for word in words:
                if current_length + len(word) <= max_width:
                    current_line.append(word)
                    current_length += len(word) + 1  # +1 for the space
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)

            if current_line:
                lines.append(' '.join(current_line))

            return '\n'.join(lines)

        def enter(event=None):
            nonlocal tooltipwindow
            x = y = 0
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20

            # Creates a toplevel window
            tooltipwindow = tk.Toplevel(widget)
            # Leaves only the label and removes the app window
            tooltipwindow.wm_overrideredirect(True)
            tooltipwindow.wm_geometry(f"+{x}+{y}")
            label = tk.Label(tooltipwindow, text=wrap_text(text, max_width), justify="left",
                            background="#ffffff", relief="solid", borderwidth=1,
                            font=("Arial", "11", "normal"))
            label.pack(ipadx=1)

        def leave(event=None):
            nonlocal tooltipwindow
            if tooltipwindow:
                tooltipwindow.destroy()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def update_checkboxes(self, content_type: str, option_type: str = "edit_then_delete") -> None:
        """
        Update checkbox states to ensure content handling options are mutually exclusive.

        Args:
            content_type (str): The type of content being updated ('comments' or 'posts').
            option_type (str): The type of option being selected:
                - "edit_then_delete": Edit content before deleting
                - "only_edit": Only edit without deleting
                - "delete_without_edit": Delete without editing
        """
        if content_type in ["comments", "posts"]:
            if option_type == "edit_then_delete":
                if self.content_vars[content_type].get():
                    self.only_edit_vars[content_type].set(False)
                    self.delete_without_edit_vars[content_type].set(False)
            elif option_type == "only_edit":
                if self.only_edit_vars[content_type].get():
                    self.content_vars[content_type].set(False)
                    self.delete_without_edit_vars[content_type].set(False)
            elif option_type == "delete_without_edit":
                if self.delete_without_edit_vars[content_type].get():
                    self.content_vars[content_type].set(False)
                    self.only_edit_vars[content_type].set(False)

            self.update_entry_states()

    def update_entry_states(self) -> None:
        """
        Update the state of karma threshold entry fields based on checkbox states.
        """
        comment_state = "normal" if (self.content_vars["comments"].get() or
                                     self.only_edit_vars["comments"].get() or
                                     self.delete_without_edit_vars["comments"].get()) else "disabled"

        post_state = "normal" if (self.content_vars["posts"].get() or
                                  self.only_edit_vars["posts"].get() or
                                  self.delete_without_edit_vars["posts"].get()) else "disabled"

        self.comment_threshold.config(state=comment_state)
        self.post_threshold.config(state=post_state)

        self.comment_label.config(fg="#ffffff" if comment_state == "normal" else "#808080")
        self.post_label.config(fg="#ffffff" if post_state == "normal" else "#808080")


    def start_removal(self) -> None:
        """Prepare user preferences and start the content removal process."""
        for content_type, var in self.content_vars.items():
            setattr(self.preferences, f"delete_{content_type}", var.get())

        self.preferences.only_edit_comments = self.only_edit_vars["comments"].get()
        self.preferences.only_edit_posts = self.only_edit_vars["posts"].get()
        self.preferences.delete_without_edit_comments = self.delete_without_edit_vars["comments"].get()
        self.preferences.delete_without_edit_posts = self.delete_without_edit_vars["posts"].get()

        self.preferences.preserve_gilded = self.preserve_vars["gilded"].get()
        self.preferences.preserve_distinguished = self.preserve_vars["distinguished"].get()

        self.preferences.comment_karma_threshold = None if self.comment_threshold.get() == "*" else int(self.comment_threshold.get())
        self.preferences.post_karma_threshold = None if self.post_threshold.get() == "*" else int(self.post_threshold.get())
        self.preferences.dry_run = self.dry_run_var.get()
        self.preferences.advertise_ereddicator = self.advertise_var.get()

        whitelist_text = self.whitelist_entry.get()
        blacklist_text = self.blacklist_entry.get()

        self.preferences.whitelist_subreddits = [s.strip().lower() for s in whitelist_text.split(",") if s.strip() and s != "You can leave this blank."]
        self.preferences.blacklist_subreddits = [s.strip().lower() for s in blacklist_text.split(",") if s.strip() and s != "You can leave this blank."]

        if self.preferences.whitelist_subreddits and self.preferences.blacklist_subreddits:
            messagebox.showerror("Error", "You cannot set both a whitelist and a blacklist. Please choose one or leave both blank.")
            return

        # Get date range
        start_date = self.start_date_entry.get_date() if self.start_date_entry.get() else None
        end_date = self.end_date_entry.get_date() if self.end_date_entry.get() else None

        # Convert to datetime objects if dates are selected
        self.preferences.start_date = datetime.combine(start_date, datetime.min.time()) if start_date else None
        self.preferences.end_date = datetime.combine(end_date, datetime.max.time()) if end_date else None

        # Validate date range
        if self.preferences.start_date and self.preferences.end_date:
            if self.preferences.start_date > self.preferences.end_date:
                messagebox.showerror("Error", "Start date must be before end date.")
                return

        # Get custom replacement text
        custom_text = self.custom_text_entry.get()
        self.preferences.custom_replacement_text = custom_text if custom_text != "You can leave this blank." else None

        # Handle export from Reddit option
        export_dir = self.export_directory_entry.get()
        if export_dir and export_dir != "Optional: Select folder containing Reddit data export":
            self.preferences.reddit_export_directory = export_dir
        else:
            self.preferences.reddit_export_directory = None

        self.master.destroy()
        self.start_removal_callback(self.preferences)
