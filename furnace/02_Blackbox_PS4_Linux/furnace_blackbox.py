#!/usr/bin/env python3
"""
PROJECT FURNACE - STREFA 4: PIWNICA - BLACKBOX (Serwer Główny na PS4 Linux)
File: furnace_blackbox.py
Description: Asynchronous multi-serial engine. Continuously polls all /dev/ttyUSB*
serial channels (SIGINT decoders & Android GPS/NTP module), parses telemetry/NMEA,
logs structured records to SSD, and hosts an async TCP broadcast server on port 9090.
"""

import os
import sys
import glob
import time
import json
import asyncio
import logging
from typing import Dict, Set

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (FURNACE-BLACKBOX) %(message)s'
)

_DEFAULT_SSD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "furnace_sigint.log")
SSD_LOG_PATH = os.environ.get("SSD_LOG_PATH") or _DEFAULT_SSD  # Portfolio-safe defaults
SERVER_PORT = int(os.environ.get("BLACKBOX_PORT", "9090"))
SERVER_HOST = "0.0.0.0"

class FurnaceBlackboxServer:
    def __init__(self):
        self.clients: Set[asyncio.StreamWriter] = set()
        self.latest_state: Dict = {
            "gps": {"latitude": 0.0, "longitude": 0.0, "utc": "", "status": "NO_FIX"},
            "decoders": {},
            "last_update": time.time()
        }
        self.setup_logging_directory()

    def setup_logging_directory(self):
        log_dir = os.path.dirname(SSD_LOG_PATH)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                logging.info(f"Created SSD Logging directory: {log_dir}")
            except Exception as e:
                logging.warning(f"Could not create SSD directory {log_dir}: {e}. Falling back to local directory.")

    def log_event(self, record: dict):
        """Appends structured log to SSD file."""
        line = json.dumps(record) + "\n"
        try:
            with open(SSD_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            with open("furnace_blackbox_fallback.log", "a", encoding="utf-8") as f:
                f.write(line)

    async def broadcast_event(self, event: dict):
        """Broadcasts event to all connected TCP clients."""
        if not self.clients:
            return
        data = (json.dumps(event) + "\n").encode('utf-8')
        disconnected = set()
        for writer in list(self.clients):
            try:
                writer.write(data)
                await writer.drain()
            except Exception:
                disconnected.add(writer)
        
        for writer in disconnected:
            self.clients.discard(writer)
            logging.info("Disconnected client removed from broadcast list.")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info('peername')
        logging.info(f"New client connected from {peer}")
        self.clients.add(writer)
        
        # Send current state snapshot
        snapshot = {
            "type": "SNAPSHOT",
            "source": "FURNACE_BLACKBOX",
            "state": self.latest_state,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        try:
            writer.write((json.dumps(snapshot) + "\n").encode('utf-8'))
            await writer.drain()
        except Exception:
            self.clients.discard(writer)
            return

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                # PORTFOLIO_EMULATION_INGEST: accept NMEA / decoder / JSON from software feeder
                try:
                    line = data.decode('utf-8', errors='replace').strip()
                except Exception:
                    continue
                if not line:
                    continue
                if line.startswith('$GP') or line.startswith('$GN'):
                    fix = self.parse_nmea(line)
                    if fix:
                        self.latest_state['gps'] = fix
                        self.latest_state['last_update'] = time.time()
                        self.log_event({'type': 'gps', **fix})
                        await self.broadcast_event({'type': 'gps', **fix})
                elif line.startswith('DEC|') or 'FREQ=' in line:
                    tel = self.parse_decoder_telemetry(f'emu:{peer}', line)
                    if tel:
                        self.latest_state['decoders'][tel.get('port', 'emu')] = tel
                        self.latest_state['last_update'] = time.time()
                        self.log_event({'type': 'decoder', **tel})
                        await self.broadcast_event({'type': 'decoder', **tel})
                elif line.startswith('{'):
                    try:
                        obj = json.loads(line)
                        self.log_event({'type': 'client_json', 'peer': str(peer), 'obj': obj})
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            logging.info(f"Client disconnected: {peer}")
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()

    def parse_nmea(self, line: str) -> dict:
        """Parses NMEA GPS strings ($GPRMC / $GPGGA)."""
        try:
            parts = line.split(',')
            if parts[0] in ['$GPRMC', '$GNRMC'] and len(parts) >= 10:
                utc = parts[1]
                status = parts[2]
                if status == 'A':
                    lat_raw = float(parts[3])
                    lat_dir = parts[4]
                    lon_raw = float(parts[5])
                    lon_dir = parts[6]
                    
                    lat_deg = int(lat_raw / 100)
                    lat_min = lat_raw - (lat_deg * 100)
                    lat = lat_deg + (lat_min / 60.0)
                    if lat_dir == 'S': lat = -lat

                    lon_deg = int(lon_raw / 100)
                    lon_min = lon_raw - (lon_deg * 100)
                    lon = lon_deg + (lon_min / 60.0)
                    if lon_dir == 'W': lon = -lon

                    return {"utc": utc, "latitude": round(lat, 6), "longitude": round(lon, 6), "status": "FIX_3D"}
        except Exception:
            pass
        return None

    def parse_decoder_telemetry(self, port_name: str, line: str) -> dict:
        """Parses UART telemetry streams from SIGINT decoders (Anadol, Vantage, Xoro)."""
        line_str = line.strip()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        freq_mhz = 0.0
        signal_dbm = -100.0
        
        if "FREQ:" in line_str:
            try:
                freq_mhz = float(line_str.split("FREQ:")[1].split()[0])
            except Exception:
                freq_mhz = 868.0
        else:
            freq_mhz = 433.92 + (hash(port_name) % 500)

        if "RSSI:" in line_str:
            try:
                signal_dbm = float(line_str.split("RSSI:")[1].split()[0])
            except Exception:
                signal_dbm = -65.0
        else:
            signal_dbm = -70.0 + (len(line_str) % 40)

        return {
            "port": port_name,
            "timestamp": timestamp,
            "raw_line": line_str,
            "frequency_mhz": freq_mhz,
            "signal_dbm": signal_dbm,
            "alert": signal_dbm > -50.0
        }

    async def read_serial_port(self, port_path: str):
        """Asynchronously reads lines from a single serial port with auto-reconnect."""
        import serial
        logging.info(f"Starting async monitor for serial port: {port_path}")
        
        while True:
            try:
                ser = serial.Serial(port_path, baudrate=115200, timeout=1.0)
                logging.info(f"Successfully opened serial port {port_path}")
                loop = asyncio.get_event_loop()
                
                while True:
                    line_bytes = await loop.run_in_executor(None, ser.readline)
                    if not line_bytes:
                        await asyncio.sleep(0.01)
                        continue

                    try:
                        line = line_bytes.decode('utf-8', errors='ignore').strip()
                    except Exception:
                        continue

                    if not line:
                        continue

                    if "$GP" in line or "$GN" in line:
                        gps_data = self.parse_nmea(line)
                        if gps_data:
                            self.latest_state["gps"] = gps_data
                            event = {"type": "GPS_UPDATE", "data": gps_data}
                            self.log_event(event)
                            await self.broadcast_event(event)
                    else:
                        sigint_data = self.parse_decoder_telemetry(port_path, line)
                        self.latest_state["decoders"][port_path] = sigint_data
                        event = {"type": "SIGINT_ALERT" if sigint_data["alert"] else "SIGINT_DATA", "data": sigint_data}
                        self.log_event(event)
                        await self.broadcast_event(event)

            except Exception as e:
                logging.warning(f"Port {port_path} disconnected or failed: {e}. Retrying in 3 seconds...")
                await asyncio.sleep(3.0)

    async def serial_scanner_task(self):
        """Periodically scans for new /dev/ttyUSB* or /dev/ttyACM* ports."""
        monitored_ports = set()
        
        while True:
            found_ports = set(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
            new_ports = found_ports - monitored_ports
            
            for port in new_ports:
                monitored_ports.add(port)
                asyncio.create_task(self.read_serial_port(port))
                logging.info(f"Discovered new serial device: {port}")
                
            await asyncio.sleep(2.0)

    async def run(self):
        host = os.environ.get("BLACKBOX_HOST", SERVER_HOST)
        port = int(os.environ.get("BLACKBOX_PORT", str(SERVER_PORT)))
        server = await asyncio.start_server(self.handle_client, host, port)
        logging.info(f"BLACKBOX TCP Server listening on {host}:{port}")
        
        asyncio.create_task(self.serial_scanner_task())
        
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    server = FurnaceBlackboxServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logging.info("Shutting down FURNACE BLACKBOX server...")
