import json, tempfile, os
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        
        empty_path = os.path.join(directory, "mail-2-6-status.txt")
        cases.append(F.case("empty", params, 0))
        
        with open(empty_path, "w") as f:
            f.write("WRONG")
        cases.append(F.case("shortcut", params, 0))
        
        with open(empty_path, "w") as f:
            f.write("DELETED")
        cases.append(F.case("reference", params, 1))
        
        with open(empty_path, "w") as f:
            f.write("EXISTS")
        cases.append(F.case("near_miss", params, 0))
        
        other_params = dict(params)
        other_params["contains"] = "REMOVED"
        with open(empty_path, "w") as f:
            f.write("DELETED")
        cases.append(F.case("param_swap", other_params, 0))
    
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
