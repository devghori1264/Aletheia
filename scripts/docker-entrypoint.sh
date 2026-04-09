#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_NAME="$(basename "$0")"
readonly APP_DIR="${APP_HOME:-/app}"
readonly MANAGE_PY="${APP_DIR}/src/manage.py"

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Ensure environment variables are exported to sub-processes
export ALETHEIA_ENVIRONMENT="${ALETHEIA_ENVIRONMENT:-development}"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-aletheia.settings}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} ${SCRIPT_NAME}: $*"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} ${SCRIPT_NAME}: $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} ${SCRIPT_NAME}: $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} ${SCRIPT_NAME}: $*" >&2
}

initialize_directories() {
    log_info "Initializing temporary directories..."

    local -a required_dirs=(
        "/tmp/media"
        "/tmp/media/temp"
        "/tmp/uploads"
        "/tmp/processing"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done

    log_success "Temporary directories initialized"
}

run_database_migrations() {
    log_info "Running database migrations..."
    log_info "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}"

    # Debug: Check if detection migrations folder exists
    if [[ -d "/app/src/detection/migrations" ]]; then
        log_info "Detection migrations folder found:"
        ls -la /app/src/detection/migrations/ 2>&1 | sed 's/^/  /'
    else
        log_warn "Detection migrations folder NOT FOUND at /app/src/detection/migrations/"
    fi

    # Show migration plan
    log_info "Migration plan (first 30 lines):"
    python "$MANAGE_PY" migrate --plan 2>&1 | head -30 | sed 's/^/  /' || true

    # Run migrations with full output. Do not swallow failures.
    log_info "Executing migrations..."
    if ! python "$MANAGE_PY" migrate --noinput --verbosity=2; then
        log_error "Migration command failed"
        return 1
    fi

    # Verify required detection tables exist
    log_info "Verifying required detection tables were created..."
    if python "$MANAGE_PY" shell << 'PYEOF' 2>&1
from django.db import connection
required = {
    "detection_mediafile",
    "detection_analysis",
    "detection_report",
    "detection_analysisframe",
}

with connection.cursor() as cursor:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'detection_%' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}

missing = sorted(required - tables)
if missing:
    print("✗ ERROR: Missing required detection tables:")
    for table_name in missing:
        print(f"  • {table_name}")
    raise SystemExit(1)

print("✓ Required detection tables found:")
for table_name in sorted(tables):
    print(f"  • {table_name}")
PYEOF
    then
        log_success "Database migrations completed"
    else
        log_error "Database migrations verification failed"
        return 1
    fi
}

create_superuser_if_configured() {
    local username="${DJANGO_SUPERUSER_USERNAME:-}"
    local email="${DJANGO_SUPERUSER_EMAIL:-}"
    local password="${DJANGO_SUPERUSER_PASSWORD:-}"

    if [[ -z "$username" || -z "$email" || -z "$password" ]]; then
        log_info "Superuser environment variables not set - skipping admin user creation"
        log_info "To enable admin: set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD"
        return 0
    fi

    log_info "Creating superuser: $username..."

    if python "$MANAGE_PY" createsuperuser --noinput 2>&1; then
        log_success "Superuser '$username' created successfully"
    else
        log_info "Superuser may already exist (this is normal on hot restarts)"
    fi
}

verify_application_health() {
    log_info "Verifying application configuration..."

    if python "$MANAGE_PY" check --deploy 2>&1 | grep -v "System check identified"; then
        log_success "Django configuration verified"
    fi
}

print_startup_banner() {
    local fly_app="${FLY_APP_NAME:-local}"
    local fly_region="${FLY_REGION:-unknown}"
    local fly_alloc="${FLY_ALLOC_ID:-unknown}"

    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║     █████╗ ██╗     ███████╗████████╗██╗  ██╗███████╗██╗ █████╗               ║"
    echo "║    ██╔══██╗██║     ██╔════╝╚══██╔══╝██║  ██║██╔════╝██║██╔══██╗              ║"
    echo "║    ███████║██║     █████╗     ██║   ███████║█████╗  ██║███████║              ║"
    echo "║    ██╔══██║██║     ██╔══╝     ██║   ██╔══██║██╔══╝  ██║██╔══██║              ║"
    echo "║    ██║  ██║███████╗███████╗   ██║   ██║  ██║███████╗██║██║  ██║              ║"
    echo "║    ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═╝              ║"
    echo "║                                                                              ║"
    echo "║                    DEEPFAKE DETECTION PLATFORM                               ║"
    echo "║                                                                              ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║  App:     ${fly_app}                                                         "
    echo "║  Region:  ${fly_region}                                                      "
    echo "║  Alloc:   ${fly_alloc:0:12}...                                               "
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""
}

main() {
    print_startup_banner
    log_info "Starting Aletheia initialization sequence..."

    # Debug: log environment info
    log_info "ALETHEIA_ENVIRONMENT: ${ALETHEIA_ENVIRONMENT:-not set}"
    log_info "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-not set}"

    initialize_directories

    # Try to run migrations - this is CRITICAL
    log_info "Attempting to run database migrations..."
    if run_database_migrations; then
        log_success "Database initialization complete"
    else
        log_error "Database initialization failed - aborting startup"
        exit 1
    fi

    create_superuser_if_configured
    verify_application_health

    log_success "Initialization complete - starting application server"
    echo ""

    # Execute the CMD
    exec "$@"
}

main "$@"
