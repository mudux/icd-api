import json
import os
from pdb import set_trace
from dotenv import load_dotenv, find_dotenv
from icd_api.icd_api import Api

# set_trace()

load_dotenv(find_dotenv())

api = Api.from_environment()
api.get_linearization("mms", "2024-01")


data_folder = os.path.join(os.path.dirname(__file__), "data")
entities_folder = os.path.join(data_folder, "entities")
os.makedirs(entities_folder, exist_ok=True)

root_entity_id = "455013390"  # highest level ICD Entity 448895267  ICD 11 455013390 # smaller entity for testing: 1301318821; 1208497819
# 1435254666

# ALL ENTITIES
# root_ids = {
#     "1249056269": "try1.json"
# }
root_ids = {
    "455013390": "ALL_ICD11_LINENT.json"
}
# ALL CHAPTER ROOT ENTITIES (CHAPTER 1-26)
# root_ids = {
#     "1435254666": "stem_codes_1435254666.json",
#     "1630407678": "stem_codes_1630407678.json",
#     "1766440644": "stem_codes_1766440644.json",
#     "1954798891": "stem_codes_1954798891.json",
#     "21500692": "stem_codes_21500692.json",
#     "334423054": "stem_codes_334423054.json",
#     "274880002": "stem_codes_274880002.json",
#     "1296093776": "stem_codes_1296093776.json",
#     "868865918": "stem_codes_868865918.json",
#     "1218729044": "stem_codes_1218729044.json",
#     "426429380": "stem_codes_426429380.json",
#     "197934298": "stem_codes_197934298.json",
#     "1256772020": "stem_codes_1256772020.json",
#     "1639304259": "stem_codes_1639304259.json",
#     "1473673350": "stem_codes_1473673350.json",
#     "30659757": "stem_codes_30659757.json",
#     "577470983": "stem_codes_577470983.json",
#     "714000734": "stem_codes_714000734.json",
#     "1306203631": "stem_codes_1306203631.json",
#     "223744320": "stem_codes_223744320.json",
#     "1843895818": "stem_codes_1843895818.json",
#     "435227771": "stem_codes_435227771.json",
#     "850137482": "stem_codes_850137482.json",
#     "1249056269": "stem_codes_1249056269.json",
#     "1596590595": "stem_codes_1596590595.json",
#     "718687701": "stem_codes_718687701.json",
#     }
lin_entities = []

def get_entities_recurse(entities: list,
                         entity_id: str,
                         nested_output: bool,
                         exclude_duplicates: bool = False):
    """
    get everything for an entity:
    """
    icd_entity = api.get_entity(entity_id=entity_id)

    if nested_output:
        icd_entity.child_entities = []

    if exclude_duplicates:
        existing = [e for e in entities if e.entity_id == entity_id]
        if existing:
            # we already processed this entity and by extension its children
            # breakpoint()
            return entities
    lin_entity = api.get_linearization_entity(entity_id=entity_id)
    # breakpoint()
    # print(icd_entity.__dict__)

    entities.append(icd_entity)
    if lin_entity:
        lin_entities.append(lin_entity.to_dict())

    for child_id in icd_entity.child_ids:
        existing = next(iter([e for e in entities if e.entity_id == child_id]), None)
        if existing is None:
            if nested_output:
                recurse_child_entities = icd_entity.child_entities
            else:
                recurse_child_entities = entities
            get_entities_recurse(entities=recurse_child_entities,
                                 entity_id=child_id,
                                 nested_output=nested_output,
                                 exclude_duplicates=exclude_duplicates)
    return entities


def get_all_entities():
    # build the same treeview that's on the side panel here:
    # https://icd.who.int/dev11/f/en#/http%3a%2f%2fid.who.int%2ficd%2fentity%1920852714
    # split up stem codes from extension codes
    # this takes a while if the root node is high up enough
    # if you can run against your own local instance, it's much faster
    # write each chapter to its own file
    for child_id, target_file_name in root_ids.items():
        target_file_path = os.path.join(entities_folder, target_file_name)
        target_file_path2 = os.path.join(entities_folder, "lin_"+target_file_name)
        if not os.path.exists(target_file_path):
            print(f"get_all_entities - {child_id}")
            grandchild_entities = get_entities_recurse(
                entities=[],
                entity_id=child_id,
                nested_output=False,
                exclude_duplicates=True
            )

            # with open(target_file_path, "w") as file:
            #     data = json.dumps(grandchild_entities, default=lambda x: x.to_dict(), indent=4)
            #     file.write(data)
            with open(target_file_path2, "w") as file:
                data = json.dumps(lin_entities, default=lambda x: x.to_dict(), indent=4)
                file.write(data)
        else:
            print(f"get_all_entities - {child_id}.json already exists")


def dedupe_entities(entities: list):
    """
    get_ancestors tries to remove duplicates but sometimes two recurson paths have the same entity,
    and they don't know about each other
    """
    distinct_ids = set(e["entity_id"] for e in entities)
    if len(distinct_ids) == len(entities):
        print("bypassing dedupe_entities - no dupes found")
        return entities

    print("dedupe_entities")
    deduped = []
    for idx, entity in enumerate(entities):
        if idx % 1000 == 0:
            print(f"dedupe_entities - {idx}")
        if entity["entity_id"] not in [e["entity_id"] for e in deduped]:
            deduped.append(entity)
    return deduped


def load_entities() -> dict or None:
    entities = {}
    for k, v in root_ids.items():
        file_path = os.path.join(entities_folder, v)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf8") as file:
                cached_data = json.loads(file.read())
                if cached_data is None:
                    return None
                entities[k] = cached_data
    return entities


def get_flattened_entity_ids() -> list[dict]:
    entities_dicts = load_entities()
    entities = []
    for k, v in entities_dicts.items():
        existing_ids = [e["entity_id"] for e in entities]
        new_entities = [e for e in v if e["entity_id"] not in existing_ids]
        entities.extend(new_entities)
    return entities


def get_distinct_entity_ids() -> list[str]:
    eids_path = os.path.join(data_folder, "entity_ids.txt")
    if os.path.exists(eids_path):
        with open(eids_path, "r", encoding="utf8") as eids_file:
            eids = eids_file.readlines()
            eids = [eid.rstrip("\n") for eid in eids]
            return eids

    entities_dicts = get_flattened_entity_ids()
    entity_ids = [e["entity_id"] for e in entities_dicts]

    with open(eids_path, "w", encoding="utf8") as target_file:
        target_file.writelines([f"{eid}\n" for eid in entity_ids])

    return entity_ids


if __name__ == '__main__':
    # # to populate ancestors json files (one json per top-level entity)
    get_all_entities()

    # # to load existing ancestors into one json file (may include duplicates)
    # eids = get_distinct_entity_ids()
    # print(len(eids))
