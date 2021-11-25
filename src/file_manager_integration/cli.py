# -*- coding: utf-8 -*-

"""

file_manager_integration.cli

Command line interface

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


import argparse
import json
import logging
import pathlib

from file_manager_integration import __version__
from file_manager_integration import dialog
from file_manager_integration import file_managers


#
# Constants
#


INTERROGATOR = dialog.Interrogator()
LOGGER = INTERROGATOR.logger

RETURNCODE_OK = 0
RETURNCODE_ERROR = 1

JSON_FILE = "file_manager_integration.json"

SUPPORTED_FILE_MANAGERS = {
    single_file_manager.name: single_file_manager
    for single_file_manager in file_managers.SUPPORTED
}


#
# Functions
#


def _load_configuration():
    """Read the configuration from the JSON config file
    in the current directory, and return it as a dict
    """
    with open(
        pathlib.Path.cwd() / JSON_FILE, mode="rt", encoding="utf-8"
    ) as json_file:
        return json.load(json_file)
    #


def _question_all_items(configuration, arguments):
    """Question all configuration items interactively.
    Return the new configuration.
    """
    current_path = pathlib.Path.cwd()
    for (key, description) in file_managers.HELP.items():
        if key == "absolute_path":
            continue
        #
        new_value = None
        while True:
            try:
                old_value = getattr(arguments, key)
            except AttributeError:
                old_value = None
            try:
                if not old_value:
                    old_value = configuration[key]
                #
            except (AttributeError, KeyError):
                new_value = INTERROGATOR.get_input(
                    description, prompt=f"{key} => "
                )
            else:
                new_value = INTERROGATOR.get_input_with_preset(
                    description, prompt=f"{key} => ", preset_answer=old_value
                )
            #
            if key != "relative_path":
                break
            #
            if (current_path / new_value).is_file():
                break
            #
            LOGGER.error(
                "%s must be an existing file in %s\nPlease try again.",
                key,
                current_path,
            )
        #
        LOGGER.separator()
        LOGGER.info("%s=%r", key, new_value)
        configuration[key] = new_value
        LOGGER.separator()
    #
    return configuration


def configure(arguments):
    """Configure the JSON file"""
    current_path = pathlib.Path.cwd()
    LOGGER.heading(
        f"Configure file manager integration in {current_path}",
        style=dialog.BoxFormatter.double,
    )
    try:
        configuration = _load_configuration()
    except FileNotFoundError:
        configuration = {}
    #
    configuration = _question_all_items(configuration, arguments)
    #
    with open(
        current_path / JSON_FILE, mode="wt", encoding="utf-8"
    ) as json_file:
        json.dump(configuration, json_file, indent=2)
    #
    LOGGER.info("Saved configuration in %s", current_path / JSON_FILE)
    LOGGER.separator(style=dialog.BoxFormatter.double)
    return RETURNCODE_OK


def install(arguments):
    """Install in the specified file managers"""
    current_path = pathlib.Path.cwd()
    LOGGER.heading(
        "Installing file manager integration", style=dialog.BoxFormatter.double
    )
    try:
        configuration = _load_configuration()
    except FileNotFoundError as error:
        LOGGER.error("Could not read configuration file: %s", error)
        return RETURNCODE_ERROR
    #
    if arguments.interactive:
        configuration = _question_all_items(configuration, arguments)
    else:
        for (key, value) in configuration.items():
            LOGGER.debug("%s=%r", key, value)
        #
    #
    absolute_path = current_path / configuration["relative_path"]
    if not absolute_path.is_file():
        LOGGER.error("%s does not exist!", absolute_path)
        return RETURNCODE_ERROR
    #
    configuration.update(absolute_path=str(absolute_path))
    #
    try:
        file_manager = SUPPORTED_FILE_MANAGERS[arguments.file_manager]()
    except KeyError:
        LOGGER.error(
            "%r is not a supported file manager!", arguments.file_manager
        )
        return RETURNCODE_ERROR
    #
    if not arguments.integration_mode:
        arguments.integration_mode = file_manager.capabilities[0]
    #
    if arguments.integration_mode not in file_manager.capabilities:
        LOGGER.error(
            "%r integration is not a supported in %s!",
            arguments.integration_mode,
            arguments.file_manager,
        )
        return RETURNCODE_ERROR
    #
    LOGGER.separator(level=logging.DEBUG)
    try:
        file_manager.install(
            arguments.integration_mode, configuration, arguments
        )
    except ValueError as error:
        LOGGER.error(str(error))
        return RETURNCODE_ERROR
    #
    LOGGER.info(
        "Installed %s\nas a %s %s (%r).",
        absolute_path,
        file_manager.name.title(),
        arguments.integration_mode,
        configuration["name"],
    )
    return RETURNCODE_OK


def list_supported_file_managers(*unused_arguments):
    """Show a list of supported file managers and their capabilities"""
    LOGGER.heading("Supported file managers")
    for (name, fm_class) in SUPPORTED_FILE_MANAGERS.items():
        LOGGER.info(
            "%s (supports integration(s): %s)",
            name.title(),
            ", ".join(fm_class.capabilities),
        )
    #
    return RETURNCODE_OK


def show_configuration(*unused_arguments):
    """Show the configuration"""
    try:
        configuration = _load_configuration()
    except FileNotFoundError:
        LOGGER.error("No JSON configuration found.")
        return RETURNCODE_ERROR
    #
    for (key, value) in configuration.items():
        LOGGER.heading(f"{key} = {value!r}")
        LOGGER.debug(file_managers.HELP[key])
    #
    return RETURNCODE_OK


def main():
    """Parse command line arguments and execute the matching function"""
    main_parser = argparse.ArgumentParser(
        prog="file_manager_integration",
        description="Integrate a script in file managers",
    )
    main_parser.set_defaults(loglevel=logging.INFO)
    main_parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=logging.DEBUG,
        dest="loglevel",
        help="output all messages including debug level",
    )
    main_parser.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=logging.WARNING,
        dest="loglevel",
        help="limit message output to warnings and errors",
    )
    main_parser.add_argument(
        "--version",
        action="store_true",
        help="print version and exit",
    )
    subparsers = main_parser.add_subparsers()
    # Parser for the "list-supported" command
    parser_list_supported = subparsers.add_parser(
        "list-supported", help="list supported file managers"
    )
    parser_list_supported.set_defaults(
        execute_function=list_supported_file_managers
    )
    # Parser for the "show-config" command
    parser_show_config = subparsers.add_parser(
        "show-config", help=f"show configuration from {JSON_FILE}"
    )
    parser_show_config.set_defaults(execute_function=show_configuration)
    # Parser for the "configure" command
    parser_configure = subparsers.add_parser(
        "configure",
        help=f"ask confguration items and write the result to {JSON_FILE}",
    )
    parser_configure.set_defaults(execute_function=configure)
    # Parser for the "configure" command
    parser_install = subparsers.add_parser(
        "install", help="install the inegration in the specified file manager"
    )
    parser_install.set_defaults(execute_function=install)
    parser_install.add_argument(
        "--force-create-directories",
        action="store_true",
        help="create required directories if they do not exist yet",
    )
    parser_install.add_argument(
        "--force-overwrite",
        action="store_true",
        help="overwrite existing files or symbolic links",
    )
    parser_install.add_argument(
        "--force-rename-existing",
        action="store_true",
        help="script integrations only: rename an existing symbolic link"
        f" if it already points to the script specified in {JSON_FILE}.",
    )
    parser_install.add_argument(
        "--interactive",
        action="store_true",
        help="question all configuration items interactively",
    )
    parser_install.add_argument(
        "file_manager",
        choices=SUPPORTED_FILE_MANAGERS.keys(),
        help="the file manager to integrate the script with",
    )
    parser_install.add_argument(
        "integration_mode",
        nargs="?",
        help=f"the integration mode (eg. {file_managers.ACTION}"
        f" or {file_managers.SCRIPT})",
    )
    #
    arguments = main_parser.parse_args()
    if arguments.version:
        print(__version__)
        return RETURNCODE_OK
    #
    LOGGER.configure(level=arguments.loglevel)
    try:
        return arguments.execute_function(arguments)
    except AttributeError:
        LOGGER.error("Please specify --version or a subcommand:")
        main_parser.print_help()
    #
    return RETURNCODE_ERROR


# vim: fileencoding=utf-8 ts=4 sts=4 sw=4 autoindent expandtab syntax=python:
