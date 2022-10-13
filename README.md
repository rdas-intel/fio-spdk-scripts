# fio-spdk-scripts
#CMD to run from libaio sheet in spreadsheet

python Io_test.py --test_case_sheet libaio --test_case_xls SPR_storage_spdk.xlsx --fio_runtime 60


#CMD to run SPDK cases


python Io_test.py --test_case_sheet Fio_spdk --fio_runtime 120


There also two simple bash script added to
#spdk
run_16spdk.sh
#libaio
run_libbaio_fio.sh
