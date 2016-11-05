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
except:
    from Tkinter import *
    # noinspection PyUnresolvedReferences
    from ttk import *
from pipdate import *


__version__ = '0.1b'
__last_updated__ = "05/11/2016"
__author__ = 'just-another-user'


# noinspection PyAttributeOutsideInit,PyMissingConstructor,PyUnusedLocal
class PipdateGui(Frame):

    def __init__(self, parent, **kw):
        Frame.__init__(self, parent)

        self.parent = parent

        self.message_board = Label(self.parent)

        self.init_ui()

    def update_message_board(self, event=None, msg=None):
        if msg is None:
            self.message_board.configure(text="{} package(s) selected".format(
                len(self.outdated_packages_listbox.curselection())))
        else:
            self.message_board.configure(text=str(msg))

    def init_ui(self):
        self.parent.title("Pipdate GUI v{}".format(__version__))

        # Setup main frame.
        mainframe = Frame(self.parent)
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=2)

        # Add "Available Pips" drop down list.
        self.available_pips = get_pip_paths()
        if not self.available_pips:
            return False    # No pips found in the system. Nothing to do...     # TODO Change this...
        self.selected_pip = StringVar(value=self.available_pips[-1])
        self.available_pips_drop_down_list = OptionMenu(self.parent, self.selected_pip,
                                                        self.selected_pip.get(), *self.available_pips)
        self.selected_pip.trace("w", self.update_pip_outdated_listbox)
        self.available_pips_drop_down_list.grid(column=0, row=0, sticky=(W, E))

        # Add "Outdated Packages Listbox for Chosen Pip" listbox.
        self.outdated_packages_listbox = Listbox(self.parent, selectmode='multiple')
        for item in list_outdated_packages(self.selected_pip.get()):
            self.outdated_packages_listbox.insert(END, item)
        self.outdated_packages_listbox.grid(column=0, row=1, sticky=(W, E))

        # Add buttons
        select_all_packages_button = Button(self.parent, text="Select All Packages",
                                            command=self.select_all_packages)
        select_all_packages_button.grid(column=1, row=1, sticky=(N, W))
        clear_selections_button = Button(self.parent, text="Clear All Selections",
                                         command=self.clear_selections)
        clear_selections_button.grid(column=1, row=1, sticky=W)
        updated_selected_button = Button(self.parent, text="Update Selected Packages",
                                         command=self.update_selected_packages)
        updated_selected_button.grid(column=1, row=1, sticky=S)

        self.message_board.grid(column=0, row=2, sticky=(N, W))

        self.outdated_packages_listbox.bind("<<ListboxSelect>>", self.update_message_board)

        # for child in mainframe.winfo_children():
        #     child.grid_configure(padx=5, pady=5)

    def notify(self, msg=None):
        if msg is None:
            msg = "Notification alert"
        self.update_message_board(msg=str(msg))

    def select_all_packages(self):
        self.outdated_packages_listbox.select_set(0, END)
        self.update_message_board()

    def clear_selections(self):
        self.outdated_packages_listbox.selection_clear(0, END)
        self.update_message_board()
        # self.notify(msg="Chosen pip is {}".format(self.available_pips_drop_down_list.selection_get()))

    def update_pip_outdated_listbox(self, *args):
        self.outdated_packages_listbox.destroy()
        self.outdated_packages_listbox = Listbox(self.parent, selectmode='multiple')
        for item in list_outdated_packages(self.selected_pip.get()):
            self.outdated_packages_listbox.insert(END, item)
        self.outdated_packages_listbox.grid(column=0, row=1, sticky=(W, E))

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
            update_successful = batch_update_packages(self.selected_pip.get(), selected_packages_printable_format)
            if update_successful:
                self.notify(msg="Packages updated successfully.")
            else:
                self.notify(msg="Some packages failed to update.")
            self.update_pip_outdated_listbox()
        else:
            self.update_message_board(msg="No packages selected.")


def main():
    root = Tk()
    PipdateGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()
