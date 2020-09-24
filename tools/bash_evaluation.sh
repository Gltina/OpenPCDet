
iteration="10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190 200 210 220 230 240 250"

count=1
for i in $iteration; do
    echo "[$count]checkpoint_epoch_$i evaluation";
    python3 demo_batch.py --cfg_file cfgs/kitti_models/pv_rcnn_fine.yaml --ckpt ../output/kitti_models/pv_rcnn_fine/default/ckpt/checkpoint_epoch_$i.pth --data_path ../../../evaluation_data_fine/data/
    i=$((i+1));
done
