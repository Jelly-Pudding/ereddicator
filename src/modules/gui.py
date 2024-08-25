import tkinter as tk
from tkinter import ttk
from modules.user_preferences import UserPreferences

class RedditContentRemoverGUI:
    def __init__(self, master, start_removal_callback):
        self.master = master
        self.start_removal_callback = start_removal_callback
        master.title("Ereddicator")
        master.configure(bg='#2b2b2b')
        master.resizable(False, False)
        
        self.preferences = UserPreferences()
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.master, bg='#2b2b2b')
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.content_vars = {}
        content_types = ["comments", "posts", "saved", "upvotes", "downvotes", "hidden"]
        
        checkbox_frame = tk.Frame(main_frame, bg='#2b2b2b')
        checkbox_frame.pack(fill='x', pady=10)

        left_column = tk.Frame(checkbox_frame, bg='#2b2b2b')
        left_column.pack(side='left', fill='y', expand=True)
        right_column = tk.Frame(checkbox_frame, bg='#2b2b2b')
        right_column.pack(side='right', fill='y', expand=True)

        for i, content_type in enumerate(content_types):
            var = tk.BooleanVar(value=True)
            self.content_vars[content_type] = var
            cb = tk.Checkbutton(left_column if i < 3 else right_column, 
                                text=f"Delete {content_type}", 
                                variable=var, 
                                bg='#2b2b2b', 
                                fg='#ffffff', 
                                selectcolor='#2b2b2b',
                                activebackground='#2b2b2b', 
                                activeforeground='#ffffff',
                                font=('Arial', 12),
                                command=self.update_entry_states)
            cb.pack(anchor='w', pady=5)

        # New checkbox for advertising option with question mark
        self.advertise_var = tk.BooleanVar(value=False)
        advertise_frame = tk.Frame(main_frame, bg='#2b2b2b')
        advertise_frame.pack(fill='x', pady=10)
        
        advertise_cb = tk.Checkbutton(advertise_frame,
                                      text="Advertise Ereddicator", 
                                      variable=self.advertise_var,
                                      bg='#2b2b2b', 
                                      fg='#ffffff', 
                                      selectcolor='#2b2b2b',
                                      activebackground='#2b2b2b', 
                                      activeforeground='#ffffff',
                                      font=('Arial', 12))
        advertise_cb.pack(side='left', pady=5)

        # Question mark button with tooltip
        question_button = tk.Button(advertise_frame, text="?", font=('Arial', 10), bg='#3c3c3c', fg='#ffffff')
        question_button.pack(side='left', padx=(5, 10))
        
        tooltip_text = "Occasionally replaces content with ad instead of random text before deletion"
        self.create_tooltip(question_button, tooltip_text)

        karma_frame = tk.Frame(main_frame, bg='#2b2b2b')
        karma_frame.pack(fill='x', pady=10)

        self.comment_label = tk.Label(karma_frame, text="Comment karma threshold:", bg='#2b2b2b', fg='#ffffff', font=('Arial', 12))
        self.comment_label.pack(side='left', padx=(0,10))
        self.comment_threshold = tk.Entry(karma_frame, bg='#3c3c3c', fg='#ffffff', font=('Arial', 12), width=10, disabledbackground='#3c3c3c', disabledforeground='#ffffff')
        self.comment_threshold.pack(side='left')
        self.comment_threshold.insert(0, "*")

        karma_frame2 = tk.Frame(main_frame, bg='#2b2b2b')
        karma_frame2.pack(fill='x', pady=10)

        self.post_label = tk.Label(karma_frame2, text="Post karma threshold:", bg='#2b2b2b', fg='#ffffff', font=('Arial', 12))
        self.post_label.pack(side='left', padx=(0,10))
        self.post_threshold = tk.Entry(karma_frame2, bg='#3c3c3c', fg='#ffffff', font=('Arial', 12), width=10, disabledbackground='#3c3c3c', disabledforeground='#ffffff')
        self.post_threshold.pack(side='left')
        self.post_threshold.insert(0, "*")

        explanation = "Note: Use '*' to delete all, or enter a number to keep\ncontent with karma greater than or equal to that number."
        tk.Label(main_frame, text=explanation, bg='#2b2b2b', fg='#ffffff', 
                font=('Arial', 12), justify=tk.LEFT, wraplength=360).pack(anchor='w', pady=(10,15))

        self.start_button = tk.Button(main_frame, text="Start Content Removal", command=self.start_removal, 
                bg='#ffffff', fg='#000000', font=('Arial', 14))
        self.start_button.pack(pady=(10,20))

    def create_tooltip(self, widget, text):
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
            label = tk.Label(tooltipwindow, text=text, justify='left',
                             background="#ffffff", relief='solid', borderwidth=1,
                             font=("Arial", "11", "normal"))
            label.pack(ipadx=1)

        def leave(event=None):
            nonlocal tooltipwindow
            if tooltipwindow:
                tooltipwindow.destroy()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def update_entry_states(self):
        comment_state = 'normal' if self.content_vars['comments'].get() else 'disabled'
        post_state = 'normal' if self.content_vars['posts'].get() else 'disabled'
        
        self.comment_threshold.config(state=comment_state)
        self.post_threshold.config(state=post_state)
        
        self.comment_label.config(fg='#ffffff' if comment_state == 'normal' else '#808080')
        self.post_label.config(fg='#ffffff' if post_state == 'normal' else '#808080')

    def start_removal(self):
        for content_type, var in self.content_vars.items():
            setattr(self.preferences, f"delete_{content_type}", var.get())

        self.preferences.comment_karma_threshold = None if self.comment_threshold.get() == "*" else int(self.comment_threshold.get())
        self.preferences.post_karma_threshold = None if self.post_threshold.get() == "*" else int(self.post_threshold.get())
        self.preferences.advertise_ereddicator = self.advertise_var.get()

        self.master.destroy()
        self.start_removal_callback(self.preferences)