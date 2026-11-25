tell application "Mail"
	set acct to first account
	set addr to item 1 of (email addresses of acct)
	try
		delete (every message of drafts mailbox whose subject contains "E31-MAIL-2-4-REPLY")
	end try
	set m to make new outgoing message with properties {subject:"E31-MAIL-2-4-REPLY", content:"E31 seed message for reply task.", visible:false}
	tell m to make new to recipient at end of to recipients with properties {address:addr}
	send m
end tell
