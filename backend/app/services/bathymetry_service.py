from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path

from app.models.bathymetry import BathymetryDepthResponse


@dataclass
class VariableInfo:
    name: str
    dimids: list[int]
    nc_type: int
    begin: int


class BathymetryService:
    def __init__(self) -> None:
        self.dataset_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "bathymetry"
            / "carte_marine_tunisie.nc"
        )
        self._loaded = False
        self._buffer = b""
        self._lat_len = 0
        self._lon_len = 0
        self._lat_min = 0.0
        self._lat_step = 0.0
        self._lon_min = 0.0
        self._lon_step = 0.0
        self._elevation_begin = 0

    def _read_u32(self, offset: int) -> tuple[int, int]:
        return struct.unpack(">I", self._buffer[offset : offset + 4])[0], offset + 4

    def _read_name(self, offset: int) -> tuple[str, int]:
        size, offset = self._read_u32(offset)
        value = self._buffer[offset : offset + size].decode("ascii", errors="replace")
        offset += size
        offset += (-size) % 4
        return value, offset

    def _skip_attributes(self, offset: int) -> int:
        tag, offset = self._read_u32(offset)
        if tag == 0:
            _, offset = self._read_u32(offset)
            return offset

        count, offset = self._read_u32(offset)
        type_sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 4, 6: 8}
        for _ in range(count):
            _, offset = self._read_name(offset)
            nc_type, offset = self._read_u32(offset)
            value_count, offset = self._read_u32(offset)
            size = type_sizes[nc_type] * value_count
            offset += size
            offset += (-size) % 4
        return offset

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        self._buffer = self.dataset_path.read_bytes()
        if self._buffer[:3] != b"CDF":
            raise ValueError("Unsupported bathymetry dataset format")

        offset = 4
        _, offset = self._read_u32(offset)  # numrecs

        tag, offset = self._read_u32(offset)
        if tag == 0:
            raise ValueError("Bathymetry dataset has no dimensions")
        dim_count, offset = self._read_u32(offset)
        dims: list[tuple[str, int]] = []
        for _ in range(dim_count):
            name, offset = self._read_name(offset)
            length, offset = self._read_u32(offset)
            dims.append((name, length))

        offset = self._skip_attributes(offset)

        tag, offset = self._read_u32(offset)
        if tag == 0:
            raise ValueError("Bathymetry dataset has no variables")
        var_count, offset = self._read_u32(offset)
        variables: dict[str, VariableInfo] = {}

        for _ in range(var_count):
            name, offset = self._read_name(offset)
            ndims, offset = self._read_u32(offset)
            dimids: list[int] = []
            for _ in range(ndims):
                dimid, offset = self._read_u32(offset)
                dimids.append(dimid)
            offset = self._skip_attributes(offset)
            nc_type, offset = self._read_u32(offset)
            _, offset = self._read_u32(offset)  # vsize
            begin, offset = self._read_u32(offset)
            variables[name] = VariableInfo(
                name=name,
                dimids=dimids,
                nc_type=nc_type,
                begin=begin,
            )

        self._lat_len = dict(dims)["lat"]
        self._lon_len = dict(dims)["lon"]
        lat_var = variables["lat"]
        lon_var = variables["lon"]
        elevation_var = variables["elevation"]

        self._lat_min = self._read_f64(lat_var.begin)
        lat_next = self._read_f64(lat_var.begin + 8)
        self._lat_step = lat_next - self._lat_min
        self._lon_min = self._read_f64(lon_var.begin)
        lon_next = self._read_f64(lon_var.begin + 8)
        self._lon_step = lon_next - self._lon_min
        self._elevation_begin = elevation_var.begin
        self._loaded = True

    def _read_f64(self, offset: int) -> float:
        return struct.unpack(">d", self._buffer[offset : offset + 8])[0]

    def _read_i16(self, offset: int) -> int:
        return struct.unpack(">h", self._buffer[offset : offset + 2])[0]

    def _clamp_index(self, value: float, origin: float, step: float, length: int) -> int:
        raw = round((value - origin) / step)
        return max(0, min(length - 1, int(raw)))

    def _elevation_at_index(self, lat_index: int, lon_index: int) -> float:
        cell_offset = self._elevation_begin + ((lat_index * self._lon_len) + lon_index) * 2
        return float(self._read_i16(cell_offset))

    def _spacing_meters(self, lat_index: int) -> tuple[float, float]:
        lat_value = self._lat_min + lat_index * self._lat_step
        lat_spacing_m = abs(self._lat_step) * 111_320.0
        lon_spacing_m = abs(self._lon_step) * 111_320.0 * math.cos(math.radians(lat_value))
        return lat_spacing_m, max(lon_spacing_m, 1.0)

    def slope_at(self, lat: float, lon: float) -> float:
        self._ensure_loaded()

        lat_index = self._clamp_index(lat, self._lat_min, self._lat_step, self._lat_len)
        lon_index = self._clamp_index(lon, self._lon_min, self._lon_step, self._lon_len)

        north_index = max(lat_index - 1, 0)
        south_index = min(lat_index + 1, self._lat_len - 1)
        west_index = max(lon_index - 1, 0)
        east_index = min(lon_index + 1, self._lon_len - 1)

        north = self._elevation_at_index(north_index, lon_index)
        south = self._elevation_at_index(south_index, lon_index)
        west = self._elevation_at_index(lat_index, west_index)
        east = self._elevation_at_index(lat_index, east_index)

        lat_spacing_m, lon_spacing_m = self._spacing_meters(lat_index)
        dz_dy = (south - north) / max(lat_spacing_m * max(south_index - north_index, 1), 1.0)
        dz_dx = (east - west) / max(lon_spacing_m * max(east_index - west_index, 1), 1.0)
        slope_radians = math.atan(math.sqrt(dz_dx**2 + dz_dy**2))
        return round(math.degrees(slope_radians), 2)

    def depth_at(self, lat: float, lon: float) -> BathymetryDepthResponse:
        self._ensure_loaded()

        lat_index = self._clamp_index(lat, self._lat_min, self._lat_step, self._lat_len)
        lon_index = self._clamp_index(lon, self._lon_min, self._lon_step, self._lon_len)
        elevation = self._elevation_at_index(lat_index, lon_index)
        depth = max(0.0, -elevation)
        slope = self.slope_at(lat, lon)

        return BathymetryDepthResponse(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            depth_m=round(depth, 2),
            slope_deg=slope,
            status="success",
            source="GEBCO 2024 offline NetCDF",
        )

    def sample_depths_along_line(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        samples: int = 6,
    ) -> list[float]:
        self._ensure_loaded()
        values: list[float] = []
        sample_count = max(samples, 2)
        for index in range(sample_count):
            ratio = index / (sample_count - 1)
            lat = start_lat + (end_lat - start_lat) * ratio
            lon = start_lon + (end_lon - start_lon) * ratio
            values.append(self.depth_at(lat, lon).depth_m)
        return values


bathymetry_service = BathymetryService()
