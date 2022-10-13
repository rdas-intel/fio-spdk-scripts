FIO_RUNTIME_DEFAULT=90
if test -z $1; then export ENV_FIO_RUNTIME=$FIO_RUNTIME_DEFAULT ; else export ENV_FIO_RUNTIME=$1 ; fi
#export ENV_FIO_RUNTIME=90
run_fio_case.sh fio_nvme_reset
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 2 numactl##-m#0# /dev/nvme0n1 128k 8 read NA 128 NA 1 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 3 numactl##-m#0# /dev/nvme1n1 128k 8 read NA 128 NA 2 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 4 numactl##-m#0# /dev/nvme2n1 128k 8 read NA 128 NA 3 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 5 numactl##-m#0# /dev/nvme3n1 128k 8 read NA 128 NA 4 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 6 numactl##-m#0# /dev/nvme4n1 128k 8 read NA 128 NA 5 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 7 numactl##-m#0# /dev/nvme5n1 128k 8 read NA 128 NA 6 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 8 numactl##-m#0# /dev/nvme6n1 128k 8 read NA 128 NA 7 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 9 numactl##-m#0# /dev/nvme7n1 128k 8 read NA 128 NA 8 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 10 numactl##-m#0# /dev/nvme8n1 128k 8 read NA 128 NA 9 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 11 numactl##-m#0 /dev/nvme9n1 128k 8 read NA 128 NA 10 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 12 numactl##-m#0 /dev/nvme10n1 128k 8 read NA 128 NA 11 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 13 numactl##-m#0 /dev/nvme11n1 128k 8 read NA 128 NA 12 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 14 numactl##-m#0 /dev/nvme12n1 128k 8 read NA 128 NA 13 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 15 numactl##-m#0 /dev/nvme13n1 128k 8 read NA 128 NA 14 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 16 numactl##-m#0 /dev/nvme14n1 128k 8 read NA 128 NA 15 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_libaio 17 numactl##-m#0 /dev/nvme15n1 128k 8 read NA 128 NA 16
