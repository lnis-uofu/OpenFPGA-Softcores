#!/bin/bash

[ -z $PROJECT_PATH ] && echo "[ERROR] source the 'setup_env.sh' first!" && exit 1

# look for specific run dirs
[ ! $# -ge 1 ] && echo "usage: $0 <search-path> <*tool-options*>" && exit 2
search_path="$1"
shift
options="$*"
echo "[INFO] Search path: '$search_path'"

# Output dir
output_dir="${PROJECT_PATH}/outputs/$(basename $search_path)"

# Report results
for run_dir in $(find $search_path -type d -name "run*"); do
    tool="${PROJECT_TOOLS_PATH}/report_route_paths.py"
    $tool $run_dir -o $output_dir/report_route_paths.$(basename $run_dir).csv $options
done
