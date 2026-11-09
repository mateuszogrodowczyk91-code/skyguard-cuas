"""NEW portfolio tests: NMEA helper, evidence chain, blackbox ingest (no hardware)."""
import asyncio
import os
import socket
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "07_Emulation"))
sys.path.insert(0, str(ROOT / "08_Evidence_API"))
sys.path.insert(0, str(ROOT / "00_Master_Launcher"))
sys.path.insert(0, str(ROOT / "02_Blackbox_PS4_Linux"))

from emulation_sensor_feed import make_decoder_line, make_gprmc, nmea_checksum  # noqa: E402
from evidence_server import EvidenceStore  # noqa: E402
from furnace_blackbox import FurnaceBlackboxServer  # noqa: E402


class TestEmulationHelpers(unittest.TestCase):
    def test_nmea_checksum_and_parse(self):
        sentence = make_gprmc(51.9851, 5.8987, utc="120000")
        self.assertTrue(sentence.startswith("$GPRMC,"))
        body, cs = sentence[1:].split("*")
        self.assertEqual(cs, nmea_checksum(body))
        bb = FurnaceBlackboxServer()
        fix = bb.parse_nmea(sentence)
        self.assertIsNotNone(fix)
        self.assertEqual(fix["status"], "FIX_3D")
        self.assertAlmostEqual(fix["latitude"], 51.9851, places=3)
        self.assertAlmostEqual(fix["longitude"], 5.8987, places=3)

    def test_decoder_line_parsed(self):
        bb = FurnaceBlackboxServer()
        line = make_decoder_line(5805.5, 22.0)
        tel = bb.parse_decoder_telemetry("emu:test", line)
        self.assertIn("frequency_mhz", tel)
        self.assertEqual(tel["port"], "emu:test")


class TestEvidenceChain(unittest.TestCase):
    def test_hash_chain(self):
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(Path(td) / "chain.json")
            a = store.append({"event": "one"})
            b = store.append({"event": "two"})
            self.assertEqual(len(a["hash"]), 64)
            self.assertEqual(b["prev_hash"], a["hash"])
            self.assertEqual(len(store.items()), 2)


class TestBlackboxTcpIngest(unittest.TestCase):
    def test_client_nmea_updates_state(self):
        async def _run():
            # bind ephemeral
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            sock.close()

            os.environ["BLACKBOX_PORT"] = str(port)
            os.environ["SSD_LOG_PATH"] = str(ROOT / "logs" / "test_bb.log")
            (ROOT / "logs").mkdir(exist_ok=True)

            # Re-import constants are already read; patch instance run manually
            server = FurnaceBlackboxServer()
            srv = await asyncio.start_server(server.handle_client, "127.0.0.1", port)
            task = asyncio.create_task(srv.serve_forever())
            try:
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                _ = await asyncio.wait_for(reader.readline(), timeout=2)
                sentence = make_gprmc(51.98, 5.90)
                writer.write((sentence + "\n").encode())
                await writer.drain()
                await asyncio.sleep(0.3)
                writer.close()
                await writer.wait_closed()
                self.assertEqual(server.latest_state["gps"].get("status"), "FIX_3D")
            finally:
                task.cancel()
                srv.close()
                await srv.wait_closed()

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
