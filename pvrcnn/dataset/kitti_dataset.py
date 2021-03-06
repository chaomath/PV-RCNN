from tqdm import tqdm
import pickle
import numpy as np
from copy import deepcopy
import os.path as osp
from torch.utils.data import Dataset

from .kitti_utils import read_calib, read_label, read_velo


class KittiDataset(Dataset):

    def __init__(self, cfg, split):
        self.split = split
        self.rootdir = cfg.DATA.ROOTDIR
        self.load_annotations(cfg)
        self.cfg = cfg

    def __len__(self):
        return len(self.inds)

    def read_splitfile(self, cfg):
        fpath = osp.join(cfg.DATA.SPLITDIR, f'{self.split}.txt')
        self.inds = np.loadtxt(fpath, dtype=np.int32).tolist()

    def try_read_cached_annotations(self, cfg):
        fpath = osp.join(cfg.DATA.CACHEDIR, f'{self.split}.pkl')
        if not osp.isfile(fpath):
            return False
        print('Found cached annotations.')
        with open(fpath, 'rb') as f:
            self.annotations = pickle.load(f)
        return True

    def cache_annotations(self, cfg):
        fpath = osp.join(cfg.DATA.CACHEDIR, f'{self.split}.pkl')
        with open(fpath, 'wb') as f:
            pickle.dump(self.annotations, f)

    def create_anno(self, idx, cfg):
        velo_path = osp.join(cfg.DATA.ROOTDIR, 'velodyne_reduced', f'{idx:06d}.bin')
        calib = read_calib(osp.join(cfg.DATA.ROOTDIR, 'calib', f'{idx:06d}.txt'))
        objects = read_label(osp.join(cfg.DATA.ROOTDIR, 'label_2', f'{idx:06d}.txt'))
        annotation = dict(velo_path=velo_path, calib=calib, objects=objects, idx=idx)
        return annotation

    def load_annotations(self, cfg):
        self.read_splitfile(cfg)
        if self.try_read_cached_annotations(cfg):
            return
        print('Generating annotations...')
        self.annotations = dict()
        for idx in tqdm(self.inds):
            self.annotations[idx] = self.create_anno(idx, cfg)
        print('Done.')
        self.cache_annotations(cfg)

    def make_simple_object(self, obj, calib):
        xyz = calib.R0 @ obj.t
        xyz = calib.C2V @ np.r_[xyz, 1]
        wlh = np.r_[obj.w, obj.l, obj.h]
        rz = np.r_[-obj.ry]
        box = np.r_[xyz, wlh, rz]
        obj = dict(box=box,  cls_id=obj.cls_id)
        return obj

    def stack_boxes(self, item):
        boxes = np.stack([obj['box'] for obj in item['objects']])
        class_ids = np.r_[[obj['cls_id'] for obj in item['objects']]]
        item.update(dict(boxes=boxes, class_ids=class_ids))

    def drop_keys(self, item):
        for key in ['velo_path', 'objects', 'calib']:
            item.pop(key)

    def filter_bad_boxes(self, item):
        xyz, wlh, _ = np.split(item['boxes'], [3, 6], axis=1)
        class_ids = item['class_ids'][:, None]
        lower, upper = np.split(self.cfg.GRID_BOUNDS, [3])
        keep = ((xyz >= lower) & (xyz <= upper) &
            (class_ids != -1) & (wlh > 0)).all(1)
        item['boxes'] = item['boxes'][keep]
        item['class_ids'] = item['class_ids'][keep]

    def __getitem__(self, idx):
        idx = self.inds[idx]
        item = deepcopy(self.annotations[idx])
        item['points'] = read_velo(item['velo_path'])
        item['objects'] = [self.make_simple_object(
            obj, item['calib']) for obj in item['objects']]
        self.stack_boxes(item)
        if self.split == 'train':
            self.filter_bad_boxes(item)
        self.drop_keys(item)
        return item
