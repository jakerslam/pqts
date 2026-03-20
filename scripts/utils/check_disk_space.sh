#!/bin/bash
#
# Disk Space Monitoring Utility for Protheus Trading System
#
# Description:
#   Monitors disk usage across critical mount points and alerts
#   when thresholds are exceeded. Designed for operational health
#   checks and proactive capacity planning.
#
# Usage:
#   ./check_disk_space.sh [--warning N] [--critical N] [--json]
#
# Author: Rohan Kapoor
# Last Updated: March 20, 2026
#

set -euo pipefail

# Default thresholds
WARNING_THRESHOLD=85
CRITICAL_THRESHOLD=95
OUTPUT_JSON=false

# Critical mount points for trading operations
MOUNT_POINTS=(
    "/"
    "/var/log"
    "/data"
    "/tmp"
)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --warning)
            WARNING_THRESHOLD="$2"
            shift 2
            ;;
        --critical)
            CRITICAL_THRESHOLD="$2"
            shift 2
            ;;
        --json)
            OUTPUT_JSON=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--warning N] [--critical N] [--json]"
            echo ""
            echo "Options:"
            echo "  --warning N   Warning threshold percentage (default: 85)"
            echo "  --critical N  Critical threshold percentage (default: 95)"
            echo "  --json        Output results as JSON"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Track overall status
OVERALL_STATUS="OK"
ALERT_COUNT=0

# Collect metrics for each mount point
declare -A MOUNT_USAGE
declare -A MOUNT_SIZE
declare -A MOUNT_STATUS

for mount in "${MOUNT_POINTS[@]}"; do
    # Skip if mount doesn't exist
    if [[ ! -d "$mount" ]]; then
        continue
    fi
    
    # Get usage percentage (strip % sign)
    usage=$(df -h "$mount" | awk 'NR==2 {print $5}' | sed 's/%//')
    size=$(df -h "$mount" | awk 'NR==2 {print $2}')
    available=$(df -h "$mount" | awk 'NR==2 {print $4}')
    
    MOUNT_USAGE[$mount]=$usage
    MOUNT_SIZE[$mount]=$size
    
    # Determine status
    if [[ $usage -ge $CRITICAL_THRESHOLD ]]; then
        MOUNT_STATUS[$mount]="CRITICAL"
        OVERALL_STATUS="CRITICAL"
        ((ALERT_COUNT++))
    elif [[ $usage -ge $WARNING_THRESHOLD ]]; then
        MOUNT_STATUS[$mount]="WARNING"
        if [[ "$OVERALL_STATUS" != "CRITICAL" ]]; then
            OVERALL_STATUS="WARNING"
        fi
        ((ALERT_COUNT++))
    else
        MOUNT_STATUS[$mount]="OK"
    fi
done

# Output results
if [[ "$OUTPUT_JSON" == true ]]; then
    # JSON output for programmatic consumption
    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"overall_status\": \"$OVERALL_STATUS\","
    echo "  \"thresholds\": {"
    echo "    \"warning\": $WARNING_THRESHOLD,"
    echo "    \"critical\": $CRITICAL_THRESHOLD"
    echo "  },"
    echo "  \"mounts\": {"
    
    first=true
    for mount in "${MOUNT_POINTS[@]}"; do
        if [[ -v MOUNT_USAGE[$mount] ]]; then
            [[ "$first" == false ]] && echo ","
            first=false
            echo -n "    \"$mount\": {"
            echo -n "\"usage_percent\": ${MOUNT_USAGE[$mount]}, "
            echo -n "\"total_size\": \"${MOUNT_SIZE[$mount]}\", "
            echo -n "\"status\": \"${MOUNT_STATUS[$mount]}\""
            echo -n "}"
        fi
    done
    echo ""
    echo "  }"
    echo "}"
else
    # Human-readable output
    echo "Disk Space Check - $(date)"
    echo "================================"
    echo ""
    printf "%-20s %8s %8s %12s\n" "Mount Point" "Usage%" "Total" "Status"
    printf "%-20s %8s %8s %12s\n" "--------------------" "--------" "--------" "------------"
    
    for mount in "${MOUNT_POINTS[@]}"; do
        if [[ -v MOUNT_USAGE[$mount] ]]; then
            status="${MOUNT_STATUS[$mount]}"
            # Color-code status (if terminal supports it)
            if [[ -t 1 ]]; then
                case $status in
                    "CRITICAL") status="\033[91m$status\033[0m" ;;
                    "WARNING") status="\033[93m$status\033[0m" ;;
                    "OK") status="\033[92m$status\033[0m" ;;
                esac
            fi
            printf "%-20s %8s %8s %12b\n" "$mount" "${MOUNT_USAGE[$mount]}%" "${MOUNT_SIZE[$mount]}" "$status"
        fi
    done
    
    echo ""
    echo "Overall Status: $OVERALL_STATUS"
    
    if [[ $ALERT_COUNT -gt 0 ]]; then
        echo ""
        echo "Alerts: $ALERT_COUNT mount(s) above threshold"
        echo ""
        echo "Recommended Actions:"
        echo "  - Review log rotation settings: ./scripts/utils/rotate_logs.sh --dry-run"
        echo "  - Check for large temporary files: find /tmp -type f -size +100M"
        echo "  - Consider archiving old data to cold storage"
    fi
fi

# Exit with appropriate code for monitoring systems
if [[ "$OVERALL_STATUS" == "CRITICAL" ]]; then
    exit 2
elif [[ "$OVERALL_STATUS" == "WARNING" ]]; then
    exit 1
else
    exit 0
fi
