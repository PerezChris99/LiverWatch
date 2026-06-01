"""
API v1 — Wearable Device Endpoints
=====================================

POST /api/v1/wearable/register          → register a new device
POST /api/v1/wearable/<device_id>/sync  → ingest biomarker readings
GET  /api/v1/wearable/devices           → list user's devices
GET  /api/v1/wearable/<device_id>/readings → paginated readings

All biomarker data is stored and flagged for anomaly detection.
Anomalies do NOT imply disease — they trigger a screening recommendation.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pytz
from flask import Blueprint, g, jsonify, request

from app import db
from app.blueprints.api.v1.auth import jwt_required
from app.models import AuditLog, BiomarkerReading, DeviceStatus, WearableDevice
from app.services.risk_engine import MEDICAL_DISCLAIMER

logger = logging.getLogger(__name__)

wearable_api_v1 = Blueprint('wearable_api_v1', __name__, url_prefix='/wearable')

# Biomarker normal ranges (indicative — NOT diagnostic thresholds)
_NORMAL_RANGES = {
    'ammonia':            (11, 35),      # μmol/L serum (indicative)
    'ph':                 (7.35, 7.45),  # blood pH
    'hydration':          (0.55, 0.75),  # body water fraction (estimated)
    'alcohol_metabolite': (0, 0.05),     # arbitrary units
    'sodium':             (135, 145),    # mmol/L
    'potassium':          (3.5, 5.0),    # mmol/L
    'stress':             (0, 0.6),      # arbitrary HRV-derived index
}

DISCLAIMER = MEDICAL_DISCLAIMER


def _is_anomaly(biomarker_type: str, value: float) -> bool:
    """Flag a reading as anomalous if outside indicative normal range."""
    r = _NORMAL_RANGES.get(biomarker_type)
    if r is None:
        return False
    return not (r[0] <= value <= r[1])


@wearable_api_v1.post('/register')
@jwt_required
def register_device():
    """
    POST /api/v1/wearable/register

    Body: {
        "device_id": "HW-UNIQUE-UUID",
        "device_type": "sweat_patch",
        "manufacturer": "...",
        "model": "...",
        "firmware_version": "1.0.0"
    }
    """
    data      = request.get_json(silent=True) or {}
    user      = g.current_user
    device_id = (data.get('device_id', '') or '').strip()

    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400

    allowed_types = ('sweat_patch', 'wristband', 'custom', 'portable_analyser')
    dtype = data.get('device_type', 'custom')
    if dtype not in allowed_types:
        return jsonify({'error': f'device_type must be one of {allowed_types}'}), 400

    if WearableDevice.query.filter_by(device_id=device_id).first():
        return jsonify({'error': 'A device with this ID is already registered'}), 409

    dev = WearableDevice(
        user_id=user.id,
        device_id=device_id,
        device_type=dtype,
        manufacturer=data.get('manufacturer', ''),
        model=data.get('model', ''),
        firmware_version=data.get('firmware_version', ''),
        status=DeviceStatus.INACTIVE.value,
    )
    db.session.add(dev)
    db.session.commit()

    _audit(user.id, 'wearable_registered', 'wearable_device', dev.id)

    return jsonify({
        'id':          dev.id,
        'device_id':   dev.device_id,
        'device_type': dev.device_type,
        'status':      dev.status,
        'registered_at': dev.registered_at.isoformat(),
        'message': 'Device registered. Begin calibration before syncing readings.',
    }), 201


@wearable_api_v1.post('/<string:device_id>/sync')
@jwt_required
def sync_readings(device_id: str):
    """
    POST /api/v1/wearable/<device_id>/sync

    Ingest a batch of biomarker readings.

    Body: {
        "readings": [
            {
                "biomarker_type": "ammonia",
                "value": 28.5,
                "unit": "umol/L",
                "quality_score": 0.92,
                "timestamp": "2024-12-01T10:30:00Z",
                "raw_data": {}
            }
        ]
    }
    """
    import json

    user = g.current_user
    dev  = WearableDevice.query.filter_by(device_id=device_id, user_id=user.id).first()

    if not dev:
        return jsonify({'error': 'Device not found or not owned by you'}), 404

    if not dev.is_active:
        return jsonify({'error': 'Device is not active'}), 400

    readings_data = (request.get_json(silent=True) or {}).get('readings', [])
    if not readings_data or not isinstance(readings_data, list):
        return jsonify({'error': '"readings" must be a non-empty list'}), 400

    if len(readings_data) > 500:
        return jsonify({'error': 'Maximum 500 readings per sync batch'}), 400

    saved         = 0
    anomaly_count = 0
    errors        = []
    valid_types   = set(_NORMAL_RANGES.keys())

    for i, r in enumerate(readings_data):
        btype = r.get('biomarker_type', '')
        if btype not in valid_types:
            errors.append(f'readings[{i}]: unknown biomarker_type {btype!r}')
            continue

        try:
            value = float(r['value'])
        except (KeyError, TypeError, ValueError):
            errors.append(f'readings[{i}]: value must be a number')
            continue

        try:
            ts = datetime.fromisoformat(r.get('timestamp', '').replace('Z', '+00:00'))
        except (ValueError, TypeError):
            ts = datetime.now(pytz.utc)

        quality = float(r.get('quality_score', 1.0))
        quality = max(0.0, min(1.0, quality))

        anomaly = _is_anomaly(btype, value)
        if anomaly:
            anomaly_count += 1

        raw = r.get('raw_data')
        reading = BiomarkerReading(
            device_id=dev.id,
            user_id=user.id,
            biomarker_type=btype,
            value=value,
            unit=r.get('unit', ''),
            quality_score=quality,
            is_anomaly=anomaly,
            anomaly_notes='Outside indicative normal range — screening recommended.' if anomaly else None,
            timestamp=ts,
            raw_data=json.dumps(raw) if raw else None,
        )
        db.session.add(reading)
        saved += 1

    dev.last_sync_at = datetime.now(pytz.utc)
    dev.status       = DeviceStatus.ACTIVE.value
    db.session.commit()

    response = {
        'saved':         saved,
        'errors':        errors,
        'anomaly_count': anomaly_count,
        'last_sync_at':  dev.last_sync_at.isoformat(),
        'disclaimer':    DISCLAIMER,
    }
    if anomaly_count > 0:
        response['anomaly_notice'] = (
            f"{anomaly_count} reading(s) fall outside indicative normal ranges. "
            "This does not indicate disease. Consider completing a risk assessment "
            "or attending a screening event in your district."
        )

    return jsonify(response), 200


@wearable_api_v1.get('/devices')
@jwt_required
def list_devices():
    """GET /api/v1/wearable/devices — list authenticated user's devices."""
    user    = g.current_user
    devices = WearableDevice.query.filter_by(user_id=user.id, is_active=True).all()

    return jsonify({
        'devices': [
            {
                'id':          d.id,
                'device_id':   d.device_id,
                'device_type': d.device_type,
                'manufacturer': d.manufacturer,
                'model':       d.model,
                'status':      d.status,
                'last_sync_at': d.last_sync_at.isoformat() if d.last_sync_at else None,
            }
            for d in devices
        ]
    }), 200


@wearable_api_v1.get('/<string:device_id>/readings')
@jwt_required
def get_readings(device_id: str):
    """GET /api/v1/wearable/<device_id>/readings — paginated reading history."""
    user = g.current_user
    dev  = WearableDevice.query.filter_by(device_id=device_id, user_id=user.id).first()

    if not dev:
        return jsonify({'error': 'Device not found or not owned by you'}), 404

    page  = request.args.get('page',  1,  type=int)
    limit = min(request.args.get('limit', 50, type=int), 200)
    btype = request.args.get('biomarker_type')

    q = BiomarkerReading.query.filter_by(device_id=dev.id)
    if btype:
        q = q.filter_by(biomarker_type=btype)

    pagination = q.order_by(BiomarkerReading.timestamp.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )

    return jsonify({
        'device_id': device_id,
        'readings': [
            {
                'id':             r.id,
                'biomarker_type': r.biomarker_type,
                'value':          r.value,
                'unit':           r.unit,
                'quality_score':  r.quality_score,
                'is_anomaly':     r.is_anomaly,
                'timestamp':      r.timestamp.isoformat(),
            }
            for r in pagination.items
        ],
        'total': pagination.total,
        'page':  page,
        'pages': pagination.pages,
        'disclaimer': DISCLAIMER,
    }), 200


# ── Audit helper ──────────────────────────────────────────────────────────

def _audit(user_id, action, resource_type, resource_id=None):
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        logger.exception("Audit log failed: action=%s", action)
