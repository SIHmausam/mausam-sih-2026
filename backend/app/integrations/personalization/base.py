from abc import (
    ABC,
    abstractmethod,
)

from app.schemas.personalization import (
    MLInteractionRequest,
    MLPersonalizationRequest,
    MLPersonalizationResponse,
)


class PersonalizationProviderError(RuntimeError):
    pass


class PersonalizationProviderUnavailableError(PersonalizationProviderError):
    pass


class PersonalizationProviderResponseError(PersonalizationProviderError):
    pass


class PersonalizationProvider(ABC):
    @abstractmethod
    async def personalize(
        self,
        request: MLPersonalizationRequest,
    ) -> MLPersonalizationResponse:
        raise NotImplementedError

    @abstractmethod
    async def record_interaction(
        self,
        request: MLInteractionRequest,
    ) -> None:
        raise NotImplementedError
