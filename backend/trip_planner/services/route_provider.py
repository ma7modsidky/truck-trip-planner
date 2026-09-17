from abc import ABC, abstractmethod

from trip_planner.domain.models import Location, Route


class RouteProvider(ABC):

    @abstractmethod
    def get_route(
        self,
        origin: Location,
        destination: Location,
    ) -> Route:
        pass