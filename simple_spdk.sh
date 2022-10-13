
FIO_RUNTIME_DEFAULT=90
if test -z $1; then export ENV_FIO_RUNTIME=$FIO_RUNTIME_DEFAULT ; else export ENV_FIO_RUNTIME=$1 ; fi
run_fio_case.sh fio_nvme_reset
PCI_ALLOWED='0000:06:00.0 0000:07:00.0 0000:08:00.0 0000:09:00.0 0000:7c:00.0 0000:7d:00.0 0000:7e:00.0 0000:7f:00.0 0000:a0:00.0 0000:a1:00.0 0000:a2:00.0 0000:a3:00.0 0000:c4:00.0 0000:c5:00.0 0000:c6:00.0 0000:c7:00.0 ' ./spdk/scripts/setup.sh
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 2 NA 0000.06.00.0 128k NA read NA 64 NA 6 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 3 NA 0000.07.00.0 128k NA read NA 64 NA 7 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 4 NA 0000.08.00.0 128k NA read NA 64 NA 8 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 5 NA 0000.09.00.0 128k NA read NA 64 NA 9 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 6 NA 0000.7c.00.0 128k NA read NA 64 NA 10 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 7 NA 0000.7d.00.0 128k NA read NA 64 NA 11 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 8 NA 0000.7e.00.0 128k NA read NA 64 NA 12 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 9 NA 0000.7f.00.0 128k NA read NA 64 NA 13 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 10 NA 0000.a0.00.0 128k NA read NA 64 NA 14 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 11 NA 0000.a1.00.0 128k NA read NA 64 NA 15 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 12 NA 0000.a2.00.0 128k NA read NA 64 NA 16 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 13 NA 0000.a3.00.0 128k NA read NA 64 NA 17 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 14 NA 0000.c4.00.0 128k NA read NA 64 NA 18 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 15 NA 0000.c5.00.0 128k NA read NA 64 NA 19 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 16 NA 0000.c6.00.0 128k NA read NA 64 NA 20 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 17 NA 0000.c7.00.0 128k NA read NA 64 NA 21
