#!/bin/bash
# resize_maple.sh

osascript <<EOF
display dialog "Starting window resize..."
tell application "System Events"
    set appName to "MapleStory Worlds"
    if exists (process appName) then
        tell process appName
            set size of window 1 to {1296, 759}
            set position of window 1 to {100, 100}
        end tell
        display dialog "Window resized successfully."
    else
        display dialog "App not found: " & appName
    end if
end tell
EOF

