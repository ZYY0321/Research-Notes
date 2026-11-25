tell application "Contacts"
    set p1 to make new person with properties {first name:"Alice", last name:"E31"}
    make new email at end of emails of p1 with properties {label:"work", value:"alice.e31@example.com"}
    set p2 to make new person with properties {first name:"Bob", last name:"E31"}
    make new email at end of emails of p2 with properties {label:"work", value:"bob.e31@example.com"}
    save
end tell