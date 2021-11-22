# -*- coding: utf-8 -*-

"""

file_manager_integration.file_managers

File manager definitions

Copyright (C) 2021 Rainer Schwarzbach

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
If not, see <http://www.gnu.org/licenses/>.

"""


import os
import logging
import pathlib
import string
import subprocess


#
# Constants
#


ACTIONS = "actions"
SCRIPTS = "scripts"

NEMO_ACTION_TEMPLATE = """[Nemo Action]
Name=${name}
Comment=${comment}
Exec=${executable} %F
Selection=S
Extensions=${extensions};
Quote=double
"""

KFM_ACTION_TEMPLATE = """[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=${mimetypes};
InitialPreference=99
Actions=${identifier}

[Desktop Action ${identifier}]
Name=${name}
Exec=${executable} %F
"""

HELP = dict(
    name="The desired name of the action",
    comment="Comment for the action (Nemo, …)",
    executable="Executable path",
    extensions="Semicolon-separated list of handled file extensions"
    " (Nemo, …)",
    mimetypes="Semicolon-separated list of handled file mime types"
    " (KDE file managers, …)",
    identifier="Internal identifier in the desktop file"
    " (KDE file managers, …)",
)


#
# Classes
#


class BaseFileManager:

    """File Manager base class"""

    name = "Unknown File Manager"
    config_path = pathlib.Path(".local/share/unknown")
    actions_subdir = "actions"
    scripts_subdir = "scripts"
    capabilities = ()
    action_template = ""
    executable = "/bin/false"

    def __init__(self):
        """Initinalize attributes"""
        if ACTIONS in self.capabilities:
            self.actions_path = self.config_path / self.actions_subdir
        #
        if SCRIPTS in self.capabilities:
            self.scripts_path = self.config_path / self.scripts_subdir
        #

    @property
    def template(self):
        """Return a string.Template object from self.action_template"""
        return string.Template(self.action_template)

    def is_installed(self):
        """Check if the file manager is installed"""
        try:
            subprocess.run(
                (self.executable, "--version"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except subprocess.CalledProcessError:
            return False
        #
        return True

    def required_keys(self):
        """Return a list of keys required by the template"""
        keys = []
        for match_obj in self.template.pattern.finditer(self.action_template):
            named = match_obj.group("named") or match_obj.group("braced")
            if named is not None:
                keys.append(named)
            #
        #
        return keys

    def check_installation(self):
        """Check installation"""
        if not self.config_path.is_dir():
            raise ValueError(f"{self.name} is probably not installed!")
        #

    def check_actions_support(self):
        """Check actions support"""
        if ACTIONS not in self.capabilities:
            raise ValueError(f"Actions not supported in {self.name}!")
        #
        self.check_installation()

    def check_scripts_support(self):
        """Check scripts support"""
        if SCRIPTS not in self.capabilities:
            raise ValueError(f"Scripts not supported in {self.name}!")
        #
        self.check_installation()


class Nautilus(BaseFileManager):

    """Nautilus file manager, also a base class for others"""

    name = "Nautilus"
    config_path = pathlib.Path(".local/share/nautilus")
    capabilities = (SCRIPTS,)
    executable = "/usr/bin/nautilus"

    def install_script(self, absolute_source_path, **options):
        """Install as Nautilus script"""
        self.check_scripts_support()
        if not self.scripts_path.is_dir():
            if options.get('force_create_directories', False):
                self.scripts_path.mkdir()
            else:
                raise ValueError(f"{self.scripts_path} not available!")
            #
        #
        display_name = options['display_name']
        target_link_path = self.scripts_path / display_name
        logging.debug("Target path: %s", target_link_path)
        if target_link_path.exists():
            raise ValueError(f"{target_link_path} already exists!")
        #
        for single_path in self.scripts_path.glob("*"):
            if single_path.is_symlink():
                if single_path.readlink() == absolute_source_path:
                    if options.get('force_rename_existing', False):
                        os.rename(single_path, target_link_path)
                        return
                    #
                    logging.warning(
                        "Found the source script already linked as %s,"
                        " but ignoring the situation.",
                        single_path,
                    )
                #
            #
        #
        os.symlink(absolute_source_path, target_link_path)


class Caja(Nautilus):

    """Caja file manager (Nautilus based)"""

    name = "Caja"
    config_path = pathlib.Path(".local/share/caja")
    capabilities = (ACTIONS, SCRIPTS)

    def install_action(self, source_path, **options):
        """Install as action"""
        raise NotImplementedError


class Nemo(Nautilus):

    """Nemo file manager (Nautilus based)"""

    name = "Nemo"
    config_path = pathlib.Path(".local/share/nemo")
    capabilities = (ACTIONS, SCRIPTS)
    action_template = NEMO_ACTION_TEMPLATE
    executable = "/usr/bin/nemo"

    def install_action(self, source_path, **options):
        """Install as action"""
        self.check_actions_support()
        action_name = options["name"]
        target_file = f"{action_name}.nemo_action"
        template = string.Template(NEMO_ACTION_TEMPLATE)
        options["exec"] = str(source_path)
        with open(
            self.actions_path / target_file,
            mode="wt",
            encoding="utf-8",
        ) as output_file:
            output_file.write(template.safe_substitute(options))
        #


class KdefileManager(BaseFileManager):

    """KDE file manager"""

    name = "KDE file manager"
    capabilities = (ACTIONS,)
    action_template = KFM_ACTION_TEMPLATE

    def install_action(self, source_path, **options):
        """Install as action"""
        raise NotImplementedError


class PcManFm(BaseFileManager):

    """PCManFM file manager"""

    name = "PCManFM"
    capabilities = (ACTIONS,)

    def install_action(self, source_path, **options):
        """Install as action"""
        raise NotImplementedError


class Thunar(BaseFileManager):

    """Thunar file manager"""

    name = "Thunar"
    capabilities = (ACTIONS,)

    def install_action(self, source_path, **options):
        """Install as action"""
        raise NotImplementedError


# vim: fileencoding=utf-8 ts=4 sts=4 sw=4 autoindent expandtab syntax=python:
