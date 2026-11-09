import time
import math
import subprocess
import requests
from requests.auth import HTTPDigestAuth

# =====================================================================
# SKYGUARD TAPO CAMERA SMOOTH PTZ TRACKER (PID / EXPONENTIAL DAMPING)
# =====================================================================

class SmoothPtzController:
    """
    Sterownik płynnego śledzenia PTZ ("z gracją").
    Używa tłumienia wykładniczego oraz płynnej kontroli prędkości PID,
    aby kamera nie szarpała przy śledzeniu ruchomego celu.
    """
    def __init__(self, camera_ip, user="admin", password=""):
        self.camera_ip = camera_ip
        self.user = user
        self.password = password
        
        # Współczynniki wygładzania ruchów ("Z gracją")
        self.pan_p = 0.003
        self.tilt_p = 0.003
        self.alpha_smoothing = 0.35  # Tłumienie drgań (Low-Pass Filter)
        
        self.last_pan_speed = 0.0
        self.last_tilt_speed = 0.0
        
        # Wymiary klatki (skalowane do środka 0.0 - 1.0)
        self.frame_center_x = 0.5
        self.frame_center_y = 0.5

    def calculate_smooth_speed(self, target_x, target_y):
        """
        Oblicza płynną wektorową prędkość obrotu na podstawie błędu położenia celu.
        target_x, target_y: znormalizowane współrzędne środka celu (0.0 - 1.0)
        """
        # Błąd względem środka kadru
        err_x = target_x - self.frame_center_x
        err_y = target_y - self.frame_center_y
        
        # Jeśli cel jest blisko środka (Strefa martwa - Deadband), nie korygujemy
        if abs(err_x) < 0.04:
            err_x = 0.0
        if abs(err_y) < 0.04:
            err_y = 0.0

        # Wyznaczenie surowych prędkości
        raw_pan_speed = err_x * self.pan_p * 100.0
        raw_tilt_speed = -err_y * self.tilt_p * 100.0  # Odwrócona os Y
        
        # Wygładzanie wykładnicze (brak gwałtownych szarpnięć silnika krokowego)
        smooth_pan = (self.alpha_smoothing * raw_pan_speed) + ((1.0 - self.alpha_smoothing) * self.last_pan_speed)
        smooth_tilt = (self.alpha_smoothing * raw_tilt_speed) + ((1.0 - self.alpha_smoothing) * self.last_tilt_speed)
        
        # Ograniczenie prędkości maksymalnej (Graceful Slew Rate)
        smooth_pan = max(-1.0, min(1.0, smooth_pan))
        smooth_tilt = max(-1.0, min(1.0, smooth_tilt))
        
        self.last_pan_speed = smooth_pan
        self.last_tilt_speed = smooth_tilt
        
        return smooth_pan, smooth_tilt

    def send_ptz_command(self, pan_speed, tilt_speed):
        """
        Wysyła niskopoziomowe rozkazy prędkości obrotu przez ONVIF / CGI.
        """
        if abs(pan_speed) < 0.01 and abs(tilt_speed) < 0.01:
            return  # Brak potrzeby ruchu

        # Niskopoziomowy strzał ONVIF ContinuousMove / CGI
        url = f"http://{self.camera_ip}/cgi-bin/ptz.cgi?action=move&pan={pan_speed:.2f}&tilt={tilt_speed:.2f}"
        try:
            requests.get(url, auth=HTTPDigestAuth(self.user, self.password), timeout=0.2)
        except Exception:
            pass # Odporność na chwilowe zgubienie pakietów w terenie

if __name__ == "__main__":
    import os
    camera_ip = os.environ.get("PTZ_CAMERA_IP", "192.168.1.101")
    user = os.environ.get("PTZ_CAMERA_USER", "admin")
    password = os.environ.get("PTZ_CAMERA_PASSWORD", "")
    print("[SKYGUARD] Tester płynnego śledzenia PTZ załadowany...")
    print(f"[SKYGUARD] PTZ target: {camera_ip} (user={user})")
    tracker = SmoothPtzController(camera_ip, user=user, password=password)
    # Symulacja ruchu celu przez kadr (no live RTSP required for this node):
    for x_pos in [0.6, 0.75, 0.8, 0.65, 0.52]:
        pan, tilt = tracker.calculate_smooth_speed(x_pos, 0.5)
        print(f"Położenie celu X: {x_pos:.2f} -> Płynna prędkość obrotu Pan: {pan:+.3f}, Tilt: {tilt:+.3f}")
        tracker.send_ptz_command(pan, tilt)
        time.sleep(0.1)
    # Stay alive for orchestrator when launched as a subsystem
    if os.environ.get("ENABLE_PTZ_TRACKER", "").lower() in ("1", "true", "yes", "on"):
        print("[SKYGUARD] PTZ tracker idle loop (waiting for fusion cues / keepalive)...")
        while True:
            time.sleep(30)
