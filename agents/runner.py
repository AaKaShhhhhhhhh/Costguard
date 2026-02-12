"""Simple agent runtime harness.

This runner loads agent `config.yaml` files from the `agents/` folder and
provides a minimal scheduler and event dispatcher for local development.

It is not a production orchestration system — use Archestra.AI for that —
but this harness is useful for local testing and demos.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Callable, Optional
import yaml
import logging

from shared.logger import logger
from agents import handlers

LOG = logging.getLogger(__name__)


@dataclass
class Agent:
    name: str
    config: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Any]


def load_agents(agent_dir: Path) -> Dict[str, Agent]:
    """Load YAML agent configs and bind them to handlers.

    The handler lookup is a simple naming convention: agent name ->
    `<name>_handler` in `agents.handlers`.
    """
    agents_map: Dict[str, Agent] = {}
    for cfg in agent_dir.glob("*/config.yaml"):
        try:
            data = yaml.safe_load(cfg.read_text()) or {}
            name = data.get("name") or cfg.parent.name
            handler_fn = getattr(handlers, f"{name}_handler", None)
            if handler_fn is None:
                LOG.warning("No handler found for agent %s", name)
                continue
            agents_map[name] = Agent(name=name, config=data, handler=handler_fn)
            LOG.info("Loaded agent %s", name)
        except Exception as exc:
            LOG.exception("Failed to load agent config %s: %s", cfg, exc)
    return agents_map


class Runner:
    """Manage agent scheduling and event dispatch.

    - `start()` schedules periodic jobs for agents with `schedule` triggers.
    - `dispatch_event()` sends events to agents that declare `event` triggers.
    """

    def __init__(self, agents: Dict[str, Agent]):
        self.agents = agents
        self.tasks: Dict[str, asyncio.Task] = {}

    async def _run_agent_periodic(self, agent: Agent, interval_seconds: int) -> None:
        LOG.info("Starting periodic agent %s every %s seconds", agent.name, interval_seconds)
        while True:
            try:
                await agent.handler(agent.config)
            except Exception:
                LOG.exception("Agent %s failed", agent.name)
            await asyncio.sleep(interval_seconds)

    async def start(self) -> None:
        # Schedule agents with schedule triggers
        for agent in self.agents.values():
            triggers = agent.config.get("triggers", [])
            for t in triggers:
                if isinstance(t, dict) and t.get("schedule"):
                    # parse simple rate expressions like 'rate(5 minutes)'
                    sched = t.get("schedule")
                    if sched.startswith("rate(") and "minute" in sched:
                        minutes = int(''.join(filter(str.isdigit, sched)))
                        interval = max(1, minutes * 60)
                    else:
                        interval = 300
                    task = asyncio.create_task(self._run_agent_periodic(agent, interval))
                    self.tasks[agent.name] = task

    async def dispatch_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        LOG.info("Dispatching event %s to agents", event_type)
        for agent in self.agents.values():
            triggers = agent.config.get("triggers", [])
            for t in triggers:
                if isinstance(t, dict) and t.get("event") == event_type:
                    try:
                        await agent.handler(payload)
                    except Exception:
                        LOG.exception("Agent %s handler failed for event %s", agent.name, event_type)


def discover_and_run(loop: Optional[asyncio.AbstractEventLoop] = None) -> Runner:
    base = Path(__file__).resolve().parent
    agents_dir = base
    agents_map = load_agents(agents_dir)
    runner = Runner(agents_map)
    if loop is None:
        loop = asyncio.get_event_loop()
    loop.create_task(runner.start())
    return runner


if __name__ == "__main__":
    # Simple CLI to start the runner and demonstrate an event dispatch
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = discover_and_run(loop)

    async def demo():
        await asyncio.sleep(2)
        # dispatch a fake llm_request event
        await runner.dispatch_event("llm_request", {"tokens": 120})

    try:
        loop.run_until_complete(demo())
    finally:
        loop.stop()
