from .create_persona import PersonaCreateService
from .delete_persona import PersonaDeleteService
from .update_persona import PersonaUpdateService
from .read_persona import PersonaReadService

class PersonaService(
    PersonaCreateService,
    PersonaDeleteService,
    PersonaUpdateService,
    PersonaReadService
):
    pass