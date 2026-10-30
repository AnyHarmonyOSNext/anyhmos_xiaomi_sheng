"""Bounded local camera captures for tablet display diagnostics.

No preview, video recording, uploads, or post-capture exposure simulation.
Camera settings are restored and the camera is released in finally.
Dependencies live in work/camera-runtime, independent of the system Python.
"""
from pathlib import Path
import argparse
import datetime
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
# Prefer the active interpreter's matching NumPy extension. The optional
# camera runtime may have been installed for a different Python minor.
try:
    import numpy
except ImportError:
    pass
sys.path.insert(0, str(ROOT / 'work/camera-runtime'))
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('--index', type=int, default=0)
parser.add_argument('--exposure', type=float, action='append')
parser.add_argument('--label', default='tablet')
parser.add_argument('--backend', choices=['dshow', 'msmf'], default='dshow')
args = parser.parse_args()
if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.label):
    parser.error('label must be an ASCII filename label')
exposures = args.exposure if args.exposure is not None else [-6.0, -8.0]
if len(exposures) > 3 or any(not -13 <= x <= -1 for x in exposures):
    parser.error('up to three hardware exposure values between -13 and -1')

destination = ROOT / 'output/camera' / (datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + args.label)
destination.mkdir(parents=True, exist_ok=False)
report = {'purpose': 'physical tablet screen observation; not a system screenshot',
          'backend': args.backend, 'index': args.index, 'captures': [], 'released': False}
capture = None
original = {}
try:
    capture = cv2.VideoCapture(args.index, cv2.CAP_DSHOW if args.backend == 'dshow' else cv2.CAP_MSMF)
    if not capture.isOpened():
        raise RuntimeError('Camera open failed; no privacy settings changed')
    original = {'auto_exposure': capture.get(cv2.CAP_PROP_AUTO_EXPOSURE),
                'exposure': capture.get(cv2.CAP_PROP_EXPOSURE)}
    report['original'] = original
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    report['dimensions'] = [capture.get(cv2.CAP_PROP_FRAME_WIDTH), capture.get(cv2.CAP_PROP_FRAME_HEIGHT)]

    def save_frame(label):
        deadline = time.monotonic() + 1.25
        frame = None
        while time.monotonic() < deadline:
            ok, candidate = capture.read()
            if ok and candidate is not None:
                frame = candidate
        if frame is None:
            raise RuntimeError('Camera did not return a frame')
        path = destination / (label + '.jpg')
        ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ok:
            raise RuntimeError('Image save failed')
        path.write_bytes(encoded.tobytes())
        return {'file': str(path), 'auto_exposure_readback': capture.get(cv2.CAP_PROP_AUTO_EXPOSURE),
                'exposure_readback': capture.get(cv2.CAP_PROP_EXPOSURE), 'shape': list(frame.shape)}

    report['captures'].append(save_frame('initial'))
    for requested in exposures:
        # DirectShow uses rounded 0=manual, 1=auto (OpenCV cap_dshow.cpp).
        auto_ok = capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        exposure_ok = capture.set(cv2.CAP_PROP_EXPOSURE, requested)
        item = save_frame('exposure-' + str(abs(requested)).replace('.', '_'))
        item.update(requested_exposure=requested, manual_mode_set_return=bool(auto_ok),
                    exposure_set_return=bool(exposure_ok))
        report['captures'].append(item)
finally:
    if capture is not None:
        try:
            if capture.isOpened() and original:
                report['restore_exposure_return'] = bool(capture.set(cv2.CAP_PROP_EXPOSURE, original['exposure']))
                if original['auto_exposure'] >= 0:
                    report['restore_auto_return'] = bool(capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, original['auto_exposure']))
                else:
                    report['restore_auto_return'] = None
                    report['auto_exposure_note'] = 'Backend cannot report original auto mode; exposure value restored, auto mode not claimed restored.'
        finally:
            capture.release()
            report['released'] = not capture.isOpened()
    (destination / 'capture.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    print('CAMERA_RELEASED=' + str(report['released']), flush=True)
