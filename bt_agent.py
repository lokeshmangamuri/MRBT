from cooperative_cuisine.base_agent.base_agent import BaseAgent, run_agent_from_args
from cooperative_cuisine.base_agent.agent_task import Task, TaskStatus
import py_trees
import numpy as np
from cooperative_cuisine.action import ActionType
from constants import TASK_POSITIONS

# ==============================================================================
# Behaviors
# ==============================================================================

class GoTo(py_trees.behaviour.Behaviour):
    def __init__(self, agent, position, name="GoTo"):
        super(GoTo, self).__init__(name)
        self.agent = agent
        self.position = position

    def setup(self):
        self.logger.debug(f"  >{self.name}.setup()")

    def initialise(self):
        self.logger.debug(f"  >{self.name}.initialise()")
        if isinstance(self.position, str) and self.position in TASK_POSITIONS:
            pos = TASK_POSITIONS[self.position]
        elif isinstance(self.position, str) and hasattr(self.agent, self.position):
             pos = getattr(self.agent, self.position)
        else:
            pos = self.position
        self.agent.set_current_task(Task(Task.GOTO, task_args=list(pos)))

    def update(self):
        self.logger.debug(f"  >{self.name}.update()")
        if self.agent.current_task is None:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        self.logger.debug(f"  >{self.name}.terminate({new_status})")

class Put(py_trees.behaviour.Behaviour):
    def __init__(self, agent, name="Put"):
        super(Put, self).__init__(name)
        self.agent = agent

    def setup(self):
        self.logger.debug(f"  >{self.name}.setup()")

    def initialise(self):
        self.logger.debug(f"  >{self.name}.initialise()")
        self.agent.set_current_task(Task(Task.PUT))

    def update(self):
        self.logger.debug(f"  >{self.name}.update()")
        if self.agent.current_task is None:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        self.logger.debug(f"  >{self.name}.terminate({new_status})")

class Interact(py_trees.behaviour.Behaviour):
    def __init__(self, agent, name="Interact"):
        super(Interact, self).__init__(name)
        self.agent = agent

    def setup(self):
        self.logger.debug(f"  >{self.name}.setup()")

    def initialise(self):
        self.logger.debug(f"  >{self.name}.initialise()")
        self.agent.set_current_task(Task(Task.INTERACT))

    def update(self):
        self.logger.debug(f"  >{self.name}.update()")
        if self.agent.current_task is None:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        self.logger.debug(f"  >{self.name}.terminate({new_status})")


class HasItem(py_trees.behaviour.Behaviour):
    def __init__(self, agent, should_have, item_type=None, name="HasItem"):
        super(HasItem, self).__init__(name)
        self.agent = agent
        self.should_have = should_have
        self.item_type = item_type

    def update(self):
        has_item = bool(self.agent.held_item)
        if self.should_have != has_item:
            return py_trees.common.Status.FAILURE
        
        if self.item_type and (not has_item or self.agent.held_item.get("type") != self.item_type):
            return py_trees.common.Status.FAILURE
            
        return py_trees.common.Status.SUCCESS

class FindFreeCounter(py_trees.behaviour.Behaviour):
    def __init__(self, agent, name="FindFreeCounter"):
        super(FindFreeCounter, self).__init__(name)
        self.agent = agent

    def update(self):
        free_counter_pos = None
        for c in self.agent.state_counters:
            if (
                c.get("occupied_by") is None
                and c.get("type") not in ("CuttingBoard", "Pan")
            ):
                free_counter_pos = np.array(c["pos"])
                break
        if free_counter_pos is None:
            free_counter_pos = np.array(TASK_POSITIONS["CUTTING_BOARD_1"])
        
        self.agent.plate_counter_pos = free_counter_pos
        return py_trees.common.Status.SUCCESS

# ==============================================================================
# Agent
# ==============================================================================

class BTAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.behaviour_tree = self.create_behaviour_tree()
        self.plate_counter_pos = None

    def create_behaviour_tree(self):
        
        root = py_trees.composites.Sequence(name="BurgerMaking", memory=True)

        # 1. Get Plate
        get_plate = py_trees.composites.Sequence(name="GetPlate", memory=True)
        get_plate.add_child(HasItem(self, should_have=False))
        get_plate.add_child(GoTo(self, "PLATE_DISPENSER"))
        get_plate.add_child(Put(self))
        get_plate.add_child(HasItem(self, should_have=True, item_type="Plate"))


        # 2. Place Plate
        place_plate = py_trees.composites.Sequence(name="PlacePlate", memory=True)
        place_plate.add_child(HasItem(self, should_have=True, item_type="Plate"))
        place_plate.add_child(FindFreeCounter(self))
        place_plate.add_child(GoTo(self, "plate_counter_pos"))
        place_plate.add_child(Put(self))
        place_plate.add_child(HasItem(self, should_have=False))

        # 3. Get & Place Bun
        get_bun = self._create_get_and_place_item_sequence("Bun", "GET_BUN")
        
        # 4. Get, Cut & Place Lettuce
        get_lettuce = self._create_get_cut_and_place_item_sequence("Lettuce", "GET_LETTUCE", "CUTTING_BOARD_1")

        # 5. Get, Cut & Place Tomato
        get_tomato = self._create_get_cut_and_place_item_sequence("Tomato", "GET_TOMATO", "CUTTING_BOARD_1")

        # 6. Get, Cut, Cook, Finish & Serve
        process_and_serve = py_trees.composites.Sequence(name="ProcessMeatAndServe", memory=True)
        process_and_serve.add_child(self._create_get_and_place_item_sequence("Meat", "GET_MEAT", "CUTTING_BOARD_1", put_on_plate=False))
        process_and_serve.add_child(self._create_interaction_sequence("RawPatty", "CUTTING_BOARD_1", "Meat"))
        process_and_serve.add_child(self._create_place_item_sequence("RawPatty", "PAN", final_placement=False))
        process_and_serve.add_child(self._create_interaction_sequence("CookedPatty", "PAN", "RawPatty"))
        # Now holding CookedPatty, go place it on the plate.
        process_and_serve.add_child(GoTo(self, "plate_counter_pos"))
        process_and_serve.add_child(Put(self))
        # The Burger is now assembled on the counter. The agent is empty-handed.
        # Pick up the burger from the same spot.
        process_and_serve.add_child(Put(self))
        # Now holding the Burger, go to serving window and drop it.
        process_and_serve.add_child(HasItem(self, should_have=True, item_type="Burger"))
        process_and_serve.add_child(GoTo(self, "SERVING_WINDOW"))
        process_and_serve.add_child(Put(self))
        process_and_serve.add_child(HasItem(self, should_have=False))


        root.add_children([get_plate, place_plate, get_bun, get_lettuce, get_tomato, process_and_serve])
        
        return py_trees.trees.BehaviourTree(root)

    def _create_get_and_place_item_sequence(self, item_name, get_pos_name, place_pos_name=None, put_on_plate=True):
        if place_pos_name is None:
            place_pos_name = "plate_counter_pos"
            
        seq = py_trees.composites.Sequence(name=f"GetAndPlace_{item_name}", memory=True)
        seq.add_child(HasItem(self, should_have=False))
        seq.add_child(GoTo(self, get_pos_name))
        seq.add_child(Put(self))
        seq.add_child(HasItem(self, should_have=True, item_type=item_name))
        seq.add_child(GoTo(self, place_pos_name))
        seq.add_child(Put(self))
        if put_on_plate:
            seq.add_child(HasItem(self, should_have=False))
        return seq

    def _create_interaction_sequence(self, resulting_item, interaction_pos, initial_item_name):
        seq = py_trees.composites.Sequence(name=f"Interact_{initial_item_name}", memory=True)
        seq.add_child(HasItem(self, should_have=False))
        seq.add_child(GoTo(self, interaction_pos))
        seq.add_child(Interact(self))
        # After interaction, we should not be holding the item
        seq.add_child(HasItem(self, should_have=False))
        # Now pick up the resulting item
        seq.add_child(Put(self))
        seq.add_child(HasItem(self, should_have=True, item_type=resulting_item))
        return seq
        
    def _create_get_cut_and_place_item_sequence(self, item_name, get_pos_name, cut_pos_name):
        seq = py_trees.composites.Sequence(name=f"Process_{item_name}", memory=True)
        # Get item and place on cutting board
        seq.add_child(self._create_get_and_place_item_sequence(item_name, get_pos_name, cut_pos_name, put_on_plate=False))
        # Cut item
        chopped_item_name = f"Chopped{item_name}"
        if item_name == "Meat":
            chopped_item_name = "RawPatty"
        seq.add_child(self._create_interaction_sequence(chopped_item_name, cut_pos_name, item_name))
        # Get chopped item and place on plate
        seq.add_child(self._create_place_item_sequence(chopped_item_name, "plate_counter_pos"))
        return seq

    def _create_place_item_sequence(self, item_to_place, place_pos_name, final_placement=True):
        seq = py_trees.composites.Sequence(name=f"Place_{item_to_place}", memory=True)
        seq.add_child(HasItem(self, should_have=True, item_type=item_to_place))
        seq.add_child(GoTo(self, place_pos_name))
        seq.add_child(Put(self))
        if final_placement:
            seq.add_child(HasItem(self, should_have=False))
        return seq

    def parse_state(self, state):
        self.state_counters = state["counters"]
        for player in state["players"]:
            if player["id"] == self.own_player_id:
                self.current_agent_pos = np.array(player["pos"])
                self.held_item = player["holding"]
                if player["current_nearest_counter_id"]:
                    for counter in self.state_counters:
                        if counter["id"] == player["current_nearest_counter_id"]:
                            self.nearest_counter = counter
                            return
        self.nearest_counter = None

    async def handle_task(self, state):
        if self.current_task:
            t = self.current_task.task_type.upper()
            if t == Task.GOTO:
                await self.handle_task_goto(state)
            elif t == Task.INTERACT:
                await self.handle_task_interact(state)
            elif t in (Task.PUT, "PICKUP", "PUTDOWN", "DROPOFF"):
                await self.handle_task_put(state)
            else:
                self.finalize_current_task(TaskStatus.FAILED, f"Unknown task type: {t}")

    async def handle_task_put(self, state):
        if self.nearest_counter is None:
            self.finalize_current_task(TaskStatus.FAILED, "No counter nearby")
        else:
            await self._execute_action(action_type=ActionType.PICK_UP_DROP)
            self.finalize_current_task(TaskStatus.SUCCESS, "Picked up or dropped off")

    async def manage_tasks(self, state):
        self.behaviour_tree.tick()

if __name__ == "__main__":
    run_agent_from_args(BTAgent) 