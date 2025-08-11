from mylabo.domain import resource
from .dns_domain import dns_domain
from .dns_record import dns_record
from .infra import infra
from .vm_image import vm_image

resource_class_map: dict[str, resource.Resource] = {
    "DNSDomain": dns_domain.DNSDomain,
    "DNSRecord": dns_record.DNSRecord,
    "VMImage": vm_image.VMImage,
    "Infra": infra.Infra,
}


def load(spec):
    if spec["kind"] in resource_class_map:
        return resource_class_map[spec["kind"]](spec)
