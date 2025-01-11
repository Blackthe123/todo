import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
from tkcalendar import Calendar
from tkinter import *
from datetime import datetime, timedelta
import re

class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List")

        # Add sort state tracking
        self.task_sort_reverse = True
        self.date_sort_reverse = False

        self.open_states = {}

        # Configure grid weights for resizing
        self.root.grid_rowconfigure(1, weight=1)  # Make task list expand
        self.root.grid_columnconfigure(0, weight=1)  # Make columns expand
        self.root.grid_columnconfigure(1, weight=1)

        #Closing kwyboard shortcut
        self.root.bind('<Control-w>', lambda e: self.on_close())
        self.root.bind('<Down>', self.handle_global_down)

        #Auto detect day mappings
        self.day_mappings = {
            'today': 0,
            'tomorrow': 1,
            'tom': 1,
            'mon': 'Monday',
            'tue': 'Tuesday',
            'wed': 'Wednesday',
            'thu': 'Thursday',
            'fri': 'Friday',
            'sat': 'Saturday',
            'sun': 'Sunday',
            'monday': 'Monday',
            'tuesday': 'Tuesday',
            'wednesday': 'Wednesday',
            'thursday': 'Thursday',
            'friday': 'Friday',
            'saturday': 'Saturday',
            'sunday': 'Sunday'
        }

        #Tasks main list
        self.tasks = []

        #Container
        self.task_frame = tk.Frame(root)
        self.task_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
        self.task_frame.grid_columnconfigure(0, weight=1)
        
        #Task input field
        self.task_entry = tk.Entry(self.task_frame)
        self.task_entry.grid(row=0, column=0, padx=5, sticky='ew')
        self.task_entry.bind("<Return>", lambda event: self.add_task())
        self.task_entry.bind("<Down>", self.handle_entry_down)
            

        #Date selected shown to user field
        self.date_var = tk.StringVar()
        self.date_display = tk.Entry(self.task_frame, textvariable=self.date_var, width=10, state='readonly')
        self.date_display.grid(row=0, column=1, padx=5)

        #Schedule button
        self.schedule_button = tk.Button(self.task_frame, text="Schedule", command=self.schedule)
        self.schedule_button.grid(row=0, column=2, padx=5)

        #Add task button (redundant with Enter key binding)
        self.add_button = tk.Button(self.task_frame, text="Add Task", command=self.add_task)
        self.add_button.grid(row=0, column=3, padx=5)

        # Add subtask button
        self.add_subtask_button = tk.Button(self.task_frame, text="Add Subtask", command=self.add_subtask)
        self.add_subtask_button.grid(row=0, column=4, padx=5)

        #Main display area - treeview table (can be changed to heirarchical tree)
        self.tree = ttk.Treeview(root, columns=('Task', 'Date', 'Day'), show='tree headings', height=15)
        self.tree.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky='nsew')
        
        #Colors for task display
        self.tree.tag_configure('red', background='#ffcccc')
        self.tree.tag_configure('yellow', background='#ffffcc')
        self.tree.tag_configure('green', background='#ccffcc')
        self.tree.tag_configure('grey', background='#ccccff')
        self.tree.tag_configure('important', background='#ffcc00')
        self.tree.tag_configure('done', foreground='gray', background='white')
        self.tree.tag_configure('subtask', font=('TkDefaultFont', 9, 'italic'))
        
        #Columns
        self.tree.heading('#0', text='#')  # Number column
        self.tree.heading('Task', text='Task', command=self.toggle_task_sort)
        self.tree.heading('Date', text='Date', command=self.sort_by_date)
        self.tree.heading('Day', text='Day')
        self.tree.column('#0', anchor=W, width=70, stretch=False)  # Number column
        self.tree.column('Task', anchor=W, width=250)
        self.tree.column('Date', width=100, anchor=W)
        self.tree.column('Day', width=100, anchor=W)
        
        # Configure style for the Treeview
        style = ttk.Style()
        style.configure('Treeview', rowheight=25)  # Optional: Adjust row height
        
        #Link scrollbar to Treeview
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.scrollbar.grid(row=1, column=2, sticky="ns")

        #Update Treeview scroll region
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        button_frame = tk.Frame(root)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')
        button_frame.grid_columnconfigure(1, weight=1)  # Space between left and right buttons

        #Bind keyboard events
        self.tree.bind('<Up>', lambda e: self.handle_arrow_key(e, 'up'))
        self.tree.bind('<Down>', lambda e: self.handle_arrow_key(e, 'down'))
        self.tree.bind('<Shift-Up>', lambda e: self.handle_shift_arrow(e, 'up'))
        self.tree.bind('<Shift-Down>', lambda e: self.handle_shift_arrow(e, 'down'))
        self.tree.bind('<BackSpace>', lambda e: self.delete_task())
        self.tree.bind('<Return>', lambda e: self.mark_done())
        self.tree.bind('<Control-a>', self.select_all)

        # Store the last selected item for shift-selection
        self.last_selected = None

        #Mark done button (redundant with Enter key binding)
        self.mark_done_button = tk.Button(button_frame, text="Mark as Done", command=self.mark_done)
        self.mark_done_button.grid(row=0, column=0, padx=10, sticky="w")
       
        #Delete task button (redundant with Backspace key binding)
        self.delete_button = tk.Button(button_frame, text="Delete Task", command=self.delete_task)
        self.delete_button.grid(row=0, column=3, padx=10, sticky="e")

        self.imp_button = tk.Button(button_frame, text="Important", command=self.mark_important)
        self.imp_button.grid(row=0, column=1, padx=10, sticky="w")

        self.no_save = tk.Button(button_frame, text="Unsave", command=self.unsave)
        self.no_save.grid(row=0, column=4, padx=10, sticky="e")

        self.unmarkbtn = tk.Button(button_frame, text="Unmark", command=self.unmark)
        self.unmarkbtn.grid(row=0, column=2, padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_tasks()
    
    def unmark(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            item_idx = self.tree.index(item)        
            # Check if the selected item is a subtask
            parent_item = self.tree.parent(item)
            if parent_item:
                # It's a subtask
                parent_idx = self.tree.index(parent_item)
                subtask_idx = self.tree.get_children(parent_item).index(item)
                subtask = self.tasks[parent_idx]["subtasks"][subtask_idx]
                if subtask.get("done", False):
                    subtask["done"] = False
                    self.tree.item(item, tags=())
            else:
                # It's a main task
                if self.tasks[item_idx].get("done", False):
                    self.tasks[item_idx]["done"] = False
                    self.tree.item(item, tags=())

                # Unmark subtasks
                if "subtasks" in self.tasks[item_idx]:
                    for subtask in self.tasks[item_idx]["subtasks"]:
                        if subtask.get("done", False):
                            subtask["done"] = False
                            subtask_item = self.tree.get_children(item)[self.tasks[item_idx]["subtasks"].index(subtask)]
                            self.tree.item(subtask_item, tags=())

        self.sort_tasks()
        
    def add_subtask(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a parent task first.")
            return

        task = self.task_entry.get().strip()
        date = self.date_var.get()
        if not task:
            messagebox.showwarning("Input Error", "Please enter a subtask.")
            return
        if task:
            auto_date = self.get_date_from_text(task)
            if auto_date and not date:
                date = auto_date

        parent_item = selected[0]
        parent_idx = self.get_task_index(parent_item)
        if parent_idx is not None:
            # Create subtask info
            subtask_info = {
                "task": task,
                "done": False,
                "date": date,
                "is_subtask": True,
                "parent_id": parent_item,
                "important": False
            }

            # Add subtask to parent's subtasks list
            if "subtasks" not in self.tasks[parent_idx]:
                self.tasks[parent_idx]["subtasks"] = []
            self.tasks[parent_idx]["subtasks"].append(subtask_info)

            # Add subtask to treeview
            subtask_item = self.tree.insert(parent_item, 'end', text=f"{self.tree.index(parent_item)+1}.{len(self.tree.get_children(parent_item))+1}", values=(task, subtask_info["date"], 
                                          self.get_day_from_date(subtask_info["date"])),
                                          tags=('subtask',))
            self.tree.item(parent_item, open=True)  # Expand parent task
            self.task_entry.delete(0, tk.END)
            self.date_var.set("")
        self.tasks[parent_idx]["subtasks"].sort(key=lambda x: datetime.strptime(x['date'], '%d/%m/%Y') if x.get('date') else datetime.max)
        self.refresh_treeview()
    
    def sort_subtasks(self):
        pass


    
    def check_open_state(self, item):
        # Get the open state of the item
        is_open = self.tree.item(item, "open")
        print(f"Item '{self.tree.item(item, 'text')}' is {'open' if is_open else 'collapsed'}")
    
    def get_task_index(self, item):
        # Get the task index in self.tasks list based on treeview item
        parent = self.tree.parent(item)
        if not parent:  # This is a main task
            return self.tree.index(item)
        return None  # This is a subtask

    def toggle_task_sort(self):
        # Simply reverse the current tasks list and refresh display
        self.tasks.reverse()
        self.sort_tasks(click=1)
    
    def sort_by_date(self):
        self.date_sort_reverse = not self.date_sort_reverse
        # Sort by date
        self.tasks.sort(key=lambda x: datetime.strptime(x['date'], '%d/%m/%Y') if x.get('date') else datetime.max,
                       reverse=self.date_sort_reverse)
        self.refresh_treeview()
    
    def refresh_treeview(self):
        user_open_list = []
        for i in self.tree.get_children():
            if self.tree.item(i, "open"):
                user_open_list.append(self.tree.index(i))        
        print(user_open_list)
        # Clear and repopulate the treeview
        for item in self.tree.get_children():
            self.open_states[item] = self.tree.item(item, "open")
            self.tree.delete(item)
            
        for i, task in enumerate(self.tasks, 1):
            task_text = task["task"]
            date = task.get("date", "")
            day = self.get_day_from_date(date) if date else ""
            
            # Insert main task with number
            item = self.tree.insert('', 'end', text=str(i), values=(task_text, date, day))
            
            # Apply color coding
            if task["done"]:
                self.tree.item(item, tags=('done',))
            elif task.get("important", False):
                self.tree.item(item, tags=('important',))
            else:
                color_tag = self.get_task_color(date)
                if color_tag:
                    self.tree.item(item, tags=(color_tag,))

            # Add subtasks if they exist
            if "subtasks" in task:
                for j, subtask in enumerate(task["subtasks"], 1):
                    subtask_item = self.tree.insert(item, 'end',
                                                  text=f"{i}.{j}",  # Numbered subtasks
                                                  values=(subtask["task"], 
                                                         subtask.get("date", ""),
                                                         self.get_day_from_date(subtask.get("date", ""))),
                                                  tags=('subtask',))
                    if subtask["done"]:
                        self.tree.item(subtask_item, tags=('done', 'subtask'))
                    if subtask.get("important", False):
                        self.tree.item(subtask_item, tags=('important', 'subtask'))
        
        for m in self.tree.get_children():
            if self.tree.index(m) in user_open_list:
                self.tree.item(m, open=True)
            
                
    
    def handle_entry_down(self, event):
        first = self.tree.get_children()[0] if self.tree.get_children() else None
        if first:
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.tree.see(first)
            self.tree.focus_set()
        return 'break'

    def handle_global_down(self, event):
        if not self.tree.focus():
            first = self.tree.get_children()[0] if self.tree.get_children() else None
            if first:
                self.tree.selection_set(first)
                self.tree.focus(first)
                self.tree.see(first)
                self.tree.focus_set()
        return 'break'
    

    def handle_arrow_key(self, event, direction):
        # Prevent default behavior
        event.widget.stop_propagation = True
        
        selection = self.tree.selection()
        if not selection:
            # If nothing is selected, select the first item
            first = self.tree.get_children()[0] if self.tree.get_children() else None
            if first:
                self.tree.selection_set(first)
                self.tree.focus(first)
                self.last_selected = first
            return 'break'

        current = selection[-1]  # Get the last selected item
        
        # Get all visible items (both main tasks and expanded subtasks)
        visible_items = self.get_visible_items()
        if not visible_items:
            return 'break'

        try:
            current_idx = visible_items.index(current)
        except ValueError:
            return 'break'

        # Calculate new index
        if direction == 'up' and current_idx > 0:
            new_idx = current_idx - 1
        elif direction == 'down' and current_idx < len(visible_items) - 1:
            new_idx = current_idx + 1
        else:
            return 'break'

        # Clear current selection and select new item
        self.tree.selection_remove(*selection)
        self.tree.selection_set(visible_items[new_idx])
        self.tree.focus(visible_items[new_idx])
        self.tree.see(visible_items[new_idx])
        self.last_selected = visible_items[new_idx]
        
        return 'break'

    def handle_shift_arrow(self, event, direction):
        # Prevent default behavior
        event.widget.stop_propagation = True
        
        visible_items = self.get_visible_items()
        if not visible_items:
            return 'break'

        # If no last_selected, treat as regular arrow key
        if not self.last_selected or self.last_selected not in visible_items:
            self.last_selected = visible_items[0]
            self.tree.selection_set(self.last_selected)
            return 'break'

        current_selection = self.tree.selection()
        if not current_selection:
            current_selection = (self.last_selected,)

        try:
            current_idx = visible_items.index(self.last_selected)
        except ValueError:
            return 'break'

        # Calculate new index
        if direction == 'up' and current_idx > 0:
            new_idx = current_idx - 1
        elif direction == 'down' and current_idx < len(visible_items) - 1:
            new_idx = current_idx + 1
        else:
            return 'break'

        # If the new item is already selected, remove selection from the last item
        new_item = visible_items[new_idx]
        if new_item in current_selection and len(current_selection) > 1:
            self.tree.selection_remove(self.last_selected)
        else:
            # Add new item to selection
            self.tree.selection_add(new_item)
        
        self.last_selected = new_item
        self.tree.focus(new_item)
        self.tree.see(new_item)
        
        return 'break'

    def get_visible_items(self):
        """Get all visible items in the treeview (both main tasks and expanded subtasks)"""
        def get_visible_children(item):
            children = self.tree.get_children(item)
            result = []
            for child in children:
                result.append(child)
                if self.tree.item(child, 'open'):  # If the item is expanded
                    result.extend(get_visible_children(child))
            return result

        visible_items = []
        root_items = self.tree.get_children()
        for item in root_items:
            visible_items.append(item)
            if self.tree.item(item, 'open'):  # If the item is expanded
                visible_items.extend(get_visible_children(item))
        return visible_items

    def select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        self.tree.focus(self.tree.get_children()[0])
        return 'break'  # Prevents default behavior
    
    def get_date_from_text(self, text):
        text_lower = text.lower()
        
        # Look for day names or keywords in the text
        for key, value in self.day_mappings.items():
            if key+" " in text_lower or " "+key in text_lower:
                today = datetime.now()
                
                if key == 'today':
                    return today.strftime('%d/%m/%Y')
                elif key == 'tomorrow' or key == 'tom':
                    tomorrow = today + timedelta(days=1)
                    return tomorrow.strftime('%d/%m/%Y')
                else:
                    # Find the next occurrence of the specified day
                    target_day = value
                    days_ahead = self.get_days_until(target_day)
                    target_date = today + timedelta(days=days_ahead)
                    return target_date.strftime('%d/%m/%Y')
        return None

    def get_days_until(self, target_day):
        today = datetime.now()
        current_day = today.strftime('%A')
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        current_index = days.index(current_day)
        target_index = days.index(target_day)
        
        if target_index <= current_index:
            # Target day is next week
            days_ahead = 7 - (current_index - target_index)
        else:
            # Target day is this week
            days_ahead = target_index - current_index
        return days_ahead

    def get_day_from_date(self, date_str):
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            return date_obj.strftime('%A')
        except:
            return ""
    
    def get_task_color(self, date_str):
        if not date_str:
            return 'grey'
            
        try:
            task_date = datetime.strptime(date_str, '%d/%m/%Y')
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_until = (task_date - today).days

            if days_until < 0:  # Past due
                return 'red'
            elif days_until == 0:  # Due today
                return 'red'
            elif days_until <= 3:  # Due within 3 days
                return 'yellow'
            else:  # Due later
                return 'green'
        except ValueError:
            return None

    def sort_tasks(self, click=0):
        if click == 1:
            self.task_sort_reverse = not self.task_sort_reverse
        def get_task_sort_key(task):
            # First sort by completion status (done tasks at bottom)
            done_priority = 0
            if task.get('important', False):
                done_priority = -1
            else:
                if task.get('done', False):
                    done_priority = 1
            
            # Then sort by date
            if not task.get('date'):
                date_priority = datetime.max
            else:
                try:
                    date_priority = datetime.strptime(task['date'], '%d/%m/%Y')
                except ValueError:
                    date_priority = datetime.max
                    
            return (done_priority, date_priority)
        
        if click == 0 and self.task_sort_reverse:
            self.tasks.sort(key=get_task_sort_key)
        elif click == 0 and not self.task_sort_reverse:
            self.tasks.sort(key=get_task_sort_key, reverse=True)
        elif(self.task_sort_reverse) and click == 1:
            self.tasks.sort(key=get_task_sort_key)
        elif not self.task_sort_reverse and click == 1:
            self.tasks.sort(key=get_task_sort_key, reverse=True)
        
        
        # Refresh the treeview
        self.refresh_treeview()

    def add_task(self):
        task = self.task_entry.get().strip()
        date = self.date_var.get()
        
        if task:
            # Check if task text contains a date reference
            auto_date = self.get_date_from_text(task)
            if auto_date and not date:  # Use auto-detected date if no date was manually selected
                date = auto_date
            
            task_info = {
                "task": task,
                "done": False,
                "date": date
            }
            self.tasks.append(task_info)
            
            # Sort tasks and refresh display
            self.sort_tasks()
            
            self.task_entry.delete(0, tk.END)
            self.date_var.set("")  # Clear the date after adding task
        else:
            messagebox.showwarning("Input Error", "Please enter a task.")

    def schedule(self):
        date_window = Toplevel(self.root)
        date_window.title("Schedule Task")
        date_window.geometry("300x350")
        date_window.grab_set()

        cal = Calendar(date_window, selectmode="day", date_pattern="dd/mm/yyyy")
        cal.pack(pady=20)

        def grab_date():
            self.date_var.set(cal.get_date())
            date_window.destroy()

        btn_frame = Frame(date_window)
        btn_frame.pack(pady=10)

        submit_btn = Button(btn_frame, text="Submit", command=grab_date)
        submit_btn.pack(side=LEFT, padx=5)

    def mark_done(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            parent = self.tree.parent(item)
            if not parent:  # Main task
                item_idx = self.tree.index(item)
                self.tasks[item_idx]["done"] = True
                self.tasks[item_idx]["important"] = False
                # Mark all subtasks as done
                if "subtasks" in self.tasks[item_idx]:
                    for subtask in self.tasks[item_idx]["subtasks"]:
                        subtask["done"] = True
            else:  # Subtask
                parent_idx = self.tree.index(parent)
                subtask_idx = self.tree.index(item)
                self.tasks[parent_idx]["subtasks"][subtask_idx]["done"] = True
                if self.tasks[parent_idx]["subtasks"][subtask_idx].get("important", False):
                    self.tasks[parent_idx]["subtasks"][subtask_idx]["important"] = False
        self.sort_tasks()

    def mark_important(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            item_idx = self.tree.index(item)
            parent_item = self.tree.parent(item)

            if parent_item:  # If it's a subtask
                parent_idx = self.tree.index(parent_item)
                subtask_idx = self.tree.get_children(parent_item).index(item)
                subtask = self.tasks[parent_idx]["subtasks"][subtask_idx]

                # Toggle importance
                if subtask.get("important", False):
                    subtask["important"] = False
                else:
                    subtask["important"] = True
                    self.tree.tag_configure('important', background='#ffcc00')  # Highlight important tasks
                    self.tree.item(item, tags=('important',))

                # Sort subtasks by importance and date
                self.tasks[parent_idx]["subtasks"].sort(
                    key=lambda x: (
                        not x.get("important", False),  # Important tasks come first
                        datetime.strptime(x["date"], '%d/%m/%Y') if x.get("date") else datetime.max
                    )
                )

            else:  # If it's a main task
                task = self.tasks[item_idx]

                # Toggle importance
                if task.get("important", False):
                    task["important"] = False
                else:
                    task["important"] = True
                    self.tree.tag_configure('important', background='#ffcc00')  # Highlight important tasks
                    self.tree.item(item, tags=('important',))

        self.sort_tasks()  # Sort and refresh the task tree


    def delete_task(self):
        selected_items = self.tree.selection()
        for item in reversed(selected_items):
            parent = self.tree.parent(item)
            if not parent:  # Main task
                item_idx = self.tree.index(item)
                del self.tasks[item_idx]
            else:  # Subtask
                parent_idx = self.tree.index(parent)
                subtask_idx = self.tree.index(item)
                del self.tasks[parent_idx]["subtasks"][subtask_idx]
            self.tree.delete(item)
        self.sort_tasks()
    
    #Auto save tasks
    def save_tasks(self):
        try:
            with open("tasks.json", "w") as file:
                json.dump(self.tasks, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tasks: {e}")

    #Auto load tasks
    def load_tasks(self):
        try:
            with open("tasks.json", "r") as file:
                self.tasks = json.load(file)
            self.sort_tasks()
        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {e}")
    
    #Save and close
    def on_close(self):
        self.save_tasks()
        self.root.destroy()
    
    def unsave(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)
    root.mainloop()