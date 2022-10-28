#!/bin/bash

#日志自动清理脚本
PATH="/var/log"

MODULES=("camel" "defender" "controller" "ros_solver" "IDoo" "nav" "ros_plc" "plc_core")

echo "Start to clean up logs!"

for path in ${MODULES[*]}
do
    LOGDIR="${PATH}/${path}"
    
    if [ -d ${LOGDIR} ]; 
    then
        echo "${LOGDIR} clean up!!"
        
        /bin/rm -r ${LOGDIR}
    
    fi

done




