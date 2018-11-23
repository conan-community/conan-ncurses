#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from conans import tools
from cpt.packager import ConanMultiPackager


if __name__ == "__main__":

    docker_entry_script = None
    if tools.os_info.is_linux:
        docker_entry_script = "sudo apt-get -qq update && sudo apt-get install -y --no-install-recommends xterm && export TERM=xterm"

    builder = ConanMultiPackager(docker_entry_script=docker_entry_script)
    builder.add_common_builds(pure_c=True)
    builder.update_build_if(lambda bool: True, new_options={"ncurses:with_cpp": False})
    builder.add_common_builds(pure_c=False)
    builder.run()
