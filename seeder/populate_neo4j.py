import json
import os
from neo4j import GraphDatabase

# --- CONFIGURATION ---
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
# ---------------------

def clear_database(tx):
    """Deletes all nodes and relationships to start fresh."""
    tx.run("MATCH (n) DETACH DELETE n")

def create_hero(tx, hero_id, data):
    """Creates a Hero node with properties."""
    query = """
    MERGE (h:Hero {name: $name})
    SET h.id = $id,
        h.localizedName = $localized_name,
        h.primaryAttr = $primary_attr,
        h.attackType = $attack_type,
        h.roles = $roles,
        h.img = $img,
        h.baseHealth = $base_health,
        h.baseMana = $base_mana,
        h.baseArmor = $base_armor,
        h.moveSpeed = $move_speed
    """
    tx.run(query, 
           name=data['name'], 
           id=hero_id,
           localized_name=data.get('localized_name'),
           primary_attr=data.get('primary_attr'),
           attack_type=data.get('attack_type'),
           roles=data.get('roles', []),
           img=f"https://api.opendota.com{data.get('img', '')}",
           base_health=data.get('base_health'),
           base_mana=data.get('base_mana'),
           base_armor=data.get('base_armor'),
           move_speed=data.get('move_speed')
    )

def create_ability(tx, ability_key, data):
    """Creates an Ability node."""
    if not data.get('dname'): return # Skip abilities without names
    
    query = """
    MERGE (a:Ability {key: $key})
    SET a.name = $dname,
        a.description = $desc,
        a.behavior = $behavior,
        a.dmgType = $dmg_type,
        a.manaCost = $mc,
        a.cooldown = $cd,
        a.img = $img
    """
    # behaviors often come as list or string, normalize to list
    behaviors = data.get('behavior', [])
    if isinstance(behaviors, str): behaviors = [behaviors]

    tx.run(query,
           key=ability_key,
           dname=data.get('dname'),
           desc=data.get('desc'),
           behavior=behaviors,
           dmg_type=data.get('dmg_type'),
           mc=data.get('mc'),
           cd=data.get('cd'),
           img=f"https://api.opendota.com{data.get('img', '')}"
    )

def create_item(tx, item_key, data):
    """Creates an Item node."""
    query = """
    MERGE (i:Item {key: $key})
    SET i.name = $dname,
        i.cost = $cost,
        i.lore = $lore,
        i.notes = $notes,
        i.tier = $tier
    """
    tx.run(query,
           key=item_key,
           dname=data.get('dname', item_key), # Fallback to key if no dname
           cost=data.get('cost'),
           lore=data.get('lore'),
           notes=data.get('notes'),
           tier=data.get('tier')
    )

def link_hero_ability(tx, hero_name, ability_name, is_ultimate=False):
    """Creates a relationship: (:Hero)-[:HAS_ABILITY]->(:Ability)"""
    rel_type = "HAS_ULTIMATE" if is_ultimate else "HAS_ABILITY"
    query = f"""
    MATCH (h:Hero {{name: $hero_name}})
    MATCH (a:Ability {{key: $ability_key}})
    MERGE (h)-[:{rel_type}]->(a)
    """
    tx.run(query, hero_name=hero_name, ability_key=ability_name)

def link_item_component(tx, parent_item_key, component_key):
    """Creates a relationship: (:Item)-[:REQUIRES_COMPONENT]->(:Item)"""
    query = """
    MATCH (parent:Item {key: $parent_key})
    MATCH (comp:Item {key: $comp_key})
    MERGE (parent)-[:REQUIRES_COMPONENT]->(comp)
    """
    tx.run(query, parent_key=parent_item_key, comp_key=component_key)

def main():
    # 1. Load Data
    print("Loading JSON files...")
    try:
        with open('heroes.json', 'r', encoding='utf-8') as f: heroes = json.load(f)
        with open('abilities.json', 'r', encoding='utf-8') as f: abilities = json.load(f)
        with open('items.json', 'r', encoding='utf-8') as f: items = json.load(f)
        with open('hero_abilities.json', 'r', encoding='utf-8') as f: hero_abilities = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure JSON files are in the same directory.")
        return

    # 2. Connect to Neo4j
    driver = GraphDatabase.driver(URI, auth=AUTH)

    with driver.session() as session:
        print("Clearing database...")
        session.execute_write(clear_database)

        # 3. Create Abilities (Independent)
        print("Creating Abilities...")
        for key, data in abilities.items():
            if key not in ["dota_base_ability", "generic_hidden"]:
                session.execute_write(create_ability, key, data)

        # 4. Create Items (Independent)
        print("Creating Items...")
        for key, data in items.items():
            session.execute_write(create_item, key, data)
        
        # Link Item Components (after all items exist)
        print("Linking Item Components...")
        for key, data in items.items():
            if data.get('components'):
                for comp in data['components']:
                    session.execute_write(link_item_component, key, comp)

        # 5. Create Heroes and Link to Abilities
        print("Creating Heroes & Links...")
        for hero_id, data in heroes.items():
            hero_name = data['name']
            session.execute_write(create_hero, hero_id, data)

            # Link Abilities
            if hero_name in hero_abilities:
                spec = hero_abilities[hero_name]
                for idx, ab_name in enumerate(spec.get('abilities', [])):
                    if ab_name != "generic_hidden":
                        is_ult = (idx == 5) # Usually index 5 is ult in standard dota files
                        session.execute_write(link_hero_ability, hero_name, ab_name, is_ult)

    driver.close()
    print("Done! Neo4j populated.")

if __name__ == "__main__":
    main()