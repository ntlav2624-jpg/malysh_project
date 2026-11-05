from copy import deepcopy


class MindState:
    """
    One shared thinking state of ONE Malysh.

    O3/O4/O5, O345, Human Layer, Swarm, Omni,
    legacy logic and other organs are parts of this
    single thinking organism.
    """

    def __init__(self):
        self.subject = "Malysh"

        self.canonical = {}

        self.observations = {}

        self.reflections = {}

        self.experience = {}

        self.human = {}

        self.main = None

        self.possible = []


    def observe(self, name, value):
        """
        Publish an internal observation.

        Observer != independent subject.
        """

        self.observations[str(name)] = deepcopy(
            value
        )


    def reflect(self, name, value):
        """
        Store an internal reflection separately.
        """

        self.reflections[str(name)] = deepcopy(
            value
        )


    def remember(self, name, value):
        """
        Legacy/history is experience of the same Malysh.
        """

        self.experience[str(name)] = deepcopy(
            value
        )


    def set_human(self, thought):
        """
        Human Layer keeps:

            main
            possible

        inside ONE decision context.
        """

        self.human = deepcopy(
            thought
        )

        logical = self.human.get(
            "logical",
            {},
        )

        self.main = logical.get(
            "hypothesis"
        )

        self.possible = deepcopy(
            self.human.get(
                "possible",
                [],
            )
        )


    def snapshot(self):
        """
        Return isolated copy of thought state.

        No observer can mutate another observer's stored
        result through a shared reference.
        """

        return deepcopy(
            {
                "subject":
                    self.subject,

                "canonical":
                    self.canonical,

                "observations":
                    self.observations,

                "reflections":
                    self.reflections,

                "experience":
                    self.experience,

                "human":
                    self.human,

                "main":
                    self.main,

                "possible":
                    self.possible,
            }
        )


    def invariant(self):
        """
        Fundamental invariant:

            many organs
            many observers
            many thought branches
            ONE subject
        """

        return self.subject == "Malysh"



def merge_o345(
    mind,
    result,
):
    """
    Add O345 observations into ONE Malysh.

    O3/O4/O5 are views of one canonical state.

    O345 cannot independently execute a decision.
    """

    if not result.get(
        "invariant_ok"
    ):
        raise ValueError(
            "O345 invariant failed"
        )

    canonical = deepcopy(
        result.get(
            "canonical",
            {},
        )
    )

    if (
        mind.canonical
        and
        mind.canonical != canonical
    ):
        raise ValueError(
            "canonical conflict"
        )

    mind.canonical = canonical

    observers = result.get(
        "observers",
        {},
    )

    for name, value in observers.items():
        mind.observe(
            name,
            value,
        )

    mind.reflect(
        "O345",
        {
            "main":
                result.get(
                    "main"
                ),

            "possible":
                result.get(
                    "possible"
                ),

            "decision_authority":
                False,

            "state_write":
                False,

            "state_commit":
                False,
        },
    )

    return mind
