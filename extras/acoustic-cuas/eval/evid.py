import sys, glob, json, os, numpy as np, warnings
from multiprocessing import Pool
warnings.filterwarnings("ignore")
import bench
C = bench.C
def run(p):
    x, sr = bench.read(p)
    o = C.UAVAcousticOrchestrator(sr=sr)
    W, H = 12 * sr, 6 * sr
    cu = []
    for s in range(0, len(x) - W + 1, H):
        r = o.analyze_stream(x[s:s + W])
        cu.append(dict(t=s / sr, det=r.uav_detected, model=r.identified_model, cat=r.catalog_match_confidence,
                       bpf=r.kinematics_doppler["Intrinsic_BPF0_Hz"], v=r.kinematics_doppler["Flight_Velocity_km_h"],
                       snr=r.signal_quality["snr_post_dsp_db"], sfm=r.signal_quality["median_spectral_flatness"]))
    d = bench.fz(); probs = []
    for s in range(0, len(x) - 8000 + 1, 4000):
        probs.append((s / sr, d.score(x[s:s + 8000].astype(np.float32))[0]))
    import acoustic_fusion as F
    d2 = F.FusionDetector(d.net, d.m, d.y); alarms = list(d2.feed(x.astype(np.float32), 0.0))
    return dict(f=os.path.basename(p), cuas=cu, fz_thr=d.m.thr, fz_max=max(q for _, q in probs),
                fz_tmax=max(probs, key=lambda a: a[1])[0], fz_over=sum(q >= d.m.thr for _, q in probs), fz_n=len(probs),
                fz_alarms=[(round(a[0], 1), round(a[1], 3)) for a in alarms])
if __name__ == "__main__":
    fs = sorted(glob.glob("/workspace/evidence/*/SG_*.wav"))
    with Pool(2) as pool: res = pool.map(run, fs)
    json.dump(res, open("/workspace/cuas-bench/evid.json", "w"), indent=1); print("done")
