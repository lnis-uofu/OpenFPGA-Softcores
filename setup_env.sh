#!/bin/bash

# Make sure that file will be sourced to the root of the project
sourced=($_)
if [[ $sourced =~ "bash" ]] || [[ $sourced =~ "./" ]]; then
    echo "[ERROR] $0 must be sourced, not run." >> /dev/stderr
    exit 1
fi
if [ ! -d "${PWD}/.git" ] || [ ! -f "${PWD}/setup_env.sh" ]; then
    echo "[ERROR] You must go to the root directory where the 'setup_env.sh' file is located."
    return 1
fi

# OpenFPGA environment
if [ -z $OPENFPGA_PATH ]; then
    echo "[ERROR] 'OPENFPGA_PATH' environment variable not found!"
    echo "[INFO ] Source the 'openfpga.sh' first, before running soft-core simulations."
fi

# Project enviroment
export           PROJECT_PATH=$(pwd)
export     PROJECT_TASKS_PATH="${PROJECT_PATH}/fpga_archs"
export     PROJECT_TESTS_PATH="${PROJECT_PATH}/tests"
export     PROJECT_TOOLS_PATH="${PROJECT_PATH}/platform/tools"
export PROJECT_SOFTCORES_PATH="${PROJECT_PATH}/platform/softcores"

run-softcore () {
    ${PYTHON_EXEC} ${PROJECT_TOOLS_PATH}/run_softcore.py "$@"
}

report-yosys-vpr () {
    ${PYTHON_EXEC} ${PROJECT_TOOLS_PATH}/report_yosys_vpr.py "$@"
}

report-place-timing () {
    ${PYTHON_EXEC} ${PROJECT_TOOLS_PATH}/report_place_timing.py "$@"
}

report-route-paths () {
    ${PYTHON_EXEC} ${PROJECT_TOOLS_PATH}/report_route_paths.py "$@"
}

_run_softcore_completions () {
    local cur prev opts
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="-h --help -d --debug --device-layout --channel-width --cache-size --isa --run-list --run-dir"
    # optional arguments
    case ${prev} in
        --device-layout|--channel-width)
            opts="auto"
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        --cache-size)
            COMPREPLY=( $(compgen -- "${cur}") )
            return 0
            ;;
        --isa)
            opts="i im imc"
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        --run-list)
            opts=$(find ${PROJECT_TESTS_PATH}/*.csv|sed -e "s|${PROJECT_PATH}/||")
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        --run-dir)
            COMPREPLY=( $(compgen -o nospace -o dirnames -d -- "${cur}") )
            return 0
            ;;
    esac
    # positional arguments
    case ${COMP_CWORD} in
        1)
            opts=$(find ${PROJECT_SOFTCORES_PATH}/[^_]*.py|grep -oP '[^/]+\.py'|cut -f1 -d'.')
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            ;;
        2)
            opts=$(find ${PROJECT_TASKS_PATH}/*.conf|sed -e "s|${PROJECT_PATH}/||")
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            ;;
        *)
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            ;;
    esac
    return 0;
}
complete -F _run_softcore_completions run-softcore
