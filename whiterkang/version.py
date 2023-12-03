# Copyright (C) 2022 by BubbalooTeam
#


from sys import version_info
from subprocess import run
from hydrogram import __version__

def check_version():
    try:
        __version__ = (
            run(["git", "rev-list", "--count", "HEAD"], capture_output=True).stdout.decode("utf-8").strip()
        )
        __commit__ = (
            run(["git", "rev-parse", "--short", "HEAD"], capture_output=True)
            .stdout.decode("utf-8")
            .strip()
        )
        return "v{} ({})".format(__version__, __commit__)
    except Exception:
        return "N/A"


__WhiterX_version__ = check_version()
__python_version__ = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"
__pyro_version__ = __version__
