#!/bin/bash

# Keyboard layout indicator for Waybar on Hyprland
# Reads layout state via hyprctl JSON API to bypass known IPC parsing bugs
# with device names containing special characters (parentheses, periods, etc.)
#
# Dependencies: hyprctl, jq, socat
#
# Usage:
#   1. Find your keyboard name:  hyprctl devices -j | jq '.keyboards[] | .name'
#   2. Set KEYBOARD below (or pass as $1)
#   3. Add as a Waybar custom module (see README.md)

KEYBOARD="${1:-at-translated-set-2-keyboard}"
SOCKET="$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock"

get_layout() {
    local keymap
    keymap=$(hyprctl devices -j | jq -r --arg kb "$KEYBOARD" \
        '.keyboards[] | select(.name == $kb) | .active_keymap')

    case "$keymap" in
        *English*)    printf '{"text": "EN", "tooltip": "English (US)", "class": "en"}\n' ;;
        *Ukrainian*)  printf '{"text": "UA", "tooltip": "Ukrainian", "class": "ua"}\n' ;;
        *Russian*)    printf '{"text": "RU", "tooltip": "Russian", "class": "ru"}\n' ;;
        *German*)     printf '{"text": "DE", "tooltip": "German", "class": "de"}\n' ;;
        *French*)     printf '{"text": "FR", "tooltip": "French", "class": "fr"}\n' ;;
        *Spanish*)    printf '{"text": "ES", "tooltip": "Spanish", "class": "es"}\n' ;;
        *Polish*)     printf '{"text": "PL", "tooltip": "Polish", "class": "pl"}\n' ;;
        *Czech*)      printf '{"text": "CZ", "tooltip": "Czech", "class": "cz"}\n' ;;
        *Danish*)     printf '{"text": "DK", "tooltip": "Danish", "class": "dk"}\n' ;;
        *Japanese*)   printf '{"text": "JA", "tooltip": "Japanese", "class": "ja"}\n' ;;
        *Korean*)     printf '{"text": "KO", "tooltip": "Korean", "class": "ko"}\n' ;;
        *Chinese*)    printf '{"text": "ZH", "tooltip": "Chinese", "class": "zh"}\n' ;;
        *Portuguese*) printf '{"text": "PT", "tooltip": "Portuguese", "class": "pt"}\n' ;;
        *Italian*)    printf '{"text": "IT", "tooltip": "Italian", "class": "it"}\n' ;;
        *Dutch*)      printf '{"text": "NL", "tooltip": "Dutch", "class": "nl"}\n' ;;
        *Swedish*)    printf '{"text": "SE", "tooltip": "Swedish", "class": "se"}\n' ;;
        *Norwegian*)  printf '{"text": "NO", "tooltip": "Norwegian", "class": "no"}\n' ;;
        *Finnish*)    printf '{"text": "FI", "tooltip": "Finnish", "class": "fi"}\n' ;;
        *Turkish*)    printf '{"text": "TR", "tooltip": "Turkish", "class": "tr"}\n' ;;
        *Arabic*)     printf '{"text": "AR", "tooltip": "Arabic", "class": "ar"}\n' ;;
        *Hebrew*)     printf '{"text": "HE", "tooltip": "Hebrew", "class": "he"}\n' ;;
        *Greek*)      printf '{"text": "GR", "tooltip": "Greek", "class": "gr"}\n' ;;
        *Romanian*)   printf '{"text": "RO", "tooltip": "Romanian", "class": "ro"}\n' ;;
        *Hungarian*)  printf '{"text": "HU", "tooltip": "Hungarian", "class": "hu"}\n' ;;
        *Bulgarian*)  printf '{"text": "BG", "tooltip": "Bulgarian", "class": "bg"}\n' ;;
        *Serbian*)    printf '{"text": "SR", "tooltip": "Serbian", "class": "sr"}\n' ;;
        *Croatian*)   printf '{"text": "HR", "tooltip": "Croatian", "class": "hr"}\n' ;;
        *Slovak*)     printf '{"text": "SK", "tooltip": "Slovak", "class": "sk"}\n' ;;
        "")           printf '{"text": "??", "tooltip": "Unknown", "class": "unknown"}\n' ;;
        *)            printf '{"text": "%s", "tooltip": "%s"}\n' "${keymap:0:2}" "$keymap" ;;
    esac
}

# Print initial layout state
get_layout

# Listen for layout change events on Hyprland IPC socket
# When activelayout event fires, debounce rapid toggles then query actual state
socat -u UNIX-CONNECT:"$SOCKET" - 2>/dev/null | while read -r line; do
    if [[ "$line" == activelayout* ]]; then
        sleep 0.15
        get_layout
    fi
done
