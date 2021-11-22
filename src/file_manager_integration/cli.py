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
import logging
import pathlib

from file_manager_integration import core
from file_manager_integration import __version__


#
# Constants
#


RETURNCODE_OK = 0
RETURNCODE_ERROR = 1


#
# Functions
#


def __get_arguments():
    """Parse command line arguments"""
    argument_parser = argparse.ArgumentParser(
        description="Integrate the given script in file managers"
    )
    argument_parser.set_defaults(loglevel=logging.INFO)
    argument_parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=logging.DEBUG,
        dest="loglevel",
        help="Output all messages including debug level",
    )
    argument_parser.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=logging.WARNING,
        dest="loglevel",
        help="Limit message output to warnings and errors",
    )
    argument_parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    argument_parser.add_argument(
        "file",
        type=pathlib.Path,
        nargs="?",
        help="The script file to be integrated",
    )
    return argument_parser.parse_args()


def main():
    """Main script function"""
    arguments = __get_arguments()
    if arguments.version:
        print(__version__)
        return RETURNCODE_OK
    #
    logging.basicConfig(
        format="%(levelname)-8s\u2551 %(message)s", level=arguments.loglevel
    )
    core.UserInterface(arguments)
    return RETURNCODE_OK


# vim: fileencoding=utf-8 ts=4 sts=4 sw=4 autoindent expandtab syntax=python:
