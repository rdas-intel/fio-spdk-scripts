#/bin/bash
echo 3 > /proc/sys/vm/drop_caches && swapoff -a && swapon -a && printf '\n%s\n' 'Ram-cache and Swap Cleared'
sleep 1
echo "running FIO"
sleep 2
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme4n1 &
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme5n1 &
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme6n1 &
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme7n1 &
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme8n1 &
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme9n1 &
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme10n1 &
fio --name=random-writers --ioengine=libaio --iodepth=16 --rw=read --bs=128k --direct=1 --size=32G --numjobs=2 --filename=/dev/nvme11n1 &
