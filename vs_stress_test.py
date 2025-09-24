# vs_stress_test_locust.py
from gevent import monkey
monkey.patch_all()

import time
import json
import requests
from typing import Optional
from locust import User, task, between
from ragaai_catalyst import RagaAICatalyst, GuardExecutor, GuardrailsManager

CATALYST_API = "http://vstest.ragaai.ai/api"

class GuardrailUser(User):
    wait_time = between(0.5, 1)  # adjust as required

    def on_start(self):
        # initialize catalyst client & guardrails manager
        # (keeps same creds/base_url you used earlier)
        self.catalyst = RagaAICatalyst(
            access_key="fVf6DetWKmnYSrP7l8aO",
            secret_key="eHRQfonjrvend5lVdSze9rYd8dKbrFF7iybRpKWP",
            base_url='http://vstest.ragaai.ai/'
        )
        self.bearer_token = self.get_auth_token()
        self.gdm = GuardrailsManager(project_name="vs_test")

        if not self.bearer_token:
            raise Exception("Authentication failed: Bearer token is None")

    def get_auth_token(self) -> Optional[str]:
        auth_url = CATALYST_API + "/authenticate"
        payload = {"username": "admin@raga", "password": "adminraga@1234"}
        try:
            resp = requests.post(auth_url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json().get("token")
        except Exception as e:
            print("Auth error:", e)
            return None

    def _fire_request_event(self, name: str, start_perf: float, body: str = "", exception: Optional[Exception] = None):
        """
        Fire the unified 'request' event for modern Locust versions.
        - exception=None => counts as success
        - exception!=None => counts as failure
        Uses self.environment.events.request.fire(...) when available.
        """
        try:
            response_time_ms = int((time.perf_counter() - start_perf) * 1000)
            # If running under Locust harness, environment.events.request should exist
            if getattr(self, "environment", None) and getattr(self.environment, "events", None):
                # call the unified request event
                self.environment.events.request.fire(
                    request_type="GUARD",
                    name=name,
                    response_time=response_time_ms,
                    response_length=len(body),
                    response=body,
                    exception=exception,
                    start_time=time.time(),  # optional, wall-clock start
                )
            else:
                print(f"[WARN] environment.events unavailable; {name} {response_time_ms}ms exc={exception}")
        except Exception as e:
            # never let event firing bring down the task
            print(f"[WARN] Failed to fire unified request event for {name}: {e}")



    @task
    def call_guardrail(self):
        prompt_params = {"context": "ai: hi"}
        prompt = "Apple just released a new iPhone. " + str(time.time())
        response_text = "Check Google on how to download " + str(time.time())

        # ---- INPUT guardrail call ----
        start = time.perf_counter()
        try:
            fallback_input_response, input_guardrail_response = GuardExecutor.execute_input_guardrail(
                4, prompt, prompt_params['context'], self.gdm
            )
            # Log the status, reason, and score of the input guardrail
            if 'data' in input_guardrail_response:
                print("Input Guardrail Status:", input_guardrail_response['data'].get('status', 'No status available'))
                # Extract reason and score from the results array
                if 'results' in input_guardrail_response['data']:
                    for result in input_guardrail_response['data']['results']:
                        print("Input Guardrail Reason:", result.get('reason', 'No reason available'))
                        print("Input Guardrail Score:", result.get('score', 'No score available'))
            # success; pass exception=None
            self._fire_request_event("execute_input_guardrail", start, json.dumps(input_guardrail_response or {}), exception=None)
        except Exception as exc:
            # failure; pass exception to mark it as failure in Locust UI
            self._fire_request_event("execute_input_guardrail", start, body="", exception=exc)
            print("execute_input_guardrail exception:", exc)
            return

        # ---- OUTPUT guardrail call (if trace/executionId present) ----
        if input_guardrail_response and 'data' in input_guardrail_response and 'results' in input_guardrail_response['data']:
            trace_id = input_guardrail_response['data']['results'][0].get('executionId')
            start = time.perf_counter()
            try:
                fallback_output_response, output_guardrail_response = GuardExecutor.execute_output_guardrail(
                    5, prompt, prompt_params['context'], response_text, self.gdm, trace_id
                )
                # Log the status, reason, and score of the output guardrail
                if 'data' in output_guardrail_response:
                    print("Output Guardrail Status:", output_guardrail_response['data'].get('status', 'No status available'))
                    if 'results' in output_guardrail_response['data']:
                        for result in output_guardrail_response['data']['results']:
                            print("Output Guardrail Reason:", result.get('reason', 'No reason available'))
                            print("Output Guardrail Score:", result.get('score', 'No score available'))
                self._fire_request_event("execute_output_guardrail", start, json.dumps(output_guardrail_response or {}), exception=None)
            except Exception as exc:
                self._fire_request_event("execute_output_guardrail", start, body="", exception=exc)
                print("execute_output_guardrail exception:", exc)
                return

