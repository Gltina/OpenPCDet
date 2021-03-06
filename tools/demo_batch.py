import os

import argparse
import glob
from pathlib import Path

import mayavi.mlab as mlab
import numpy as np
import torch

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import DatasetTemplate
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils
from visual_utils import visualize_utils as V


class DemoDataset(DatasetTemplate):
    def __init__(self, dataset_cfg, class_names, training=True, root_path=None, logger=None, ext='.bin'):
        """
        Args:
            root_path:
            dataset_cfg:
            class_names:
            training:
            logger:
        """
        super().__init__(
            dataset_cfg=dataset_cfg, class_names=class_names, training=training, root_path=root_path, logger=logger
        )
        self.root_path = root_path
        self.ext = ext
        data_file_list = glob.glob(str(root_path / f'*{self.ext}')) if self.root_path.is_dir() else [self.root_path]

        data_file_list.sort()
        self.sample_file_list = data_file_list

    def __len__(self):
        return len(self.sample_file_list)

    def __getitem__(self, index):
        if self.ext == '.bin':
            points = np.fromfile(self.sample_file_list[index], dtype=np.float32).reshape(-1, 4)
        elif self.ext == '.npy':
            points = np.load(self.sample_file_list[index])
        else:
            raise NotImplementedError

        input_dict = {
            'points': points,
            'frame_id': index,
        }

        data_dict = self.prepare_data(data_dict=input_dict)
        return data_dict


def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--cfg_file', type=str, default='cfgs/kitti_models/second.yaml',
                        help='specify the config for demo')
    parser.add_argument('--data_path', type=str, default='demo_data',
                        help='specify the point cloud directory')
    parser.add_argument('--ckpt', type=str, default=None, help='specify the pretrained model')
    parser.add_argument('--ext', type=str, default='.bin', help='specify the extension of your point cloud data file')

    args = parser.parse_args()

    cfg_from_yaml_file(args.cfg_file, cfg)

    return args, cfg


def get_all_data(folder_name):
    return os.listdir(folder_name)


def main():
    args, cfg = parse_config()
    logger = common_utils.create_logger()
    logger.info('-----------------Quick Demo of OpenPCDet-------------------------')
    demo_dataset = DemoDataset(
        dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, training=False,
        root_path=Path(args.data_path), ext=args.ext, logger=logger
    )
    logger.info(f'Total number of samples: \t{len(demo_dataset)}')
    data_name_list = demo_dataset.sample_file_list
    # print(data_name_list)
    print('evaluation data size=', len(data_name_list))

    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=demo_dataset)
    model.load_params_from_file(filename=args.ckpt, logger=logger, to_cpu=True)
    model.cuda()
    model.eval()

    ckpt_filename=args.ckpt
    check_point_number = ckpt_filename[ckpt_filename.find('epoch_')+6:ckpt_filename.find('.pth')]
    save_dir = 'evaluation_{}'.format(check_point_number)
    
    if not os.path.exists(save_dir):
        print('no evaluation directory, created {}'.format(save_dir))
        os.mkdir(save_dir)

    with torch.no_grad():
        for idx, data_dict in enumerate(demo_dataset):
            # logger.info(f'Visualized sample index: \t{idx + 1}')
            logger.info(f'Detecte sample: \t{data_name_list[idx]}')
            data_dict = demo_dataset.collate_batch([data_dict])
            load_data_to_gpu(data_dict)
            pred_dicts, _ = model.forward(data_dict)

            # print(pred_dicts)
            # print(data_dict)
            # print(type(pred_dicts[0]['pred_boxes']))
            # print(pred_dicts[0]['pred_boxes'])
        
            # get predicted box
            res = pred_dicts[0]['pred_boxes'].cpu().numpy().round(8)
            print (type(res))

            # get labels's name
            ref_labels=pred_dicts[0]['pred_labels']
            ref_labels = ref_labels.cpu().numpy()
            ref_labels_text = ['Socket', 'Plug']
            new_ref_labels = []
            for r_f in ref_labels:
                new_ref_labels.append(ref_labels_text[r_f-1])
            print (new_ref_labels)

            save_filename = data_name_list[idx]
            save_path = save_dir + '/' + save_filename[save_filename.rfind('/')+1:].replace('.bin','.txt')

            with open(save_path, 'w') as res_f:
                for r_f_i, r_f in enumerate(new_ref_labels):
                    res_f.write(r_f + ' ')
                    for item in res[r_f_i]:
                        res_f.write(str(item) + ' ')
                    res_f.write('\n')
            # exit(1)
            # np.savetxt(save_path, res, fmt='%.08f')
            # test_f.writelines(pred_dicts[0]['pred_boxes'])

            # V.draw_scenes(
            #     points=data_dict['points'][:, 1:], ref_boxes=pred_dicts[0]['pred_boxes'],
            #     ref_scores=pred_dicts[0]['pred_scores'], ref_labels=pred_dicts[0]['pred_labels']
            # )
            # mlab.show(stop=True)

    logger.info('Demo done.')


if __name__ == '__main__':
    main()
