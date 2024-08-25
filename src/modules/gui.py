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

    def create_widgets(self) -> None:
        """
        Create and arrange the widgets for the main application GUI.
        """
        main_frame = tk.Frame(self.master, bg='#2b2b2b')
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.content_vars = {}
        content_types = ["comments", "posts", "saved", "upvotes", "downvotes", "hidden"]

        checkbox_frame = tk.Frame(main_frame, bg="#2b2b2b")
        checkbox_frame.pack(fill="x", pady=10)

        left_column = tk.Frame(checkbox_frame, bg="#2b2b2b")
        left_column.pack(side="left", fill="y", expand=True)
        right_column = tk.Frame(checkbox_frame, bg='#2b2b2b')
        right_column.pack(side="right", fill="y", expand=True)

        for i, content_type in enumerate(content_types):
            var = tk.BooleanVar(value=True)
            self.content_vars[content_type] = var
            cb = tk.Checkbutton(left_column if i < 3 else right_column,
                                text=f"Delete {content_type}",
                                variable=var,
                                bg="#2b2b2b",
                                fg="#ffffff",
                                selectcolor="#2b2b2b",
                                activebackground="#2b2b2b",
                                activeforeground="#ffffff",
                                font=("Arial", 12),
                                command=self.update_entry_states)
            cb.pack(anchor="w", pady=5)

        # Advertising option with question mark.
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

        ad_tooltip_text = "Occasionally replaces content with ad instead of random text before deletion"
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

    def update_entry_states(self) -> None:
        """
        Update the state of karma threshold entry fields based on checkbox states.
        """
        comment_state = "normal" if self.content_vars["comments"].get() else "disabled"
        post_state = "normal" if self.content_vars["posts"].get() else "disabled"

        self.comment_threshold.config(state=comment_state)
        self.post_threshold.config(state=post_state)

        self.comment_label.config(fg="#ffffff" if comment_state == "normal" else "#808080")
        self.post_label.config(fg="#ffffff" if post_state == "normal" else "#808080")

    def start_removal(self) -> None:
        """
        Prepare user preferences and start the content removal process.
        """
        for content_type, var in self.content_vars.items():
            setattr(self.preferences, f"delete_{content_type}", var.get())

        self.preferences.comment_karma_threshold = None if self.comment_threshold.get() == "*" else int(self.comment_threshold.get())
        self.preferences.post_karma_threshold = None if self.post_threshold.get() == "*" else int(self.post_threshold.get())
        self.preferences.advertise_ereddicator = self.advertise_var.get()

        self.master.destroy()
        self.start_removal_callback(self.preferences)
