# -*- coding: utf-8 -*-
"""
gpipdate - GUI for pipdate.

View and update all your outdated packages for each Python installation on your system.
"""
try:
    # noinspection PyUnresolvedReferences
    from tkinter import *
    # noinspection PyUnresolvedReferences
    from tkinter.ttk import *
    from tkinter.filedialog import askopenfilenames
except:
    # noinspection PyUnresolvedReferences
    from Tkinter import *
    # noinspection PyUnresolvedReferences
    from ttk import *
    # noinspection PyUnresolvedReferences,PyPep8Naming
    from tkFileDialog import askopenfilenames
from pipdate import get_pip_paths, list_outdated_packages, batch_update_packages, __version__ as _ver
from threading import Thread
from time import sleep


__version__ = '1.05'
__last_updated__ = "16/05/2017"
__author__ = 'just-another-user'


# noinspection PyAttributeOutsideInit,PyMissingConstructor,PyUnusedLocal
class PipdateGui(Frame):

    def __init__(self, parent, **kwargs):
        Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.parent.title("Pipdate GUI v{}".format(__version__))
        self.available_pips = get_pip_paths()
        self.loading_label = Frame(self.parent)
        if self.available_pips:
            self.init_ui()
        else:
            self.display_loading_label("No pip executables found...")

    # UI, displays and menus

    def init_ui(self):
        """
        First initialization of the ui
        """
        # Once the available executables are known, the rest of the ui can be drawn
        self.create_available_pips_drop_down_menu()

        # Create an "Outdated Packages" listbox.
        self.outdated_packages_listbox = Listbox(self.parent, selectmode='multiple')
        self.outdated_packages_listbox.grid(column=0, row=1, sticky=(W, E), rowspan=3)
        self.update_pip_outdated_listbox()

        # Create selection buttons and the 'quit' button
        buttons_frame = Frame(self.parent)
        buttons_frame.grid(column=1, row=1, sticky=NW)

        Button(buttons_frame, text="Select All Packages", command=self.select_all_packages).pack(expand=1, fill='both')
        Button(buttons_frame, text="Clear Selections", command=self.clear_selections).pack(expand=1, fill='both')
        Button(buttons_frame, text="Update Selected Packages",
               command=self.update_selected_packages).pack(expand=1, fill='both')

        Button(buttons_frame, text="Quit", command=self.master.destroy).pack(expand=1, fill='both')

        # Add a status bar on which messages to the user will be displayed.
        self.status_bar_text = StringVar()
        self.status_bar = Label(self.parent, textvariable=self.status_bar_text, relief=SUNKEN, borderwidth=1)
        self.status_bar.grid(column=0, row=4, sticky=(N, W, E, S), columnspan=2, pady=5)
        self.outdated_packages_listbox.bind("<<ListboxSelect>>", self.update_status_bar)

        self.init_menu()

    def init_menu(self):
        """
        Create a menu bar
        """
        menu = Menu(self.master)

        # Functions which add, find or replace executables
        executables_menu = Menu(menu, tearoff=0)
        executables_menu.add_command(label="Add pip executable(s)", command=self.add_executables)
        executables_menu.add_command(label="Replace all pip executable(s)", command=self.replace_executables)
        executables_menu.add_command(label="Search for pip executables...", command=self.get_executables)
        menu.add_cascade(label="Manage Executables", menu=executables_menu)

        # Create an About button in the menu
        menu.add_command(label="About...", command=self.about_menu)

        self.master.config(menu=menu)

    @staticmethod
    def about_menu():
        """
        Display a popup with relevant details
        """
        win = Toplevel()
        win.title("About pipdate")
        Label(win, text="gpipdate v{}".format(__version__), font=("Fixedsys", 30)).pack()
        Label(win, text="GUI for pipdate v{}".format(_ver), font=("Fixedsys", 15)).pack()
        Label(win, text="by {}".format(__author__), font=("Fixedsys", 11)).pack()
        Label(win, text="Last updated:  {}".format(__last_updated__), font=("Fixedsys", 8)).pack()

    def create_available_pips_drop_down_menu(self):
        self.selected_pip = StringVar(value=self.available_pips[-1])    # Arbitrarily pick the last as default
        self.available_pips_drop_down_list = OptionMenu(self.parent, self.selected_pip,
                                                        self.selected_pip.get(), *self.available_pips)

        # Set a minimum width for the drop down list to avoid getting a small column on short paths like /bin/pip
        max_pip_len = len(max(self.available_pips, key=len))
        max_pip_len = max_pip_len if max_pip_len >= 30 else 30          # 30 is arbitrary
        self.available_pips_drop_down_list.config(width=max_pip_len)

        self.selected_pip.trace("w", self.update_pip_outdated_listbox)  # Bind variable changes to refreshing the list
        self.available_pips_drop_down_list.grid(column=0, row=0, sticky=(W, E))

    def update_status_bar(self, msg=None, *args):
        """
        Wrapper for handling status bar updates, including a 'packages selected' template, 
        to be used when no text is given.
        """
        if msg is None:     # When no msg is given, use the default template
            self.status_bar_text.set("{} package(s) selected".format(
                len(self.outdated_packages_listbox.curselection())))
        else:
            self.status_bar_text.set(str(msg))

    def display_loading_label(self, msg):
        """
        Wrapper for displaying a loading message
        """
        self.loading_label = Frame(self.parent)
        Label(self.loading_label, text=msg, font=("Fixedsys", 12)).pack()
        self.loading_label.grid(column=0, row=1)

    # Executables actions

    def get_executables(self):
        """
        Overwrite the available_pips variable with executables found using the get_pip_paths function
        and re-draw the drop down menu
        """
        self.available_pips = get_pip_paths()
        self.available_pips_drop_down_list.destroy()
        self.create_available_pips_drop_down_menu()

    def add_executables(self, replace=False):
        """
        Add executables to the drop down menu
        """
        pips = askopenfilenames(title="Select the pip executable(s) to be used")
        print("Pip: {}".format(pips))
        if pips:
            if replace:
                self.available_pips = list(pips)
            else:
                self.available_pips.extend(pips)

            # Refresh the available pips drop down menu
            self.available_pips_drop_down_list.destroy()
            self.create_available_pips_drop_down_menu()

    def replace_executables(self):
        """
        Replace executable in drop down menu
        """
        self.add_executables(replace=True)

    # List actions

    def select_all_packages(self):
        self.outdated_packages_listbox.select_set(0, END)

    def clear_selections(self):
        self.outdated_packages_listbox.selection_clear(0, END)

    def update_pip_outdated_listbox(self, *args, **kwargs):
        """ 
        Start a threaded worker to refresh outdated packages
        """
        Thread(target=self.refresh_outdated_).start()

    def refresh_outdated_(self):
        """
        Refresh the outdated packages listbox.
        Should be running in a different thread.
        """
        # noinspection PyShadowingNames
        def list_outdated_():
            """
            Thread worker to fetch outdated packages for the currently selected pip
            """
            outdated_packages = list_outdated_packages(self.selected_pip.get())

        # Let the user know the process is running in the background by animating movement
        outdated_packages = ""
        t = Thread(target=list_outdated_)
        t.start()
        while t.is_alive():
            for c in "/-\\|":   # Spinners are all the craze these days...
                sleep(0.1)
                self.display_loading_label("-{}- Retrieving outdated packages...".format(c))

        # Recreate the listbox and remove the loading message
        self.outdated_packages_listbox.destroy()
        self.outdated_packages_listbox = Listbox(self.parent, selectmode='multiple')
        self.loading_label.destroy()

        if outdated_packages:                                       # If there are outdated packages
            for item in outdated_packages:                          # Populate the listbox with their names
                self.outdated_packages_listbox.insert(END, item)
        else:
            self.display_loading_label("All up-to-date :)")
        self.outdated_packages_listbox.grid(column=0, row=1, sticky=(W, E))

    def update_selected_packages(self):
        def update_selected_packages_(packages):
            """
            Update all selected packages and report results to status bar
            """
            if isinstance(packages, str):
                packages = [packages]
            update_successful = batch_update_packages(self.selected_pip.get(), packages)
            if update_successful:
                msg = "Package(s) updated successfully."
            else:
                msg = "Some packages failed to update."
            self.update_status_bar(msg=msg)
            self.update_pip_outdated_listbox()

        selected_packages = self.outdated_packages_listbox.curselection()
        if selected_packages:
            packages_list = [self.outdated_packages_listbox.get(i) for i in selected_packages]
            # Beautify display of packages names
            if len(selected_packages) == 1:
                packages_names = str(self.outdated_packages_listbox.get(selected_packages[0]))
            elif len(selected_packages) == 2:
                packages_names = " and ".join(packages_list)
            else:
                packages_names = ", ".join(packages_list[:-1] +
                                           ["and {}".format(packages_list[-1])])

            self.update_status_bar(msg="Updating {}".format(packages_names))
            Thread(target=self.update_selected_packages_, args=(packages_list,)).start()
        else:
            self.update_status_bar(msg="No package selected.")


if __name__ == '__main__':
    root = Tk()
    root.resizable(0, 0)
    PipdateGui(root)
    root.mainloop()
