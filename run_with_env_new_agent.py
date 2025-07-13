import json
from datetime import timedelta

from cooperative_cuisine import ROOT_DIR
from cooperative_cuisine.environment import Environment

from cocu_base_agents.new_agent.bt_agent import BTAgent

if __name__ == "__main__":
    env = Environment(
        env_config=ROOT_DIR / "configs" / "environment_config.yaml",
        layout_config=ROOT_DIR / "configs" / "layouts" / "basic.layout",
        item_info=ROOT_DIR / "configs" / "item_info.yaml"
    )
    env.add_player("0")
    
    env.env_time_end = env.env_time + timedelta(
        seconds=200 # Increased time to allow burger completion
    )
    
    recipe_graphs = env.recipe_validation.get_recipe_graphs()
    
    agent = BTAgent()
    agent.own_player_id = "0"
    agent.run_via_env_reference(env)