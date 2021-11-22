# -*- coding: utf-8 -*-

"""

file_manager_integration.core

Core application module

"""


import json
import logging
import os
import pathlib
import tkinter

from tkinter import filedialog
from tkinter import messagebox

# local modules

from file_manager_integration import file_managers
from file_manager_integration import gui
from file_manager_integration import __version__


#
# Constants
#


HOMEPAGE = "https://github.com/blackstream-x/file-manager-integration"

COPYRIGHT_NOTICE = """Copyright (C) 2021 Rainer Schwarzbach

This file is part of file_manager_integration.

file_manager_integration is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

file_manager_integration is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with file_manager_integration (see LICENSE).
If not, see <http://www.gnu.org/licenses/>."""


# Grid parameters
BUTTONS_GRID_W = dict(padx=3, pady=3, sticky=tkinter.W)
BUTTONS_GRID_E = dict(padx=3, pady=3, sticky=tkinter.E)
GRID_FULLWIDTH = dict(padx=4, pady=2, sticky=tkinter.E + tkinter.W)
WITH_BORDER = dict(borderwidth=2, padx=5, pady=5, relief=tkinter.GROOVE)

IMPLEMENTED_FILE_MANAGERS = (file_managers.Nautilus, file_managers.Nemo)


#
# Classes
#


class Namespace(dict):

    """A dict subclass that exposes its items as attributes.

    Warning: Namespace instances only have direct access to the
    attributes defined in the visible_attributes tuple
    """

    visible_attributes = ("items", "update")

    def __repr__(self):
        """Object representation"""
        return "{0}({1})".format(type(self).__name__, super().__repr__())

    def __dir__(self):
        """Members sequence"""
        return tuple(self)

    def __getattribute__(self, name):
        """Access a visible attribute
        or return an existing dict member
        """
        if name in type(self).visible_attributes:
            return object.__getattribute__(self, name)
        #
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(
                "{0!r} object has no attribute {1!r}".format(
                    type(self).__name__, name
                )
            ) from error
        #

    def __setattr__(self, name, value):
        """Set an attribute"""
        self[name] = value

    def __delattr__(self, name):
        """Delete an attribute"""
        del self[name]

    def update(self, **kwargs):
        """Add attributes from kwargs"""
        for key, value in kwargs.items():
            self[key] = value
        #


class InterfacePlugin:

    """Class instantiated with the UserInterface
    to access its varuables and widgets
    """

    def __init__(self, application):
        """Store the application"""
        self.application = application
        self.tkvars = application.tkvars
        self.vars = application.vars
        self.widgets = application.widgets
        self.main_window = application.main_window


class Callbacks(InterfacePlugin):

    """Callback methods"""

    def get_traced_intvar(self, method_name, value=None):
        """Return a traced IntVar() calling
        this intance's method methodname
        """
        return gui.traced_variable(
            getattr(self, method_name), constructor=tkinter.IntVar, value=value
        )

    def get_traced_stringvar(self, method_name, value=None):
        """Return a traced IntVar() calling
        this intance's method methodname
        """
        return gui.traced_variable(getattr(self, method_name), value=value)

    def update_buttons(self, *unused_arguments):
        """Trigger button state updates in subclasses"""
        raise NotImplementedError


class Panels(InterfacePlugin):

    """Panel and panel component methods"""

    def select_file_manager(self):
        """Show the select_file_manager panel"""
        ...


class UserInterface:

    """GUI using tkinter"""

    # phase_open_file = "open_file"
    phase_select_fm = "select_file_manager"
    phase_enter_vars = "enter_variables"
    phase_show_result = "show_result"

    phases = (phase_select_fm, phase_enter_vars, phase_show_result)
    panel_names = {}
    looped_panels = set()

    action_class = InterfacePlugin
    callback_class = Callbacks
    panel_class = Panels
    post_panel_action_class = InterfacePlugin
    rollback_class = InterfacePlugin

    default_settings = {}

    script_name = "<module file_manager_integration.core>"
    version = __version__
    homepage = HOMEPAGE
    copyright_notice = COPYRIGHT_NOTICE

    file_type = "image file"

    def __init__(self, options):
        """Build the GUI"""
        self.options = options
        self.main_window = tkinter.Tk()
        self.main_window.title(self.script_name)
        self.vars = Namespace(
            current_panel=None,
            errors=[],
            capabilities={},
            panel_stack=[],
            post_panel_methods={},
            user_settings=Namespace(),
            settings_path=None,
            loop_counter={key: [] for key in self.looped_panels},
            undo_buffer=[],
            disable_key_events=False,
        )
        self.tkvars = Namespace()
        self.widgets = Namespace(
            action_area=None,
            # buttons_area=None,
            canvas=None,
            height=None,
            preview_active=None,
        )
        self.actions = self.action_class(self)
        self.callbacks = self.callback_class(self)
        self.panels = self.panel_class(self)
        self.post_panel_actions = self.post_panel_action_class(self)
        self.rollbacks = self.rollback_class(self)
        #
        # Fill self.tkvars after the callbacks plugin has been initialized
        self.tkvars.update(
            file_name=tkinter.StringVar(),
            show_preview=tkinter.IntVar(),
            scripts={},
            actions={}
        )
        for file_manager_cls in IMPLEMENTED_FILE_MANAGERS:
            capabilities = file_manager_cls.capabilities
            if file_managers.ACTIONS in capabilities:
                self.tkvars.actions[file_manager_cls.name] = tkinter.IntVar()
            #
            if file_managers.SCRIPTS in capabilities:
                self.tkvars.scripts[file_manager_cls.name] = tkinter.IntVar()
            #
            self.vars.capabilities[file_manager_cls.name] = capabilities
        #
        self.jump_to_panel(self.phase_select_fm)
        self.main_window.protocol("WM_DELETE_WINDOW", self.quit)
        self.main_window.mainloop()

    def execute_post_panel_action(self):
        """Execute the post panel action for the current panel"""
        try:
            method = self.vars.post_panel_methods.pop(self.vars.current_panel)
        except KeyError:
            logging.debug(
                "Post-panel action for %r not defined or already executed.",
                self.vars.current_panel,
            )
        else:
            method()
        #

# =============================================================================
#     def open_file(
#         self, keep_existing=False, preset_path=None, quit_on_empty_choice=False
#     ):
#         """Open a file via file dialog"""
#         self.vars.update(current_panel=self.phase_open_file)
#         file_path = self.vars.original_path
#         if preset_path:
#             if not preset_path.is_dir():
#                 initial_dir = str(preset_path.parent)
#             #
#         elif file_path:
#             initial_dir = str(file_path.parent)
#         else:
#             initial_dir = os.getcwd()
#         #
#         while True:
#             if not keep_existing or file_path is None:
#                 self.vars.update(disable_key_events=True)
#                 selected_file = filedialog.askopenfilename(
#                     initialdir=initial_dir,
#                     parent=self.main_window,
#                     title=f"Load a {self.file_type}",
#                 )
#                 self.vars.update(disable_key_events=False)
#                 if not selected_file:
#                     if quit_on_empty_choice:
#                         self.quit()
#                     #
#                     return
#                 #
#                 file_path = pathlib.Path(selected_file)
#             #
#             # check for a supported file type,
#             # and show an error dialog and retry
#             # if the selected file is not an image
#             if not self.check_file_type(file_path):
#                 messagebox.showerror(
#                     "Unsupported file type",
#                     f"{file_path.name!r} is not a supported file.",
#                     icon=messagebox.ERROR,
#                 )
#                 initial_dir = str(file_path.parent)
#                 file_path = None
#                 continue
#             #
#             if self.vars.unapplied_changes or self.vars.undo_buffer:
#                 confirmation = messagebox.askokcancel(
#                     "Unsaved Changes",
#                     "Discard the chages made to"
#                     f" {self.vars.original_path.name!r}?",
#                     icon=messagebox.WARNING,
#                 )
#                 if not confirmation:
#                     return
#                 #
#             #
#             # Set original_path and read image data
#             try:
#                 self.load_file(file_path)
#             except (OSError, ValueError) as error:
#                 messagebox.showerror(
#                     "Load error", str(error), icon=messagebox.ERROR
#                 )
#                 initial_dir = str(file_path.parent)
#                 file_path = None
#                 continue
#             #
#             break
#         #
#         self.vars.undo_buffer.clear()
#         self.next_panel()
#
# =============================================================================

# =============================================================================
#     def check_file_type(self, file_path):
#         """Return True if the file is a supported file,
#         False if not
#         """
#         raise NotImplementedError
# =============================================================================

    def heading_with_help_button(
        self,
        parent_frame,
        subject,
        heading_column_span=4,
        parent_window=None,
    ):
        """A heading with an adjacent help button"""
        heading = gui.Heading(
            parent_frame,
            text=f"{subject}:",
            sticky=tkinter.W,
            columnspan=heading_column_span,
        )

        # Inner function for the "extra arguments" trick, see
        # <https://tkdocs.com/shipman/extra-args.html>
        def show_help(self=self, parent_window=parent_window):
            return self.show_help(topic=subject, parent_window=parent_window)

        #
        help_button = tkinter.Button(
            parent_frame,
            text="?",
            command=show_help,
        )
        help_button.grid(
            row=gui.grid_row_of(heading),
            column=heading_column_span,
            sticky=tkinter.E,
        )

# =============================================================================
#     def load_file(self, file_path):
#         """Load the file"""
#         raise NotImplementedError
#
#     def save_file(self):
#         """Save as the selected file,
#         return True if the file was saved
#         """
#         raise NotImplementedError
# =============================================================================

    def jump_to_panel(self, panel_name):
        """Jump to the specified panel
        after executing its action method
        """
        method_display = f"Action method for panel {panel_name!r}"
        try:
            action_method = getattr(self.actions, panel_name)
        except AttributeError:
            logging.debug("%s is undefined", method_display)
        else:
            try:
                action_method()
            except NotImplementedError:
                self.vars.errors.append(
                    f"{method_display} has not been implemented yet"
                )
            except ValueError as error:
                self.vars.errors.append(str(error))
            #
        #
        self.vars.update(current_phase=panel_name)
        self.__show_panel()

    def next_panel(self, *unused_arguments):
        """Go to the next panel,
        executing the old panel’s post-panel action mrthod,
        and then the new panel’s (pre-panel) action method
        before showing the new panel
        """
        self.execute_post_panel_action()
        self.vars.panel_stack.append(self.vars.current_panel)
        if self.vars.current_panel in self.looped_panels:
            panel_name = self.vars.current_panel
            self.vars.loop_counter[panel_name].append(False)
        else:
            current_index = self.phases.index(self.vars.current_panel)
            next_index = current_index + 1
            try:
                panel_name = self.phases[next_index]
            except IndexError:
                self.vars.errors.append(
                    f"Phase number #{next_index} out of range"
                )
            #
        #
        self.jump_to_panel(panel_name)

    def previous_panel(self):
        """Go to the previous panel, executing the current panel’s
        rollback method before.
        """
        panel_name = self.vars.current_panel
        phase_index = self.phases.index(panel_name)
        method_display = (
            f"Rollback method for panel #{phase_index} ({panel_name})"
        )
        try:
            rollback_method = getattr(self.rollbacks, panel_name)
        except AttributeError:
            logging.warning("%s is undefined", method_display)
        else:
            try:
                rollback_method()
            except NotImplementedError:
                self.vars.errors.append(
                    f"{method_display} has not been implemented yet"
                )
            #
            self.vars.update(current_phase=self.vars.panel_stack.pop())
        #
        self.__show_panel()

    def pre_quit_check(self):
        """Pre-quit checks eg. for files to save.
        If this method of an inherited class returns False,
        the application will NOT exit,
        """
        # raise NotImplementedError
        return True

    def quit(self, event=None):
        """Save user settings and exit the application"""
        del event
        if self.pre_quit_check():
            self.main_window.destroy()
        #

    def show_additional_buttons(self, buttons_area):
        """Additional buttons for the pixelate_image script.
        Return the number of rows (= the row index for th last row)
        """
        raise NotImplementedError

    def __show_about(self):
        """Show information about the application
        in a modal dialog
        """
        gui.InfoDialog(
            self.main_window,
            (
                self.script_name,
                f"Version: {self.version}\nProject homepage: {self.homepage}",
            ),
            ("Copyright/License:", self.copyright_notice),
            title="About…",
        )
        #

    def __show_errors(self):
        """Show errors if there are any"""
        if self.vars.errors:
            gui.InfoDialog(
                self.main_window,
                ("Errors:", "\n".join(self.vars.errors)),
                title="Errors occurred!",
            )
            self.vars.errors.clear()
        #

    def show_help(self, topic=None, parent_window=None):
        """Show help for the provided topic.
        The topic defaults to the current panel.
        """
        if topic is None:
            topic = self.vars.current_panel
            title = f"Panel {self.panel_names[topic]!r}"
        else:
            title = topic
        #
        try:
            info_sequence = list(self.vars.help[topic].items())
        except AttributeError:
            # Not a hash -> generate a heading
            info_sequence = [(None, self.vars.help[topic])]
        except KeyError:
            info_sequence = [("Error:", f"No help for {title} available yet")]
        #
        if parent_window is None:
            parent_window = self.main_window
        #
        gui.InfoDialog(parent_window, *info_sequence, title=f"Help ({title})")

    def __show_panel(self):
        """Show a panel.
        Add the "Previous", "Next", "Choose another relase",
        "About" and "Quit" buttons at the bottom
        """
        try:
            self.widgets.action_area.destroy()
        except AttributeError:
            pass
        #
        self.widgets.update(action_area=tkinter.Frame(self.main_window))
        try:
            panel_method = getattr(self.panels, self.vars.current_phase)
        except AttributeError:
            self.vars.errors.append(
                f"Panel for Phase {self.vars.current_phase!r}"
                " has not been implemented yet,"
                f" going back to phase {self.vars.current_panel!r}."
            )
            self.vars.update(current_phase=self.vars.current_panel)
            panel_method = getattr(self.panels, self.vars.current_phase)
        else:
            self.vars.update(current_panel=self.vars.current_phase)
        #
        self.__show_errors()
        logging.debug("Showing panel %r", self.vars.current_panel)
        try:
            self.vars.post_panel_methods[self.vars.current_phase] = getattr(
                self.post_panel_actions, self.vars.current_phase
            )
        except AttributeError:
            logging.debug(
                "No post-panel method defined for %r",
                self.vars.current_panel,
            )
        #
        gui.Heading(
            self.widgets.action_area,
            text=self.panel_names[self.vars.current_panel],
            row=0,
            column=0,
            # **GRID_FULLWIDTH,
            sticky=tkinter.E + tkinter.W,
            **WITH_BORDER,
        )
        panel_method()
        self.widgets.action_area.grid(**GRID_FULLWIDTH)
        #
        # Show global application buttons
        buttons_area = tkinter.Frame(self.widgets.action_area)
        last_row = self.show_additional_buttons(buttons_area)
        self.callbacks.update_buttons()
        help_button = tkinter.Button(
            buttons_area, text="Help", command=self.show_help
        )
        about_button = tkinter.Button(
            buttons_area, text="\u24d8 About", command=self.__show_about
        )
        quit_button = tkinter.Button(
            buttons_area, text="\u2717 Quit", command=self.quit
        )
        help_button.grid(row=last_row, column=0, **BUTTONS_GRID_E)
        about_button.grid(row=last_row, column=1, **BUTTONS_GRID_W)
        quit_button.grid(row=last_row, column=2, **BUTTONS_GRID_E)
        self.widgets.action_area.rowconfigure(2, weight=100)
        buttons_area.grid(row=3, column=1, sticky=tkinter.E)
        # Add global key / mouse button bindings if desired


#
# Helper functions
#


def shortened_file_name(file_name, threshold=45):
    """Return file_name shortened
    by replacing characters in its middle by dots
    if its length exceeds threshold,
    or unchanged in the other case
    """
    if len(file_name) <= threshold:
        return file_name
    #
    maximum_part_length = int((threshold - 3) / 2)
    return "[…]".join(
        (
            file_name[:maximum_part_length],
            file_name[-maximum_part_length:],
        )
    )


# vim: fileencoding=utf-8 ts=4 sts=4 sw=4 autoindent expandtab syntax=python:
