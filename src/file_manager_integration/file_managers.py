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


ACTION = "action"
SCRIPT = "script"

SCRIPT_REQUIRED_KEYS = {"name", "absolute_path"}

NEMO_ACTION_TEMPLATE = """[Nemo Action]
Name=${name}
Comment=${comment}
Exec=${absolute_path} %F
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
Exec=${absolute_path} %F
"""

HELP = dict(
    name="The desired name of the menu entry",
    comment="Comment for the action (Nemo, …)",
    absolute_path="Absolute path of the script to integrate",
    relative_path="Relative path of the script to integrate",
    extensions="Semicolon-separated list of handled file extensions"
    " (Nemo, …)",
    mimetypes="Semicolon-separated list of handled file mime types"
    " (Dolphin, …)",
    identifier="Internal identifier in the desktop file (Dolphin, …)",
)


#
# Helper functions
#


def check_target_directory(target_directory_path, options):
    """Check if the target directory exists,
    If it does not, and the --force-create-directories option
    was set, create it.
    """
    if not target_directory_path.is_dir():
        if options.force_create_directories:
            target_directory_path.mkdir()
        else:
            raise ValueError(f"{target_directory_path} not available!")
        #
    #


def check_target_file(target_file_path, options):
    """Check if the target file already exists.
    If it does, is a regular file,
    and the --force-overwrite option was set,
    ignore the situation and allow overwriting it.
    """
    if target_file_path.exists():
        if target_file_path.is_file() and options.force_overwrite:
            return
        #
        raise ValueError(f"{target_file_path} already exists!")
        #
    #


def check_target_symlink(target_link_path, options):
    """Check if the target symlink already exists.
    If it does, is a symbolic link,
    and the --force-overwrite option was set,
    delete it.
    """
    if target_link_path.exists():
        if target_link_path.is_symlink() and options.force_overwrite:
            target_link_path.unlink()
            return
        #
        raise ValueError(f"{target_link_path} already exists!")
        #
    #


#
# Classes
#


class EnhancedTemplate(string.Template):

    """string.Template subclass aware of the required keys"""

    @property
    def required_keys(self):
        """Return the set of keys required by the template"""
        keys = set()
        for match_obj in self.pattern.finditer(self.template):
            named = match_obj.group("named") or match_obj.group("braced")
            if named is not None:
                keys.add(named)
            #
        #
        return keys


class BaseFileManager:

    """File Manager base class"""

    name = "Unknown File Manager"
    config_directory = ".local/share/unknown-file-manager"
    subdirs = {ACTION: "actions", SCRIPT: "scripts"}
    capabilities = ()
    action_template = ""
    executable = "/bin/false"

    def __init__(self):
        """Initialize attributes"""
        self.template = EnhancedTemplate(self.action_template)
        self.config_path = pathlib.Path.home() / self.config_directory

    def check_availability(self):
        """Check installation"""
        if not self.is_installed():
            raise ValueError(f"{self.name} is not installed!")
        #
        if not self.config_path.is_dir():
            raise ValueError(
                f"Configuration path for {self.name} is not available!"
            )
        #

    def install(self, integration_mode, configuration, options):
        """Execute the install method defined in the subclass"""
        if integration_mode not in self.capabilities:
            raise ValueError(
                f"{integration_mode} not supported in {self.name}!"
            )
        #
        self.check_availability()
        target_directory_path = (
            self.config_path / self.subdirs[integration_mode]
        )
        try:
            install_method = getattr(self, f"install_{integration_mode}")
        except AttributeError as error:
            raise NotImplementedError from error
        #
        logging.debug("File manager: %s", self.name.title())
        logging.debug("Integration mode: %s", integration_mode)
        install_method(target_directory_path, configuration, options)

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

    def required_keys(self, integration_mode):
        """Required keys for the integration_mode"""
        if integration_mode == SCRIPT:
            return SCRIPT_REQUIRED_KEYS
        #
        return self.template.required_keys


class Nautilus(BaseFileManager):

    """Nautilus file manager, also a base class for others"""

    name = "nautilus"
    config_directory = ".local/share/nautilus"
    capabilities = (SCRIPT,)
    executable = "/usr/bin/nautilus"

    @staticmethod
    def install_script(target_directory_path, configuration, options):
        """Install as Nautilus script in target_path"""
        check_target_directory(target_directory_path, options)
        source_path = pathlib.Path(
            os.path.realpath(configuration["absolute_path"])
        )
        if source_path.is_symlink():
            source_path = source_path.readlink()
        #
        if not source_path.is_file():
            raise ValueError(f"{source_path} does not exist!")
        #
        target_link_path = target_directory_path / configuration["name"]
        logging.debug("Target path: %s", target_link_path)
        check_target_symlink(target_link_path, options)
        for single_path in target_directory_path.glob("*"):
            if single_path.is_symlink():
                if single_path.readlink() == source_path:
                    if options.force_rename_existing:
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
        os.symlink(source_path, target_link_path)


class Caja(Nautilus):

    """Caja file manager (Nautilus based)"""

    name = "caja"
    config_directory = ".local/share/caja"
    # capabilities = (ACTION, SCRIPT)


class Nemo(Nautilus):

    """Nemo file manager (Nautilus based)"""

    name = "nemo"
    config_directory = ".local/share/nemo"
    capabilities = (ACTION, SCRIPT)
    action_template = NEMO_ACTION_TEMPLATE
    executable = "/usr/bin/nemo"

    def install_action(self, target_directory_path, configuration, options):
        """Install as Nemo action in tagret path"""
        check_target_directory(target_directory_path, options)
        action_name = configuration["name"]
        target_file_path = target_directory_path / f"{action_name}.nemo_action"
        check_target_file(target_file_path, options)
        target_file_path.write_text(
            self.template.safe_substitute(configuration),
            encoding="utf-8",
        )


class KdefileManager(BaseFileManager):

    """KDE file manager"""

    name = "dolphin"
    capabilities = (ACTION,)
    action_template = KFM_ACTION_TEMPLATE


class PcManFm(BaseFileManager):

    """PCManFM file manager"""

    name = "pcmanfm"
    capabilities = (ACTION,)


class Thunar(BaseFileManager):

    """Thunar file manager"""

    name = "thunar"
    capabilities = (ACTION,)


#
# Constant: Supported file managers
#


SUPPORTED = (Nautilus, Nemo)


# vim: fileencoding=utf-8 ts=4 sts=4 sw=4 autoindent expandtab syntax=python:
