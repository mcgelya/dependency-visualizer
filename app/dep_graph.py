from typing import List
from pip._internal.req import InstallRequirement
from piptools.utils import install_req_from_line
from piptools.repositories import PyPIRepository
from piptools.resolver import BacktrackingResolver
from pip._vendor.resolvelib.resolvers import ResolutionImpossible
from pip._internal.exceptions import DistributionNotFound
import networkx as nx
import warnings


def _parse_requirements(requirements: List[str]) -> List[InstallRequirement]:
    return [install_req_from_line(req) for req in requirements if req.strip()]


class DependencyCompiler:
    def __init__(self):
        self.repo = PyPIRepository([], "./pip_session")

    def generate_graph(
            self,
            requirements: List[str],
    ) -> nx.DiGraph:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            constraints = _parse_requirements(requirements)
            try:
                resolver = BacktrackingResolver(
                    constraints=constraints,
                    repository=self.repo,
                    existing_constraints={},
                )
                resolved = resolver.resolve()

            except DistributionNotFound as e:
                cause_exc = e.__cause__
                if cause_exc is None:
                    raise e
                if not isinstance(cause_exc, ResolutionImpossible):
                    raise e
                err = "Cannot satisfy requirements: " + ", ".join(str(cause.requirement) for cause in cause_exc.causes)
                raise ValueError(err)

            dep_graph = nx.DiGraph()

            dep_graph.add_node("Your project")
            for req in resolved:
                dep_graph.add_node(req.name, version=f"{req.specifier}")

            for req in resolved:
                required_by = set(getattr(req, "_required_by", set()))
                if len(required_by) == 0:
                    dep_graph.add_edge("Your project", req.name)
                for dep in required_by:
                    dep_graph.add_edge(dep, req.name)

            return dep_graph
