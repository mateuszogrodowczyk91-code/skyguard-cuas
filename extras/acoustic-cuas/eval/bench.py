import sys, os, glob, json, wave, warnings, numpy as np, random
from multiprocessing import Pool
from scipy.signal import resample_poly
warnings.filterwarnings("ignore")
sys.path.insert(0, "/workspace/wt-cuas/tools/acoustic/cuas")
FZ = "/workspace/sg-db-ens/tools/windows/skyguard-centrum"
sys.path.insert(0, FZ)
import cuas_reference as C
_fz = None
def fz():
    global _fz
    if _fz is None:
        import acoustic_net, acoustic_fusion as F
        net = acoustic_net.load_model(os.path.join(FZ, "models", "sg_drone_net_v1.sgan"))
        _fz = F.FusionDetector(net, F.FusionModel.load("/workspace/acoustic-ens/sg_fusion_v2.txt"), F.Yamnet())
    return _fz
def read(p):
    with wave.open(p) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        b = w.readframes(w.getnframes())
    x = np.frombuffer(b, "<i2" if sw == 2 else "<i4").astype(np.float64)
    x /= 32768.0 if sw == 2 else 2**31
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    return x, sr
def to8k(x, sr):
    if sr == 8000: return x
    from math import gcd
    g = gcd(sr, 8000); return resample_poly(x, 8000 // g, sr // g)
def job(a):
    label, p = a
    x, sr = read(p); x8 = to8k(x, sr)
    if len(x8) < 8192: x8 = np.pad(x8, (0, 8192 - len(x8)))
    r = C.UAVAcousticOrchestrator(sr=8000).analyze_stream(x8, flyby_window_s=None)
    d = fz(); probs = []
    for s in range(0, max(1, len(x8) - 8000 + 1), 4000):
        w = x8[s:s + 8000]
        if len(w) < 8000: w = np.pad(w, (0, 8000 - len(w)))
        probs.append(d.score(w)[0])
    return dict(label=label, f=os.path.basename(p), cuas=bool(r.uav_detected), cuas_model=r.identified_model,
                bpf=r.kinematics_doppler["Intrinsic_BPF0_Hz"], snr=r.signal_quality["snr_post_dsp_db"],
                sfm=r.signal_quality["median_spectral_flatness"], fz_max=max(probs), fz=max(probs) >= d.m.thr)
if __name__ == "__main__":
    random.seed(0)
    O = "/workspace/acoustic-data/ood"
    drone = glob.glob(O + "/neaptide_*/*/*.wav")
    indoor = random.sample(glob.glob(O + "/DroneAudioDataset/Binary_Drone_Audio/yes_drone/*.wav"), 100)
    unk = random.sample(glob.glob(O + "/DroneAudioDataset/Binary_Drone_Audio/unknown/*.wav"), 150)
    import csv
    meta = list(csv.DictReader(open("/workspace/acoustic-data/esc50/ESC-50-master/meta/esc50.csv")))
    esc = ["/workspace/acoustic-data/esc50/ESC-50-master/audio/" + m["filename"] for m in meta]
    cat = {m["filename"]: m["category"] for m in meta}
    tasks = [("drone_neaptide", p) for p in drone] + [("drone_indoor", p) for p in indoor] + \
            [("neg_unknown", p) for p in unk] + [("neg_esc50", p) for p in esc]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 8) as pool:
        res = pool.map(job, tasks, chunksize=4)
    for r in res:
        if r["label"] == "neg_esc50": r["cat"] = cat[r["f"]]
    json.dump(res, open("/workspace/cuas-bench/bench.json", "w"))
    print("done", len(res))
