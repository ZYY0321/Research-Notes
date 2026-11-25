set outDir to (POSIX path of (path to home folder)) & "Desktop/e31-newapps/out"
do shell script "mkdir -p " & quoted form of outDir
set outPath to outDir & "/mail-2-6-mail-mailbox-create-sub.txt"
set txt to ""
tell application "Mail"
	if (exists mailbox "E31P26") then set txt to txt & "MBOX=E31P26" & linefeed
	if (exists mailbox "E31P26/E31S26") then set txt to txt & "MBOX=E31P26/E31S26" & linefeed
	if (exists mailbox "E31S26") then set txt to txt & "MBOX=E31S26" & linefeed
end tell
set fileRef to open for access (POSIX file outPath) with write permission
set eof of fileRef to 0
write txt to fileRef
close access fileRef
