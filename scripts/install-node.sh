#!/bin/bash
# Install Node.js 22.14 (Nixpacks default 22.10 breaks Vite 8)
set -e

NODE_VERSION="22.14.0"

if command -v node &> /dev/null; then
  CURRENT_VERSION=$(node -v | sed 's/v//')
  if [ "$CURRENT_VERSION" = "$NODE_VERSION" ]; then
    echo "Node.js $NODE_VERSION is already installed"
    exit 0
  fi
fi

echo "Installing Node.js $NODE_VERSION..."

# Download and install Node.js
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
  ARCH="x64"
elif [ "$ARCH" = "aarch64" ]; then
  ARCH="arm64"
fi

curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${ARCH}.tar.xz" -o node.tar.xz
tar -xf node.tar.xz
rm node.tar.xz
mv "node-v${NODE_VERSION}-linux-${ARCH}" /usr/local/node
ln -sf /usr/local/node/bin/node /usr/local/bin/node
ln -sf /usr/local/node/bin/npm /usr/local/bin/npm
ln -sf /usr/local/node/bin/npx /usr/local/bin/npx

node -v
npm -v
