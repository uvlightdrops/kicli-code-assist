#!/bin/bash
export PYTHONPATH="/home/flow/dev_flow/flowpy:/home/flow/dev_flow/ki-core/src:/home/flow/dev_flow/yaml_cfg_wizard/src:$PYTHONPATH"
kicli-assist "$@"
