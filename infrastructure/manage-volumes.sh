#!/bin/bash
# Volume management script for Fly.io
# Manages persistent volumes defined in volumes.toml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VOLUMES_CONFIG="${SCRIPT_DIR}/volumes.toml"
DRY_RUN="${DRY_RUN:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Check if flyctl is available
check_flyctl() {
    if ! command -v flyctl &> /dev/null; then
        log_error "flyctl is not installed or not in PATH"
        log_info "Install it from: https://fly.io/docs/getting-started/installing-flyctl/"
        exit 1
    fi
}

# Extract value from TOML file for a given section and key
get_toml_value() {
    local section="$1"
    local key="$2"
    local file="$3"
    
    # Extract value after the key, handling quoted and unquoted values
    awk -v section="$section" -v key="$key" '
        BEGIN { in_section=0 }
        /^\[volumes\./ { 
            # Check if this section matches
            match($0, /\[volumes\.([^]]+)\]/, arr)
            if (arr[1] == section) {
                in_section=1
            } else {
                in_section=0
            }
        }
        in_section && $0 ~ "^[[:space:]]*" key "[[:space:]]*=" {
            gsub(/^[[:space:]]*[^=]+=[[:space:]]*["'\'']?/, "")
            gsub(/["'\'']?[[:space:]]*$/, "")
            gsub(/[[:space:]]*#.*$/, "")  # Remove inline comments
            gsub(/^[[:space:]]+|[[:space:]]+$/, "")  # Trim whitespace
            print
            exit
        }
    ' "$file"
}

# Check if volume exists
volume_exists() {
    local volume_name="$1"
    local app_name="$2"

    if flyctl volumes list --app "$app_name" --json 2>/dev/null | grep -q "\"name\":\"$volume_name\""; then
        return 0
    else
        return 1
    fi
}

# Get volume details
get_volume_info() {
    local volume_name="$1"
    local app_name="$2"

    flyctl volumes list --app "$app_name" --json 2>/dev/null | \
        jq -r ".[] | select(.name == \"$volume_name\") | \"\(.name)|\(.size_gb)|\(.region)\"" 2>/dev/null || echo ""
}

# Ensure volume exists (idempotent)
ensure_volume() {
    local volume_id="$1"
    local name="$2"
    local size_gb="$3"
    local region="$4"
    local app="$5"
    local required="${6:-true}"

    log_info "Checking volume: $name (app: $app)"

    if volume_exists "$name" "$app"; then
        local volume_info=$(get_volume_info "$name" "$app")
        if [[ -n "$volume_info" ]]; then
            IFS='|' read -r vol_name vol_size vol_region <<< "$volume_info"
            log_info "Volume '$name' already exists (size: ${vol_size}GB, region: $vol_region)"
            return 0
        fi
    fi

    log_info "Volume '$name' does not exist, creating..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN: Would create volume '$name' (${size_gb}GB) in region '$region' for app '$app'"
        return 0
    fi

    if flyctl volumes create "$name" --size "$size_gb" --region "$region" --app "$app"; then
        log_info "Successfully created volume '$name'"
        return 0
    else
        if [[ "$required" == "true" ]]; then
            log_error "Failed to create required volume '$name'"
            return 1
        else
            log_warn "Failed to create optional volume '$name', continuing..."
            return 0
        fi
    fi
}

# Ensure all volumes from config
ensure_all_volumes() {
    log_info "Ensuring all volumes from $VOLUMES_CONFIG"

    if [[ ! -f "$VOLUMES_CONFIG" ]]; then
        log_error "Volume configuration file not found: $VOLUMES_CONFIG"
        exit 1
    fi

    # Find all volume sections in TOML
    local volume_ids
    volume_ids=$(grep -E '^\[volumes\.' "$VOLUMES_CONFIG" | sed 's/^\[volumes\.\([^]]*\)\]/\1/')

    if [[ -z "$volume_ids" ]]; then
        log_warn "No volume sections found in $VOLUMES_CONFIG"
        return 0
    fi

    # Process each volume
    while IFS= read -r volume_id; do
        [[ -z "$volume_id" ]] && continue

        local name
        local size_gb
        local region
        local app
        local required

        name=$(get_toml_value "$volume_id" "name" "$VOLUMES_CONFIG")
        size_gb=$(get_toml_value "$volume_id" "size_gb" "$VOLUMES_CONFIG")
        region=$(get_toml_value "$volume_id" "region" "$VOLUMES_CONFIG")
        app=$(get_toml_value "$volume_id" "app" "$VOLUMES_CONFIG")
        required=$(get_toml_value "$volume_id" "required" "$VOLUMES_CONFIG")

        # Validate required fields
        if [[ -z "$name" ]] || [[ -z "$size_gb" ]] || [[ -z "$region" ]] || [[ -z "$app" ]]; then
            log_error "Invalid volume configuration for '$volume_id': missing required fields"
            log_error "  name: ${name:-MISSING}, size_gb: ${size_gb:-MISSING}, region: ${region:-MISSING}, app: ${app:-MISSING}"
            if [[ "${required:-true}" == "true" ]]; then
                exit 1
            else
                continue
            fi
        fi

        # Default required to true if not specified
        [[ -z "$required" ]] && required="true"

        ensure_volume "$volume_id" "$name" "$size_gb" "$region" "$app" "$required"
    done <<< "$volume_ids"
}

# List all volumes for app
list_volumes() {
    local app="${1:-}"

    if [[ -z "$app" ]]; then
        # Try to get app from fly.toml
        local fly_toml="${SCRIPT_DIR}/fly.toml"
        if [[ -f "$fly_toml" ]]; then
            app=$(grep -E "^app\s*=" "$fly_toml" | head -1 | sed 's/.*=\s*"\([^"]*\)".*/\1/' | sed 's/.*=\s*\([^ ]*\).*/\1/')
        fi
    fi

    if [[ -z "$app" ]]; then
        log_error "App name not specified and cannot be determined from fly.toml"
        exit 1
    fi

    log_info "Listing volumes for app: $app"
    flyctl volumes list --app "$app"
}

# Extend volume size
extend_volume() {
    local volume_name="$1"
    local new_size="$2"
    local app="${3:-}"

    if [[ -z "$app" ]]; then
        local fly_toml="${SCRIPT_DIR}/fly.toml"
        if [[ -f "$fly_toml" ]]; then
            app=$(grep -E "^app\s*=" "$fly_toml" | head -1 | sed 's/.*=\s*"\([^"]*\)".*/\1/' | sed 's/.*=\s*\([^ ]*\).*/\1/')
        fi
    fi

    if [[ -z "$app" ]]; then
        log_error "App name not specified and cannot be determined from fly.toml"
        exit 1
    fi

    log_info "Extending volume '$volume_name' to ${new_size}GB for app '$app'"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN: Would extend volume '$volume_name' to ${new_size}GB"
        return 0
    fi

    flyctl volumes extend "$volume_name" --size "$new_size" --app "$app"
}

# Main command handler
main() {
    local command="${1:-help}"

    check_flyctl

    case "$command" in
        ensure)
            ensure_all_volumes
            ;;
        list)
            list_volumes "${2:-}"
            ;;
        extend)
            if [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]]; then
                log_error "Usage: $0 extend <volume_name> <size_gb> [app_name]"
                exit 1
            fi
            extend_volume "$2" "$3" "${4:-}"
            ;;
        help|--help|-h)
            cat << EOF
Usage: $0 <command> [options]

Commands:
    ensure              Ensure all volumes from volumes.toml exist (idempotent)
    list [app_name]    List all volumes for app (defaults to app from fly.toml)
    extend <name> <size_gb> [app_name]
                       Extend volume to new size
    help               Show this help message

Environment Variables:
    DRY_RUN            Set to 'true' to perform dry-run (no actual changes)

Examples:
    $0 ensure
    $0 list
    $0 list gm-chatbot
    $0 extend chatbot_data 20
    DRY_RUN=true $0 ensure
EOF
            ;;
        *)
            log_error "Unknown command: $command"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"
