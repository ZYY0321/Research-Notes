import json, copy
import evaluation
import fixturelib as F


def with_dump(base, dump):
    p = copy.deepcopy(base)
    for check in p["checks"]:
        check["dump"] = dump
    return p


def main():
    cases = []
    base = copy.deepcopy(evaluation.PARAMS)

    empty = with_dump(base, "")
    cases.append(F.case("empty", empty, 0))

    shortcut = with_dump(base, "SUBJECT=E31-MAIL24-GROUP\nBODY=\nTO=\nATTACH=\n----\n")
    cases.append(F.case("shortcut", shortcut, 0))

    good_dump = "SUBJECT=E31-MAIL24-GROUP\nBODY=\nTO=e31.alice@example.com, e31.bob@example.com\nATTACH=\n----\n"
    good = with_dump(base, good_dump)
    cases.append(F.case("reference", good, 1))

    near_dump = "SUBJECT=E31-MAIL24-GROUP\nBODY=\nTO=E31 Team\nATTACH=\n----\n"
    near = with_dump(base, near_dump)
    cases.append(F.case("near_miss", near, 0))

    swapped = copy.deepcopy(base)
    for check in swapped["checks"]:
        check["subject"] = "E31-OTHER"
    swapped = with_dump(swapped, good_dump)
    cases.append(F.case("param_swap", swapped, 0))

    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
