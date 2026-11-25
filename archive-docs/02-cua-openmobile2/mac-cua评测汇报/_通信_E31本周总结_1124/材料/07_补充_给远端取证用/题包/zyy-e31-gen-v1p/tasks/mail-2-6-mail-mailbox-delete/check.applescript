tell application "Mail"
	set mailboxNames to name of every mailbox
	if mailboxNames contains "E31DeleteTest" then
		do shell script "echo EXISTS > ~/Desktop/e31-newapps/out/mail-2-6-status.txt"
	else
		do shell script "echo DELETED > ~/Desktop/e31-newapps/out/mail-2-6-status.txt"
	end if
end tell