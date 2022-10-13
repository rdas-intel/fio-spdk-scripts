#!/bin/bash

#pip install python-dateutil

#ENV_FIO_IOSTAT_LOG=TRUE # export ENV_FIO_IOSTAT_LOG=TRUE
#ENV_FIO_CPU_FREQUENCY_LOG=TRUE # 

#ENV_FIO_EMON=TRUE #as 
ENV_FIO_EMON="" # False

#ENV_FIO_PCM_IIO=TRUE #
ENV_FIO_PCM_IIO= #
#ENV_FIO_PCM_PCIE=TRUE #
ENV_FIO_PCM_PCIE= #

CASE_ROW=$2
NUMA_CTL_=$3
echo "Runing $0 $1 $2 $3 $4 $5 $6 $7 $8 $9 ${10} ${11}"

SPDK_DEFAULT=./spdk
FIO_DEFAULT=fio


NUMA_CTL=`echo ${NUMA_CTL_//#/ }`    # #==>empty

_fn=$4
FIO_BS=$5
FIO_NUMJOBS=$6
FIO_RW=$7
FIO_RWMIX=$8
FIO_IODEPTH=$9
FIO_ADDITIONAL_=${10}
FIO_ADDITIONAL=`echo ${FIO_ADDITIONAL_//#/ }`    # #==>empty
FIO_CPUS_ALLOWED=${11}


#get env settings
WORK_SPACE_DEFAULT=`pwd`
FIO_RUNTIME_DEFAULT=10
FIO_RAMPUP_DEFAULT=1
FIO_ENGINE_DEFAULT=sync
#FIO_ENGINE_DEFAULT=async=1 
FIO_IODEPTH_DEFAULT=1
FIO_OUTPUT_DEFAULT="--output-format=json"
FIO_OUTPUT_FILE_EXT=json
FIO_CPUS_ALLOWED_DEFAULT=NA 

FIO_CMD_LOG_FILE_NAME=fio_test_command.txt

if test -z ${FIO_CPUS_ALLOWED}; then    FIO_CPUS_ALLOWED=${FIO_CPUS_ALLOWED_DEFAULT} ; fi


if test -z ${ENV_WS_SPDK}; then    ENV_WS_SPDK=${SPDK_DEFAULT} ; fi
if test -z ${ENV_WS_FIO}; then    ENV_WS_FIO=${FIO_DEFAULT} ; fi


if test -z ${ENV_WORK_SPACE}; then    ENV_WORK_SPACE=${WORK_SPACE_DEFAULT} ; fi
WORK_SPACE=${ENV_WORK_SPACE}
if test -z ${ENV_FIO_RUNTIME}; then    ENV_FIO_RUNTIME=${FIO_RUNTIME_DEFAULT} ; fi
FIO_RUNTIME=${ENV_FIO_RUNTIME}
if test -z ${ENV_FIO_ENGINE}; then    ENV_FIO_ENGINE=${FIO_ENGINE_DEFAULT} ; fi

if test -z ${ENV_FIO_RAMPUP}; then    ENV_FIO_RAMPUP=${FIO_RAMPUP_DEFAULT} ; fi
FIO_RAMPUP=${ENV_FIO_RAMPUP}

#if test -z ${ENV_FIO_IODEPTH}; then    ENV_FIO_IODEPTH=${FIO_IODEPTH_DEFAULT} ; fi
#FIO_IODEPTH=${ENV_FIO_IODEPTH}

if [ "$ENV_FIO_OUTPUT"x = "JSON"x ]; then    ENV_FIO_OUTPUT=${FIO_OUTPUT_DEFAULT} ; else ENV_FIO_OUTPUT=""; FIO_OUTPUT_FILE_EXT=txt; fi
FIO_OUTPUT_S=${ENV_FIO_OUTPUT}


if  [ "$NUMA_CTL"x = "NA"x ]; then NUMA_CTL_S="";  else NUMA_CTL_S="$NUMA_CTL" ; fi   
if  [ "$FIO_RWMIX"x = "NA"x ]; then FIO_RWMIX_S="";  else FIO_RWMIX_S="-rwmixread=$FIO_RWMIX" ; fi  
if  [ "$FIO_ADDITIONAL"x = "NA"x ]; then FIO_ADDITIONAL_S="";  else FIO_ADDITIONAL_S=$FIO_ADDITIONAL ; fi
if  [ "$FIO_CPUS_ALLOWED"x = "NA"x ]; then FIO_CPUS_ALLOWED_S="";  else FIO_CPUS_ALLOWED_S="--cpus_allowed=${FIO_CPUS_ALLOWED}" ; fi

RUNTIME_S=runtime  
SPECIAL_RUNTIME=$(echo $FIO_ADDITIONAL | grep "${RUNTIME_S}")
if [[ "$SPECIAL_RUNTIME" != "" ]]
then
    RUNTIME_DEFAULT=""  #using runtime in addtional string
else
    RUNTIME_DEFAULT=--runtime=${FIO_RUNTIME}  #using runtime default
fi


RESULT_FOLDER=${WORK_SPACE}/_result
FULL_FIO_CMD_LOG_FILE_NAME=$RESULT_FOLDER/$FIO_CMD_LOG_FILE_NAME

# Enter into workspace folder and create the result folder
mkdir -p ${RESULT_FOLDER}
cd ${WORK_SPACE}
LOG_FILE=${RESULT_FOLDER}/_log.txt

function start_pcm_iio(){
    if [ "$ENV_FIO_PCM_IIO"x = "TRUE"x ]; then  
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then      
            pcm_iio_session=pcm_iio_recording
            pcm_iio_s_started=`tmux ls  | grep  ${pcm_iio_session} `  
            if  [ -z ${pcm_iio_s_started} ]; then 
            _pcm_iio_log_fn=$1
            #pcm_log_dir_name=`dirname ${_pcm_iio_log_fn} `
            #if [ ! -d ${pcm_log_dir_name} ]; then 
            #    mkdir -p ${pcm_log_dir_name}
            #fi
            rm -f ${_pcm_iio_log_fn} > /dev/null
            
            pcm_iio_session=pcm_iio_recording
            tmux new-session -d -s ${pcm_iio_session}
                tmux send-keys -t "${pcm_iio_session}:0" "pcm-iio 1.0 -csv=${_pcm_iio_log_fn}"  ENTER
            fi 
        fi
    fi
}
function stop_pcm_iio(){
    if [ "$ENV_FIO_PCM_IIO"x = "TRUE"x ]; then  
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then       
            #_pcm_iio_log_fn=$1
            tmux send-keys -t "${pcm_iio_session}:0" "C-c "  ENTER
            
            tmux kill-session -t  ${pcm_iio_session}
            echo " "
            echo " "
            echo "pcm_iio log is saved result to ${_pcm_iio_log_fn} "
            ls -lh ${_pcm_iio_log_fn}
            echo " "
        fi
    fi
}

function start_pcm_pcie(){
    if [ "$ENV_FIO_PCM_PCIE"x = "TRUE"x ]; then   
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then       
            pcm_pcie_s_started=`tmux ls  | grep  ${pcm_pcie_session} `
            if  [ -z ${pcm_pcie_s_started} ]; then 
                _pcm_pcie_log_fn=$1
                pcm_log_dir_name=`dirname ${_pcm_pcie_log_fn} `
                if [ ! -d ${pcm_log_dir_name} ]; then 
                    mkdir -p ${pcm_log_dir_name}
                fi
                rm -f ${_pcm_pcie_log_fn} > /dev/null
                pcm_pcie_session=pcm_pcie_recording        
                tmux new-session -d -s ${pcm_pcie_session}
                tmux send-keys -t "${pcm_pcie_session}:0" "pcm-pcie 1.0 -csv=${_pcm_pcie_log_fn}"  ENTER
            fi 
        fi
    fi
}
function stop_pcm_pcie(){
    if [ "$ENV_FIO_PCM_PCIE"x = "TRUE"x ]; then   
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then       
            _pcm_pcie_log_fn_=$1
            tmux send-keys -t "${pcm_pcie_session}:0" "C-c "  ENTER
            tmux kill-session -t  ${pcm_pcie_session}
            echo " "
            echo " "
            echo "pcm_pcie log is saved result to ${_pcm_pcie_log_fn_} "
            ls -lh ${_pcm_pcie_log_fn_}
            echo " "
        fi
    fi
}
#t_memory_size=`top -E g -n 1 | grep "GiB Mem :" | awk  '{print $4}'`
function start_emon(){
    if [ "$ENV_FIO_EMON"x = "TRUE"x ]; then  
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then       
            basic_dir_name=$WS_ROOT/_emon_result
            sub_dir=${paras}
            dir_name=$basic_dir_name/$sub_dir
            echo ""
            echo "###dir_name:  "$dir_name
            echo ""
            if [ ! -d ${dir_name} ]; then 
                mkdir -p ${dir_name}
            fi
            
            emon -i /opt/intel/sep/spr-events.txt > ${dir_name}/emon_0.out &
            pid=$!
        fi
    fi
}
function stop_emon(){
    if [ "$ENV_FIO_EMON"x = "TRUE"x ]; then 
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then       
            kill $pid
        fi
    fi
}

function start_cpu_frequency_watch(){
    if [ "$ENV_FIO_CPU_FREQUENCY_LOG"x = "TRUE"x ]; then   
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then   
            _fn=$1
            _cpu=$2
            rm -rf ${_fn}
            #iostat_pid=`ps -a | grep iostat | awk  '{print $1}'` | kill
            
            frequency_session=cpu_frequecny_recording
            tmux new-session -d -s ${frequency_session}
            window=${frequency_session}:0
            pane=${window}.0
            
            #iostat_recording.sh /tmp/isostate_log.txt  &
            #tmux send-keys -t "${frequency_session}:0" "watch -n 1 cpu_frequency_log.sh $_cpu /tmp/isostate_log.txt "  ENTER
            tmux send-keys -t "${frequency_session}:0" "watch -n 1 cpu_frequency_log.sh ${_cpu} ${_fn} "  ENTER
            
            #iostat_pid=`ps -a | grep iostat | awk  '{print $1}'`
        fi
    fi
}
function stop_cpu_frequency_watch(){
    if [ "$ENV_FIO_CPU_FREQUENCY_LOG"x = "TRUE"x ]; then   
        _fn=$1
        tmux send-keys -t "${frequency_session}:0" "C-c "  ENTER
        
        tmux kill-session -t  ${frequency_session}
        echo " "
        echo " "
        echo "iostate log is saved result to ${_fn} "
        ls -lh ${_fn}
        echo " "
    fi
}

function start_iostat(){
    if [ "$ENV_FIO_IOSTAT_LOG"x = "TRUE"x ]; then   
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then   
            _fn=$1
            rm -rf ${_fn}
            #iostat_pid=`ps -a | grep iostat | awk  '{print $1}'` | kill
            
            session=iostat_recording
            tmux new-session -d -s ${session}
            window=${session}:0
            pane=${window}.0
            
            #iostat_recording.sh /tmp/isostate_log.txt  &
            #tmux send-keys -t "${session}:0" "iostat_recording.sh /tmp/isostate_log.txt "  ENTER
            tmux send-keys -t "${session}:0" "iostat_recording.sh ${_fn} "  ENTER
        fi
        #iostat_pid=`ps -a | grep iostat | awk  '{print $1}'`
    fi
}
function stop_iostat(){
    if [ "$ENV_FIO_IOSTAT_LOG"x = "TRUE"x ]; then  
        if [ "$FIO_SIMULATION"x != "TRUE"x ]; then       
            _fn=$1
            tmux send-keys -t "${session}:0" "C-c "  ENTER
            
            tmux kill-session -t  ${session}
            echo " "
            echo " "
            echo "iostate log is saved result to ${_fn} "
            ls -lh ${_fn}
            echo " "
        fi
    fi
}
function Run_FIO_Case(){
    array=(${_fn//_/ }) 
    _extr_fn=${array[0]}
    FIO_FILENAME=`echo ${_extr_fn//-//}`

    #Set_FIO_Parameters

    FIO_NAME=xx   
    extr_fn=`echo ${FIO_FILENAME////-}`
    #paras=${CASE_ROW}_${extr_fn}_${FIO_BS}_${FIO_NUMJOBS}_${FIO_RW}_${FIO_RWMIX}
    paras=row_${CASE_ROW}   
        #_${FIO_NAME}
    paras2=${FIO_FILENAME}_${FIO_BS}_${FIO_NUMJOBS}_${FIO_RW}
        #_${FIO_NAME}
    fio_output_file=${RESULT_FOLDER}/${paras}.${FIO_OUTPUT_FILE_EXT}

        #--direct=1 --ioengine=libaio \
        #--direct=1 --ioengine=sync --fdatasync=1 \
        #--direct=1 --ioengine=${ENV_FIO_ENGINE} --fdatasync=1  \        


    default_settings="--iodepth=${FIO_IODEPTH} \
        --direct=1  --ioengine=libaio --sync=0  \
        --time_based ${RUNTIME_DEFAULT} \
        ${FIO_CPUS_ALLOWED_S} \
        --thread --cpus_allowed_policy=split \
        --group_reporting --ramp_time=${FIO_RAMPUP} \
        --allow_mounted_write=1   --size=32G   "
        
        #--allow_mounted_write=1 --size=%50 "        
        #--allow_mounted_write=1 --size=32G "	
    echo ${FIO_ADDITIONAL_S}
    parameters=" --numjobs=${FIO_NUMJOBS} --name=${FIO_NAME} --bs=${FIO_BS} --rw=${FIO_RW} --filename=${FIO_FILENAME} ${FIO_RWMIX_S} ${FIO_ADDITIONAL_S}"

    echo $default_settings
    echo $parameters    
    rm -f ${fio_output_file}
    
    fn_iostat=${fio_output_file}_iostat_log.txt
    start_iostat ${fn_iostat}

    fn_cpufrequency=${fio_output_file}_cpu_frequency_log_c_${FIO_CPUS_ALLOWED}.csv
    start_cpu_frequency_watch ${fn_cpufrequency} ${FIO_CPUS_ALLOWED}
    
    start_emon
    
     
    pcm_iio_log=${fio_output_file}_pcm_iio.csv
    start_pcm_iio $pcm_iio_log
    
    pcm_pcie_log=${fio_output_file}_pcm_pcie.csv
    start_pcm_pcie ${pcm_pcie_log}
    fio_cmd="${NUMA_CTL_S}  fio ${default_settings} ${parameters} ${FIO_OUTPUT_S} --output=${fio_output_file}  "
    #echo "FIO_COMMAND_LINE: "$paras" "$fio_cmd
    echo $paras" FIO_COMMAND_LINE: "$fio_cmd>>$FULL_FIO_CMD_LOG_FILE_NAME
    export FIO_RUNNING_CMD=$fio_cmd    
    if [ "$FIO_SIMULATION"x = "TRUE"x ]; then
        echo "Simulation mode: "$paras" "$fio_cmd

        exit 0
    else
        bash -c "${fio_cmd}"
    fi
    stop_emon
    stop_iostat ${fn_cpufrequency}
    
    stop_pcm_iio ${pcm_iio_log}
    stop_pcm_pcie ${pcm_pcie_log}  
    
    stop_cpu_frequency_watch    
    if [ ! -s $fio_output_file ]; then
        echo "$fio_output_file file size is 0!"
        exit 1
    fi

    if test -z ${FIO_OUTPUT}; then  cat ${fio_output_file} ; fi
    
    echo ""
    echo "Saved result to ${fio_output_file} "

}

function Run_SPDK_FIO(){


    #Set_FIO_Parameters

    paras=row_${CASE_ROW}   

    paras2=${FIO_FILENAME}_${FIO_BS}_${FIO_NUMJOBS}_${FIO_RW}

    fio_output_file=${RESULT_FOLDER}/${paras}.${FIO_OUTPUT_FILE_EXT}

    default_settings="--iodepth=${FIO_IODEPTH} \
        --direct=1 --ioengine=spdk --thread=1 \
        --time_based ${RUNTIME_DEFAULT} \
        --ramp_time=${FIO_RAMPUP} \
        ${FIO_CPUS_ALLOWED_S} \
        --group_reporting \
        	"	
    export SPDK_FILE_NAME="trtype=PCIe traddr=${_fn} ns=1"
    
    parameters=" --bs=${FIO_BS} --rw=${FIO_RW}  ${FIO_RWMIX_S} ${FIO_ADDITIONAL_S}"

    rm -f ${fio_output_file}

    if [ ! -f ${ENV_WS_FIO}/fio ];then   echo ${ENV_WS_FIO}/fio" does not exist" ;     exit 1 ;    fi
    if [ ! -f ${ENV_WS_SPDK}/build/fio/spdk_nvme ];then  echo ${ENV_WS_SPDK}/build/fio/spdk_nvme" does not exist" ;     exit 1 ;    fi    
    
    echo "export SPDK_FILE_NAME=\"trtype=PCIe  traddr=${_fn} ns=1 \" ; LD_PRELOAD=${ENV_WS_SPDK}/build/fio/spdk_nvme  ${ENV_WS_FIO}/fio ./spdk.fio ${default_settings} ${parameters} ${FIO_OUTPUT_S} --output=${fio_output_file}">>$FULL_FIO_CMD_LOG_FILE_NAME
    
    if [ "$FIO_SIMULATION"x != "TRUE"x ]; then   
    
        LD_PRELOAD=${ENV_WS_SPDK}/build/fio/spdk_nvme  ${ENV_WS_FIO}/fio ./spdk.fio ${default_settings} ${parameters} ${FIO_OUTPUT_S} --output=${fio_output_file}  

        if [ ! -s $fio_output_file ]; then
            echo "$fio_output_file file size is 0!"
            exit 1
        fi

        if test -z ${FIO_OUTPUT}; then  cat ${fio_output_file} ; fi
        
        echo ""
        echo "Saved result to ${fio_output_file} "    
    fi
}

function Reset_nvme(){
    ${ENV_WS_SPDK}/scripts/setup.sh reset
}
# Main functions
case $1 in 
    parse_result) #Set FIO parameters
        python ParseFioResult.py
    ;;  
   
    fio_libaio) #Set FIO parameters
        #echo "Running run_fio_case"
        Run_FIO_Case
    ;;   

    fio_spdk) 
        Run_SPDK_FIO
    ;; 
    fio_nvme_reset) 
        Reset_nvme
    ;; 
    fio_nvme_list) 
        all_nvme_device=`lspci -vv | grep "Non-Volatile memory controller" | awk '{print $1}'`
        for nvme in $all_nvme_device; do
            echo "0000:$nvme"
        done
    ;;      
    fio_nvme_set_up_for_spdk) 
        device_id=$2
        
        #PCI_BLOCKED="0000:5e:00.0" ${ENV_WS_SPDK}/scripts/setup.sh  
        #PCI_ALLOWED="0000:5e:00.0" ${ENV_WS_SPDK}/scripts/setup.sh     
        PCI_ALLOWED="${device_id}" ${ENV_WS_SPDK}/scripts/setup.sh             
    ;;
     
    fio_nvme_devices_warming_up)
        #dvices="nvme0n1 nvme1n1 nvme3n1 nvme4n1 nvme5n1 nvme6n1 nvme7n1 nvme8n1 nvme9n1"
        dvices="nvme0n1 nvme1n1 nvme2n1"
        echo $devices
        for d in $dvices ; do  
            time_=`date`
            echo " "
            echo " "            
            echo "Warming up $d ... started at ${time_}"
            python CFio.py  --device $d
            
        done
    ;;     
    
    *)
        echo ""
        echo ""   

    ;;
    esac
#echo "FIO done"
exit 0


