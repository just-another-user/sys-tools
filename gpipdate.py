# -*- coding: utf-8 -*-
"""
gpipdate - Graphical Pipdate.

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


__version__ = '1.01'
__last_updated__ = "12/05/2017"
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

    def refresh_outdated(self):
        """
        Refresh the outdated packages listbox.
        Should be running in a different thread.
        """
        self.display_loading_label("Retrieving outdated packages...")

        outdated_packages = list_outdated_packages(self.selected_pip.get())
        self.outdated_packages_listbox.destroy()
        self.outdated_packages_listbox = Listbox(self.parent, selectmode='multiple')
        self.loading_label.destroy()
        if outdated_packages:
            for item in outdated_packages:
                self.outdated_packages_listbox.insert(END, item)
        else:
            self.display_loading_label("All up-to-date :)")
        self.outdated_packages_listbox.grid(column=0, row=1, sticky=(W, E))

    def display_loading_label(self, msg):
        self.loading_label = Frame(self.parent)
        Label(self.loading_label, text=msg, font=("Fixedsys", 12)).pack()
        self.loading_label.grid(column=0, row=1)

    def get_executables(self):
        self.available_pips = get_pip_paths()
        self.available_pips_drop_down_list.destroy()
        self.create_available_pips_drop_down_menu()

    def create_available_pips_drop_down_menu(self):
        # Add "Available Pips" drop down list.
        self.selected_pip = StringVar(value=self.available_pips[-1])
        self.available_pips_drop_down_list = OptionMenu(self.parent, self.selected_pip,
                                                        self.selected_pip.get(), *self.available_pips)
        max_pip_len = len(max(self.available_pips, key=len))
        max_pip_len = max_pip_len if max_pip_len >= 30 else 30
        self.available_pips_drop_down_list.config(width=max_pip_len)
        self.selected_pip.trace("w", self.update_pip_outdated_listbox)
        self.available_pips_drop_down_list.grid(column=0, row=0, sticky=(W, E))

    def init_ui(self):
        self.create_available_pips_drop_down_menu()

        # Add "Outdated Packages Listbox for Chosen Pip" listbox.
        self.outdated_packages_listbox = Listbox(self.parent, selectmode='multiple')
        self.outdated_packages_listbox.grid(column=0, row=1, sticky=(W, E), rowspan=3)
        self.update_pip_outdated_listbox()

        # Add buttons
        buttons_frame = Frame(self.parent)
        buttons_frame.grid(column=1, row=1, sticky=NW)

        Button(buttons_frame, text="Select All Packages", command=self.select_all_packages).pack(expand=1, fill='both')
        Button(buttons_frame, text="Clear All Selections", command=self.clear_selections).pack(expand=1, fill='both')
        Button(buttons_frame, text="Update Selected Packages",
               command=self.update_selected_packages).pack(expand=1, fill='both')

        Button(buttons_frame, text="Quit", command=self.master.destroy).pack(expand=1, fill='both')

        # Add 'message board' on which messages to the user will be displayed.
        self.message_board_text = StringVar()
        self.message_board = Label(self.parent, textvariable=self.message_board_text, relief=SUNKEN, borderwidth=1)
        self.message_board.grid(column=0, row=4, sticky=(N, W, E, S), columnspan=2, pady=5)
        self.outdated_packages_listbox.bind("<<ListboxSelect>>", self.update_message_board)

        self.init_menu()

    def init_menu(self):
        menu = Menu(self.master)

        executables_menu = Menu(menu, tearoff=0)
        executables_menu.add_command(label="Add pip executable(s)", command=self.add_executables)
        executables_menu.add_command(label="Replace all pip executable(s)", command=self.replace_executables)
        executables_menu.add_command(label="Search for pip executables...", command=self.get_executables)
        menu.add_cascade(label="Manage Executables", menu=executables_menu)
        menu.add_command(label="About...", command=self.about_menu)

        self.master.config(menu=menu)

    def replace_executables(self):
        self.add_executables(replace=True)

    def add_executables(self, replace=False):
        pips = askopenfilenames(title="Choose the pip executable(s) to be used")
        print("Pip: {}".format(pips))
        if pips:
            if replace:
                self.available_pips = list(pips)
            else:
                self.available_pips.extend(pips)
            self.available_pips_drop_down_list.destroy()
            self.create_available_pips_drop_down_menu()

    @staticmethod
    def about_menu():
        win = Toplevel()
        win.title("About pipdate")
        Label(win, text="gpipdate v{}".format(__version__), font=("Fixedsys", 30)).pack()
        Label(win, text="GUI for pipdate v{}".format(_ver), font=("Fixedsys", 15)).pack()
        Label(win, text="by {}".format(__author__), font=("Fixedsys", 15)).pack()
        Label(win, text="Last updated:  {}".format(__last_updated__), font=("Fixedsys", 15)).pack()

    def update_message_board(self, msg=None, *args):
        if msg is None:
            self.message_board_text.set("{} package(s) selected".format(
                len(self.outdated_packages_listbox.curselection())))
        else:
            self.message_board_text.set(str(msg))

    def select_all_packages(self):
        self.outdated_packages_listbox.select_set(0, END)
        self.update_message_board()

    def clear_selections(self):
        self.outdated_packages_listbox.selection_clear(0, END)
        self.update_message_board()

    def update_pip_outdated_listbox(self, *args, **kwargs):
        Thread(target=self.refresh_outdated).start()

    def update_selected_packages(self):
        selected_packages = self.outdated_packages_listbox.curselection()
        if selected_packages:
            selected_packages_printable_format = [self.outdated_packages_listbox.get(i) for i in selected_packages]
            # Beautify display of packages names
            if len(selected_packages) == 1:
                packages_names = str(self.outdated_packages_listbox.get(selected_packages[0]))
            elif len(selected_packages) == 2:
                packages_names = " and ".join(selected_packages_printable_format)
            else:
                packages_names = ", ".join(selected_packages_printable_format[:-1] +
                                           ["and {}".format(selected_packages_printable_format[-1])])

            self.update_message_board(msg="Updating {}".format(packages_names))
            t = Thread(target=self.update_selected_packages_, args=selected_packages_printable_format)
            t.start()
        else:
            self.update_message_board(msg="No package selected.")

    def update_selected_packages_(self, packages):
            if not isinstance(packages, list):
                packages = [packages]
            update_successful = batch_update_packages(self.selected_pip.get(), packages)
            if update_successful:
                msg = "Package(s) updated successfully."
            else:
                msg = "Some packages failed to update."
            self.update_message_board(msg=msg)
            self.update_pip_outdated_listbox()


def main():
    root = Tk()
    root.resizable(0, 0)
    PipdateGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()
