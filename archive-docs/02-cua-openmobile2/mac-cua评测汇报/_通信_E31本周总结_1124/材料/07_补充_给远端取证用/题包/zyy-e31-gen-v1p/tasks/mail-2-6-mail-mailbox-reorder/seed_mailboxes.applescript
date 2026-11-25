tell application "Mail"
    repeat with mboxName in {"E31-Alpha", "E31-Beta", "E31-Gamma"}
        set nameText to (mboxName as text)
        if not (exists mailbox nameText) then
            make new mailbox with properties {name:nameText}
        end if
    end repeat
end tell