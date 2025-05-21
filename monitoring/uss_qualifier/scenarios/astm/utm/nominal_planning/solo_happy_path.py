from typing import Dict, Optional

import arrow
from uas_standards.astm.f3548.v21.constants import Scope

from monitoring.monitorlib.clients.flight_planning.client import FlightPlannerClient
from monitoring.monitorlib.clients.flight_planning.flight_info import (
    AirspaceUsageState,
    UasState,
)
from monitoring.monitorlib.clients.flight_planning.flight_info_template import (
    FlightInfoTemplate,
)
from monitoring.monitorlib.temporal import Time, TimeDuringTest
from monitoring.uss_qualifier.resources.astm.f3548.v21 import DSSInstanceResource
from monitoring.uss_qualifier.resources.astm.f3548.v21.dss import DSSInstance
from monitoring.uss_qualifier.resources.flight_planning import FlightIntentsResource
from monitoring.uss_qualifier.resources.flight_planning.flight_intent_validation import (
    ExpectedFlightIntent,
    validate_flight_intent_templates,
)
from monitoring.uss_qualifier.resources.flight_planning.flight_planners import (
    FlightPlannerResource,
)
from monitoring.uss_qualifier.scenarios.astm.utm.test_steps import OpIntentValidator
from monitoring.uss_qualifier.scenarios.flight_planning.test_steps import (
    cleanup_flights,
    plan_flight,
    activate_flight,
    delete_flight,
)
from monitoring.uss_qualifier.scenarios.scenario import TestScenario
from monitoring.uss_qualifier.suites.suite import ExecutionContext


class SoloHappyPath(TestScenario):

    times: Dict[TimeDuringTest, Time]

    flight1_id: Optional[str] = None
    flight1_planned: FlightInfoTemplate
    flight1_activated: FlightInfoTemplate

    tested_uss: FlightPlannerClient
    dss: DSSInstance

    def __init__(
        self,
        tested_uss: FlightPlannerResource,
        dss: DSSInstanceResource,
        flight_intents: Optional[FlightIntentsResource] = None,
    ):
        super().__init__()
        self.tested_uss = tested_uss.client

        scopes = {
            Scope.StrategicCoordination: "search for operational intent references to verify outcomes of planning activities and retrieve operational intent details"
        }

        self.dss = dss.get_instance(scopes)

        expected_flight_intents = [
            ExpectedFlightIntent(
                "flight1_planned",
                "Flight",
                usage_state=AirspaceUsageState.Planned,
                uas_state=UasState.Nominal,
            ),
            ExpectedFlightIntent(
                "flight1_activated",
                "Flight",
                usage_state=AirspaceUsageState.InUse,
                uas_state=UasState.Nominal,
            ),
        ]

        templates = flight_intents.get_flight_intents()
        try:
            self._intents_extent = validate_flight_intent_templates(
                templates, expected_flight_intents
            )
        except ValueError as e:
            raise ValueError(
                f"`{self.me()}` TestScenario requirements for flight_intents not met: {e}"
            )

        for efi in expected_flight_intents:
            setattr(self, efi.intent_id, templates[efi.intent_id])

    def run(self, context: ExecutionContext):
        self.times = {
            TimeDuringTest.StartOfTestRun: Time(context.start_time),
            TimeDuringTest.StartOfScenario: Time(arrow.utcnow().datetime),
        }

        self.begin_test_scenario(context)

        self.begin_test_step("Plan flight 1")
        self.flight1_id, _ = plan_flight(
            scenario=self,
            flight_planner=self.tested_uss,
            flight_info=self.flight1_planned,
        )
        self.end_test_step()

        self.begin_test_step("Validate flight 1 sharing (planned)")
        with OpIntentValidator(
            scenario=self,
            flight_planner=self.tested_uss,
            dss=self.dss,
            extent=self.flight1_planned,
        ) as validator:
            oi_ref_planned = validator.expect_shared(self.flight1_planned)
        self.end_test_step()

        self.begin_test_step("Activate flight 1")
        _, _ = activate_flight(
            scenario=self,
            flight_planner=self.tested_uss,
            flight_info=self.flight1_activated,
            flight_id=self.flight1_id,
        )
        self.end_test_step()

        self.begin_test_step("Validate flight 1 sharing (activated)")
        with OpIntentValidator(
            scenario=self,
            flight_planner=self.tested_uss,
            dss=self.dss,
            extent=self.flight1_activated,
            orig_oi_ref=oi_ref_planned,
        ) as validator:
            oi_ref_activated = validator.expect_shared(self.flight1_activated)
        self.end_test_step()

        self.begin_test_step("Delete flight 1")
        delete_flight(
            scenario=self,
            flight_planner=self.tested_uss,
            flight_id=self.flight1_id,
        )
        self.end_test_step()

        self.begin_test_step("Validate flight 1 removal")
        with OpIntentValidator(
            scenario=self,
            flight_planner=self.tested_uss,
            dss=self.dss,
            extent=self.flight1_activated,
            orig_oi_ref=oi_ref_activated,
        ) as validator:
            validator.expect_removed(oi_ref_activated.id)
        self.end_test_step()

        self.end_test_scenario()

    def cleanup(self):
        self.begin_cleanup()
        cleanup_flights(self, (self.tested_uss,))
        self.end_cleanup()
