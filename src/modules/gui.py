import tkinter as tk
from tkinter import messagebox
from typing import Dict, Callable
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

        # Adjust window size after creating widgets.
        self.master.update()
        self.master.geometry(f"{self.master.winfo_reqwidth()}x{self.master.winfo_reqheight()}")
        self.master.resizable(False, False)

    def create_widgets(self) -> None:
        """
        Create and arrange the widgets for the credentials input GUI.
        """
        main_frame = tk.Frame(self.master, bg="#2b2b2b")
        main_frame.pack(padx=10, pady=10)

        fields = ["Client ID", "Client Secret", "Username", "Password"]

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

            self.credential_entries[field] = entry

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
            if not value:
                messagebox.showerror("Error", f"{field} cannot be empty")
                return
            credentials[field.lower()] = value

        self.submitted_credentials = credentials
        self.master.quit()

    def get_credentials(self) -> Dict[str, str]:
        """
        Retrieve the credentials entered by the user.

        Returns:
            Dict[str, str]: A dictionary containing the user's credentials with keys
                            'client id', 'client secret', 'username', and 'password'.
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

    def create_widgets(self) -> None:
        main_frame = tk.Frame(self.master, bg='#2b2b2b')
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.content_vars = {}
        self.only_edit_vars = {}

        checkbox_frame = tk.Frame(main_frame, bg="#2b2b2b")
        checkbox_frame.pack(fill="x", pady=10)

        left_column = tk.Frame(checkbox_frame, bg="#2b2b2b")
        left_column.pack(side="left", fill="y", expand=True)
        right_column = tk.Frame(checkbox_frame, bg='#2b2b2b')
        right_column.pack(side="right", fill="y", expand=True)

        # Comments
        self.content_vars["comments"] = tk.BooleanVar(value=True)
        self.only_edit_vars["comments"] = tk.BooleanVar(value=False)
        tk.Checkbutton(left_column, text="Delete comments", variable=self.content_vars["comments"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12),
                    command=lambda: self.update_checkboxes("comments")).pack(anchor="w", pady=5)
        tk.Checkbutton(right_column, text="Only edit comments", variable=self.only_edit_vars["comments"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12),
                    command=lambda: self.update_checkboxes("comments", edit=True)).pack(anchor="w", pady=5)

        # Posts
        self.content_vars["posts"] = tk.BooleanVar(value=True)
        self.only_edit_vars["posts"] = tk.BooleanVar(value=False)
        tk.Checkbutton(left_column, text="Delete posts", variable=self.content_vars["posts"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12),
                    command=lambda: self.update_checkboxes("posts")).pack(anchor="w", pady=5)
        tk.Checkbutton(right_column, text="Only edit posts", variable=self.only_edit_vars["posts"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12),
                    command=lambda: self.update_checkboxes("posts", edit=True)).pack(anchor="w", pady=5)

        # Upvotes and Downvotes
        self.content_vars["upvotes"] = tk.BooleanVar(value=True)
        self.content_vars["downvotes"] = tk.BooleanVar(value=True)
        tk.Checkbutton(left_column, text="Delete upvotes", variable=self.content_vars["upvotes"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12)).pack(anchor="w", pady=5)
        tk.Checkbutton(right_column, text="Delete downvotes", variable=self.content_vars["downvotes"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12)).pack(anchor="w", pady=5)

        # Saved and Hidden
        self.content_vars["saved"] = tk.BooleanVar(value=True)
        self.content_vars["hidden"] = tk.BooleanVar(value=True)
        tk.Checkbutton(left_column, text="Delete saved", variable=self.content_vars["saved"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12)).pack(anchor="w", pady=5)
        tk.Checkbutton(right_column, text="Delete hidden", variable=self.content_vars["hidden"],
                    bg="#2b2b2b", fg="#ffffff", selectcolor="#2b2b2b", activebackground="#2b2b2b",
                    activeforeground="#ffffff", font=("Arial", 12)).pack(anchor="w", pady=5)

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
                                    font=("Arial", 12))
        advertise_cb.pack(side="left", pady=5)

        ad_question_button = tk.Button(advertise_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        ad_question_button.pack(side="left", padx=(5, 10))

        ad_tooltip_text = "Occasionally replaces content with ad instead of random text when editing"
        self.create_tooltip(ad_question_button, ad_tooltip_text)

        # Comment karma threshold with question mark
        karma_frame = tk.Frame(main_frame, bg="#2b2b2b")
        karma_frame.pack(fill="x", pady=10)

        self.comment_label = tk.Label(karma_frame, text="Comment karma threshold:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 12))
        self.comment_label.pack(side="left", padx=(0, 10))
        self.comment_threshold = tk.Entry(karma_frame, bg="#3c3c3c", fg="#ffffff", font=("Arial", 12), width=10, disabledbackground="#3c3c3c", disabledforeground="#ffffff")
        self.comment_threshold.pack(side="left")
        self.comment_threshold.insert(0, "*")

        comment_question_button = tk.Button(karma_frame, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        comment_question_button.pack(side="left", padx=(5, 10))

        comment_tooltip_text = "Use '*' to delete all comments, or enter a number to keep comments with karma greater than or equal to that number"
        self.create_tooltip(comment_question_button, comment_tooltip_text)

        # Post karma threshold with question mark
        karma_frame2 = tk.Frame(main_frame, bg="#2b2b2b")
        karma_frame2.pack(fill="x", pady=10)

        self.post_label = tk.Label(karma_frame2, text="Post karma threshold:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 12))
        self.post_label.pack(side="left", padx=(0, 10))
        self.post_threshold = tk.Entry(karma_frame2, bg="#3c3c3c", fg="#ffffff", font=("Arial", 12), width=10, disabledbackground="#3c3c3c", disabledforeground="#ffffff")
        self.post_threshold.pack(side="left")
        self.post_threshold.insert(0, "*")

        post_question_button = tk.Button(karma_frame2, text="?", font=("Arial", 10), bg="#3c3c3c", fg="#ffffff")
        post_question_button.pack(side="left", padx=(5, 10))

        post_tooltip_text = "Use '*' to delete all posts, or enter a number to keep posts with karma greater than or equal to that number"
        self.create_tooltip(post_question_button, post_tooltip_text)

        # Whitelist Subreddits input
        whitelist_frame = tk.Frame(main_frame, bg="#2b2b2b")
        whitelist_frame.pack(fill="x", pady=10)

        whitelist_label = tk.Label(whitelist_frame, text="Whitelist Subreddits:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 12))
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

        blacklist_label = tk.Label(blacklist_frame, text="Blacklist Subreddits:", bg="#2b2b2b", fg="#ffffff", font=("Arial", 12))
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

        self.start_button = tk.Button(main_frame, text="Start Content Removal", command=self.start_removal,
                                    bg="#ffffff", fg="#000000", font=("Arial", 14))
        self.start_button.pack(pady=(20, 20))

    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """
        Create a tooltip for a widget.

        Args:
            widget (tk.Widget): The widget to attach the tooltip to.
            text (str): The text to display in the tooltip.
        """
        tooltipwindow = None

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
            label = tk.Label(tooltipwindow, text=text, justify="left",
                             background="#ffffff", relief="solid", borderwidth=1,
                             font=("Arial", "11", "normal"))
            label.pack(ipadx=1)

        def leave(event=None):
            nonlocal tooltipwindow
            if tooltipwindow:
                tooltipwindow.destroy()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def update_checkboxes(self, content_type: str, edit: bool = False) -> None:
        """
        Update checkbox states to ensure "Delete" and "Only Edit" are mutually exclusive.

        Args:
            content_type (str): The type of content being updated ('comments' or 'posts').
            edit (bool): Whether the update is triggered by the "Only Edit" checkbox.
        """
        if content_type in ["comments", "posts"]:
            if edit:
                if self.only_edit_vars[content_type].get():
                    self.content_vars[content_type].set(False)
            else:
                if self.content_vars[content_type].get():
                    self.only_edit_vars[content_type].set(False)

        self.update_entry_states()

    def update_entry_states(self) -> None:
        """
        Update the state of karma threshold entry fields based on checkbox states.
        """
        comment_state = "normal" if self.content_vars["comments"].get() or self.only_edit_vars["comments"].get() else "disabled"
        post_state = "normal" if self.content_vars["posts"].get() or self.only_edit_vars["posts"].get() else "disabled"

        self.comment_threshold.config(state=comment_state)
        self.post_threshold.config(state=post_state)

        self.comment_label.config(fg="#ffffff" if comment_state == "normal" else "#808080")
        self.post_label.config(fg="#ffffff" if post_state == "normal" else "#808080")

    def start_removal(self) -> None:
        for content_type, var in self.content_vars.items():
            setattr(self.preferences, f"delete_{content_type}", var.get())

        self.preferences.only_edit_comments = self.only_edit_vars["comments"].get()
        self.preferences.only_edit_posts = self.only_edit_vars["posts"].get()

        self.preferences.comment_karma_threshold = None if self.comment_threshold.get() == "*" else int(self.comment_threshold.get())
        self.preferences.post_karma_threshold = None if self.post_threshold.get() == "*" else int(self.post_threshold.get())
        self.preferences.advertise_ereddicator = self.advertise_var.get()

        whitelist_text = self.whitelist_entry.get()
        blacklist_text = self.blacklist_entry.get()

        self.preferences.whitelist_subreddits = [s.strip() for s in whitelist_text.split(",") if s.strip() and s != "You can leave this blank."]
        self.preferences.blacklist_subreddits = [s.strip() for s in blacklist_text.split(",") if s.strip() and s != "You can leave this blank."]

        if self.preferences.whitelist_subreddits and self.preferences.blacklist_subreddits:
            messagebox.showerror("Error", "You cannot set both a whitelist and a blacklist. Please choose one or leave both blank.")
            return

        self.master.destroy()
        self.start_removal_callback(self.preferences)