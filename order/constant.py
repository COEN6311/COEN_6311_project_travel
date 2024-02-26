from enum import Enum


class OrderStatus(Enum):
    PENDING_PAYMENT = 1
    PENDING_DEPARTURE = 2
    TRAVELING = 3
    TRAVELLED = 4
    CANCELLED = 9

    @classmethod
    def get_description(cls, status_code):
        return status_mapping.get(status_code)


status_mapping = {
    1: "Pending Payment",
    2: "Pending Departure",
    3: "Traveling",
    4: "Travelled",
    9: "Cancelled"
}
