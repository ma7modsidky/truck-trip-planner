from trip_planner.domain.models import Location, Route


class FakeRouteProvider:

    def __init__(self, route: Route):
        self.route = route

    def get_route(
        self,
        origin: Location,
        destination: Location,
    ) -> Route:
        return self.route