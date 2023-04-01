"""
Check version matches in multiple files
"""
import argparse
import toml
import re
import sys

EXAMPLES = """
example:
  Sync version of this program, and upgrade mismatches to the latest version.
    version-sync example.toml -u

"""


def process_config(config: dict, upgrade=False):
    upgrades = {}
    for package_name, package_config in config.items():
        upgrade_to = process_package(package_name, package_config, upgrade)
        if upgrade_to:
            upgrades[package_name] = upgrade_to

    if not upgrades:
        print("All versions match")
        return True

    if not upgrade:
        print("Run with -u to automatically upgrade the following packages:")
        for package_name, version in upgrades.items():
            print(f"{package_name} to {version}")

        return True

    assert False


def process_package(package_name: str, package_config: dict, upgrade=False):
    versions = {}  # file -> version string
    for file_config in package_config:
        file_name = file_config["file"]
        versions[file_name] = get_version_str(
            file_name,
            int(file_config["line"]),
            int(file_config["char"]),
            file_config["end"]
        )

    if not versions_match(versions):
        highest_version = get_highest_version(versions)
        if upgrade:
            print(f"Upgrading {package_name} to version {highest_version}")
            for file_config in package_config:
                file_name = file_config["file"]
                if versions[file_name] == highest_version:
                    continue
                print(f"  Updated {file_name}")
                set_version_str(
                    file_name,
                    int(file_config["line"]),
                    int(file_config["char"]),
                    file_config["end"],
                    highest_version
                )
            print()
            return None
        else:
            report_mismatch(package_name, versions)
            return highest_version
    return None


def get_version_str(file, line_number, position, end):
    """Get version string"""
    with open(file, "r", encoding="utf-8") as in_file:
        for i, line in enumerate(in_file):
            if i == line_number-1:
                if end:
                    end_index = line.find(end, position)
                    return line[position:end_index]

                return line[position:-1]  # remove \n


def set_version_str(file, line_number, position, end, version):
    """Set version string"""
    with open(file, "r", encoding="utf-8") as in_file:
        lines = in_file.readlines()
    line = lines[line_number-1]
    if end:
        end_index = line.find(end, position)

    if not end or end_index == -1:
        lines[line_number-1] = line[:position] + version + "\n"
    else:
        lines[line_number-1] = line[:position] + version + line[end_index:]

    with open(file, "w", encoding="utf-8") as out_file:
        out_file.writelines(lines)


def versions_match(versions):
    """Check if the versions are the same"""
    base = None
    for name in versions:
        if base is None:
            base = versions[name]
        elif base != versions[name]:
            return False
    return True


def report_mismatch(package, versions):
    """Print the mismatched versions"""
    print(f"Version mismatch found in {package}")
    for name in versions:
        print(f"{versions[name]} in {name}")
    print()


def get_highest_version(versions: dict):
    highest_version = None
    highest_str = None
    for v in versions.values():
        v_arr = list(map(int, re.findall(r"\d+", v)))
        if not v_arr:
            continue
        if highest_version is None:
            highest_version = v_arr
            highest_str = v
        else:
            for i in range(len(highest_version)):
                if i >= len(v_arr):
                    break
                if v_arr[i] > highest_version[i]:
                    highest_version = v_arr
                    highest_str = v
                    break
                elif v_arr[i] < highest_version[i]:
                    break
    return highest_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="version-sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Basic version sync checker",
        epilog=EXAMPLES)

    parser.add_argument(
        "input",
        nargs=1,
        help="Input TOML config file")

    parser.add_argument(
        "-u",
        "--upgrade",
        action="store_true",
        help="Automatically upgrade to the highest version number")

    args = parser.parse_args()

    with open(args.input[0], "r", encoding="utf-8") as f:
        config = toml.load(f)

    ok = process_config(config, upgrade=args.upgrade)
    sys.exit(0 if ok else 1)
