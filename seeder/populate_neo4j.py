import json
import os
from neo4j import GraphDatabase

# ==========================================
# CONFIGURATION
# ==========================================
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
# ==========================================

def clear_database(tx):
    """Deletes all nodes and relationships to start fresh."""
    print("  > Clearing database...")
    tx.run("MATCH (n) DETACH DELETE n")

# ==========================================
# HELPER FUNCTIONS (Name Resolution)
# ==========================================
def get_readable_ability_name(key, abilities_data):
    if key in abilities_data and 'dname' in abilities_data[key]:
        return abilities_data[key]['dname']
    return key.replace('_', ' ').title()

def get_readable_item_name(key, items_data):
    if key in items_data and 'dname' in items_data[key]:
        return items_data[key]['dname']
    return key.replace('_', ' ').title()

def process_stat_value(value):
    """
    Parses a value that can be a single string/number or a list of them.
    Returns the minimum numerical value as a float/int, or 0 if invalid.
    """
    if value is None:
        return 0

    def to_float(v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    if isinstance(value, list):
        numerics = [to_float(v) for v in value]
        valid_nums = [n for n in numerics if n is not None]
        if valid_nums:
            return min(valid_nums)
        return 0

    result = to_float(value)
    return result if result is not None else 0

# ==========================================
# NODE CREATION FUNCTIONS
# ==========================================

def create_static_nodes(tx):
    print("  > Creating Static Nodes (Attributes, Roles, Types)...")

    # 1. Attributes
    for attr in ["Strength", "Agility", "Intelligence", "Universal"]:
        tx.run("MERGE (:Attribute {name: $name})", name=attr)

    # 2. Roles
    roles = ["Carry", "Support", "Nuker", "Disabler", "Jungler",
             "Durable", "Escape", "Pusher", "Initiator"]
    for role in roles:
        tx.run("MERGE (:Role {name: $name})", name=role)

    # 3. Attack Types
    for atk in ["Melee", "Ranged"]:
        tx.run("MERGE (:AttackType {name: $name})", name=atk)

def create_behavior_nodes(tx, parent_label, parent_name, behaviors):
    if not behaviors: return
    if isinstance(behaviors, str): behaviors = [behaviors]

    for b_name in behaviors:
        clean_name = b_name.strip()
        query = f"""
        MATCH (p:{parent_label} {{name: $p_name}})
        MERGE (b:Behavior {{name: $b_name}})
        MERGE (p)-[:HAS_BEHAVIOR]->(b)
        """
        tx.run(query, p_name=parent_name, b_name=clean_name)

def create_damage_type_node(tx, ability_name, dmg_type):
    if not dmg_type: return
    clean_name = str(dmg_type).strip().title()

    query = """
    MATCH (a:Ability {name: $a_name})
    MERGE (d:DamageType {name: $d_name})
    MERGE (a)-[:DEALS_DAMAGE_TYPE]->(d)
    """
    tx.run(query, a_name=ability_name, d_name=clean_name)

def create_ability(tx, key, data):
    readable_name = data.get('dname')
    if not readable_name: return

    # Pure Graph: No duplicate properties for behavior/dmgType
    query = """
    MERGE (a:Ability {name: $name})
    SET a.key = $key,
        a.description = $desc,
        a.manaCost = $mc,
        a.cooldown = $cd
    """
    tx.run(query,
           name=readable_name,
           key=key,
           desc=data.get('desc'),
           mc=process_stat_value(data.get('mc')),
           cd=process_stat_value(data.get('cd'))
    )

def create_item(tx, key, data):
    readable_name = data.get('dname')
    if not readable_name: return

    # Pure Graph: No duplicate property for behavior
    query = """
    MERGE (i:Item {name: $name})
    SET i.key = $key,
        i.cost = $cost,
        i.lore = $lore,
        i.notes = $notes,
        i.attributes = $attributes_json
    """
    tx.run(query,
           name=readable_name,
           key=key,
           cost=data.get('cost'),
           lore=data.get('lore'),
           notes=data.get('notes'),
           attributes_json=json.dumps(data.get('attrib', []))
    )

def create_hero(tx, data):
    readable_name = data['localized_name']

    # Pure Graph: No duplicate properties for Attr/Role/AttackType
    query = """
    MERGE (h:Hero {name: $name})
    SET h.internalId = $id,
        h.baseHealth = $base_health,
        h.baseMana = $base_mana,
        h.moveSpeed = $move_speed,
        h.legs = $legs,
        h.attackRange = $attack_range
    """
    tx.run(query,
           name=readable_name,
           id=data['name'],
           base_health=data.get('base_health'),
           base_mana=data.get('base_mana'),
           move_speed=data.get('move_speed'),
           legs=data.get('legs'),
           attack_range=data.get('attack_range')
    )

# ==========================================
# RELATIONSHIP LINKING FUNCTIONS
# ==========================================

def link_hero_details(tx, hero_data):
    hero_name = hero_data['localized_name']

    # 1. Link Primary Attribute
    attr_map = {'str': 'Strength', 'agi': 'Agility', 'int': 'Intelligence', 'all': 'Universal'}
    p_attr = hero_data.get('primary_attr')
    if p_attr in attr_map:
        tx.run("""
            MATCH (h:Hero {name: $h_name})
            MATCH (a:Attribute {name: $a_name})
            MERGE (h)-[:HAS_PRIMARY_ATTR]->(a)
        """, h_name=hero_name, a_name=attr_map[p_attr])

    # 2. Link Roles
    for role in hero_data.get('roles', []):
        tx.run("""
            MATCH (h:Hero {name: $h_name})
            MATCH (r:Role {name: $r_name})
            MERGE (h)-[:HAS_ROLE]->(r)
        """, h_name=hero_name, r_name=role)

    # 3. Link Attack Type
    atk_type = hero_data.get('attack_type')
    if atk_type:
        tx.run("""
            MATCH (h:Hero {name: $h_name})
            MATCH (at:AttackType {name: $at_name})
            MERGE (h)-[:HAS_ATTACK_TYPE]->(at)
        """, h_name=hero_name, at_name=atk_type)

def link_hero_skills(tx, hero_name, hero_spec, abilities_db):
    # 1. Abilities
    for idx, ab_key in enumerate(hero_spec.get('abilities', [])):
        if ab_key in ["generic_hidden", "dota_base_ability"]: continue

        ab_name = get_readable_ability_name(ab_key, abilities_db)
        is_ult = (idx == 5)
        rel_type = "HAS_ULTIMATE" if is_ult else "HAS_ABILITY"

        tx.run(f"""
            MATCH (h:Hero {{name: $h_name}})
            MATCH (a:Ability {{name: $a_name}})
            MERGE (h)-[:{rel_type}]->(a)
        """, h_name=hero_name, a_name=ab_name)

    # 2. Facets
    for facet in hero_spec.get('facets', []):
        facet_name = facet.get('title', facet['name'])

        tx.run("""
            MATCH (h:Hero {name: $h_name})
            MERGE (f:Facet {name: $f_name})
            SET f.description = $desc
            MERGE (h)-[:HAS_FACET]->(f)
        """, h_name=hero_name, f_name=facet_name, desc=facet.get('description'))

def link_item_components(tx, item_key, item_data, items_db):
    parent_name = item_data.get('dname')
    if not parent_name or not item_data.get('components'): return

    for comp_key in item_data['components']:
        if not comp_key: continue
        comp_name = get_readable_item_name(comp_key, items_db)

        tx.run("""
            MATCH (p:Item {name: $p_name})
            MATCH (c:Item {name: $c_name})
            MERGE (p)-[:REQUIRES_COMPONENT]->(c)
        """, p_name=parent_name, c_name=comp_name)


def link_item_abilities(tx, item_name, item_abilities):
    if not item_abilities: return

    for ability in item_abilities:
        ability_title = ability.get('title')
        if not ability_title: continue

        # Create the item ability node with description
        tx.run("""
            MERGE (a:ItemAbility {name: $name})
            SET a.description = $desc, a.type = $type
        """, name=ability_title, desc=ability.get('description'), type=ability.get('type'))

        # Link it to the item
        tx.run("""
            MATCH (i:Item {name: $item_name})
            MATCH (a:ItemAbility {name: $ability_name})
            MERGE (i)-[:HAS_ABILITY]->(a)
        """, item_name=item_name, ability_name=ability_title)


def main():
    print("Step 1: Loading JSON files...")
    files = ['heroes.json', 'abilities.json', 'items.json', 'hero_abilities.json']
    if not all(os.path.exists(f) for f in files):
        print(f"Error: Missing files. Ensure {files} are in the folder.")
        return

    with open('heroes.json', 'r', encoding='utf-8') as f: heroes = json.load(f)
    with open('abilities.json', 'r', encoding='utf-8') as f: abilities = json.load(f)
    with open('items.json', 'r', encoding='utf-8') as f: items = json.load(f)
    with open('hero_abilities.json', 'r', encoding='utf-8') as f: hero_abilities = json.load(f)

    print("Step 2: Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=AUTH)

    with driver.session() as session:
        # A. Clear Old Data
        session.execute_write(clear_database)

        # B. Create Static Nodes
        session.execute_write(create_static_nodes)

        # C. Create Abilities
        print("  > Processing Abilities...")
        for key, data in abilities.items():
            if key not in ["dota_base_ability", "generic_hidden"]:
                # Base Node
                session.execute_write(create_ability, key, data)

                readable = data.get('dname')
                if readable:
                    # Link Behavior
                    if 'behavior' in data:
                        session.execute_write(create_behavior_nodes, "Ability", readable, data['behavior'])
                    # Link Damage Type
                    if 'dmg_type' in data:
                        session.execute_write(create_damage_type_node, readable, data['dmg_type'])

        # D. Create Items
        print("  > Processing Items...")
        for key, data in items.items():
            # Base Node
            session.execute_write(create_item, key, data)

            readable = data.get('dname')
            if readable:
                # Link Behavior
                if 'behavior' in data:
                    session.execute_write(create_behavior_nodes, "Item", readable, data['behavior'])
                # Link Abilities
                if 'abilities' in data:
                    session.execute_write(link_item_abilities, readable, data['abilities'])

        print("  > Linking Item Recipes...")
        for key, data in items.items():
            session.execute_write(link_item_components, key, data, items)

        # E. Create Heroes & Link Everything
        print("  > Processing Heroes...")
        for hero_id, data in heroes.items():
            internal_name = data['name']
            readable_name = data['localized_name']

            # Base Node
            session.execute_write(create_hero, data)

            # Link Attributes, Roles, AttackTypes
            session.execute_write(link_hero_details, data)

            # Link Skills (Abilities & Facets only)
            if internal_name in hero_abilities:
                session.execute_write(link_hero_skills,
                                      readable_name,
                                      hero_abilities[internal_name],
                                      abilities)

    driver.close()
    print("\n[SUCCESS] Neo4j population complete!")

if __name__ == "__main__":
    main()
