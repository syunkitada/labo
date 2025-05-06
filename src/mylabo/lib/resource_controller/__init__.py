from .dns_domain import dns_domain
from .dns_record import dns_record
from .vm_image import vm_image

resource_class_map = {
    "DNSDomain": dns_domain.DNSDomain,
    "DNSRecord": dns_record.DNSRecord,
    "VMImage": vm_image.VMImage,
}


def load(kind: str):
    if kind in resource_class_map:
        return resource_class_map[kind]()
