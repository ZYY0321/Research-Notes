tell application "Contacts"
    if not (exists group "E31 Team") then
        set g to make new group with properties {name:"E31 Team"}
        set p1 to make new person with properties {first name:"E31", last name:"Alice"}
        make new email at end of emails of p1 with properties {value:"e31.alice@example.com", label:"work"}
        set p2 to make new person with properties {first name:"E31", last name:"Bob"}
        make new email at end of emails of p2 with properties {value:"e31.bob@example.com", label:"work"}
        add p1 to g
        add p2 to g
        save
    end if
end tell