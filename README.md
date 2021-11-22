# file-manager-integration
File manager integration for scripts

## Supported file managers

### planned 

- Caja (MATE)
- KDE file manager 
- Nautilus (GNOME)
- Nemo (Cinnamon)
- PCManFM (LXDE)
- Thunar (XFCE)

## Scripts requirements

The scripts being integrated **must** support the following:

For script integration:
Read the selected file or directory from environment variables:
`CAJA_SCRIPT_SELECTED_FILE_PATHS` for Caja,
`NAUTILUS_SCRIPT_SELECTED_FILE_PATHS` for Nautilus,
`NEMO_SCRIPT_SELECTED_FILE_PATHS` for Nemo.

For action integration:
Read the selected file or directory as a single command line argument.

The scripts **should** provide a graphical user interface.

