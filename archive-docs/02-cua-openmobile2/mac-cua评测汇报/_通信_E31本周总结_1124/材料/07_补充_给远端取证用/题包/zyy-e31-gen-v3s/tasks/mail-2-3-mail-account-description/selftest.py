import json, os, sqlite3, tempfile
import evaluation
import fixturelib as F


def fill(path, description, column="ZACCOUNTDESCRIPTION", bundle="com.apple.mail"):
    if os.path.lexists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE ZACCOUNT (Z_PK INTEGER, %s TEXT, ZNOTES TEXT, ZOWNINGBUNDLEID TEXT)" % column)
    conn.execute("INSERT INTO ZACCOUNT (Z_PK, %s, ZNOTES, ZOWNINGBUNDLEID) VALUES (1, ?, '', ?)" % column, (description, bundle))
    conn.commit()
    conn.close()


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        paths = params["paths"]
        if not paths or any(not str(path).startswith(directory) for path in paths):
            raise SystemExit("path escaped the temp directory")
        target = next(path for path in paths if path.endswith("Accounts4.sqlite"))
        for path in paths:
            F.remove(path)
        results.append(F.case("empty", params, 0))
        F.write(target, "E31 Research Mail")
        results.append(F.case("shortcut", params, 0))
        fill(target, "E31 Research Mail")
        results.append(F.case("reference", params, 1))
        fill(target, "E31 Research")
        results.append(F.case("near_miss", params, 0))
        if os.path.lexists(target):
            os.remove(target)
        conn = sqlite3.connect(target)
        conn.execute("CREATE TABLE ZACCOUNT (Z_PK INTEGER, ZNOTES TEXT, ZOWNINGBUNDLEID TEXT)")
        conn.execute("INSERT INTO ZACCOUNT VALUES (1, 'E31 Research Mail', 'com.apple.mail')")
        conn.commit()
        conn.close()
        results.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
