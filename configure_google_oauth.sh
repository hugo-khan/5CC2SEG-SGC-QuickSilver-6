#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# configure_google_oauth.sh
# Helper script for macOS/Linux to create/update the .env file with Google
# OAuth credentials. Usage: ./configure_google_oauth.sh
# -----------------------------------------------------------------------------

cd "$(dirname "$0")"

echo "This script will create/overwrite the local .env file with your credentials."
echo
read -rp "Enter your Google Client ID (ends with .apps.googleusercontent.com): " GOOGLE_CLIENT_ID
read -rp "Enter your Google Client Secret: " GOOGLE_CLIENT_SECRET
echo

cat > .env <<EOF
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET
EOF

echo "Done! The .env file has been updated."
echo "Restart \"python manage.py runserver\" to pick up the new values."

