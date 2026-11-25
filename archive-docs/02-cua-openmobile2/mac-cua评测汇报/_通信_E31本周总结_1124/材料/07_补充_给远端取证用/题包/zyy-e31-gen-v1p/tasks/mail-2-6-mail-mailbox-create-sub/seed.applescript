tell application "Mail"
	if not (exists mailbox "E31P26") then
		make new mailbox with properties {name:"E31P26"}
	end if
	if (exists mailbox "E31P26/E31S26") then
		delete mailbox "E31P26/E31S26"
	end if
	if (exists mailbox "E31S26") then
		delete mailbox "E31S26"
	end if
end tell
