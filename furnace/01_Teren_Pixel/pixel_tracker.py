#!/usr/bin/env python3
"""
PROJECT FURNACE - STREFA 1: TEREN (Moduł Taktyczny / Wizja)
File: pixel_tracker.py
Description: Termux/Python node on Google Pixel. Fetches RTSP stream from PTZ camera,
runs YOLOv8 / OpenCV fallback detection, and streams structured JSON TCP telemetry
packets to the Windows Tactical HUD and PS4 Blackbox server.
"""

import os
import sys
import time
import json
import socket
import logging
import threading
import numpy as np
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (PIXEL-TRACKER) %(message)s'
)

class PixelTrackerNode:
    def __init__(self, rtsp_url: str, hud_host: str, hud_port: int, model_path: str = "yolov8n.pt"):
        self.rtsp_url = rtsp_url
        self.hud_host = hud_host
        self.hud_port = hud_port
        self.model_path = model_path
        self.running = False
        self.tcp_socket = None
        self.yolo_model = None
        
        # Try loading YOLOv8, fallback to OpenCV background subtractor if unavailable
        self.use_yolo = False
        try:
            from ultralytics import YOLO
            if os.path.exists(self.model_path):
                self.yolo_model = YOLO(self.model_path)
            else:
                self.yolo_model = YOLO("yolov8n.pt")
            self.use_yolo = True
            logging.info("YOLOv8 Engine successfully initialized.")
        except Exception as e:
            logging.warning(f"YOLOv8 unavailable ({e}). Falling back to OpenCV Motion & Frame Difference Engine.")
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25, detectShadows=True)

    def connect_tcp(self):
        """Establishes persistent TCP connection with auto-reconnect."""
        while self.running:
            try:
                logging.info(f"Connecting to HUD/Base Server at {self.hud_host}:{self.hud_port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((self.hud_host, self.hud_port))
                sock.settimeout(None)
                self.tcp_socket = sock
                logging.info("TCP Connection established with HUD/Base Server.")
                return
            except Exception as e:
                logging.error(f"TCP Connection failed: {e}. Retrying in 3 seconds...")
                time.sleep(3.0)

    def send_telemetry(self, payload: dict):
        """Sends JSON packet over TCP stream."""
        if not self.tcp_socket:
            return False
        try:
            raw_bytes = (json.dumps(payload) + "\n").encode('utf-8')
            self.tcp_socket.sendall(raw_bytes)
            return True
        except Exception as e:
            logging.error(f"Socket send error: {e}. Resetting socket.")
            try:
                self.tcp_socket.close()
            except Exception:
                pass
            self.tcp_socket = None
            return False

    def process_frame_yolo(self, frame):
        detections = []
        results = self.yolo_model(frame, verbose=False)[0]
        for box in results.boxes:
            coords = box.xyxy[0].cpu().numpy().tolist()
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            class_name = self.yolo_model.names.get(cls_id, f"class_{cls_id}")
            if conf >= 0.35:
                detections.append({
                    "class": class_name,
                    "confidence": round(conf, 3),
                    "bbox": [round(c, 1) for c in coords]
                })
        return detections

    def process_frame_cv(self, frame):
        detections = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fg_mask = self.bg_subtractor.apply(gray)
        _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 400:
                x, y, w, h = cv2.boundingRect(cnt)
                detections.append({
                    "class": "motion_target",
                    "confidence": round(min(1.0, area / 5000.0), 3),
                    "bbox": [float(x), float(y), float(x + w), float(y + h)]
                })
        return detections

    def start(self):
        self.running = True
        tcp_thread = threading.Thread(target=self._connection_keepalive, daemon=True)
        tcp_thread.start()

        logging.info(f"Connecting to PTZ Camera RTSP Stream: {self.rtsp_url}")
        cap = cv2.VideoCapture(self.rtsp_url)
        
        if not cap.isOpened():
            logging.error(f"Failed to open RTSP stream at {self.rtsp_url}. Entering retry loop.")
            
        frame_id = 0
        while self.running:
            ret, frame = cap.read()
            if not ret or frame is None:
                logging.warning("RTSP frame capture timeout. Re-opening stream...")
                cap.release()
                time.sleep(2.0)
                cap = cv2.VideoCapture(self.rtsp_url)
                continue

            frame_id += 1
            timestamp = time.time()
            iso_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp))

            if self.use_yolo:
                targets = self.process_frame_yolo(frame)
            else:
                targets = self.process_frame_cv(frame)

            telemetry = {
                "source": "PIXEL_TACTICAL_NODE",
                "frame_id": frame_id,
                "timestamp": iso_time,
                "epoch_ms": int(timestamp * 1000),
                "target_count": len(targets),
                "targets": targets,
                "status": "OPERATIONAL"
            }

            if len(targets) > 0 or frame_id % 30 == 0:
                sent = self.send_telemetry(telemetry)
                if sent and len(targets) > 0:
                    logging.info(f"Frame #{frame_id}: Detections sent! Target count: {len(targets)}")

            time.sleep(0.033)  # ~30 FPS

        cap.release()
        if self.tcp_socket:
            self.tcp_socket.close()

    def _connection_keepalive(self):
        while self.running:
            if self.tcp_socket is None:
                self.connect_tcp()
            time.sleep(2.0)

if __name__ == "__main__":
    RTSP_URL = os.environ.get("RTSP_URL", "rtsp://192.168.1.100:554/stream1")
    HUD_HOST = os.environ.get("HUD_HOST", "192.168.1.50")
    HUD_PORT = int(os.environ.get("HUD_PORT", "9091"))

    tracker = PixelTrackerNode(rtsp_url=RTSP_URL, hud_host=HUD_HOST, hud_port=HUD_PORT)
    try:
        tracker.start()
    except KeyboardInterrupt:
        logging.info("Terminating Pixel Tracker Node...")
        tracker.running = False
