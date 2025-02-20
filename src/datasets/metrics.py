import os
import random
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import torch
import torchaudio
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

# from src.utils.io_utils import ROOT_PATH


class MetricsCalculatorDataset(Dataset):
    def __init__(self, dir_separated, dir_ground_truth, transform=None):
        """
        Arguments:
            dir (string): A path, root directory.
        """
        self.dir_separated = dir_separated
        self.dir_ground_truth = dir_ground_truth
        self.files = os.listdir(Path(dir_separated) / 's1')
        self.transform = transform
        print("Transform MetricsCalculatorDataset: ", transform)

        self.filter_index()

    def filter_index(self):
        files = []
        for file in tqdm(self.files, desc="Filter data"):
            id = file.split(".")[0]
            try:
                format = "wav"
                name = f"{id}.{format}"

                signal1, sr1 = torchaudio.load(
                    Path(self.dir_ground_truth) / "s1" / name, format=format
                )
                signal2, sr2 = torchaudio.load(
                    Path(self.dir_ground_truth) / "s2" / name, format=format
                )

                files.append(file)
            except:
                print(f"Cannot locate the Ground Truth for {file}")
        self.files = files

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        speaker1, speaker2 = self.files[idx].split(".")[0].split("_")

        sample = {
            "speaker1": speaker1,
            "speaker2": speaker2,
        }
        unmixed1, sr0 = torchaudio.load(Path(self.dir_separated) / "s1" / self.files[idx], format="wav")
        unmixed2, sr0 = torchaudio.load(Path(self.dir_separated) / "s2" / self.files[idx], format="wav")
        unmixed = torch.stack((unmixed1, unmixed2), dim=1).squeeze(0)

        format = "wav"
        name = f"{speaker1}_{speaker2}.{format}"

        signal1, sr1 = torchaudio.load(
            Path(self.dir_ground_truth) / "s1" / name, format=format
        )
        signal2, sr2 = torchaudio.load(
            Path(self.dir_ground_truth) / "s2" / name, format=format
        )
        assert sr1 == sr2
        sr = sr1

        sample.update(
            {
                "signal1": signal1.cpu(),
                "signal2": signal2.cpu(),
                "unmixed": unmixed.cpu(),
                "sr": sr,
            }
        )

        # if not self.meter:
        #     self.meter = pyln.Meter(sr)
        # signal_numpy = signal.numpy()[0, :]
        # louds = self.meter.integrated_loudness(signal_numpy)
        # signal = torch.Tensor(pyln.normalize.loudness(signal_numpy, louds, self.lufs)).unsqueeze(0)

        if self.transform is not None:
            for key, transform in self.transform.items():
                sample[key] = transform(sample[key])

        return sample


if __name__ == "__main__":
    import sys

    d = MetricsCalculatorDataset(sys.argv[1], sys.argv[2])
    print(f"len(d) = {len(d)}")
    print("d[1]:")
    for k, v in d[1].items():
        print(f"  {k}: {v}")
