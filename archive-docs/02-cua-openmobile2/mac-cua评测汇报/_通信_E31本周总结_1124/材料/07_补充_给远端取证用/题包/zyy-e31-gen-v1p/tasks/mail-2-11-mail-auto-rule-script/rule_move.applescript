using terms from application "Mail"
	on perform mail action with messages theMessages for rule theRule
		tell application "Mail"
			repeat with eachMessage in theMessages
				move eachMessage to drafts mailbox
			end repeat
		end tell
	end perform mail action with messages
end using terms from
