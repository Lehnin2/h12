from app.domain.ports import TARGET_PORTS
from app.models.shared import Port


class CatalogService:
    def list_ports(self) -> list[Port]:
        return TARGET_PORTS

    def get_port(self, port_id: str) -> Port:
        normalized = port_id.strip().lower()
        for port in TARGET_PORTS:
            if port.id == normalized:
                return port
        fallback = next((port for port in TARGET_PORTS if port.id == "zarrat"), TARGET_PORTS[0])
        return fallback


catalog_service = CatalogService()

