# Copyright (C) 2019 Intel Corporation (opendroneid/receiver-android)
# SPDX-License-Identifier: Apache-2.0
#
# Ramkowanie Remote ID jak w opendroneid/receiver-android (BluetoothScanner,
# WiFiBeaconScanner): BLE Service Data UUID 0xFFFA, kod aplikacji 0x0D,
# licznik wiadomości, potem wiadomość/paczka; Wi-Fi Beacon: element
# dostawcy 0xDD z OUI FA:0B:BC (ASD-STAN), typ 0x0D, licznik, paczka.
# Zmiany SKYGUARD: czyste funkcje Pythona operujące na surowych bajtach.
"""Wyciąganie wiadomości Remote ID z reklam BLE i ramek beacon Wi-Fi."""
from __future__ import annotations

from .odid import decode_any

ODID_UUID = 0xFFFA
ODID_APP_CODE = 0x0D
ASD_STAN_OUI = bytes([0xFA, 0x0B, 0xBC])


def extract_ble_service_data(adv: bytes) -> bytes | None:
    """Z danych reklamy BLE (ciąg struktur AD) zwraca ładunek po kodzie 0x0D i liczniku."""
    i = 0
    while i < len(adv):
        ln = adv[i]
        if ln == 0 or i + 1 + ln > len(adv):
            break
        ad_type, payload = adv[i + 1], adv[i + 2:i + 1 + ln]
        if ad_type == 0x16 and len(payload) >= 4 and payload[0] | (payload[1] << 8) == ODID_UUID \
                and payload[2] == ODID_APP_CODE:
            return bytes(payload[4:])
        i += 1 + ln
    return None


def extract_wifi_beacon_ie(ies: bytes) -> bytes | None:
    """Z tagowanych parametrów beacona (ID, len, dane…) zwraca paczkę ASD-STAN."""
    i = 0
    while i + 2 <= len(ies):
        eid, ln = ies[i], ies[i + 1]
        body = ies[i + 2:i + 2 + ln]
        if eid == 0xDD and len(body) >= 5 and body[:3] == ASD_STAN_OUI and body[3] == ODID_APP_CODE:
            return bytes(body[5:])
        i += 2 + ln
    return None


def decode_ble_advert(adv: bytes) -> list[dict]:
    p = extract_ble_service_data(adv)
    return decode_any(p) if p else []


def decode_wifi_beacon(ies: bytes) -> list[dict]:
    p = extract_wifi_beacon_ie(ies)
    return decode_any(p) if p else []
