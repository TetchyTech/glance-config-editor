#!/bin/bash

# Restore original glance.yaml from initial backup
# Use this if you need to revert to your original configuration

set -e

echo "🔄 Glance Configuration Restore Script"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment to get config path
if [ -f "/opt/glance-editor/.env" ]; then
    source /opt/glance-editor/.env
else
    print_error ".env file not found. Cannot determine config path."
    exit 1
fi

BACKUP_DIR="/opt/glance-editor/backups"

# Find original backup
ORIGINAL_BACKUP=$(ls -1 ${BACKUP_DIR}/glance_original_backup_*.yaml 2>/dev/null | head -1)

if [ -z "$ORIGINAL_BACKUP" ]; then
    print_error "No original backup found!"
    print_status "Looking for files matching: ${BACKUP_DIR}/glance_original_backup_*.yaml"
    print_status "Available backups:"
    ls -la ${BACKUP_DIR}/*.yaml 2>/dev/null || echo "  No backups found"
    exit 1
fi

print_status "Found original backup: $(basename $ORIGINAL_BACKUP)"
print_status "Current config path: $GLANCE_CONFIG_PATH"

# Confirm restore
echo ""
print_warning "This will replace your current glance.yaml with the original backup."
read -p "Are you sure you want to continue? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_status "Restore cancelled."
    exit 0
fi

# Create a backup of current state before restoring
if [ -f "$GLANCE_CONFIG_PATH" ]; then
    print_status "Creating backup of current configuration..."
    CURRENT_BACKUP_NAME="glance_pre_restore_backup_$(date +%Y%m%d_%H%M%S).yaml"
    cp "$GLANCE_CONFIG_PATH" "${BACKUP_DIR}/$CURRENT_BACKUP_NAME"
    print_status "Current config backed up as: $CURRENT_BACKUP_NAME"
fi

# Restore original
print_status "Restoring original configuration..."
cp "$ORIGINAL_BACKUP" "$GLANCE_CONFIG_PATH"

# Restart glance-editor service if running
if systemctl is-active --quiet glance-editor; then
    print_status "Restarting glance-editor service..."
    systemctl restart glance-editor
fi

# Restart glance service if it exists
if systemctl list-unit-files | grep -q "glance.service"; then
    if systemctl is-active --quiet glance; then
        print_status "Restarting glance service..."
        systemctl restart glance
    fi
fi

print_status "✅ Original configuration restored successfully!"
echo ""
print_status "What was restored:"
echo "  📁 From: $(basename $ORIGINAL_BACKUP)"
echo "  📍 To: $GLANCE_CONFIG_PATH"
echo ""
print_status "Services restarted:"
echo "  🔄 glance-editor (if running)"
echo "  🔄 glance (if running)"
echo ""
print_warning "Your changes have been lost. The backup of your current config is saved as:"
echo "  📦 $CURRENT_BACKUP_NAME"