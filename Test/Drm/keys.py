# 15.06.26
# ruff: noqa: E402

import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(src_path)


from VibraVid.core.decryptor import KeysManager


# Real KIDs/KEYs shaped like the Apple TV+ command that surfaced the bug.
KID1, KEY1 = "000000005154b4fa6335202020202020", "9243ffb228cc0071e153bb1c32d76b0a"
KID2, KEY2 = "000000005154b4fa6332202020202020", "792cbaec5e8839faf59af244bd0d9c5e"
KID3, KEY3 = "000000005154b4fa6336202020202020", "cb055c589c95b271149f22c7fcd8edc8"

EXPECTED_3 = [f"{KID1}:{KEY1}", f"{KID2}:{KEY2}", f"{KID3}:{KEY3}"]


CASES = [
    (
        "single --key, pipe-joined (well formed)",
        [f"{KID1}:{KEY1}|{KID2}:{KEY2}|{KID3}:{KEY3}"],
        EXPECTED_3,
    ),
    (
        "single --key, MISSING '|' between 2nd and 3rd pair (the original crash input)",
        [f"{KID1}:{KEY1}|{KID2}:{KEY2}{KID3}:{KEY3}"],
        EXPECTED_3,
    ),
    (
        "repeated --key (argparse append list)",
        [f"{KID1}:{KEY1}", f"{KID2}:{KEY2}", f"{KID3}:{KEY3}"],
        EXPECTED_3,
    ),
    (
        "plain 'kid:key|kid:key' string",
        f"{KID1}:{KEY1}|{KID2}:{KEY2}",
        [f"{KID1}:{KEY1}", f"{KID2}:{KEY2}"],
    ),
    (
        "uppercase + dashed-UUID KID is normalised",
        ["00000000-5154-b4fa-6335-202020202020:" + KEY1.upper()],
        [f"{KID1}:{KEY1}"],
    ),
    (
        "whitespace / comma separated",
        f"{KID1}:{KEY1} , {KID2}:{KEY2}",
        [f"{KID1}:{KEY1}", f"{KID2}:{KEY2}"],
    ),
    (
        "duplicates are dropped",
        [f"{KID1}:{KEY1}", f"{KID1}:{KEY1}"],
        [f"{KID1}:{KEY1}"],
    ),
    (
        "(kid, key) tuple",
        (KID1, KEY1),
        [f"{KID1}:{KEY1}"],
    ),
    (
        "dict {'kid', 'key'}",
        {"kid": KID2, "key": KEY2},
        [f"{KID2}:{KEY2}"],
    ),
    (
        "re-ingesting a KeysManager is idempotent",
        KeysManager(EXPECTED_3),
        EXPECTED_3,
    ),
    (
        "empty / None yields no keys",
        None,
        [],
    ),
]


def main() -> None:
    failures = 0
    for label, value, expected in CASES:
        got = KeysManager(value).get_keys_list()
        ok = got == expected
        failures += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        if not ok:
            print(f"        input    : {value!r}")
            print(f"        expected : {expected}")
            print(f"        got      : {got}")

    # Helper methods also live on the class (no module-level key functions).
    assert KeysManager.is_zero_kid("0" * 32) is True
    assert KeysManager.is_zero_kid(KID1) is False
    assert KeysManager.normalize(f"{KID1}:{KEY1}") == [(KID1, KEY1)]

    print(f"\n{len(CASES) - failures}/{len(CASES)} cases passed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()