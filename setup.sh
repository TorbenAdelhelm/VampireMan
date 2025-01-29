#!/bin/sh
set -eu

echo "-- Ensure everything is setup"
if [ -z "${XDG_CONFIG_HOME+set}" ]; then
  XDG_CONFIG_HOME="$HOME/.config"
fi

BIN_TARGET="$HOME/.local/bin"
NIX_BINARY_LOC="$BIN_TARGET/nix"

echo "-- Create directories"
mkdir -p "$BIN_TARGET" # For holding the binaries, ~/.bin gets overwritten by vscode-server
mkdir -p "$XDG_CONFIG_HOME/nix" # For the Nix config file

echo "-- Add $BIN_TARGET to the PATH variable in the .profile.my if not already set"
touch "$HOME/.profile.my"
if [ "$(grep "export PATH=\$PATH:$BIN_TARGET" "$HOME/.profile.my" -c)" -eq 0 ]; then
  echo "export PATH=\$PATH:$BIN_TARGET" >> "$HOME/.profile.my"
  echo "export XDG_CONFIG_HOME=$XDG_CONFIG_HOME" >> "$HOME/.profile.my"
fi

echo "-- Download Nix"
if [ ! -f "$NIX_BINARY_LOC" ]; then
  wget https://hydra.nixos.org/job/nix/master/buildStatic.x86_64-linux/latest/download-by-type/file/binary-dist -O "$NIX_BINARY_LOC"
fi
chmod 755 "$NIX_BINARY_LOC"

echo "-- Where should the nix store be placed?"
STORE_LOC_DEFAULT="/data/scratch/$(whoami)"
read -p "(default is $STORE_LOC_DEFAULT) " STORE_LOC
if [ -z "$STORE_LOC" ]; then
    STORE_LOC="$STORE_LOC_DEFAULT"
fi

echo "-- Write the nix.conf file if it doesn't exist"
if [ ! -f "$XDG_CONFIG_HOME/nix/nix.conf" ]; then
  cat <<EOF > "$XDG_CONFIG_HOME/nix/nix.conf"
store = $STORE_LOC
experimental-features = nix-command flakes
warn-dirty = false
EOF
fi

echo "-- Please restart your session (logout & login again). After that, nix should be available in your path."
