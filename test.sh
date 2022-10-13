#/bin/bash

/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 2 NA 0000.06.00.0 256k NA read NA 1 NA 5 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 3 NA 0000.07.00.0 256k NA read NA 1 NA 6 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 4 NA 0000.08.00.0 256k NA read NA 1 NA 7 &
/home/jason/data/ml/storage_io/Storage/run_fio_case.sh fio_spdk 5 NA 0000.09.00.0 256k NA read NA 1 NA 8 &

