#!/bin/bash
#!author: github.com/egely1337

check_permissions() {
    if [ "$EUID" != 0 ]; then
        echo "Please run as root."
        exit
    fi
}

install_msi_ec() {
    install -C msi-ec.py /usr/bin/msi-ec
    chmod +x /usr/bin/msi-ec
    echo "Installed msi-ec to /usr/bin/msi-ec"
}

install_as_application() {
    install -C msi-ec.desktop /usr/share/applications/msi-ec.desktop
}

check_permissions
install_as_application
install_msi_ec