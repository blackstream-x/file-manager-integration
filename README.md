# file-manager-integration

A small utility for integrating scripts into various Unix/Linux file managers.

It uses a file named `file_manager_integration.json` specifying the script
and the parameters of the file manager integration.

## Requirements

Python 3.6 or newer

## Installation

```
pip install file-manager-integration
```

I recommend either installing into a virtual environment or doing a
[user install](https://pip.pypa.io/en/stable/user_guide/#user-installs):

```
pip install --user file-manager-integration
```

## Usage

The utility can be invoked on the command line either directly
(`file_manager_integration`) or via `python3 -m`
(`python -m` in a Python 3 virtual environment):

```
python3 -m file_manager_integration
```

In the following examples, the short variant is used.

### List supported file managers

```
file_manager_integration list-supported
```

### Show configuration

Reads `file_manager_integration.json` from the current working directory
and shows its contents.

```
file_manager_integration list-supported
```

### Edit / create a configuration

Interactively asks the user for each parameter of a new configuration
and writes the new configuration to `file_manager_integration.json`
in the current working directory.
If the file already existed before, values are read from it and used as presets.

```
file_manager_integration configure
```

### Do the integration

Call `file_manager_integration install` with at least the name of the file manager
and optionally the integration mode (`action`or `script`).
If the integration mode is omitted, the first one listed for the file manager
when calling `file_manager_integration list-supported` will be used
(that’s usually `action` if supported).

The `action` integration mode creates files,
and the `script` integration modes creates symbolic links,
both in locations specific to the file manager (see the `file_managers` module source).

```
file_manager_integration install [ Options ] <file manager> [ <integration mode> ]
```

Options:
- `--interactive` asks for each parameter interactively, using the values from the
  `file_manager_integration.json` file as presets.
- `--force-create-directories` creates required directories if they do not exist yet.
- `--force-overwrite` overwrites pre-existing target files or symbolic links
- `--force-rename-existing` renames an existing symbolic link pointing to the same
  path as the script to be integrated to the name specified in the parameters.

## Scripts requirements

The scripts being integrated **must** support the following:

- For script integration:
  Read the selected file or directory from environment variables
  set by the file manager:
  - `CAJA_SCRIPT_SELECTED_FILE_PATHS`
  - `NAUTILUS_SCRIPT_SELECTED_FILE_PATHS`
  - `NEMO_SCRIPT_SELECTED_FILE_PATHS`
- For action integration:
  Read the selected file or directory as a single command line argument.

The scripts **should** provide a graphical user interface.

## Supported file managers

### implemented

- Nautilus (GNOME)
- Nemo (Cinnamon)

### planned support

- Caja (MATE)
- KDE file manager
- PCManFM (LXDE)
- Thunar (XFCE)

## Bugs / Feature requests

Feel free to open an issue [here](https://github.com/blackstream-x/file-manager-integration/issues)
